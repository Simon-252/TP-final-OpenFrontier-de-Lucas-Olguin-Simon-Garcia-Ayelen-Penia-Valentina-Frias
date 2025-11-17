from flask import Flask, render_template, request, jsonify

from config.config import DATABASE_CONNECTION_URI, SECRET_KEY, WEATHER_API_KEY

from models.db import db

from models.paso_models import Paso

from models.users_models import User

from models.messages_models import Message

from routes.about import about

from routes.tomar_paso_routes import pasos, actualizar_estado

from routes.users_routes import auth_bp

from routes.clima_routes import clima_bp

from routes.profile_user_routes import profile_bp

from routes.messages_routes import messages_bp

from flask_migrate import Migrate

from flask_apscheduler import APScheduler

import logging

from logging.handlers import RotatingFileHandler

from config.constantes import token_required

from werkzeug.utils import secure_filename

import os

from flask_login import LoginManager, UserMixin, current_user





# ---------------------------------------------------

# Inicialización de Flask

# ---------------------------------------------------

app = Flask(__name__)

app.secret_key = "clave_secreta"



# ---------------------------------------------------

# Configuración

# ---------------------------------------------------

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_CONNECTION_URI

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SECRET_KEY"] = SECRET_KEY

app.config["JWT_SECRET_KEY"] = SECRET_KEY

app.config["WEATHER_API_KEY"] = WEATHER_API_KEY



# 🔑 CORRECCIÓN 1: Definir la carpeta de subidas

UPLOAD_DIR = 'static/uploads/incident_photos'

app.config['UPLOAD_FOLDER'] = UPLOAD_DIR



db.init_app(app)

# ---------------------------------------------------

# Migraciones

# ---------------------------------------------------

migrate = Migrate(app, db)

migrate.init_app(app, db)



login_manager = LoginManager()

login_manager.init_app(app)



login_manager.login_view = 'login'



scheduler = APScheduler()





# ===================================================

# 🪵 CONFIGURACIÓN DEL LOGGING ROTATIVO 🪵

# ===================================================



# 1. Crear la carpeta 'logs' si no existe

log_dir = 'logs'

if not os.path.exists(log_dir):

    os.makedirs(log_dir)



# 2. Configurar el manejador (handler) para el archivo rotativo

# maxBytes: 5 MB por archivo | backupCount: Mantiene 5 archivos de respaldo

file_handler = RotatingFileHandler(

    os.path.join(log_dir, 'app.log'),

    maxBytes=1024 * 1024 * 5,

    backupCount=5,

    encoding='utf-8'

)



# 3. Definir el formato del mensaje de log

formatter = logging.Formatter(

    '%(levelname)s: %(asctime)s - %(name)s:%(lineno)d - %(message)s'

)

file_handler.setFormatter(formatter)





# 4. Asignar el handler al logger de la aplicación

# Limpia los handlers previos y agrega los tuyos

if app.logger.handlers:

    app.logger.handlers.clear() # Limpia los handlers que pone Flask



# Añade el handler de archivo rotativo

app.logger.addHandler(file_handler)



# Añade también el de consola

app.logger.addHandler(logging.StreamHandler())



# Nivel de log

app.logger.setLevel(logging.DEBUG)



# 5. Establecer el nivel mínimo a registrar

app.logger.setLevel(logging.DEBUG)



# Log de inicio para verificar que funciona

app.logger.info(' Aplicación iniciada y sistema de logging rotativo configurado.')



# ===================================================

# FIN DEL LOGGING

# ===================================================



@login_manager.user_loader

def load_user(user_id):

    # Usa el método .get() de SQLAlchemy para buscar por clave primaria

    return db.session.get(User, user_id)



# ---------------------------------------------------

# Registro de Blueprints

# ---------------------------------------------------

app.register_blueprint(clima_bp)

app.register_blueprint(pasos)

app.register_blueprint(about)

app.register_blueprint(auth_bp)

app.register_blueprint(profile_bp)

app.register_blueprint(messages_bp)







# ---------------------------------------------------

# Rutas

# ---------------------------------------------------

@app.route("/")

def index():

    return render_template("layout.html")



@app.route('/clima')

def clima_page():

    paso_data = Paso.query.first()

    return render_template('clima.html', paso=paso_data)



