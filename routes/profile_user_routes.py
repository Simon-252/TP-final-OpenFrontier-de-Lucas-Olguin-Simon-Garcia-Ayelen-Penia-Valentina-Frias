from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import jwt
from models.users_models import User
from models.db import db
from config.constantes import token_required # Asumo que esta es la ubicación correcta
from flask import current_app

# Crea la nueva Blueprint para el perfil
profile_bp = Blueprint('profile', __name__) 


# =========================================================================
# 1. RUTA DE VISTA (GET /profile)
# =========================================================================

@profile_bp.route("/profile", methods=["GET"], endpoint="view_profile_page")
@token_required 
def profile_page(current_user): 
    """Muestra la página del perfil del usuario logueado."""
    return render_template("profile.html", user=current_user)


# =========================================================================
# 2. API DE ACTUALIZACIÓN (PUT /api/profile)
# =========================================================================

@profile_bp.route("/api/profile", methods=["PUT"], endpoint="update_profile_api")
@token_required
def update_profile(current_user):
    data = request.get_json()
    changes_made = False
    
    # ------------------------------------
    # Lógica de Actualización de Datos
    # ------------------------------------
    
    # --- Actualizar nombre de usuario ---
    if 'username' in data and data['username'] != current_user.username:
        # Verificar si el nuevo username ya existe
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'message': 'El nombre de usuario ya está en uso.'}), 400
        current_user.username = data['username']
        changes_made = True 

    # --- Actualizar número de teléfono ---
    # Usamos .get() para manejar la posible ausencia de la clave si solo se actualiza la contraseña
    # Si el valor es None (o la cadena vacía si es un PUT desde el formulario) lo guarda.
    if 'phone' in data and data['phone'] != current_user.phone:
        # Nota: La validación de formato (e.g., regex) debería hacerse aquí o en el frontend.
        current_user.phone = data['phone'] if data['phone'] else None # Guardar None si está vacío
        changes_made = True 
    
    # --- Actualizar contraseña ---
    password_changed = False # Nuevo flag para manejo de mensaje
    if 'new_password' in data and data['new_password']:
        old_password = data.get('old_password')
        if not old_password or not current_user.check_password(old_password):
            return jsonify({'message': 'Contraseña actual incorrecta.'}), 401
        current_user.set_password(data['new_password']) 
        changes_made = True
        password_changed = True

    # ------------------------------------
    # Manejo de Respuesta y Token
    # ------------------------------------
    
    # Si no hubo cambios en datos ni en contraseña, devolver un 200 sin hacer commit
    if not changes_made:
        return jsonify({'message': 'No se proporcionaron datos nuevos para actualizar.'}), 200

    try:
        db.session.commit()
        
        # Generar un nuevo token con los datos actualizados
        new_token_payload = {
            'id': str(current_user.id),
            'exp': datetime.utcnow() + timedelta(hours=1),
            'role': current_user.role,
            'username': current_user.username,
            # Asegurar que el teléfono esté en el payload para el frontend
            'phone': current_user.phone
        }

        new_token = jwt.encode(new_token_payload, 
                               current_app.config['SECRET_KEY'], 
                               algorithm="HS256")
        
        # Determinar el mensaje de éxito
        if password_changed and changes_made:
            success_message = 'Perfil y contraseña actualizados con éxito.'
        elif password_changed:
             success_message = 'Contraseña actualizada con éxito.'
        else:
             success_message = 'Perfil actualizado con éxito.'

        return jsonify({
            'message': success_message, 
            'username': current_user.username,
            'token': new_token,
            'phone': current_user.phone
        }), 200
        
    except Exception as e:
        db.session.rollback()
        # Puedes loguear el error 'e' aquí para debug
        return jsonify({'message': f'Error al guardar cambios en la base de datos.'}), 500

# =========================================================================
# 3. API DE GESTIÓN DE CUENTA (DELETE, PUT /api/profile/status)
# =========================================================================

@profile_bp.route("/api/profile/status", methods=["PUT", "DELETE"], endpoint="manage_profile_status")
@token_required
def manage_account(current_user):
    action = request.method
    
    if action == "PUT":
        # Activar/Desactivar cuenta (Suspender / Reactivar)
        data = request.get_json()
        if 'is_active' in data:
            current_user.is_active = data['is_active']
            action_name = "Activada" if data['is_active'] else "Suspendida"
            try:
                db.session.commit()
                # Devolver un mensaje más específico si es solo una actualización de estado
                return jsonify({'message': f'Cuenta {action_name} con éxito. Se requiere relogear.'}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': 'Error al cambiar estado de cuenta.'}), 500
        else:
            return jsonify({'message': 'Parámetro is_active requerido.'}), 400

    elif action == "DELETE":
        # Eliminar cuenta
        try:
            db.session.delete(current_user)
            db.session.commit()
            return jsonify({'message': 'Cuenta eliminada con éxito.'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': 'Error al eliminar cuenta.'}), 500
            
    return jsonify({'message': 'Método no permitido.'}), 405

# =========================================================================
# 4. API DE PREFERENCIAS DE NOTIFICACIÓN (PATCH /api/settings/notifications)
# =========================================================================

@profile_bp.route("/api/settings/notifications", methods=["PATCH"], endpoint="toggle_notifications_api")
@token_required
def toggle_notifications(current_user):
    data = request.get_json()
    
    if 'enabled' not in data:
        return jsonify({"message": "Falta el campo 'enabled'."}), 400
        
    # El valor 'enabled' debe ser un booleano (True/False)
    # Flask ya lo convierte si viene de JSON como true/false, pero bool() asegura la conversión.
    new_state = bool(data['enabled']) 
    
    current_user.notifications_enabled = new_state
    
    try:
        db.session.commit()
        return jsonify({
            "message": "Preferencias de notificación actualizadas.",
            "new_state": new_state
        }), 200
    except Exception as e:
        db.session.rollback()
        # Nota: Es útil loguear 'str(e)' en tu log de errores para debug.
        return jsonify({"message": "Error al guardar preferencia.", "error": "Contacte a soporte."}), 500
    



    