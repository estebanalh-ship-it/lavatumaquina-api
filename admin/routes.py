from functools import wraps
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from sqlalchemy import text
from database import engine

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