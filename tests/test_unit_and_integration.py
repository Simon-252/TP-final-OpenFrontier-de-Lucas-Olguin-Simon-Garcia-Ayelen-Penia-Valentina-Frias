
""""
import unittest
from flask import current_app
from models.db import db
from models.users_models import User # Asumo que tu modelo de usuario está aquí
from werkzeug.security import generate_password_hash
from app import app # Importa tu aplicación Flask principal
import jwt
import json
from datetime import datetime, timedelta

# 1. CLASE BASE DE PRUEBAS CON CONFIGURACIÓN AISLADA

class BaseTestCase(unittest.TestCase):
    ####""""""Clase base para configurar la aplicación en modo de prueba.""""""

    def setUp(self):
        ####""""""Se ejecuta antes de cada método de prueba.""""""
        
        # 1. Configuración de la aplicación en modo de prueba
        app.config.from_object('config.config') # Opcional: Cargar config principal
        app.config['TESTING'] = True
        
        # 2. **Base de Datos de Prueba Aislada**
        # Usamos una base de datos en memoria o un archivo de prueba específico.
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' 
        app.config['SECRET_KEY'] = 'supersecreto123' # Clave de prueba (debe coincidir con la de token_required)
        
        # 3. Inicializar DB y Cliente de Prueba
        self.app = app
        self.client = app.test_client()
        
        # 4. Crear el contexto de la aplicación
        with app.app_context():
            db.create_all() # Crea las tablas en la DB en memoria

    def tearDown(self):
       ### """"""Se ejecuta después de cada método de prueba.""""""
        with app.app_context():
            db.session.remove()
            db.drop_all() # Elimina las tablas de la DB en memoria

# 2. TEST DE INTEGRACIÓN: FLUJO ADMINISTRATIVO COMPLETO (CRUD)

class AdminIntegrationTest(BaseTestCase):

    def create_admin_and_login(self):
        ###""""""Registra un administrador y devuelve su token.""""""
        with self.app.app_context():
            admin_data = {
                "username": "admin_test",
                "email": "admin@test.com",
                "password": "adminpassword",
                "role": "admin",
                "phone": "12345678"
            }
            
            # Registrar Admin (usando la ruta de registro API)
            response = self.client.post('/api/auth/register', 
                                        data=json.dumps(admin_data), 
                                        content_type='application/json')
            self.assertEqual(response.status_code, 201)
            
            # Obtener el token del login exitoso
            token = response.json['token']
            return token

    def test_full_admin_crud_flow(self):
        ####""""""Prueba el flujo completo: Login -> Registro User -> CRUD por Admin.""""""
        
        # --- PASO 1: LOGIN Y OBTENCIÓN DE TOKEN DE ADMIN ---
        admin_token = self.create_admin_and_login()
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        
        # --- PASO 2: REGISTRAR UN USUARIO REGULAR PARA MODIFICAR ---
        user_data = {
            "username": "user_to_mod",
            "email": "user@mod.com",
            "password": "userpassword",
            "role": "user",
            "phone": "87654321"
        }
        response = self.client.post('/api/auth/register', 
                                    data=json.dumps(user_data), 
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        
        # Obtener el ID del nuevo usuario (usamos la lista para encontrarlo)
        response = self.client.get('/api/users', headers=admin_headers)
        self.assertEqual(response.status_code, 200)
        users = response.json['users']
        user_id_to_mod = next(u['id'] for u in users if u['email'] == user_data['email'])

        # --- PASO 3: MODIFICAR ROL (PATCH) ---
        new_role = 'admin' if users[0]['role'] == 'user' else 'user'
        response = self.client.patch(f'/api/users/{user_id_to_mod}',
                                     headers=admin_headers,
                                     data=json.dumps({'role': new_role}),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('role updated', response.json['message'])

        # Verificación del Rol en la DB
        with self.app.app_context():
            mod_user = User.query.get(user_id_to_mod)
            self.assertEqual(mod_user.role, new_role)

        # --- PASO 4: SUSPENDER/REACTIVAR CUENTA (PUT status) ---
        response = self.client.put(f'/api/users/{user_id_to_mod}/status',
                                    headers=admin_headers,
                                    data=json.dumps({'is_active': False}), # Suspender
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('suspendida', response.json['message'])

        # Verificación del Estado en la DB
        with self.app.app_context():
            mod_user = User.query.get(user_id_to_mod)
            self.assertFalse(mod_user.is_active)

        # --- PASO 5: ELIMINAR USUARIO (DELETE) ---
        response = self.client.delete(f'/api/users/{user_id_to_mod}',
                                      headers=admin_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('deleted successfully', response.json['message'])

        # Verificación de Eliminación en la DB
        with self.app.app_context():
            deleted_user = User.query.get(user_id_to_mod)
            self.assertIsNone(deleted_user)


# 3. TEST UNITARIO: VALIDACIÓN DEL MODELO/LÓGICA SIMPLE
class UnitTests(BaseTestCase):
    
    def test_user_model_creation(self):
        ####""""Verifica la creación y hash de contraseña del modelo User.""""""
        with self.app.app_context():
            hashed_password = generate_password_hash("testpassword")
            user = User(
                username='unituser', 
                email='unit@test.com', 
                password=hashed_password
            )
            db.session.add(user)
            db.session.commit()
            
            retrieved_user = User.query.filter_by(email='unit@test.com').first()
            
            self.assertIsNotNone(retrieved_user)
            self.assertEqual(retrieved_user.username, 'unituser')
            # Verifica que el hash de la contraseña funcione
            self.assertTrue(retrieved_user.check_password("testpassword"))

"""""
import unittest
from flask import current_app
# **Importación corregida:** Añadimos 'timezone' para ser compatibles con la corrección de utcnow() en otros archivos
from datetime import datetime, timedelta, timezone 
from models.db import db
from models.users_models import User
from models.messages_models import Message
from werkzeug.security import generate_password_hash, check_password_hash
from app import app 
import jwt
import json

