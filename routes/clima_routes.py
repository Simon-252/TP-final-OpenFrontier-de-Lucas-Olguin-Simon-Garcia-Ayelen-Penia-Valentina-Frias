from flask import Blueprint, jsonify, current_app
from models.db import db
# 💡 Importamos el nuevo modelo que soporta Pronósticos Diarios
from models.clima_models import PronosticoDiario 
from models.paso_models import Paso
import requests
from routes.users_routes import token_required
from datetime import datetime, date
from collections import defaultdict
import math

clima_bp = Blueprint("clima", __name__, url_prefix="/api/clima")

# --- Rutas Públicas (para uso del frontend) ---

# Obtener los 4 últimos pronósticos registrados para un paso
@clima_bp.route("/pronostico/<paso_id>", methods=["GET"])
def get_pronostico(paso_id):
    """Devuelve los últimos 4 pronósticos diarios para un paso específico."""

    # 💡 Cambio Clave: Usar .filter() en lugar de .filter_by() para una comparación explícita
    # y ordenar por fecha_pronostico DESCENDENTE para obtener los "últimos" días primero,
    # y luego limitarlos y REVERSARLOS para que queden ascendentes (Hoy, Mañana, etc.)

    # 1. Obtener los 4 pronósticos MÁS RECIENTES (por fecha de pronóstico)
    pronosticos = PronosticoDiario.query.filter(PronosticoDiario.paso_id == paso_id) \
                                        .order_by(PronosticoDiario.fecha_pronostico.desc()) \
                                        .limit(4) \
                                        .all()

    if not pronosticos:
        # Si no encuentra nada, devuelve 404
        return jsonify({"message": "No hay pronósticos registrados para este paso"}), 404

    # 2. Reversar la lista para que el día más cercano aparezca primero (Hoy, Mañana,...)
    pronosticos.reverse()

    # 3. Devolver la respuesta (Status 200 OK)
    return jsonify([p.to_dict() for p in pronosticos])


# --- Rutas de Actualización (con autenticación o scheduler) ---

# Consultar API de OpenWeather y guardar en BD (requiere usuario autenticado)
@clima_bp.route("/actualizar/<paso_id>", methods=["POST"])
@token_required()
def actualizar(current_user, paso_id):
    # Ahora llamamos a la función con el nombre del modelo actualizado
    return _actualizar_pronostico(paso_id)

# Función para el scheduler (sin login)
def actualizar_automatico():
    """Actualiza el pronóstico automáticamente para el primer Paso registrado en la BD."""
    paso = Paso.query.first()
    if not paso:
        print(" No hay pasos registrados en la base de datos. No se pudo actualizar el clima.")
        return None
    
    # Ahora llamamos a la función con el nombre del modelo actualizado
    return _actualizar_pronostico(paso.id)


# --- Funciones Auxiliares para el Fetch y Procesamiento ---

def _procesar_datos_pronostico(data):
    """
    Procesa el JSON de la API de 5 Day / 3 Hour Forecast
    y calcula el Min/Max diario y la descripción principal.
    """
    pronostico_por_dia = defaultdict(lambda: {
        'temp_min': float('inf'), # Inicializamos con infinito para encontrar el mínimo
        'temp_max': float('-inf'), # Inicializamos con menos infinito para encontrar el máximo
        'viento_velocidad': 0,
        'viento_count': 0,
        'descripciones': defaultdict(int) # Contador de descripciones para encontrar la más común
    })
    
    # Iterar sobre las mediciones cada 3 horas
    for item in data['list']:
        # Obtener la fecha sin la hora
        dt_object = datetime.fromtimestamp(item['dt'])
        fecha_str = dt_object.strftime('%Y-%m-%d')
        fecha_date = dt_object.date()

        # 1. Calcular Min/Max
        # OpenWeather proporciona temp_min/max en el bloque principal para el rango de 3h, 
        # pero para el Min/Max diario, es mejor usar 'main.temp' y buscar el rango
        # global para ese día. Aquí usaremos 'main.temp_min' y 'main.temp_max' de las mediciones de 3h
        # y calcularemos el min/max general del día:
        
        temp_actual = item['main']['temp'] # Usamos la temperatura real para el cálculo
        
        dia_data = pronostico_por_dia[fecha_str]
        
        dia_data['fecha_date'] = fecha_date
        
        if temp_actual < dia_data['temp_min']:
            dia_data['temp_min'] = temp_actual
            
        if temp_actual > dia_data['temp_max']:
            dia_data['temp_max'] = temp_actual

        # 2. Viento: Sumar y contar para calcular el promedio de velocidad del día
        dia_data['viento_velocidad'] += item['wind']['speed']
        dia_data['viento_count'] += 1

        # 3. Descripción: Contar ocurrencias de la descripción
        descripcion = item['weather'][0]['description']
        dia_data['descripciones'][descripcion] += 1
        
    
    resultados_finales = []
    
    # Finalizar el procesamiento
    for fecha_str, data in pronostico_por_dia.items():
        # Encontrar la descripción más común
        descripcion_mas_comun = max(data['descripciones'], key=data['descripciones'].get)
        
        # Calcular velocidad promedio del viento
        viento_avg = data['viento_velocidad'] / data['viento_count'] if data['viento_count'] else 0
        
        # 💡 NOTA: No podemos obtener la Visibilidad ni la Dirección del Viento con la API gratuita
        # en formato diario fácilmente, por lo que usaremos datos simulados o lo dejaremos en None/N/A.
        # En este caso, usaremos 'N/A' y '10000' (visibilidad estándar del wireframe)
        
        resultados_finales.append({
            'fecha_pronostico': data['fecha_date'],
            'temp_min': round(data['temp_min'], 1),
            'temp_max': round(data['temp_max'], 1),
            'descripcion': descripcion_mas_comun.capitalize(),
            'viento_velocidad_kmh': round(viento_avg * 3.6, 1), # Convierte m/s a km/h
            'viento_direccion': 'Oeste', # Este dato es difícil de resumir por día y se simula aquí.
            'visibilidad_metros': 10000 
        })
        
    # Devolvemos solo los primeros 4 pronósticos (Hoy + 3 días)
    return resultados_finales[:4] 


