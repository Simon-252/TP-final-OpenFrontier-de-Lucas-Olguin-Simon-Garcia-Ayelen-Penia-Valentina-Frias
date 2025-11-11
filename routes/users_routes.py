from flask import Blueprint, request, jsonify, render_template, current_app
from models.users_models import User
from models.db import db
from config.constantes import token_required
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from flask import current_app as app 
from functools import wraps 
from datetime import datetime, timedelta
from models.messages_models import Message

auth_bp = Blueprint('auth', __name__)



# --- 1. RUTA DE REGISTRO (API) ---
@auth_bp.route("/api/auth/register", methods=["POST"]) 
def register():
    data = request.get_json()
    
    # 1. Verificar existencia de email
    if User.query.filter_by(email=data['email']).first():
        # *** CORRECCIÓN DE LOGGING ***
        current_app.logger.warning(f"🔴 Intento de registro fallido: Email {data['email']} ya existe.") 
        return jsonify({'message': 'Email already exists'}), 400

    # 2. Lógica de creación de usuario
    hashed_pw = generate_password_hash(data['password'])
    new_user = User(
        username=data['username'],
        email=data['email'],
        password=hashed_pw,
        role=data.get('role', 'user'),
        phone=data['phone']
    )
    
    # 3. Guardar en la DB y hacer commit
    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # *** CORRECCIÓN DE LOGGING ***
        current_app.logger.error(f"🔴 Error de DB al registrar usuario {data['email']}: {str(e)}")
        return jsonify({"message": "Error interno al guardar el usuario."}), 500

    # 4. Generación de token (usa 'app' que es un alias de current_app)
    token = jwt.encode({
        'id': str(new_user.id),
        'exp': datetime.utcnow() + timedelta(hours=1),
        'role': new_user.role
    }, app.config['SECRET_KEY'], algorithm="HS256")


    # 5. Logging de éxito
    # *** CORRECCIÓN DE LOGGING ***
    current_app.logger.info(f"🟢 Nuevo usuario registrado exitosamente: ID {new_user.id} ({new_user.username})") 
    
    
    # 6. Retorno de éxito
    return jsonify({
        'message': 'User created successfully',
        'token': token,
        'redirect_url': '/' 
    }), 201


