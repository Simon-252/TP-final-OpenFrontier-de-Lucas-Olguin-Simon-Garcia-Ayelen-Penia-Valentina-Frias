import uuid

from models.db import db

from werkzeug.security import generate_password_hash, check_password_hash

# ^ Asegúrate de que ambas funciones están importadas



class User(db.Model):

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    username = db.Column(db.String(90), unique=True, nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password = db.Column(db.Text, nullable=False) # Almacena el hash aquí

    role = db.Column(db.String(20), default="user", nullable=False)

    phone = db.Column(db.String(20), nullable=True)

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    notifications_enabled = db.Column(db.Boolean, default=True, nullable=False)



    # 🔐 MÉTODOS DE SEGURIDAD DE CONTRASEÑA (NUEVO)



    def set_password(self, password):

        """Hashea la contraseña y la asigna a la columna self.password."""

        self.password = generate_password_hash(password)



    def check_password(self, password):

        """Compara una contraseña en texto plano con el hash almacenado."""

        # Esta es la función que requería el test:

        return check_password_hash(self.password, password)



    # SERIALIZACIÓN



    def to_dict(self):

        return {

            'id': self.id,

            'username': self.username,

            'email': self.email,

            'role': self.role,

            'phone': self.phone,

            'is_active': self.is_active

        }