@app.route("/notifications")
def notifications_page():
    return render_template("notifications.html")





# =======================================================
# 1. RUTA GET (Solo muestra el HTML) - SIN DECORADOR
# =======================================================

@app.route('/report_incident')
def report_incident():
    """Muestra el formulario para reportar un incidente."""
    return render_template('report_incident.html')





# =======================================================

# 2. RUTA API POST (Recibe el reporte) - CON DECORADOR

# =======================================================

@app.route('/api/report', methods=['POST'])

@token_required

def handle_report_submission(current_user):

   

    # 1. Obtener datos

    subject = request.form.get('subject')

    description = request.form.get('description')

    latitude = request.form.get('lat')

    longitude = request.form.get('lng')

    incident_photo = request.files.get('incident_photo')

    photo_path = None

   

    # Lógica para guardar la foto en el disco

    if incident_photo and incident_photo.filename:

       

        # 🔑 CORRECCIÓN 2: Asegurar la creación del directorio

        upload_dir = app.config['UPLOAD_FOLDER']

        os.makedirs(upload_dir, exist_ok=True)

       

        filename = secure_filename(incident_photo.filename)

        save_path = os.path.join(upload_dir, filename)

       

        try:

            incident_photo.save(save_path) # Intenta guardar

            # La ruta pública que se guardará en la DB

            photo_path = os.path.join('uploads/incident_photos', filename)

        except Exception as e:

            app.logger.error(f"Error al guardar archivo en disco: {e}")

            return jsonify({"msg": "Error al guardar la imagen. Verifique permisos del servidor."}), 500

   

    # 2. Construir el 'body' del mensaje

    message_body = f"Descripción:\n{description}\n\n"

    message_body += f"Ubicación:\n- Latitud: {latitude}\n- Longitud: {longitude}\n\n"

    if photo_path:

        message_body += f"Foto Adjunta:\n{photo_path}"



    # 3. BUSCAR TODOS los administradores

    admin_users = User.query.filter_by(role='admin').all()

   

    if not admin_users:

        # Esto es un error crítico si no hay nadie para recibir el reporte

        return jsonify({"msg": "Error: No se encontró un administrador para recibir el reporte."}), 500



    # 4. ITERAR y crear un mensaje para CADA administrador

    messages_sent = 0

    for admin_user in admin_users:

        new_report_message = Message(

            sender_id=current_user.id,

            recipient_id=admin_user.id,

            subject=subject,

            body=message_body,

            message_type='support',

            is_read_by_recipient=False

        )

        db.session.add(new_report_message)

        messages_sent += 1

   

    try:

        db.session.commit()

        return jsonify({"msg": f"Reporte enviado y registrado para {messages_sent} administradores."}), 201

    except Exception as e:

        db.session.rollback()

        app.logger.error(f"Error al guardar los reportes en la DB: {e}")

        return jsonify({"msg": "Error al guardar los reportes. Detalles logueados en el servidor."}), 500



# ---------------------------------------------------

# Jobs automáticos

# ---------------------------------------------------

def job_actualizar_estado():

    """Ejecuta la actualización del paso dentro del contexto de la app"""

    app.logger.info("🔧 Ejecutando job de actualización de estado de paso.")

    with app.app_context():

        actualizar_estado()



def job_actualizar_clima():

    """Ejecuta la actualización del clima dentro del contexto de la app"""

    app.logger.info("🔧 Ejecutando job de actualización de clima.")

    from routes.clima_routes import actualizar_automatico

    with app.app_context():

        actualizar_automatico()



# ---------------------------------------------------

# Main

# ---------------------------------------------------

if __name__ == "__main__":

    with app.app_context():

        #db.drop_all()  #esto se descomenta para reiniciar la base de datos!!!

        db.create_all()

        print("")

        actualizar_estado()

   

    scheduler.init_app(app)



    # Programa la tarea: ejecutar la función cada 30 minutos

    scheduler.add_job(

        id="actualizar_estado_paso",

        func=job_actualizar_estado,

        trigger="interval",

        minutes=30

    )



    # Programa la tarea: ejecutar la función cada 10 minutos (clima)

    scheduler.add_job(

        id="actualizar_clima",

        func=job_actualizar_clima,

        trigger="interval",

        minutes=10

    )



    scheduler.start()

    app.run(debug=True, use_reloader=False)