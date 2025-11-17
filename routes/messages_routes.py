import json
import os
from flask import Blueprint, request, jsonify, current_app
from models.db import db
from models.messages_models import Message
from models.users_models import User
from utils.auth import token_required 
from sqlalchemy import or_ 
from datetime import datetime
from sqlalchemy.orm import joinedload

messages_bp = Blueprint("messages", __name__)

# ----------------- Funciones de Utilidad para JSON -----------------

def get_json_filepath():
    """Construye y devuelve la ruta absoluta del archivo puntos_interes.json."""
    return os.path.join(current_app.root_path, 'static', 'data', 'puntos_interes.json')

def load_points_from_json():
    """Carga la lista de puntos de interés y alertas desde el archivo JSON."""
    json_path = get_json_filepath()
    if not os.path.exists(json_path):
        # Si el archivo no existe, devuelve una lista vacía para evitar errores
        return []
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Advertencia: Archivo {json_path} vacío o mal formado. Devolviendo lista vacía.")
        return []
    except Exception as e:
        print(f"Error al leer el JSON: {e}")
        return []

def save_points_to_json(data):
    """Guarda la lista completa de puntos de interés y alertas en el archivo JSON."""
    json_path = get_json_filepath()
    with open(json_path, 'w', encoding='utf-8') as f:
        # Usa ensure_ascii=False para guardar caracteres especiales como tildes
        json.dump(data, f, indent=4, ensure_ascii=False)

# FUNCIONALIDAD MODIFICADA: Eliminado el argumento photo_url
def add_point_to_json(subject, body, latitude, longitude):
    """
    Transfor ma la alerta en un punto de interés de tipo 'incidente' 
    y lo guarda en el JSON. Asume que latitude y longitude son válidos.
    """
    
    all_data = load_points_from_json()
    
    # Asigna un ID único basado en el tamaño actual de la lista.
    new_id = len(all_data) + 1 
    
    # Creamos la estructura específica para el mapa (sin photo_url)
    alert_point = {
        "id_map": new_id, 
        "name": subject, # Usamos el asunto como nombre del punto
        "body_alert": body, # Agregamos el cuerpo de la alerta para el popup del mapa
        "lat": latitude,
        "lng": longitude,
        
        # === INICIO DE CORRECCIÓN: Usar solo 'incidente' en minúsculas ===
        "iconType": "incidente", 
        "type": "incidente", 
        # === FIN DE CORRECCIÓN ===
        
        "color": "#FF4136", # Rojo para incidentes
        "is_temporary_alert": True, # Bandera de alerta
        "address": f"Lat: {latitude}, Lng: {longitude}",
        # ¡CAMBIO CLAVE: photo_url ELIMINADO de aquí!
    }
    
    all_data.append(alert_point)
    save_points_to_json(all_data)
    
    return new_id # Devuelve el ID generado en el JSON

# ----------------- Rutas de Envío (POST) -----------------

