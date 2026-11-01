from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()

class ParkingSlot(db.Model):
    __tablename__ = 'parking_slots'

    id = db.Column(db.Integer, primary_key=True)
    slot_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False, index=True)  # Disabled Parking, EV Charging Parking, Normal Parking
    status = db.Column(db.String(20), nullable=False, default="VACANT")  # VACANT, RESERVED, OCCUPIED, BLOCKED
    previous_status = db.Column(db.String(20), nullable=True)  # Used when restoring from BLOCKED
    current_session_id = db.Column(db.Integer, db.ForeignKey('parking_sessions.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    current_session = db.relationship('ParkingSession', foreign_keys=[current_session_id], post_update=True)

    def to_dict(self):
        return {
            "id": self.id,
            "slot_number": self.slot_number,
            "category": self.category,
            "status": self.status,
            "previous_status": self.previous_status,
            "current_session_id": self.current_session_id,
            "registration_number": self.current_session.registration_number if self.current_session else None,
            "ticket_id": self.current_session.ticket_id if self.current_session else None,
            "parked_start_time": self.current_session.parked_start_time.isoformat() if (self.current_session and self.current_session.parked_start_time) else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ParkingSession(db.Model):
    __tablename__ = 'parking_sessions'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    registration_number = db.Column(db.String(20), nullable=False, index=True)
    parking_category = db.Column(db.String(50), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('parking_slots.id'), nullable=False)
    entry_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    parked_start_time = db.Column(db.DateTime, nullable=True)
    exit_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(30), nullable=False, default="ACTIVE_RESERVED")  # ACTIVE_RESERVED, ACTIVE_PARKED, COMPLETED, CANCELLED
    actual_duration_seconds = db.Column(db.Integer, default=0)
    final_amount = db.Column(db.Float, default=0.0)
    pricing_snapshot = db.Column(db.Text, nullable=True)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    slot = db.relationship('ParkingSlot', foreign_keys=[slot_id])

    def get_pricing_snapshot(self):
        if self.pricing_snapshot:
            try:
                return json.loads(self.pricing_snapshot)
            except Exception:
                return None
        return None

    def set_pricing_snapshot(self, rules_dict):
        self.pricing_snapshot = json.dumps(rules_dict)

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "registration_number": self.registration_number,
            "parking_category": self.parking_category,
            "slot_id": self.slot_id,
            "slot_number": self.slot.slot_number if self.slot else None,
            "entry_time": self.entry_time.isoformat() if self.entry_time else None,
            "parked_start_time": self.parked_start_time.isoformat() if self.parked_start_time else None,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "status": self.status,
            "actual_duration_seconds": self.actual_duration_seconds,
            "final_amount": self.final_amount,
            "pricing_snapshot": self.get_pricing_snapshot(),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class PricingRule(db.Model):
    __tablename__ = 'pricing_rules'

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), unique=True, nullable=False)
    free_minutes = db.Column(db.Integer, default=60, nullable=False)
    grace_minutes = db.Column(db.Integer, default=10, nullable=False)
    charge_amount = db.Column(db.Float, default=50.0, nullable=False)
    billing_interval_minutes = db.Column(db.Integer, default=120, nullable=False)
    rounding_policy = db.Column(db.String(20), default="CEIL", nullable=False)
    updated_by = db.Column(db.String(100), default="System")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "free_minutes": self.free_minutes,
            "grace_minutes": self.grace_minutes,
            "charge_amount": self.charge_amount,
            "billing_interval_minutes": self.billing_interval_minutes,
            "rounding_policy": self.rounding_policy,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Guard(db.Model):
    __tablename__ = 'guards'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), default="Duty Guard")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), default="WARNING")  # INFO, WARNING, CRITICAL
    description = db.Column(db.Text, nullable=False)
    registration_number = db.Column(db.String(20), nullable=True)
    slot_id = db.Column(db.Integer, nullable=True)
    lane_id = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), default="OPEN")  # OPEN, ACKNOWLEDGED, RESOLVED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "description": self.description,
            "registration_number": self.registration_number,
            "slot_id": self.slot_id,
            "lane_id": self.lane_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


class SimulationEvent(db.Model):
    __tablename__ = 'simulation_events'

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False)
    slot_id = db.Column(db.Integer, nullable=True)
    registration_number = db.Column(db.String(20), nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "slot_id": self.slot_id,
            "registration_number": self.registration_number,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class RecognitionLog(db.Model):
    __tablename__ = 'recognition_logs'

    id = db.Column(db.Integer, primary_key=True)
    gate_type = db.Column(db.String(20), nullable=False)  # ENTRY, EXIT
    raw_ocr_text = db.Column(db.String(100), nullable=True)
    normalized_registration_number = db.Column(db.String(50), nullable=True)
    confidence = db.Column(db.Float, default=0.0)
    image_path = db.Column(db.String(255), nullable=True)
    recognition_status = db.Column(db.String(50), default="SUCCESS")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "gate_type": self.gate_type,
            "raw_ocr_text": self.raw_ocr_text,
            "normalized_registration_number": self.normalized_registration_number,
            "confidence": self.confidence,
            "image_path": self.image_path,
            "recognition_status": self.recognition_status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ParkingEvent(db.Model):
    __tablename__ = 'parking_events'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, nullable=True)
    event_type = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "event_type": self.event_type,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

