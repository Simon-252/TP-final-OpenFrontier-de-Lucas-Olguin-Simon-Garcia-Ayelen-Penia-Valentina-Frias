import uuid
from models.db import db

class Clima(db.Model):
    __tablename__ = "climas"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    paso_id = db.Column(db.String(36), db.ForeignKey("pasos.id"), nullable=False)  # Relación con Paso
    temperatura = db.Column(db.Float, nullable=True)
    descripcion = db.Column(db.String(120), nullable=True)
    viento = db.Column(db.Float, nullable=True)
    fecha = db.Column(db.DateTime, server_default=db.func.now())

    paso = db.relationship("Paso", backref="climas")

    def to_dict(self):
        return {
            "id": self.id,
            "paso_id": self.paso_id,
            "temperatura": self.temperatura,
            "descripcion": self.descripcion,
            "viento": self.viento,
            "fecha": self.fecha.isoformat() if self.fecha else None
        }
