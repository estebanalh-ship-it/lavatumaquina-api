from functools import wraps
import os
import json
import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from sqlalchemy import text
from database import engine
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.drawing.image import Image as ExcelImage 
from flask import send_file

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Por favor, inicia sesión para acceder a esta página.', 'warning')
            return redirect(url_for('admin_bp.login'))
        return f(*args, **kwargs)
    return decorated_function

admin_bp = Blueprint('admin', __name__,
                     template_folder='templates',
                     static_folder='static',
                     static_url_path='/admin/static')

@admin_bp.route('/')
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        EMAIL_ADMIN = os.getenv('EMAIL_ADMIN')
        PASSWORD_ADMIN = os.getenv('PASSWORD_ADMIN')

        print(f"DEBUG - EMAIL_ADMIN: '{EMAIL_ADMIN}'")
        print(f"DEBUG - PASSWORD_ADMIN: '{PASSWORD_ADMIN}'")
        print(f"DEBUG - Input email: '{email}', password: '{password}'")

        if email == EMAIL_ADMIN and password == PASSWORD_ADMIN:
            session['admin_logged_in'] = True
            flash('¡Inicio de sesión exitoso!', 'success')
            return redirect(url_for('admin.control_principal'))

        flash('Credenciales inválidas', 'danger')
        return render_template('login.html', error='Credenciales inválidas')

    return render_template('login.html')

@admin_bp.route('/control_principal')
@login_required
def control_principal():
    with engine.connect() as conn:
        total_agendas = conn.execute(text("SELECT COUNT(*) AS c FROM agendas")).scalar()
        total_clientes = conn.execute(text("SELECT COUNT(*) AS c FROM clientes")).scalar()
        clientes = conn.execute(text("""
            SELECT nombre, telefono, email
            FROM clientes
            ORDER BY id_cliente DESC
        """)).mappings().all()
        agendas = conn.execute(text("""
            SELECT
                c.nombre AS cliente,
                a.fecha_agenda AS fecha,
                s.nombre AS servicio,
                s.duracion_min AS duracion
            FROM agendas AS a
            INNER JOIN clientes AS c ON c.id_cliente = a.id_cliente
            INNER JOIN servicios AS s ON s.id_servicio = a.id_servicio
            ORDER BY a.id_agenda DESC
        """)).mappings().all()

    return render_template(
        'control_principal.html',
        total_agendas=total_agendas,
        total_clientes=total_clientes,
        clientes=clientes,
        agendas=agendas
    )
@admin_bp.route('/agenda_manual', methods=['GET', 'POST'])
@login_required
def agenda_manual():
    if request.method == 'POST':
        id_cliente = request.form['id_cliente']
        id_servicio = request.form['id_servicio']
        fecha_agenda = request.form['fecha_agenda']
        hora_agenda = request.form['hora_agenda']

        try:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO agendas (id_cliente, id_servicio, fecha_agenda, estado, fecha_creacion)
                    VALUES (:id_cliente, :id_servicio, :fecha_agenda, 'pendiente', NOW())
                """), {
                    'id_cliente': id_cliente,
                    'id_servicio': id_servicio,
                    'fecha_agenda': f"{fecha_agenda} {hora_agenda}"
                })
            flash('Agenda creada correctamente', 'success')
            return redirect(url_for('admin.agenda_manual'))  # Limpia el formulario
        except Exception as e:
            flash(f'Error al crear agenda: {e}', 'danger')

    # Consulta para llenar selects
    with engine.connect() as conn:
        clientes = conn.execute(text("SELECT id_cliente, nombre FROM clientes")).mappings().all()
        servicios = conn.execute(text("SELECT id_servicio, nombre, tipo_servicio FROM servicios")).mappings().all()

    return render_template('agenda_manual.html', clientes=clientes, servicios=servicios)

@admin_bp.route('/nuevo_cliente', methods=['GET', 'POST'])
@login_required
def nuevo_cliente():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        rut = request.form.get('rut')
        email = request.form.get('email')
        telefono = request.form.get('telefono')

        if not nombre or not rut or not email or not telefono:
            flash('Por favor completa los campos obligatorios.', 'danger')
            return redirect(url_for('admin.nuevo_cliente'))

        try:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO clientes (rut, nombre, apellido, email, telefono, fecha_registro, activo)
                    VALUES (:rut, :nombre, :apellido, :email, :telefono, NOW(), 1)
                """), {
                    'rut': rut,
                    'nombre': nombre,
                    'apellido': apellido,
                    'email': email,
                    'telefono': telefono
                })

            flash('Cliente agregado correctamente.', 'success')
            return redirect(url_for('admin.nuevo_cliente'))
        except Exception as e:
            flash(f'Error al agregar cliente: {e}', 'danger')
            return redirect(url_for('admin.nuevo_cliente'))

    return render_template('nuevo_cliente.html')