# --- 2. RUTA DE LOGIN (API) ---
@auth_bp.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()

    if not user or not user.check_password(data['password']):
        current_app.logger.warning(f"🔴 Intento de inicio de sesión fallido para el email: {data.get('email')}")
        return jsonify({'message': 'Invalid credentials'}), 401
    
    # Si la cuenta está suspendida
    if not user.is_active:
        current_app.logger.warning(f"🔴 Intento de inicio de sesión bloqueado: Cuenta suspendida para el email: {data.get('email')}")
        return jsonify({'message': 'Account is suspended. Please contact support.'}), 403


    # Éxito:
    token = jwt.encode({
        'id': str(user.id),
        'exp': datetime.utcnow() + timedelta(hours=1),
        'role': user.role
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    # *** CORRECCIÓN DE LOGGING ***
    current_app.logger.info(f"🟢 Inicio de sesión exitoso: Usuario ID {user.id} ({user.username})")
    
    # ... (Lógica de redirección y return final) ...
    if user.role == 'admin':
        final_redirect_url = '/dashboard' 
    else:
        final_redirect_url = '/' 

    return jsonify({
        'token': token,
        'role': user.role,
        'username': user.username,
        'redirect_url': final_redirect_url
    })


# --- 3. RUTA DE LOGOUT (API) ---
@auth_bp.route("/api/auth/logout", methods=["POST"])
@token_required
def api_logout(current_user):
    # Log del evento de cierre de sesión
    current_app.logger.info(f"🚪 Usuario cerró sesión: {current_user.username} (ID: {current_user.id})")
    return jsonify({"message": "Logout registered"}), 200


# --- 4. RUTA DE LISTAR USUARIOS (Admin) con BÚSQUEDA, PAGINACIÓN y ORDENAMIENTO ---
@auth_bp.route("/api/users", methods=["GET"])
@token_required("admin") 
def list_users(current_user): 
    
    # 1. Parámetros de Paginación y Ordenamiento
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int) 
    sort_by = request.args.get('sort_by', 'username') 
    
    # 🔥 Nuevos Parámetros de Búsqueda y Filtro 🔥
    search_term = request.args.get('search', None) # Busca por nombre/email
    filter_role = request.args.get('role', None) # 'user' o 'admin'
    filter_id = request.args.get('user_id', None, type=str) # Busca por ID específico
    
    query = User.query
    
    # --- 2. Aplicar FILTRO por ID Específico ---
    if filter_id:
        # Esto busca por ID (útil para consultas directas)
        query = query.filter(User.id == filter_id)
        
    # --- 3. Aplicar FILTRO por Rol (Tipo de usuario) ---
    if filter_role and filter_role in ['user', 'admin']:
        # Esto filtra por el tipo de usuario (user o admin)
        query = query.filter(User.role == filter_role)
    
    # --- 4. Aplicar Filtro de Búsqueda por Nombre o Email (Búsqueda por Texto) ---
    if search_term:
        search_pattern = f'%{search_term}%'
        query = query.filter(
            db.or_(
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern)
            )
        )
    
    # 5. Aplicar Ordenamiento
    if sort_by == 'email':
        query = query.order_by(User.email)
    elif sort_by == 'role':
        query = query.order_by(User.role)
    elif sort_by == 'id': # Opcional: ordenar por ID
        query = query.order_by(User.id)
    else: 
        query = query.order_by(User.username)
        
    # 6. Aplicar Paginación
    users_page = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # 7. Formatear la lista de usuarios para la página actual
    users_data = []
    for u in users_page.items: 
        users_data.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active if u.is_active is not None else False 
        })
        
    # 8. Devolver los datos de los usuarios MÁS la información de paginación
    return jsonify({
        'users': users_data,
        'pagination': {
            'total_items': users_page.total,
            'total_pages': users_page.pages,
            'current_page': users_page.page,
            'per_page': users_page.per_page,
            'has_next': users_page.has_next,
            'has_prev': users_page.has_prev
        }
    }), 200

# --- 5. Rutas HTML (render_template) ---
@auth_bp.route("/register", methods=["GET"]) 
def register_page():
    return render_template("register.html")

@auth_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@auth_bp.route("/dashboard", methods=["GET"])
def dashboard_page():
    return render_template("dashboard_lista_de_usuario.html")

@auth_bp.route("/panel_clima_y_pasos", methods=["GET"])
def panel_clima_y_pasos():
    return render_template("panel_clima_y_pasos.html")

@auth_bp.route("/mapa", methods=["GET"])
def map_page():
    return render_template("mapa.html")

@auth_bp.route("/api/dashboard", methods=["GET"])
@token_required
def dashboard_api(current_user):
    return jsonify({
        'username': current_user.username,
        'role': current_user.role
    })


# --- 6. Rutas de ADMINISTRACIÓN (Mantener current_app.logger) ---

