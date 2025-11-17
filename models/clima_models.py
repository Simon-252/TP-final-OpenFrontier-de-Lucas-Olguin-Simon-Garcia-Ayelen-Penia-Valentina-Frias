import uuid
from models.db import db
from datetime import date # 🔑 Importa 'date' para el campo de fecha de pronóstico

class PronosticoDiario(db.Model):
    __tablename__ = "pronosticos_diarios" # 💡 Recomendado: Cambiar el nombre para reflejar que es un pronóstico.

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    paso_id = db.Column(db.String(36), db.ForeignKey("pasos.id"), nullable=False) 
    
    # 🔑 CLAVE: Fecha del pronóstico (Ej: 2025-11-14). No incluye la hora.
    fecha_pronostico = db.Column(db.Date, nullable=False) 
    
    # 🔑 CLAVE: Temperatura Mínima y Máxima
    temp_min = db.Column(db.Float, nullable=True) 
    temp_max = db.Column(db.Float, nullable=True)
    
    # Descripción del estado del tiempo (Ej: Bueno, Despejado, Nieve)
    descripcion = db.Column(db.String(120), nullable=True)
    
    # Viento: lo separamos en velocidad y dirección para mayor detalle
    viento_velocidad_kmh = db.Column(db.Float, nullable=True) # (Ej: 20 A 28)
    viento_direccion = db.Column(db.String(10), nullable=True) # (Ej: Oeste)
    
    # Campo de Visibilidad (según tu wireframe)
    visibilidad_metros = db.Column(db.Integer, nullable=True) 
    
    # Fecha de actualización del registro (cuándo se guardó en la DB)
    fecha_creacion = db.Column(db.DateTime, server_default=db.func.now())
    
    # Restricción para asegurar que solo haya un pronóstico por día para cada paso
    __table_args__ = (db.UniqueConstraint('paso_id', 'fecha_pronostico', name='_paso_fecha_uc'),)


    paso = db.relationship("Paso", backref="pronosticos")

    def to_dict(self):
        return {
            "id": self.id,
            "paso_id": self.paso_id,
            "fecha_pronostico": self.fecha_pronostico.isoformat() if self.fecha_pronostico else None,
            "temp_min": self.temp_min,
            "temp_max": self.temp_max,
            "descripcion": self.descripcion,
            "viento_velocidad_kmh": self.viento_velocidad_kmh,
            "viento_direccion": self.viento_direccion,
            "visibilidad_metros": self.visibilidad_metros,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }