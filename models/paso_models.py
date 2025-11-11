import uuid
from models.db import db

class Paso(db.Model):
    __tablename__ = "pasos"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    estado = db.Column(db.String(50), nullable=True)
    horario_atencion = db.Column(db.Text, nullable=True)
    actualizado = db.Column(db.Text, nullable=True)  # texto de fecha que trae la web
    fuente = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "estado": self.estado,
            "horario_atencion": self.horario_atencion,
            "actualizado": self.actualizado,
            "fuente": self.fuente,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

