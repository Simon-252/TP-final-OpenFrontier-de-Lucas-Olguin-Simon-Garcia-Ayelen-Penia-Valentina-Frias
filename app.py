from flask import Flask, render_template
from config.config import DATABASE_CONNECTION_URI, SECRET_KEY, WEATHER_API_KEY
from models.db import db
from routes.about import about
from routes.tomar_paso_routes import pasos, actualizar_estado # Importa actualizar_estado
from routes.users_routes import auth_bp
from routes.clima_routes import clima_bp
from routes.profile_user_routes import profile_bp
from flask_migrate import Migrate 
from flask_apscheduler import APScheduler 
from routes.messages_routes import messages_bp
import logging
from logging.handlers import RotatingFileHandler
import os


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
app.config["WEATHER_API_KEY"] = WEATHER_API_KEY 


db.init_app(app)
# ---------------------------------------------------
# Migraciones
# ---------------------------------------------------
migrate = Migrate(app, db)
migrate.init_app(app, db)

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

@app.route("/notifications") 
def notifications_page():
    return render_template("notifications.html")
# ---------------------------------------------------
# Jobs automáticos
# ---------------------------------------------------
def job_actualizar_estado():
    """Ejecuta la actualización del paso dentro del contexto de la app"""
    # Usamos app.logger.info para registrar cuándo se ejecuta la tarea
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
        #db.create_all()
        print("")
        # Esta llamada solo se ejecuta cuando el script se inicia directamente, NO en el import de pytest
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