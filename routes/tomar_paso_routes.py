# routes/tomar_paso_routes.py
from flask import current_app, Blueprint, jsonify, render_template
import requests, re
from bs4 import BeautifulSoup
from config.constantes import URL, IMAGE_FILENAMES
from models.db import db
from models.paso_models import Paso 
from routes.users_routes import token_required
import random


# Blueprint para /paso
pasos = Blueprint("pasos", __name__, url_prefix="/paso")


@pasos.route("/api", methods=["GET"])
@token_required()
def api_paso(current_user):
    """Devuelve el último Paso en JSON (protegido)."""
    paso = Paso.query.first()
    if paso:
        return jsonify(paso.to_dict())
    return jsonify({"message": "No hay registros de paso"}), 404

# Nuevo endpoint público para el layout.html (usuarios no autenticados)
@pasos.route("/public_api", methods=["GET"])
def public_api_paso():
    """Devuelve el último Paso en JSON (público, sin token) y una imagen al azar."""
    paso = Paso.query.first()

    # Lógica para elegir una imagen al azar
    random_image = random.choice(IMAGE_FILENAMES)

    if paso:
        # Crea el diccionario de datos de la BD
        data = paso.to_dict()
        
        # Agrega el nombre de la imagen al diccionario de respuesta
        data['image_filename'] = random_image
        
        return jsonify(data), 200
    
    # Si la BD está vacía, devuelve el error 404, pero también una imagen por defecto
    return jsonify({
        "message": "No hay registros de paso",
        "estado": "desconocido", 
        "horario": "0000 HS A 0000 HS", # Valor por defecto con el formato deseado
        "image_filename": random_image 
    }), 404

@pasos.route("/", methods=["GET"])
def ver_paso():
    """Vista HTML para debug/manual (opcional)."""
    paso = Paso.query.first()
    return render_template("paso/paso.html", pasos=paso.to_dict() if paso else {})


def actualizar_estado():
    """
    Scrapea la web y actualiza el estado, la hora de actualización y el horario de atención en la BD.
    """
    with current_app.app_context():
        # --- Variables de Scraping ---
        horario_atencion = "Horario no disponible"
        estado = "Error de scraping"
        # 🚨 Cambiamos 'actualizado' para que capture el texto del tiempo de actualización
        tiempo_actualizacion = "No se pudo determinar el tiempo" 
        # -----------------------------

        # PATRÓN REGULAR PARA EL HORARIO (ej: 0900 HS A 2100 HS)
        HORARIO_PATTERN = r'(\d{4}\s*HS\s*A\s*\d{4}\s*HS)' 

        try:
            resp = requests.get(URL, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # 1. 🔍 Extracción del ESTADO y TIEMPO DE ACTUALIZACIÓN
            
            # Buscamos el tag que contiene el estado (ej: <span class="label label-success ...">Abierto</span>)
            estado_tag = soup.find('span', class_=re.compile(r"label-(success|warning|danger)", re.IGNORECASE))
            
            if estado_tag:
                estado = estado_tag.get_text(strip=True)
                
                #NUEVA LÓGICA: Buscamos el nodo de texto inmediatamente adyacente
                # que contiene el tiempo ("Actualizado hace X horas...")
                tiempo_nodo = estado_tag.next_sibling
                
                if tiempo_nodo and tiempo_nodo.strip():
                    # Limpiamos y guardamos solo el texto de la actualización
                    tiempo_actualizacion = tiempo_nodo.strip()
                else:
                    tiempo_actualizacion = "Tiempo no visible en el nodo adyacente"
            else:
                estado = "Estado no encontrado"
            
            # 2.Extracción del HORARIO
            horario_tag = soup.find('strong', string=re.compile(r"Horarios de atención:", re.IGNORECASE))
            
            if horario_tag:
                texto_despues_del_strong = horario_tag.next_sibling
                
                if texto_despues_del_strong:
                    match_horario = re.search(HORARIO_PATTERN, texto_despues_del_strong, re.IGNORECASE)
                    
                    if match_horario:
                        horario_atencion = match_horario.group(1).strip()
                    else:
                        horario_atencion = "Patrón de hora no encontrado"
                else:
                    horario_atencion = "No se encontró texto adyacente"
            else:
                horario_atencion = "Etiqueta 'Horarios de atención:' no encontrada"


        except Exception as e:
            estado = "Error de conexión/parsing"
            tiempo_actualizacion = str(e)
            horario_atencion = "No disponible debido a error de conexión" 

        # 3. 💾 Actualizar la BD
        paso = Paso.query.first()
        if not paso:
            paso = Paso(nombre="Cristo Redentor")

        paso.estado = estado
        paso.actualizado = tiempo_actualizacion # Guardamos el string del tiempo de actualización
        paso.horario_atencion = horario_atencion 
        paso.fuente = URL
        paso.timestamp = db.func.now()

        db.session.add(paso)
        db.session.commit()

        return paso.to_dict()