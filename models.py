"""
Database models for HKPC PPE Detection System
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class DetectionConfig(db.Model):
    """Configuration for which PPE classes are required for access"""
    __tablename__ = 'detection_config'
    
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(50), unique=True, nullable=False)
    enabled = db.Column(db.Boolean, default=False, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DetectionConfig {self.class_name}: {self.enabled}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'class_name': self.class_name,
            'enabled': self.enabled,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DetectionLog(db.Model):
    """Log of all detection events"""
    __tablename__ = 'detection_log'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    detected_classes = db.Column(db.Text, nullable=False)  # JSON string of detected classes
    access_granted = db.Column(db.Boolean, nullable=False)
    confidence_scores = db.Column(db.Text)  # JSON string of confidence scores
    
    def __repr__(self):
        return f'<DetectionLog {self.timestamp}: Access={self.access_granted}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'detected_classes': self.detected_classes,
            'access_granted': self.access_granted,
            'confidence_scores': self.confidence_scores
        }


class SystemSettings(db.Model):
    """System-wide settings"""
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(50), unique=True, nullable=False)
    setting_value = db.Column(db.String(200), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemSettings {self.setting_key}: {self.setting_value}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'setting_key': self.setting_key,
            'setting_value': self.setting_value,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AuthorizedPerson(db.Model):
    """Authorized personnel with face recognition data"""
    __tablename__ = 'authorized_persons'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    face_encoding = db.Column(db.Text, nullable=False)  # JSON string of face encoding array
    photo_path = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<AuthorizedPerson {self.name} ({self.employee_id})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'employee_id': self.employee_id,
            'photo_path': self.photo_path,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AccessLog(db.Model):
    """Detailed access control logs with face recognition"""
    __tablename__ = 'access_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('authorized_persons.id'), nullable=True)
    person_name = db.Column(db.String(100))  # Stored even if person is deleted
    employee_id = db.Column(db.String(50), nullable=True)  # Employee ID (stored even if person is deleted)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    face_matched = db.Column(db.Boolean, default=False)
    face_confidence = db.Column(db.Float)
    detected_classes = db.Column(db.Text, nullable=False)  # JSON string
    ppe_complete = db.Column(db.Boolean, default=False)
    access_granted = db.Column(db.Boolean, default=False)
    photo_path = db.Column(db.String(200))  # Snapshot of the access attempt
    
    person = db.relationship('AuthorizedPerson', backref='access_logs')
    
    def __repr__(self):
        return f'<AccessLog {self.timestamp}: {self.person_name} - {self.access_granted}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'person_id': self.person_id,
            'person_name': self.person_name,
            'employee_id': self.employee_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'face_matched': self.face_matched,
            'face_confidence': self.face_confidence,
            'detected_classes': self.detected_classes,
            'ppe_complete': self.ppe_complete,
            'access_granted': self.access_granted,
            'photo_path': self.photo_path
        }


class AdminAuth(db.Model):
    """Admin PIN code authentication"""
    __tablename__ = 'admin_auth'
    
    id = db.Column(db.Integer, primary_key=True)
    pin_hash = db.Column(db.String(200), nullable=False)
    failed_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<AdminAuth locked_until={self.locked_until}>'

