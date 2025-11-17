from flask import Blueprint, request, jsonify, render_template, current_app
from models.users_models import User
from models.db import db
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps #sirve para decorar funciones
from datetime import datetime, timedelta
#Constantes para actualizar el estado del paso
ARCHIVO = "estado.json"
URL = "https://www.argentina.gob.ar/seguridad/pasosinternacionales/detalle/ruta/29/Cristo-Redentor"

IMAGE_FILENAMES = [
    "paso_verano_1.png",
    "paso_nieve_2.png",
    "paso_tarde_3.png",
    "paso_dia_4.png",
    "paso_5.png",
    "paso_6.png",
    "paso_7.png",
    "paso_8.jpg",
    "paso_9.jpg"
]

# Función decoradora constante para proteger rutas con token JWT
def _token_required_impl(f, role=None):
    """Implementación interna del decorador."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            token = token.split()[1]
            # Usar current_app.config de forma segura
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"]) 
            current_user = User.query.get(data['id'])
            
            if not current_user:
                return jsonify({'message': 'User not found'}), 404
            
            # Comprobación de rol
            if role and current_user.role != role: 
                return jsonify({'message': 'Unauthorized role'}), 403
                
        except Exception as e:
            return jsonify({'message': 'Token is invalid', 'error': str(e)}), 401
            
        # Pasa el usuario actual como primer argumento a la función de la vista
        return f(current_user, *args, **kwargs)
    return decorated

def token_required(arg=None):
    """
    Función decoradora principal.
    Puede ser llamada como @token_required o @token_required('admin').
    """
    if callable(arg):
        # Caso 1: Se usa sin argumentos, ej: @token_required
        # 'arg' es la función de vista (f).
        return _token_required_impl(arg)
    else:
        # Caso 2: Se usa con argumentos, ej: @token_required('admin')
        # 'arg' es el 'role'.
        def wrapper(f):
            return _token_required_impl(f, role=arg)
        return wrapper
