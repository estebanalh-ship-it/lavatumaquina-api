from flask import Flask, request, jsonify, redirect, url_for, render_template
import mysql.connector
import os
from flask_mail import Mail, Message
from database import db_config
from dotenv import load_dotenv
from admin import admin_bp
load_dotenv('/home/Lavatumaquina01/proyecto01/.env')
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = ('Lava Tu Maquina', os.environ.get("MAIL_USERNAME"))
mail = Mail(app)
app.register_blueprint(admin_bp, url_prefix='/admin')

def enviar_correos_confirmacion(datos_cita):
    try:
        asunto_cliente = "Confirmación de tu cita en Lava Tu Maquina"
        msg_cliente = Message(asunto_cliente, recipients=[datos_cita['email_cliente']])
        msg_cliente.html = f"""<h3>Hola {datos_cita['nombre_cliente']},</h3><p>Tu cita ha sido confirmada con éxito.</p><p><b>Detalles de la reserva:</b></p><ul><li><b>Servicio:</b> {datos_cita['nombre_servicio']}</li><li><b>Fecha:</b> {datos_cita['fecha']}</li><li><b>Hora:</b> {datos_cita['hora']}</li></ul><p>¡Te esperamos!</p><p>Atentamente,<br>El equipo de <b>Lava Tu Maquina</b></p>"""
        mail.send(msg_cliente)
        asunto_empresa = f"Nueva Cita Agendada: {datos_cita['nombre_servicio']} para {datos_cita['nombre_cliente']}"
        msg_empresa = Message(asunto_empresa, recipients=['lavatumaquina.rengo@gmail.com'])
        msg_empresa.html = f"""<h3>Se ha agendado una nueva cita:</h3><ul><li><b>Cliente:</b> {datos_cita['nombre_cliente']}</li><li><b>Email:</b> {datos_cita['email_cliente']}</li><li><b>Teléfono:</b> {datos_cita['telefono']}</li><li><b>Patente:</b> {datos_cita['patente']}</li><li><b>Servicio:</b> {datos_cita['nombre_servicio']}</li><li><b>Fecha:</b> {datos_cita['fecha']}</li><li><b>Hora:</b> {datos_cita['hora']}</li></ul>"""
        mail.send(msg_empresa)
        print("¡Correos de confirmación enviados exitosamente!")
    except Exception as e:
        print(f"ERROR AL ENVIAR CORREOS: {e}")

