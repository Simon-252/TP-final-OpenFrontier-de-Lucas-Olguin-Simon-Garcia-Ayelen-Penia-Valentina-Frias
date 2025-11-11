import os
import json
# Importamos 'app' y el contexto de Flask
from app import app 
from models.db import db
# Importamos el modelo de Usuario
from models.users_models import User 
# Necesitamos la herramienta de seguridad para hashear contraseñas
from werkzeug.security import generate_password_hash

DATA_DIR = 'data'

def populate_users(data):
    """Carga usuarios ficticios en la tabla User, hasheando sus contraseñas."""
    created = 0
    for item in data:
        # 1. Obtener datos del JSON
        username = item.get('username')
        email = item.get('email')
        password = item.get('password')
        phone = item.get('phone')
        role = item.get('role', 'user') # 'user' por defecto

        # 2. Validación mínima de campos
        if not all([username, email, password, phone]):
            print(f"Skipping user due to missing data: {username}")
            continue

        # 3. Verificar si el usuario ya existe por email o username
        exists = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()

        if exists:
            print(f"User already exists: {email}")
            continue

        # 4. Hashear la contraseña antes de guardarla
        hashed_pw = generate_password_hash(password)

        # 5. Crear y añadir el nuevo usuario
        user = User(
            username=username, 
            email=email, 
            password=hashed_pw, 
            phone=phone,
            role=role
        )
        db.session.add(user)
        created += 1

    return created

def populate_all():
    """Busca archivos JSON en el directorio 'data' y los procesa."""
    with app.app_context():
        print("Entrando en el contexto de la app...")
        
        # Opcional: Eliminar usuarios existentes antes de cargar (descomenta si quieres un borrado limpio)
        # db.session.query(User).delete() 
        # print("Tabla de Usuarios limpiada.")
        
        for filename in os.listdir(DATA_DIR):
            if filename.endswith('users.json'):
                filepath = os.path.join(DATA_DIR, filename)
                print(f"Procesando archivo: {filename}")
                
                with open(filepath, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                
                created = populate_users(data)
                print(f'{created} usuarios cargados y hasheados.')
        
        print("Haciendo commit a la base de datos...")
        db.session.commit()
        print("Carga de datos finalizada con éxito.")


if __name__ == '__main__':
    populate_all()