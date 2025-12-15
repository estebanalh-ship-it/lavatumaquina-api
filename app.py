from flask import Flask, request, jsonify, redirect, url_for, render_template
import mysql.connector
from flask_mail import Mail, Message
from database import db_config

from dotenv import load_dotenv
from admin import admin_bp
load_dotenv()


app = Flask(__name__)
app.secret_key = 'dianadegales2025'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'lavatumaquina.rengo@gmail.com'
app.config['MAIL_PASSWORD'] = 'giag cnyt huxv iuyq'
app.config['MAIL_DEFAULT_SENDER'] = ('Lava Tu Maquina', 'lavatumaquina.rengo@gmail.com')

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

BANDAS_HORARIAS_LAVADOS = ['09:00-10:00', '10:00-11:00', '15:00-16:00', '16:00-17:00']
BANDAS_HORARIAS_MECANICO = ['11:00-12:00', '12:00-13:00']
BANDAS_HORARIAS_LAVADOTAPIZ = ['11:00-12:00', '12:00-13:00']

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

            cursor.execute(
                "SELECT id_vehiculo FROM vehiculos WHERE patente = %s AND id_cliente = %s",
                (patente, id_cliente)
            )
            vehiculo = cursor.fetchone()

            if vehiculo:
                id_vehiculo = vehiculo['id_vehiculo']
            else:
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

            datos_cita = {
                'nombre_cliente': nombre,
                'email_cliente': email,
                'telefono': telefono,
                'patente': patente,
                'nombre_servicio': 'Lavado Auto',
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
    try:
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT DISTINCT tamaño_auto AS nombre_tamaño
            FROM servicios
            WHERE tipo_servicio = 'lavado' AND tamaño_auto IS NOT NULL
            ORDER BY FIELD(tamaño_auto, 'pequeño city car', 'mediano Sedan - suv', 'grande camioneta')
        """)
        tamanos_lavado = cursor.fetchall()

        cursor.execute("""
            SELECT id_servicio, nombre, precio, tamaño_auto
            FROM servicios
            WHERE tipo_servicio = 'lavado' AND tamaño_auto = 'pequeño city car'
        """)
        servicios_lavado_actual = cursor.fetchall()
        for servicio in servicios_lavado_actual:
            servicio['precio'] = int(servicio['precio'])

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

@app.route('/get_lavados/<tamano>')
def get_lavados(tamano):
    try:
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT id_servicio, nombre, precio
            FROM servicios
            WHERE tipo_servicio = 'lavado' AND tamaño_auto = %s
        """, (tamano,))
        servicios = cursor.fetchall()
        for servicio in servicios:
            servicio['precio'] = int(servicio['precio'])
        return jsonify(servicios)
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
            return jsonify({'existe': True, 'id_cliente': cliente['id_cliente'], 'nombre': cliente['nombre']})
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
        sql = "SELECT DATE_FORMAT(fecha_agenda, '%H:%i:00') AS hora_inicio FROM agendas WHERE DATE(fecha_agenda) = %s"
        cursor.execute(sql, (fecha,))
        horas_ocupadas = [row[0] for row in cursor.fetchall()]

        disponibles_lavados = [b for b in BANDAS_HORARIAS_LAVADOS if f"{b.split('-')[0]}:00" not in horas_ocupadas]
        disponibles_mecanicos = [b for b in BANDAS_HORARIAS_MECANICO if f"{b.split('-')[0]}:00" not in horas_ocupadas]
        disponibles_lavadotapiz = [b for b in BANDAS_HORARIAS_LAVADOTAPIZ if f"{b.split('-')[0]}:00" not in horas_ocupadas]

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