# 1. CLASE BASE DE PRUEBAS CON CONFIGURACIÓN AISLADA

class BaseTestCase(unittest.TestCase):
    """Clase base para configurar la aplicación en modo de prueba."""

    def setUp(self):
        """Se ejecuta antes de cada método de prueba."""
        
        # 1. Configuración de la aplicación en modo de prueba
        # app.config.from_object('config.config') # Opcional: Cargar config principal
        app.config['TESTING'] = True
        
        # 2. **Base de Datos de Prueba Aislada**
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' 
        app.config['SECRET_KEY'] = 'supersecreto123' # Clave de prueba
        
        # 3. Inicializar DB y Cliente de Prueba
        self.app = app
        self.client = app.test_client()
        
        # 4. Crear el contexto de la aplicación y las tablas
        with app.app_context():
            # Importa modelos aquí para asegurar que se registren
            from models.users_models import User
            from models.messages_models import Message 
            db.create_all() # Crea las tablas en la DB en memoria

    def tearDown(self):
        """Se ejecuta después de cada método de prueba."""
        with app.app_context():
            db.session.remove()
            db.drop_all() # Elimina las tablas de la DB en memoria

# 2. TEST DE INTEGRACIÓN: FLUJO ADMINISTRATIVO COMPLETO (CRUD)