@admin_bp.route('/bloqueo_agenda', methods=['GET', 'POST'])
@login_required
def bloqueo_agenda():
    if request.method == 'POST':
        fecha_bloqueo = request.form.get('fecha_bloqueo')
        bandas = request.form.getlist('bandas')  # Obtiene todas las bandas seleccionadas
        motivo = request.form.get('motivo', 'Bloqueo por fuerza mayor')

        # Validación
        if not bandas:
            flash('⚠️ Debes seleccionar al menos una banda horaria', 'warning')
            return redirect(url_for('admin.bloqueo_agenda'))

        try:
            with engine.begin() as conn:
                # Mapeo de tipos a id_servicio (ajusta estos IDs según tu base de datos)
                tipo_a_servicio = {
                    'lavado': 1,      # Reemplaza con el ID real de servicios de lavado
                    'mecanico': 11,   # ID del servicio mecánico
                    'tapiz': 13        # ID del servicio de tapiz (ajusta según tu BD)
                }

                contador_bloqueos = 0

                # Procesar cada banda seleccionada
                for banda_completa in bandas:
                    # Separar tipo y banda: "lavado|09:00-10:00"
                    tipo, banda = banda_completa.split('|')
                    hora_inicio = banda.split('-')[0]  # Obtiene "09:00" de "09:00-10:00"

                    # Obtener el id_servicio correspondiente
                    id_servicio = tipo_a_servicio.get(tipo, 1)

                    fecha_hora_completa = f"{fecha_bloqueo} {hora_inicio}"

                    # INSERT sin el campo 'observaciones'
                    conn.execute(text("""
                        INSERT INTO agendas
                        (id_cliente, id_servicio, fecha_agenda, estado, fecha_creacion)
                        VALUES (NULL, :id_servicio, :fecha_agenda, 'bloqueado', NOW())
                    """), {
                        'id_servicio': id_servicio,
                        'fecha_agenda': fecha_hora_completa
                    })

                    contador_bloqueos += 1

                flash(f'✅ Se bloquearon {contador_bloqueos} bandas horarias correctamente. Motivo: {motivo}', 'success')
                return redirect(url_for('admin.bloqueo_agenda'))

        except Exception as e:
            flash(f'❌ Error al crear bloqueos: {e}', 'danger')

    # GET: solo mostramos el formulario
    return render_template('bloqueo_agenda.html')

@admin_bp.route('/gestion_precios', methods=['GET', 'POST'])
@login_required
def gestion_precios():
    if request.method == 'POST':
        id_servicio = request.form.get('id_servicio')
        precio_nuevo = request.form.get('precio_nuevo')

        try:
            with engine.begin() as conn:
                # Actualizar el precio del servicio
                conn.execute(text("""
                    UPDATE servicios
                    SET precio = :precio_nuevo
                    WHERE id_servicio = :id_servicio
                """), {
                    'precio_nuevo': precio_nuevo,
                    'id_servicio': id_servicio
                })

                # Obtener nombre del servicio para el mensaje
                servicio = conn.execute(text("""
                    SELECT nombre FROM servicios WHERE id_servicio = :id_servicio
                """), {'id_servicio': id_servicio}).fetchone()

                flash(f'✅ Precio actualizado correctamente para {servicio[0]}', 'success')
                return redirect(url_for('admin.gestion_precios'))

        except Exception as e:
            flash(f'❌ Error al actualizar precio: {e}', 'danger')

    # GET: Cargar todos los servicios con sus precios actuales
    with engine.connect() as conn:
        servicios = conn.execute(text("""
            SELECT id_servicio, nombre, tipo_servicio, precio
            FROM servicios
            ORDER BY tipo_servicio, nombre
        """)).mappings().all()

    return render_template('gestion_precios.html', servicios=servicios)
# --- MÓDULO DE COTIZACIONES ---
@admin_bp.route('/cotizaciones')
@login_required
def lista_cotizaciones():
    """Muestra la tabla con el historial de cotizaciones."""
    with engine.connect() as conn:
        # Traemos solo los datos resumen, no el detalle JSON pesado
        cotizaciones = conn.execute(text("""
            SELECT id, fecha, nombre_cliente, rut_cliente, total_final, estado 
            FROM cotizaciones 
            ORDER BY id DESC
        """)).mappings().all()
    
    return render_template('cotizaciones_lista.html', cotizaciones=cotizaciones)

