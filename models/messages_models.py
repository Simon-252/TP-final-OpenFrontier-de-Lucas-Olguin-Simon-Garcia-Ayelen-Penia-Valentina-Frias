import uuid
from models.db import db
from datetime import datetime
from sqlalchemy import or_

class Message(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 1. ID del remitente
    sender_id = db.Column(
        db.String(36), 
        db.ForeignKey('user.id', ondelete='CASCADE'), 
        nullable=False
    )
    # Nota: Tu relación usa backref='sent_messages', lo cual simplifica el User model.
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_messages', lazy=True))

    # 2. ID del destinatario
    recipient_id = db.Column(
        db.String(36), 
        db.ForeignKey('user.id', ondelete='CASCADE'), #
        nullable=True # Puede ser NULL si es un mensaje masivo (Alerta).
    )
    # Nota: Tu relación usa backref='received_messages', lo cual simplifica el User model.
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref=db.backref('received_messages', lazy=True))
    
    # ... (el resto de las columnas y el método to_dict se mantienen igual) ...
    
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='support', nullable=False) 
    is_read_by_recipient = db.Column(db.Boolean, default=False, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'sender_username': self.sender.username if self.sender else 'Sistema',
            'recipient_id': self.recipient_id,
            'subject': self.subject,
            'body': self.body,
            'message_type': self.message_type,
            'is_read_by_recipient': self.is_read_by_recipient,
            'timestamp': self.timestamp.isoformat()
        }