class AdminIntegrationTest(BaseTestCase):

    def create_admin_and_login(self):
        """Registra un administrador y devuelve su token."""
        with self.app.app_context():
            admin_data = {
                "username": "admin_test",
                "email": "admin@test.com",
                "password": "adminpassword",
                "role": "admin",
                "phone": "12345678"
            }
            
            # Registrar Admin (usando la ruta de registro API)
            response = self.client.post('/api/auth/register', 
                                         data=json.dumps(admin_data), 
                                         content_type='application/json')
            self.assertEqual(response.status_code, 201)
            
            # Obtener el token del login exitoso
            token = response.json['token']
            return token

    def test_full_admin_crud_flow(self):
        """Prueba el flujo completo: Login -> Registro User -> CRUD por Admin."""
        
        # --- PASO 1: LOGIN Y OBTENCIÓN DE TOKEN DE ADMIN ---
        admin_token = self.create_admin_and_login()
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        
        # --- PASO 2: REGISTRAR UN USUARIO REGULAR PARA MODIFICAR ---
        user_data = {
            "username": "user_to_mod",
            "email": "user@mod.com",
            "password": "userpassword",
            "role": "user",
            "phone": "87654321"
        }
        response = self.client.post('/api/auth/register', 
                                     data=json.dumps(user_data), 
                                     content_type='application/json')
        self.assertEqual(response.status_code, 201)
        
        # Obtener el ID del nuevo usuario (usamos la lista para encontrarlo)
        response = self.client.get('/api/users', headers=admin_headers)
        self.assertEqual(response.status_code, 200)
        users = response.json['users']
        user_id_to_mod = next(u['id'] for u in users if u['email'] == user_data['email'])

        # --- PASO 3: MODIFICAR ROL (PATCH) ---
        new_role = 'admin'
        response = self.client.patch(f'/api/users/{user_id_to_mod}',
                                     headers=admin_headers,
                                     data=json.dumps({'role': new_role}),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('role updated', response.json['message'])

        # Verificación del Rol en la DB
        with self.app.app_context():
            # CORRECCIÓN DE WARNING: Reemplazado User.query.get() por db.session.get()
            mod_user = db.session.get(User, user_id_to_mod)
            self.assertEqual(mod_user.role, new_role)

        # --- PASO 4: SUSPENDER/REACTIVAR CUENTA (PUT status) ---
        response = self.client.put(f'/api/users/{user_id_to_mod}/status',
                                   headers=admin_headers,
                                   data=json.dumps({'is_active': False}), # Suspender
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('suspendida', response.json['message'])

        # Verificación del Estado en la DB
        with self.app.app_context():
            # CORRECCIÓN DE WARNING: Reemplazado User.query.get() por db.session.get()
            mod_user = db.session.get(User, user_id_to_mod)
            self.assertFalse(mod_user.is_active)

        # --- PASO 5: ELIMINAR USUARIO (DELETE) ---
        response = self.client.delete(f'/api/users/{user_id_to_mod}',
                                      headers=admin_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('deleted successfully', response.json['message'])

        # Verificación de Eliminación en la DB
        with self.app.app_context():
            # CORRECCIÓN DE WARNING: Reemplazado User.query.get() por db.session.get()
            deleted_user = db.session.get(User, user_id_to_mod)
            self.assertIsNone(deleted_user)


# 3. TEST UNITARIO: VALIDACIÓN DEL MODELO/LÓGICA SIMPLE
class UnitTests(BaseTestCase):
    
    # --- TEST UNITARIO 1: Creación básica de Usuario ---
    def test_user_model_creation(self):
        """Verifica la creación y hash de contraseña del modelo User."""
        with self.app.app_context():
            user = User(
                username='unituser', 
                email='unit@test.com', 
            )
            user.set_password("testpassword")
            
            db.session.add(user)
            db.session.commit()
            
            # Aquí se usa .filter_by().first(), que no genera el warning.
            retrieved_user = User.query.filter_by(email='unit@test.com').first()
            
            self.assertIsNotNone(retrieved_user)
            self.assertEqual(retrieved_user.username, 'unituser')
            self.assertTrue(retrieved_user.check_password("testpassword"))

    # --- TEST UNITARIO 2: Verificación de Contraseña ---
    def test_password_hashing_utility(self):
        """Verifica que la utilidad de hashing funcione correctamente (correcto/incorrecto)."""
        user = User(username='hashcheck', email='hash@test.com')
        user.set_password("SecurePwd123") 
        
        # Prueba 1: Contraseña Correcta (Debe ser True)
        self.assertTrue(user.check_password("SecurePwd123"))
        
        # Prueba 2: Contraseña Incorrecta (Debe ser False)
        self.assertFalse(user.check_password("WrongPwd321"))
        
        # Prueba 3: Verificar que el hash no es el texto plano
        self.assertNotEqual(user.password, "SecurePwd123")

    # --- TEST UNITARIO 3: Creación de Mensaje (CORREGIDO) ---
    def test_message_creation_logic(self):
        """Verifica que un mensaje se pueda crear y asociar correctamente a un usuario."""
        with self.app.app_context():
            # 1. Crear usuarios de prueba
            recipient_user = User(username='msg_recipient', email='msg@test.com')
            recipient_user.set_password('pwd')
            sender_user = User(username='msg_sender', email='sender@test.com')
            sender_user.set_password('sender_pwd')
            
            db.session.add_all([recipient_user, sender_user])
            db.session.commit()

            # 2. Crear un mensaje asociado
            message = Message(
                subject='Test Subject',
                body='Test Body for Unit Test',
                recipient_id=recipient_user.id,
                sender_id=sender_user.id,
                is_read_by_recipient=False
            )
            db.session.add(message)
            db.session.commit()

            # 3. Verificación
            # CORRECCIÓN DE WARNING: Reemplazado Message.query.get() por db.session.get()
            retrieved_message = db.session.get(Message, message.id) 
        
            self.assertIsNotNone(retrieved_message)
            self.assertEqual(retrieved_message.recipient_id, recipient_user.id)
            self.assertEqual(retrieved_message.sender_id, sender_user.id)
            self.assertEqual(retrieved_message.subject, 'Test Subject')
            
            # Verificación de la relación inversa
            self.assertEqual(retrieved_message.recipient.username, 'msg_recipient')
            self.assertEqual(retrieved_message.sender.username, 'msg_sender')


            