@admin_bp.route('/nueva_cotizacion', methods=['GET', 'POST'])
@login_required
def nueva_cotizacion():
    """Formulario para crear y guardar una nueva cotización."""
    if request.method == 'POST':
        # 1. Datos del Cliente
        rut = request.form.get('rut')
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        telefono = request.form.get('telefono')

        # 2. Datos de los Ítems (Productos)
        # En el HTML usaremos inputs con nombres como name="items_producto[]"
        # .getlist() nos permite recuperar todos los valores en una lista
        productos = request.form.getlist('items_producto[]')
        cantidades = request.form.getlist('items_cantidad[]')
        precios = request.form.getlist('items_precio[]')

        # 3. Procesar los datos y calcular totales (Backend es más seguro que JS)
        lista_items = []
        total_neto = 0

        # Zip une las tres listas para recorrerlas juntas (fila por fila)
        for prod, cant, prec in zip(productos, cantidades, precios):
            if prod.strip(): # Solo si hay nombre de producto
                c = float(cant) if cant else 0
                p = float(prec) if prec else 0
                subtotal = c * p
                
                lista_items.append({
                    "producto": prod,
                    "cantidad": c,
                    "precio_unitario": p,
                    "subtotal": subtotal
                })
                total_neto += subtotal

        iva = total_neto * 0.19
        total_final = total_neto + iva
        
        # Convertimos la lista de Python a Texto JSON para guardarla en BD
        items_json = json.dumps(lista_items)

        try:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO cotizaciones 
                    (rut_cliente, nombre_cliente, email_cliente, telefono_cliente, 
                     total_neto, iva, total_final, detalle_items, fecha)
                    VALUES (:rut, :nombre, :email, :tel, :neto, :iva, :final, :items, NOW())
                """), {
                    'rut': rut, 'nombre': nombre, 'email': email, 'tel': telefono,
                    'neto': total_neto, 'iva': iva, 'final': total_final, 'items': items_json
                })
            
            flash('✅ Cotización creada con éxito.', 'success')
            return redirect(url_for('admin.lista_cotizaciones'))

        except Exception as e:
            flash(f'❌ Error al guardar cotización: {e}', 'danger')

    return render_template('cotizaciones_nueva.html')

@admin_bp.route('/descargar_cotizacion/<int:id_cotizacion>')
@login_required
def descargar_cotizacion(id_cotizacion):
    """Genera y descarga el archivo Excel de una cotización específica."""
    
    try:
        # 1. Buscar datos en la BD
        with engine.connect() as conn:
            cot = conn.execute(text("SELECT * FROM cotizaciones WHERE id = :id"), 
                               {'id': id_cotizacion}).mappings().fetchone()
        
        if not cot:
            flash('Cotización no encontrada', 'danger')
            return redirect(url_for('admin.lista_cotizaciones'))

        # 2. Recuperar items del JSON
        items = json.loads(cot['detalle_items'])

        # 3. Crear Excel
        wb = Workbook()
        ws = wb.active
        ws.title = f"Cotizacion_{cot['id']}"

        # Encabezado Empresa
        ws['A1'] = "COMERCIAL Y SERVICIOS INTEGRALES LTM SPA"
        ws['A1'].font = Font(bold=True, size=14)
        ws.merge_cells('A1:E1')
        ws['A1'].alignment = Alignment(horizontal='center')

        ws['A2'] = "RUT: 78.290.357-8"
        ws.merge_cells('A2:E2')
        ws['A2'].alignment = Alignment(horizontal='center')

        ws['A3'] = "Tel: +569 36473898"
        ws.merge_cells('A3:E3')
        ws['A3'].alignment = Alignment(horizontal='center')

        ws['A4'] = "Emails: lavatumaquina.rengo@gmail.com | vicentealvarado987@gmail.com"
        ws.merge_cells('A4:E4')
        ws['A4'].alignment = Alignment(horizontal='center')

        ws['A5'] = "Dirección: Elicura #375, Rengo, Sexta Región, Chile."
        ws.merge_cells('A5:E5')
        ws['A5'].alignment = Alignment(horizontal='center')

        # --- COMIENZO COTIZACION ---
        ws['A7'] = "COTIZACIÓN DE SERVICIOS"
        ws['A7'].font = Font(bold=True, size=16)
        ws.merge_cells('A7:E7')
        ws['A7'].alignment = Alignment(horizontal='center')

        # Datos del Cliente (bajamos desde fila 9)
        ws['A9']  = "Cliente:";  ws['B9']  = cot['nombre_cliente'] or ""
        ws['A10'] = "RUT:";      ws['B10'] = cot['rut_cliente'] or ""
        ws['A11'] = "Fecha:";    ws['B11'] = str(cot['fecha'])
        ws['C9']  = "Email:";    ws['D9']  = cot['email_cliente'] or ""
        ws['C10'] = "Teléfono:"; ws['D10'] = cot.get('telefono_cliente', '') or ""

        # Encabezados de Tabla
        headers = ["Descripción / Servicio", "Cantidad", "Precio Neto", "IVA (19%)", "Total"]
        ws.append([])       # Espacio (fila 12)
        ws.append(headers)  # Headers (fila 13)
        
        # Capturar la fila donde quedaron los headers
        header_row = ws.max_row  # <-- ✅ Esto guarda el número de fila donde están los encabezados
        
        # Estilo para cabecera
        for col_num in range(1, 6):
            cell = ws.cell(row=header_row, column=col_num)
            cell.font = Font(bold=True)
        for item in items:
            # Asegurar que sean números para evitar error matemático
            cant = float(item.get('cantidad', 0))
            precio = float(item.get('precio_unitario', 0))
            subtotal = float(item.get('subtotal', 0))
            
            iva_linea = subtotal * 0.19
            total_linea = subtotal * 1.19
            
            ws.append([
                item.get('producto', ''), 
                cant, 
                precio,
                iva_linea,
                total_linea
            ])
            current_row = ws.max_row # La fila que acabas de escribir
            # Aplicar formato #,##0 a Precio(C), IVA(D) y Total(E)
            ws.cell(row=current_row, column=3).number_format = '#,##0'
            ws.cell(row=current_row, column=4).number_format = '#,##0'
            ws.cell(row=current_row, column=5).number_format = '#,##0'
        # Totales Finales
        thin_border = Border(
            left=Side(style='thin', color='000000'),
            right=Side(style='thin', color='000000'),
            top=Side(style='thin', color='000000'),
            bottom=Side(style='thin', color='000000')
        )
        # La última fila con datos de ítems es la fila actual máxima
        last_item_row = ws.max_row
        # Recorremos desde la fila de encabezados hasta la última de ítems
        for row in range(header_row, last_item_row + 1):
            for col in range(1, 6):  # Columnas A(1) a E(5)
                ws.cell(row=row, column=col).border = thin_border
          
        ws.append([]) # Espacio
        ws.append(["", "", "Total Neto:", int(float(cot['total_neto'] or 0))])
        ws.append(["", "", "IVA (19%):", int(float(cot['iva'] or 0))])
        ws.append(["", "", "TOTAL FINAL:", int(float(cot['total_final'] or 0))])
        # Negrita en totales
        ult_fila = ws.max_row
        for r in range(ult_fila-2, ult_fila+1):
            ws.cell(row=r, column=3).font = Font(bold=True) # Columna C ("Total Neto:")
            ws.cell(row=r, column=4).number_format = '#,##0' # Columna D (El valor)
        # --- AUTO-AJUSTE DE COLUMNAS (Versión Segura) ---
        # Definimos anchos mínimos para que no quede muy flaco
        column_widths = {'A': 30, 'B': 18, 'C': 15, 'D': 15, 'E': 15}

        for col_letter, width in column_widths.items():
            ws.column_dimensions[col_letter].width = width

        try:
            from flask import current_app
            img_path = os.path.join(current_app.root_path, 'static', 'cot.png')
            print(f"Buscando imagen en: {img_path}")
            
            img =ExcelImage(img_path)
            img.height = 110
            ratio = img.width / img.height
            img.width = 100 * ratio
            img.anchor = f'A{ws.max_row +1}'
            ws.add_image(img)
        except FileNotFoundError:
            print(f"⚠️Imagen no encontrada REVISALO!⚠️: {img_path}")
        except Exception as e:
            print(f"⚠️ Error insertando imagen: {e}")
            
        # 4. Guardar y Enviar
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        nombre_cliente_safe = str(cot['nombre_cliente']).replace(' ', '_')
        nombre_archivo = f"Cotizacion_{cot['id']}_{nombre_cliente_safe}.xlsx"
        
        return send_file(
            buffer, 
            as_attachment=True, 
            download_name=nombre_archivo, 
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        print(f"ERROR EXCEL: {e}") # Esto saldrá en tu consola de error log
        flash(f'Error al generar el Excel: {str(e)}', 'danger')
        return redirect(url_for('admin.lista_cotizaciones'))

@admin_bp.route('/stock_productos')
@login_required
def stock_productos():
    return render_template('stock_productos.html')

@admin_bp.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('admin_bp.login'))