@auth_bp.route("/api/users/<user_id>", methods=["PATCH"])
@token_required("admin")
def update_user_role(current_user, user_id):
# ... (El cuerpo de esta función está correcto) ...
    user_to_update = User.query.get(user_id)
    
    if not user_to_update:
        current_app.logger.warning(f"🟡 Admin {current_user.username} (ID: {current_user.id}) intentó modificar el rol del Usuario ID {user_id}, pero no fue encontrado.")
        return jsonify({"message": "User not found"}), 404
        
    data = request.get_json()
    new_role = data.get('role')

    if user_to_update.id == current_user.id and new_role != 'admin':
        current_app.logger.warning(f"🔴 Admin {current_user.username} (ID: {current_user.id}) fue bloqueado al intentar degradar su propio rol.")
        return jsonify({"message": "Admin cannot downgrade their own role via API"}), 403

    
    if not new_role or new_role not in ['user', 'admin']:
        current_app.logger.warning(f"🟡 Admin {current_user.username} (ID: {current_user.id}) intentó establecer un rol inválido: '{new_role}' en Usuario ID {user_id}.")
        return jsonify({"message": "Invalid role provided"}), 400

    old_role = user_to_update.role
    user_to_update.role = new_role
    try:
        db.session.commit()
        current_app.logger.info(f"🟢 Admin {current_user.username} (ID: {current_user.id}) cambió el rol de {user_to_update.username} (ID: {user_id}) de '{old_role}' a '{new_role}'.")
        return jsonify({"message": f"User {user_id} role updated to {new_role}"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"🔴 Error de DB: Admin {current_user.username} no pudo cambiar el rol de {user_id}: {str(e)}")
        return jsonify({"message": "Error al actualizar el rol."}), 500




@auth_bp.route("/api/users/<user_id>", methods=["DELETE"])
@token_required("admin")
def delete_user(current_user, user_id): # <-- ESTE ES EL NOMBRE CORRECTO AQUÍ
    user_to_delete = User.query.get(user_id)
    
    # ... (verificaciones previas: user_to_delete existe, no es el admin actual)
    
    try:
        # **ELIMINACIÓN MANUAL DE DEPENDENCIAS**
        from models.messages_models import Message # Aseguramos la importación aquí si no está al principio
        
        # 1. ELIMINAR MENSAJES ENVIADOS
        Message.query.filter(Message.sender_id == user_to_delete.id).delete(synchronize_session=False)
        
        # 2. ELIMINAR MENSAJES RECIBIDOS
        Message.query.filter(Message.recipient_id == user_to_delete.id).delete(synchronize_session=False)
        
        # 3. Eliminar el usuario (ahora libre de dependencias)
        db.session.delete(user_to_delete)
        db.session.commit()
        
        current_app.logger.info(f"🟢 Admin {current_user.username} (ID: {current_user.id}) ELIMINÓ la cuenta del usuario: {user_to_delete.username} (ID: {user_id}) y sus mensajes asociados.")
        return jsonify({"message": f"User {user_id} deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"🔴 Error de DB: Admin {current_user.username} no pudo eliminar el usuario {user_id}: {str(e)}")
        return jsonify({"message": "Error al eliminar el usuario."}), 500


@auth_bp.route('/api/users/<string:user_id>/status', methods=['PUT'])
@token_required("admin")
# Cambiar el nombre aquí:
def toggle_user_status(current_user, user_id): 
    # Aquí debe ir la lógica para cambiar el estado de la cuenta (que se perdió).
    # DEBES REINSERTAR LA LÓGICA ORIGINAL DE toggle_user_status aquí.
    # El código que pusiste aquí era la LÓGICA DE ELIMINAR, ¡hay que quitarlo!
    
    # Aquí va la lógica original (la que tenías antes de intentar la solución CASCADE/manual):
    data = request.get_json()
    new_status = data.get('is_active')

    if not isinstance(new_status, bool):
        return jsonify({"message": "El valor de 'is_active' debe ser booleano (true/false)."}), 400

    user = User.query.get(user_id)
    if user is None:
        return jsonify({"message": "Usuario no encontrado"}), 404
        
    if user.id == current_user.id:
        current_app.logger.warning(f"🔴 Admin {current_user.username} (ID: {current_user.id}) fue bloqueado al intentar cambiar su propio estado de cuenta.")
        return jsonify({"message": "No puedes cambiar tu propio estado de cuenta desde el panel de usuarios."}), 403

    try:
        old_status_text = "activa" if user.is_active else "suspendida"
        user.is_active = new_status
        db.session.commit()
        
        status_text = "activada" if new_status else "suspendida"
        current_app.logger.info(f"🟢 Admin {current_user.username} (ID: {current_user.id}) cambió el estado de {user.username} (ID: {user_id}) de '{old_status_text}' a '{status_text}'.")
        
        return jsonify({"message": f"Cuenta de usuario {user.username} ha sido {status_text} exitosamente."}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"🔴 Error de DB: Admin {current_user.username} no pudo cambiar el estado del usuario {user_id}: {str(e)}")
        return jsonify({"message": f"Error del servidor al actualizar el estado: {str(e)}"}), 500
#-------------