BANDAS_HORARIAS_LAVADOS = ['09:00', '11:00', '15:00', '16:00']
BANDAS_HORARIAS_MECANICO = ['11:00', '12:00']
BANDAS_HORARIAS_LAVADOTAPIZ = ['11:00', '12:00']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lavado', methods=['GET', 'POST'])
def lavado():
    if request.method == 'POST':
        try:
            rut = request.form['rut']
            nombre = request.form['nombre']
            email = request.form['email']
            telefono = str(request.form.get('telefono', ''))
            if not telefono.startswith('+569'):
                telefono = '+569' + telefono.replace('+569', '')
            patente = request.form['patente']
            id_servicio = request.form['id_servicio']
            fecha_agenda = request.form['fecha'] + ' ' + request.form['hora']

            if not id_servicio or not id_servicio.isdigit():
                return jsonify({'error': 'Seleccione un servicio válido'}), 400

            conexion = mysql.connector.connect(**db_config)
            cursor = conexion.cursor(dictionary=True)

            # 1. Gestionar Cliente
            cursor.execute("SELECT * FROM clientes WHERE rut = %s", (rut,))
            cliente_existente = cursor.fetchone()

            if cliente_existente:
                id_cliente = cliente_existente['id_cliente']
            else:
                cursor.execute(
                    "INSERT INTO clientes (rut, nombre, email, telefono) VALUES (%s, %s, %s, %s)",
                    (rut, nombre, email, telefono)
                )
                id_cliente = cursor.lastrowid

            # 2. Gestionar Vehículo
            cursor.execute(
                "SELECT id_vehiculo FROM vehiculos WHERE patente = %s AND id_cliente = %s",
                (patente, id_cliente)
            )
            vehiculo = cursor.fetchone()

            if vehiculo:
                id_vehiculo = vehiculo['id_vehiculo']
            else:
                # Asumimos 'auto' por defecto como pediste
                cursor.execute(
                    "INSERT INTO vehiculos (id_cliente, patente, tipo) VALUES (%s, %s, 'auto')",
                    (id_cliente, patente)
                )
                id_vehiculo = cursor.lastrowid

            cursor.execute(
                "INSERT INTO agendas (id_cliente, id_vehiculo, id_servicio, fecha_agenda) VALUES (%s, %s, %s, %s)",
                (id_cliente, id_vehiculo, int(id_servicio), fecha_agenda)
            )
            conexion.commit()

            # Obtener nombre del servicio para el correo
            cursor.execute("SELECT nombre FROM servicios WHERE id_servicio = %s", (int(id_servicio),))
            serv_data = cursor.fetchone()
            nombre_servicio_final = serv_data['nombre'] if serv_data else 'Lavado Auto'

            datos_cita = {
                'nombre_cliente': nombre,
                'email_cliente': email,
                'telefono': telefono,
                'patente': patente,
                'nombre_servicio': nombre_servicio_final,
                'fecha': request.form['fecha'],
                'hora': request.form['hora']
            }
            enviar_correos_confirmacion(datos_cita)

            return redirect(url_for('exito', nombre=nombre, fecha=request.form['fecha'], hora=request.form['hora'], servicio_id=id_servicio))
        except Exception as e:
            return f"Error: {str(e)}", 500
        finally:
            if 'conexion' in locals() and conexion.is_connected():
                cursor.close()
                conexion.close()
    
    # --- LÓGICA GET: PREPARAR LA VISTA CON LOS 3 NUEVOS ESTÁNDARES ---
    try:
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor(dictionary=True)

        categorias_negocio = [
            {'id': 'cat_pequeno', 'nombre': 'Auto Pequeño (City Car)', 'tamano_db': 'pequeño City Car'},
            {'id': 'cat_mediano', 'nombre': 'Auto Mediano (Sedan - Suv)', 'tamano_db': 'mediano Sedan - suv'},
            {'id': 'cat_grande', 'nombre': 'Auto Grande (Camioneta - Jeep)', 'tamano_db': 'grande Camioneta'}
        ]
        
        tamanos_lavado = categorias_negocio
        servicios_lavado_actual = []

    except Exception as e:
        print(f"Error al cargar servicios de lavado: {str(e)}")
        tamanos_lavado = []
        servicios_lavado_actual = []
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

    return render_template(
        'lavado.html',
        tamanos_lavado=tamanos_lavado,
        servicios_lavado_actual=servicios_lavado_actual
    )

@app.route('/get_lavados/<categoria>')
def get_lavados(categoria):
    """
    Devuelve los servicios según la categoría seleccionada.
    Categorías: cat_pequeno, cat_mediano, cat_grande
    """
    try:
        # Mapeo de categoría a valor en BD
        mapa_tamanos = {
            'cat_pequeno': 'pequeño City Car',
            'cat_mediano': 'mediano Sedan - suv',
            'cat_grande': 'grande Camioneta'
        }
        
        tamano_db = mapa_tamanos.get(categoria)
        if not tamano_db:
            return jsonify([])

        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor(dictionary=True)
        
        # Obtenemos todos los servicios de lavado para ese tamaño
        cursor.execute("""
            SELECT id_servicio, nombre, precio
            FROM servicios
            WHERE tipo_servicio = 'lavado' AND tamaño_auto = %s
            ORDER BY precio ASC
        """, (tamano_db,))
        
        servicios = cursor.fetchall()
        for servicio in servicios:
            servicio['precio'] = int(servicio['precio'])
            
        return jsonify(servicios)
    except Exception as e:
        print(f"Error al obtener lavados: {e}")
        return jsonify([])
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()

