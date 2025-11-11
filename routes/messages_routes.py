from flask import Blueprint, request, jsonify
from models.db import db
from models.messages_models import Message
from models.users_models import User
from utils.auth import token_required # Asegúrate de que esta importación sea correcta
from sqlalchemy import or_ 
from datetime import datetime

messages_bp = Blueprint("messages", __name__)

# ----------------- Rutas de ENVÍO (POST) -----------------

@messages_bp.route("/api/messages/support", methods=["POST"])
@token_required
def send_support_message(current_user):
    # ... (verificaciones iniciales) ...

    # Busca al primer administrador para asignarlo como destinatario del ticket
    admin_user = User.query.filter_by(role='admin').first() # Asigna el primer Admin encontrado

    if not admin_user:
        # Esto es vital: asegura que exista un Admin para evitar NULL en recipient_id
        return jsonify({"message": "Error: No hay administradores disponibles para soporte."}), 500

    data = request.get_json()
    subject = data.get('subject')
    body = data.get('body')
    
    if not subject or not body:
        return jsonify({"message": "Asunto y cuerpo del mensaje son requeridos."}), 400

    new_message = Message(
        sender_id=current_user.id,
        recipient_id=admin_user.id, # <--- ¡Aquí se asigna el ID!
        subject=subject,
        body=body,
        message_type='support',
        is_read_by_recipient=False
    )

    try:
        db.session.add(new_message)
        db.session.commit()
        return jsonify({"message": "Mensaje de soporte enviado."}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error interno al guardar el mensaje.", "error": str(e)}), 500

@messages_bp.route("/api/messages/alert", methods=["POST"])
@token_required 
def send_global_alert(current_user):
    """Ruta para que un administrador envíe una alerta global a todos los usuarios."""
    if current_user.role != 'admin':
        return jsonify({"message": "Acceso denegado. Solo administradores pueden enviar alertas."}), 403
        
    data = request.get_json()
    body = data.get('body')
    subject = data.get('subject', 'ALERTA DEL SISTEMA') 

    if not body:
        return jsonify({"message": "El cuerpo de la alerta es requerido."}), 400

    new_alert = Message(
        sender_id=current_user.id,
        recipient_id=None,  # NULL para indicar que es un broadcast
        subject=subject,
        body=body,
        message_type='alert',
        is_read_by_recipient=False
    )

    try:
        db.session.add(new_alert)
        db.session.commit()
        return jsonify({"message": "Alerta global enviada con éxito."}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error interno al guardar la alerta.", "error": str(e)}), 500


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


# ----------------- Rutas de LECTURA/ESTADO (GET/PATCH) -----------------

@messages_bp.route("/api/messages", methods=["GET"])
@token_required
def get_user_messages(current_user):
    """
    Obtiene el buzón de mensajes del usuario logueado.
    Regla: Las alertas de paso son OBLIGATORIAS. Los mensajes privados/soporte son OPCIONALES.
    """
    
    # 1. Filtro base: Siempre mostramos las alertas del sistema.
    filters = (Message.message_type == 'alert') 
    
    # 2. Si las notificaciones están activadas, añadimos la condición para ver
    #    mensajes donde el usuario es el destinatario (privados/soporte).
    if current_user.notifications_enabled:
        
        # Usamos 'or_' para combinar:
        # a) Alertas (siempre)
        # b) Mensajes dirigidos al usuario (solo si el interruptor está ON)
        filters = or_(
            (Message.message_type == 'alert'), 
            (Message.recipient_id == current_user.id) 
        )
    
    # 3. Si las notificaciones están desactivadas, 'filters' solo contiene la condición 'alert'.
    #    La consulta final será: WHERE message_type = 'alert'
    #    Esto cumple la regla: alertas sí, privados no.
    
    messages = Message.query.filter(filters).order_by(Message.timestamp.desc()).all()
    
    # ... (El resto de la función para construir 'output' sigue igual) ...
    
    output = []
    for msg in messages:
        sender_user = User.query.get(msg.sender_id)
        sender_username = sender_user.username if sender_user else "Sistema" 
        
        output.append({
            "id": msg.id,
            "sender_username": sender_username,
            "subject": msg.subject,
            "body": msg.body,
            "message_type": msg.message_type,
            "is_read_by_recipient": msg.is_read_by_recipient,
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
    
    # routes/messages_routes.py (Añadir al final)

@messages_bp.route("/api/messages/<string:message_id>", methods=["DELETE"])
@token_required
def delete_message(current_user, message_id):
    """Permite al destinatario directo de un mensaje (privado o soporte) borrarlo."""
    
    message = Message.query.get(message_id)

    if not message:
        return jsonify({"message": "Mensaje no encontrado"}), 404

    # Regla de borrado:
    # 1. Solo el destinatario DIRECTO puede borrar (privado/soporte).
    # 2. Las ALERTA GLOBAL no pueden ser borradas por usuarios (deben ser borradas por Admin o no borrarse).
    if message.recipient_id != current_user.id or message.message_type == 'alert':
        return jsonify({"message": "Acceso denegado o mensaje no borrable."}), 403

    try:
        db.session.delete(message)
        db.session.commit()
        return jsonify({"message": "Mensaje eliminado con éxito."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error al eliminar el mensaje.", "error": str(e)}), 500
    
    