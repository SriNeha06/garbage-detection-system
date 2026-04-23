import uuid
import json
from datetime import datetime, timezone
from .db import db


def generate_uuid():
    return str(uuid.uuid4())


class Camera(db.Model):
    __tablename__ = 'cameras'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(200), nullable=False)
    location_name = db.Column(db.String(300), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    stream_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    zone = db.Column(db.String(50), default='residential')  # residential, commercial, industrial, park
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_checked = db.Column(db.DateTime, nullable=True)

    detections = db.relationship('Detection', backref='camera', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location_name': self.location_name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'stream_url': self.stream_url,
            'is_active': self.is_active,
            'zone': self.zone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None,
        }


class Detection(db.Model):
    __tablename__ = 'detections'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    camera_id = db.Column(db.String(36), db.ForeignKey('cameras.id'), nullable=True)
    image_path = db.Column(db.String(500), nullable=True)
    image_base64 = db.Column(db.Text, nullable=True)
    detected_classes = db.Column(db.Text, nullable=True)  # JSON string list
    detection_count = db.Column(db.Integer, default=0)
    critical_count = db.Column(db.Integer, default=0)
    confidence_scores = db.Column(db.Text, nullable=True)  # JSON string dict
    bin_fill_level = db.Column(db.String(20), default='empty')  # empty, half, full, overflow
    severity = db.Column(db.String(20), default='low')  # low, medium, high, critical
    location_name = db.Column(db.String(300), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    alert_sent = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)

    alerts = db.relationship('Alert', backref='detection', lazy=True)

    def get_detected_classes(self):
        if self.detected_classes:
            try:
                return json.loads(self.detected_classes)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def set_detected_classes(self, classes_list):
        self.detected_classes = json.dumps(classes_list)

    def get_confidence_scores(self):
        if self.confidence_scores:
            try:
                return json.loads(self.confidence_scores)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    def set_confidence_scores(self, scores_dict):
        self.confidence_scores = json.dumps(scores_dict)

    def to_dict(self, include_image=False):
        result = {
            'id': self.id,
            'camera_id': self.camera_id,
            'image_path': self.image_path,
            'detected_classes': self.get_detected_classes(),
            'detection_count': self.detection_count,
            'critical_count': self.critical_count,
            'confidence_scores': self.get_confidence_scores(),
            'bin_fill_level': self.bin_fill_level,
            'severity': self.severity,
            'location_name': self.location_name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'alert_sent': self.alert_sent,
        }
        if include_image:
            result['image_base64'] = self.image_base64
        return result


class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    detection_id = db.Column(db.String(36), db.ForeignKey('detections.id'), nullable=True)
    alert_type = db.Column(db.String(20), default='system')  # email, sms, system
    severity = db.Column(db.String(20), default='low')
    message = db.Column(db.Text, nullable=True)
    location_name = db.Column(db.String(300), nullable=True)
    assigned_worker = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, sent, acknowledged, resolved
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'detection_id': self.detection_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'message': self.message,
            'location_name': self.location_name,
            'assigned_worker': self.assigned_worker,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
        }


class Zone(db.Model):
    __tablename__ = 'zones'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(200), nullable=False)
    zone_type = db.Column(db.String(50), nullable=True)
    total_detections = db.Column(db.Integer, default=0)
    critical_detections = db.Column(db.Integer, default=0)
    last_detection = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'zone_type': self.zone_type,
            'total_detections': self.total_detections,
            'critical_detections': self.critical_detections,
            'last_detection': self.last_detection.isoformat() if self.last_detection else None,
        }