@app.route('/mecanico', methods=['GET', 'POST'])
def mecanico():
    if request.method == 'POST':
        try:
            rut = request.form['rut']
            nombre = request.form['nombre']
            email = request.form['email']
            telefono = str(request.form.get('telefono', ''))
            if not telefono.startswith('+569'):
                telefono = '+569' + telefono.replace('+569', '')
            patente = request.form['patente']
            id_servicio = request.form['id_servicio']
            fecha_agenda = request.form['fecha'] + ' ' + request.form['hora']

            if not id_servicio or not id_servicio.isdigit():
                return jsonify({'error': 'Seleccione un servicio válido'}), 400

            conexion = mysql.connector.connect(**db_config)
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM clientes WHERE rut = %s", (rut,))
            cliente_existente = cursor.fetchone()

            if cliente_existente:
                id_cliente = cliente_existente['id_cliente']
            else:
                cursor.execute("INSERT INTO clientes (rut, nombre, email, telefono) VALUES (%s, %s, %s, %s)", (rut, nombre, email, telefono))
                id_cliente = cursor.lastrowid

            cursor.execute("SELECT id_vehiculo FROM vehiculos WHERE patente = %s AND id_cliente = %s", (patente, id_cliente))
            vehiculo = cursor.fetchone()

            if vehiculo:
                id_vehiculo = vehiculo['id_vehiculo']
            else:
                cursor.execute("INSERT INTO vehiculos (id_cliente, patente, tipo) VALUES (%s, %s, 'auto')", (id_cliente, patente))
                id_vehiculo = cursor.lastrowid

            cursor.execute("INSERT INTO agendas (id_cliente, id_vehiculo, id_servicio, fecha_agenda) VALUES (%s, %s, %s, %s)", (id_cliente, id_vehiculo, int(id_servicio), fecha_agenda))
            conexion.commit()

            datos_cita = {
                'nombre_cliente': nombre, 'email_cliente': email, 'telefono': telefono,
                'patente': patente, 'nombre_servicio': 'Mecanico',
                'fecha': request.form['fecha'], 'hora': request.form['hora']
            }
            enviar_correos_confirmacion(datos_cita)

            return redirect(url_for('exito', nombre=nombre, fecha=request.form['fecha'], hora=request.form['hora'], servicio_id=id_servicio))
        except Exception as e:
            return f"Error: {str(e)}", 500
        finally:
            if 'conexion' in locals() and conexion.is_connected():
                cursor.close()
                conexion.close()

    try:
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id_servicio, nombre, precio FROM servicios WHERE tipo_servicio in ('mecanico', 'pintura')")
        servicios = cursor.fetchall()
        for servicio in servicios:
            servicio['precio'] = int(servicio['precio'])
    except Exception as e:
        print(f"Error al cargar servicios: {str(e)}")
        servicios = []
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()
    return render_template('mecanico.html', servicios=servicios)

@app.route('/lavadotapiz', methods=['GET', 'POST'])
def lavadotapiz():
    if request.method == 'POST':
        try:
            rut = request.form['rut']
            nombre = request.form['nombre']
            email = request.form['email']
            telefono = str(request.form.get('telefono', ''))
            if not telefono.startswith('+569'):
                telefono = '+569' + telefono.replace('+569', '')
            patente = request.form['patente']
            id_servicio = request.form['id_servicio']
            fecha_agenda = request.form['fecha'] + ' ' + request.form['hora']

            if not id_servicio or not id_servicio.isdigit():
                return jsonify({'error': 'Seleccione un servicio válido'}), 400

            conexion = mysql.connector.connect(**db_config)
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM clientes WHERE rut = %s", (rut,))
            cliente_existente = cursor.fetchone()

            if cliente_existente:
                id_cliente = cliente_existente['id_cliente']
            else:
                cursor.execute("INSERT INTO clientes (rut, nombre, email, telefono) VALUES (%s, %s, %s, %s)", (rut, nombre, email, telefono))
                id_cliente = cursor.lastrowid

            cursor.execute("SELECT id_vehiculo FROM vehiculos WHERE patente = %s AND id_cliente = %s", (patente, id_cliente))
            vehiculo = cursor.fetchone()

            if vehiculo:
                id_vehiculo = vehiculo['id_vehiculo']
            else:
                cursor.execute("INSERT INTO vehiculos (id_cliente, patente, tipo) VALUES (%s, %s, 'auto')", (id_cliente, patente))
                id_vehiculo = cursor.lastrowid

            cursor.execute("INSERT INTO agendas (id_cliente, id_vehiculo, id_servicio, fecha_agenda) VALUES (%s, %s, %s, %s)", (id_cliente, id_vehiculo, int(id_servicio), fecha_agenda))
            conexion.commit()

            datos_cita = {
                'nombre_cliente': nombre, 'email_cliente': email, 'telefono': telefono,
                'patente': patente, 'nombre_servicio': 'Lavado Tapiz',
                'fecha': request.form['fecha'], 'hora': request.form['hora']
            }
            enviar_correos_confirmacion(datos_cita)

            return redirect(url_for('exito', nombre=nombre, fecha=request.form['fecha'], hora=request.form['hora'], servicio_id=id_servicio))
        except Exception as e:
            return f"Error: {str(e)}", 500
        finally:
            if 'conexion' in locals() and conexion.is_connected():
                cursor.close()
                conexion.close()

    try:
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id_servicio, nombre, precio FROM servicios WHERE tipo_servicio in ('Lavado-Tapiz')")
        servicios = cursor.fetchall()
        for servicio in servicios:
            servicio['precio'] = int(servicio['precio'])
    except Exception as e:
        print(f"Error al cargar servicios: {str(e)}")
        servicios = []
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()
    return render_template('lavadotapiz.html', servicios=servicios)

