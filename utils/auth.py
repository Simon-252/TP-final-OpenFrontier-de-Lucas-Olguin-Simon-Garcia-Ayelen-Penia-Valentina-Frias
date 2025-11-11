from functools import wraps
from flask import request, jsonify, current_app
from models.users_models import User
import jwt

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            print("⚠️ No se recibió token en headers.")
            return jsonify({'message': 'Token requerido.'}), 401

        try:
            data = jwt.decode(token, 'supersecreto123', algorithms=["HS256"])
            print(f"🟢 DEBUG PAYLOAD: {data}")

            user_id = data.get('id') or data.get('user_id')
            current_user = User.query.get(user_id)

            if not current_user:
                print(f"❌ Usuario con ID {user_id} no encontrado en la BD.")
                return jsonify({'message': 'Usuario no encontrado.'}), 401

        except jwt.ExpiredSignatureError:
            print("❌ Token expirado.")
            return jsonify({'message': 'Token expirado.'}), 401
        except jwt.InvalidTokenError:
            print("❌ Token inválido.")
            return jsonify({'message': 'Token inválido.'}), 401
        except Exception as e:
            print(f"💥 Error general al validar token: {e}")
            return jsonify({'message': f'Error al validar token: {e}'}), 500

        return f(current_user, *args, **kwargs)

    return decorated