def _actualizar_pronostico(paso_id):
    """Consulta la API de OpenWeatherMap, procesa el pronóstico y lo guarda en la BD."""
    api_key = current_app.config["WEATHER_API_KEY"]
    lat, lon = -32.8322, -70.0450  # Coordenadas del paso Cristo Redentor

    # 🔑 Cambiamos el endpoint de '/weather' a '/forecast'
    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=es"
    
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status() # Lanza un error para códigos de estado 4xx/5xx
        data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con OpenWeatherMap: {e}")
        return {"error": "Error de conexión con el proveedor de clima"}
    
    if "list" not in data:
        return {"error": "Respuesta inválida de la API", "respuesta": data}

    # 1. Procesar los datos para obtener el resumen diario (Min/Max, Descripción)
    pronosticos_diarios = _procesar_datos_pronostico(data)
    
    if not pronosticos_diarios:
        return {"error": "No se pudieron procesar los datos de pronóstico"}

    # 2. Guardar o actualizar cada día del pronóstico en la base de datos
    dias_guardados = []
    
    for pronostico_data in pronosticos_diarios:
        
        # Intentar encontrar un pronóstico existente para este paso y fecha
        pronostico_existente = PronosticoDiario.query.filter_by(
            paso_id=paso_id,
            fecha_pronostico=pronostico_data['fecha_pronostico']
        ).first()

        if pronostico_existente:
            # Si existe, actualizamos los campos
            pronostico_existente.temp_min = pronostico_data['temp_min']
            pronostico_existente.temp_max = pronostico_data['temp_max']
            pronostico_existente.descripcion = pronostico_data['descripcion']
            pronostico_existente.viento_velocidad_kmh = pronostico_data['viento_velocidad_kmh']
            pronostico_existente.viento_direccion = pronostico_data['viento_direccion']
            pronostico_existente.visibilidad_metros = pronostico_data['visibilidad_metros']
            dias_guardados.append(pronostico_existente.to_dict())
        else:
            # Si no existe, creamos un nuevo registro
            nuevo_pronostico = PronosticoDiario(
                paso_id=paso_id,
                **pronostico_data # Desempaquetamos el diccionario
            )
            db.session.add(nuevo_pronostico)
            dias_guardados.append(nuevo_pronostico.to_dict())

    try:
        db.session.commit()
        return {"message": f"Pronóstico actualizado para {len(dias_guardados)} días.", "dias_actualizados": dias_guardados}
    except Exception as e:
        db.session.rollback()
        print(f"Error al guardar pronósticos en BD: {e}")
        return {"error": "Error al guardar los datos en la base de datos"}

# Las rutas get_all y get_last (del modelo antiguo) DEBERÍAN SER ELIMINADAS O ACTUALIZADAS
# para usar el nuevo modelo PronosticoDiario si ya no usas el modelo Clima.
# Aquí se asume que las mantienes por ahora, pero NO DEBES usarlas para el pronóstico.
# ... (dejas get_all y get_last como están si aún usas el modelo Clima para otra cosa)



# from flask import Blueprint, jsonify, current_app
# from models.db import db
# from models.clima_models import Clima
# from models.paso_models import Paso
# import requests
# from routes.users_routes import token_required

# clima_bp = Blueprint("clima", __name__, url_prefix="/api/clima")

# # Obtener todos los registros (opcional, solo para debugging)
# @clima_bp.route("/", methods=["GET"])
# @token_required()
# def get_all(current_user):
#     climas = Clima.query.all()
#     return jsonify([c.to_dict() for c in climas])

# # Obtener el último clima registrado de un paso
# @clima_bp.route("/ultimo/<paso_id>", methods=["GET"])
# @token_required()
# def get_last(current_user, paso_id):
#     clima = Clima.query.filter_by(paso_id=paso_id).order_by(Clima.fecha.desc()).first()
#     if not clima:
#         return jsonify({"message": "No hay clima registrado para este paso"}), 404
#     return jsonify(clima.to_dict())

# # Consultar API de OpenWeather y guardar en BD (requiere usuario autenticado)
# @clima_bp.route("/actualizar/<paso_id>", methods=["POST"])
# @token_required()
# def actualizar(current_user, paso_id):
#     return _actualizar_clima(paso_id)

# # Función para el scheduler (sin login)
# def actualizar_automatico():
#     """Actualiza el clima automáticamente para el primer Paso registrado en la BD."""
#     paso = Paso.query.first()
#     if not paso:
#         print(" No hay pasos registrados en la base de datos. No se pudo actualizar el clima.")
#         return None
    
#     return _actualizar_clima(paso.id)

# # Función auxiliar para reutilizar en ambos casos
# def _actualizar_clima(paso_id):
#     api_key = current_app.config["WEATHER_API_KEY"]
#     lat, lon = -32.8322, -70.0450  # Coordenadas del paso Cristo Redentor

#     url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=es"
#     resp = requests.get(url, timeout=10)
#     data = resp.json()
    

#     if "main" not in data:
#         return {"error": "No se pudo obtener clima", "respuesta": data}

#     clima = Clima(
#         paso_id=paso_id,
#         temperatura=data["main"]["temp"],
#         descripcion=data["weather"][0]["description"],
#         viento=data["wind"]["speed"]
#     )
#     db.session.add(clima)
#     db.session.commit()
#     return clima.to_dict()