@app.route('/buscar_cliente')
def buscar_cliente():
    rut = request.args.get('rut')
    try:
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM clientes WHERE rut = %s", (rut,))
        cliente = cursor.fetchone()
        
        if cliente:
            # Lógica para limpiar el teléfono (quitar el +569 si viene de la BD)
            # Porque en el HTML el usuario solo debe ver los 8 dígitos
            telefono_bd = str(cliente['telefono']) if cliente['telefono'] else ""
            telefono_limpio = telefono_bd.replace('+569', '')

            return jsonify({
                'existe': True, 
                'id_cliente': cliente['id_cliente'], 
                'nombre': cliente['nombre'],
                'email': cliente['email'],       # ✅ Agregamos Email
                'telefono': telefono_limpio      # ✅ Agregamos Teléfono (8 dígitos)
            })
        else:
            return jsonify({'existe': False})
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

@app.route('/vehiculos_cliente')
def vehiculos_cliente():
    id_cliente = request.args.get('id_cliente')
    try:
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM vehiculos WHERE id_cliente = %s AND activo = TRUE", (id_cliente,))
        vehiculos = cursor.fetchall()
        return jsonify(vehiculos)
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

@app.route('/exito', methods=['GET'])
def exito():
    nombre = request.args.get('nombre')
    fecha = request.args.get('fecha')
    hora = request.args.get('hora')
    servicio_id = request.args.get('servicio_id')
    nombre_servicio = "Servicio no encontrado"
    try:
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT nombre FROM servicios WHERE id_servicio = %s", (servicio_id,))
        servicio_db = cursor.fetchone()
        if servicio_db:
            nombre_servicio = servicio_db['nombre']
    except Exception as e:
        print(f"Error al buscar servicio: {str(e)}")
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()
    return render_template('exito.html', nombre=nombre, fecha=fecha, hora=hora, servicio=nombre_servicio)

@app.route('/horas_disponibles', methods=['GET'])
def horas_disponibles():
    fecha = request.args.get('fecha')
    if not fecha:
        return jsonify({'error': 'Fecha requerida'}), 400
    try:
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor()
        # Obtenemos solo la hora (HH:MM) de las agendas ocupadas
        sql = "SELECT DATE_FORMAT(fecha_agenda, '%H:%i') AS hora_inicio FROM agendas WHERE DATE(fecha_agenda) = %s"
        cursor.execute(sql, (fecha,))
        horas_ocupadas = [row[0] for row in cursor.fetchall()]

        # Comparación directa ya que las bandas son solo 'HH:MM'
        disponibles_lavados = [b for b in BANDAS_HORARIAS_LAVADOS if b not in horas_ocupadas]
        disponibles_mecanicos = [b for b in BANDAS_HORARIAS_MECANICO if b not in horas_ocupadas]
        disponibles_lavadotapiz = [b for b in BANDAS_HORARIAS_LAVADOTAPIZ if b not in horas_ocupadas]

        return jsonify({
            'disponibles_lavados': disponibles_lavados,
            'disponibles_mecanicos': disponibles_mecanicos,
            'disponibles_lavadotapiz': disponibles_lavadotapiz
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)