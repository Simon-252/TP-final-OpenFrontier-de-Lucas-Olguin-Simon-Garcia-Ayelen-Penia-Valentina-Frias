from flask import Blueprint, jsonify, current_app
from models.db import db
from models.clima_models import Clima
from models.paso_models import Paso
import requests
from routes.users_routes import token_required

clima_bp = Blueprint("clima", __name__, url_prefix="/api/clima")

# Obtener todos los registros (opcional, solo para debugging)
@clima_bp.route("/", methods=["GET"])
@token_required()
def get_all(current_user):
    climas = Clima.query.all()
    return jsonify([c.to_dict() for c in climas])

# Obtener el último clima registrado de un paso
@clima_bp.route("/ultimo/<paso_id>", methods=["GET"])
@token_required()
def get_last(current_user, paso_id):
    clima = Clima.query.filter_by(paso_id=paso_id).order_by(Clima.fecha.desc()).first()
    if not clima:
        return jsonify({"message": "No hay clima registrado para este paso"}), 404
    return jsonify(clima.to_dict())

# Consultar API de OpenWeather y guardar en BD (requiere usuario autenticado)
@clima_bp.route("/actualizar/<paso_id>", methods=["POST"])
@token_required()
def actualizar(current_user, paso_id):
    return _actualizar_clima(paso_id)

# Función para el scheduler (sin login)
def actualizar_automatico():
    """Actualiza el clima automáticamente para el primer Paso registrado en la BD."""
    paso = Paso.query.first()
    if not paso:
        print(" No hay pasos registrados en la base de datos. No se pudo actualizar el clima.")
        return None
    
    return _actualizar_clima(paso.id)

# Función auxiliar para reutilizar en ambos casos
def _actualizar_clima(paso_id):
    api_key = current_app.config["WEATHER_API_KEY"]
    lat, lon = -32.8322, -70.0450  # Coordenadas del paso Cristo Redentor

    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=es"
    resp = requests.get(url, timeout=10)
    data = resp.json()
    

    if "main" not in data:
        return {"error": "No se pudo obtener clima", "respuesta": data}

    clima = Clima(
        paso_id=paso_id,
        temperatura=data["main"]["temp"],
        descripcion=data["weather"][0]["description"],
        viento=data["wind"]["speed"]
    )
    db.session.add(clima)
    db.session.commit()
    return clima.to_dict()