@messages_bp.route("/api/messages/alert", methods=["POST"])
@token_required 
def send_global_alert(current_user):
    """
    Ruta para que un administrador envíe una alerta global a la DB, 
    opcionalmente genera el punto de incidente en el JSON del mapa.
    """
    if current_user.role != 'admin':
        return jsonify({"message": "Acceso denegado. Solo administradores pueden enviar alertas."}), 403
        
    data = request.get_json()
    body = data.get('body')
    subject = data.get('subject', 'ALERTA DEL SISTEMA') 
    
    # *** CAMPOS QUE AHORA SON OPCIONALES ***
    latitude = data.get('latitude') # Puede ser None
    longitude = data.get('longitude') # Puede ser None
    # ¡CAMBIO CLAVE: photo_url ELIMINADO de la recepción de datos!
    # photo_url = data.get('photo_url') 
    
    # Validación mínima: el cuerpo del mensaje siempre es obligatorio
    if not body:
        return jsonify({
            "message": "El cuerpo del mensaje de la alerta es requerido."
        }), 400

    point_id = None
    alert_type = 'Aviso General'
    
    # Lógica Condicional: Intentar crear un punto de mapa SOLO SI hay latitud y longitud
    if latitude is not None and longitude is not None:
        try:
            # Intentamos convertir a flotante (si falla, significa que los valores son inválidos)
            lat = float(latitude)
            lng = float(longitude)
            
            # 1. Guardar el punto de interés en el JSON
            # ¡CAMBIO CLAVE: Ya no se pasa photo_url!
            point_id = add_point_to_json(
                subject=subject, 
                body=body,
                latitude=lat, 
                longitude=lng
            )
            alert_type = 'Incidente Geolocalizado'

        except ValueError:
            # Esto se dispara si lat/lng no pueden convertirse a float
            return jsonify({"message": "Latitud y Longitud deben ser valores numéricos válidos."}), 400
        except Exception as e:
            # Error al guardar en el JSON, podemos continuar o abortar, elegimos abortar
            return jsonify({"message": "Error al guardar el punto en el mapa JSON.", "error": str(e)}), 500


    # 2. Guardar la alerta en la Base de Datos (Siempre se guarda)
    new_alert = Message(
        sender_id=current_user.id,
        recipient_id=None, # NULL para indicar que es un broadcast
        subject=subject,
        body=body,
        message_type='alert',
        is_read_by_recipient=False
        # Si tienes un campo 'map_point_id' en el modelo Message, deberías asociarlo aquí:
        # map_point_id=point_id 
    )

    try:
        db.session.add(new_alert)
        db.session.commit()
        
        return jsonify({
            "message": f"Alerta de {alert_type} enviada a la DB y procesada con éxito.",
            "db_alert_id": new_alert.id,
            "map_point_id": point_id # Será None si no se geolocalizó
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error interno al guardar la alerta en la DB.", "error": str(e)}), 500


@messages_bp.route("/api/messages/user/<string:user_id>", methods=["POST"])
@token_required
def send_private_message(current_user, user_id):
    """Ruta para que un administrador envíe un mensaje privado a un usuario específico."""
    if current_user.role != 'admin':
        return jsonify({"message": "Acceso denegado. Solo admins pueden enviar mensajes privados directos."}), 403


    user_to_send = User.query.get(user_id)
    if not user_to_send:
        return jsonify({"message": "Usuario destinatario no encontrado."}), 404

    data = request.get_json()
    subject = data.get('subject', 'Mensaje Privado')
    body = data.get('body')
            
    if not body:
        return jsonify({"message": "El cuerpo del mensaje es requerido."}), 400

    new_message = Message(
        sender_id=current_user.id,
        recipient_id=user_id,
        subject=subject,
        body=body,
        message_type='private'
    )
            
    try:
        db.session.add(new_message)
        db.session.commit()
        return jsonify({"message": f"Mensaje enviado a {user_to_send.username}."}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error interno al guardar el mensaje.", "error": str(e)}), 500


# ----------------- Rutas de LECTURA/ESTADO (GET/PATCH/DELETE) -----------------

@messages_bp.route("/api/messages", methods=["GET"])
@token_required
def get_user_messages(current_user):
    """
    Obtiene el buzón de mensajes del usuario logueado.
    Optimizado con joinedload para evitar consultas N+1.
    """
    
    # 1. Configuración de filtros 
    filters = (Message.message_type == 'alert') 
    
    if hasattr(current_user, 'notifications_enabled') and current_user.notifications_enabled:
        filters = or_(
            (Message.message_type == 'alert'), 
            (Message.recipient_id == current_user.id) 
        )
    else:
        # Si las notificaciones están desactivadas, solo se muestran las alertas masivas.
        filters = Message.message_type == 'alert'
    
    
    # 2. Consulta de Mensajes OPTIMIZADA (uso de joinedload)
    messages = Message.query.options(joinedload(Message.sender)).filter(filters).order_by(
        Message.timestamp.desc()
    ).all()
    
    # 3. Construcción del output
    output = []
    for msg in messages:
        sender_username = msg.sender.username if msg.sender else "Sistema"
        # Las alertas globales no tienen estatus "leído" para un destinatario específico (es broadcast)
        is_read_status = msg.is_read_by_recipient if msg.recipient_id else False 
        
        output.append({
            "id": msg.id,
            "sender_username": sender_username,
            "subject": msg.subject,
            "body": msg.body,
            "message_type": msg.message_type,
            "is_read_by_recipient": is_read_status, 
            "timestamp": msg.timestamp.isoformat() 
        })
            
    return jsonify(output), 200

@messages_bp.route("/api/messages/<string:message_id>/read", methods=["PATCH"])
@token_required
def mark_message_as_read(current_user, message_id):
    """Marca un mensaje como leído (solo si el usuario actual es el destinatario)."""
    message = Message.query.get(message_id)

    if not message:
        return jsonify({"message": "Mensaje no encontrado"}), 404

    # Solo el destinatario DIRECTO puede marcarlo como leído.
    if message.recipient_id != current_user.id:
        return jsonify({"message": "Acceso denegado. No eres el destinatario."}), 403

    message.is_read_by_recipient = True
    
    try:
        db.session.commit()
        return jsonify({"message": "Mensaje marcado como leído."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error al actualizar el mensaje.", "error": str(e)}), 500

@messages_bp.route("/api/messages/<string:message_id>", methods=["DELETE"])
@token_required
def delete_message(current_user, message_id):
    """Permite al destinatario directo de un mensaje (privado) o al Admin borrar cualquier mensaje."""
    
    message = Message.query.get(message_id)

    if not message:
        return jsonify({"message": "Mensaje no encontrado"}), 404

    # NORMALIZACIÓN DEL ROL para asegurar la verificación
    user_role = current_user.role.lower() if current_user.role else ''

    # --- LÓGICA DE PERMISOS DE BORRADO ---
    
    can_delete = False
    
    # 1. El Admin puede borrar CUALQUIER mensaje
    if user_role == 'admin':
        can_delete = True
        
    # 2. El Usuario solo puede borrar mensajes privados donde él es el destinatario
    elif message.recipient_id == current_user.id and message.message_type != 'alert':
        can_delete = True
        
    # Si no tiene permiso, retorna 403
    if not can_delete:
        # Mensaje de error más específico para el usuario
        error_msg = "Acceso denegado. Solo el destinatario directo puede borrar mensajes privados, y solo los administradores pueden borrar alertas."
        return jsonify({"message": error_msg}), 403

    # --- EJECUTAR BORRADO ---
    try:
        db.session.delete(message)
        db.session.commit()
        return jsonify({"message": "Mensaje eliminado con éxito."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error al eliminar el mensaje.", "error": str(e)}), 500