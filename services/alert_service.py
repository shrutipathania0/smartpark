from datetime import datetime
from database.models import db, Alert

class AlertService:
    @staticmethod
    def create_alert(alert_type: str, severity: str, description: str,
                     registration_number: str = None, slot_id: int = None,
                     lane_id: str = None) -> Alert:
        """Create and persist a new parking or system alert."""
        alert = Alert(
            alert_type=alert_type,
            severity=severity,
            description=description,
            registration_number=registration_number,
            slot_id=slot_id,
            lane_id=lane_id,
            status="OPEN",
            created_at=datetime.utcnow()
        )
        db.session.add(alert)
        db.session.commit()
        return alert

    @staticmethod
    def get_open_alerts() -> list:
        """Get all unresolved alerts (OPEN or ACKNOWLEDGED)."""
        alerts = Alert.query.filter(Alert.status.in_(["OPEN", "ACKNOWLEDGED"])).order_by(Alert.created_at.desc()).all()
        return [a.to_dict() for a in alerts]

    @staticmethod
    def get_all_alerts(limit: int = 50) -> list:
        """Get alert history ordered by creation time."""
        alerts = Alert.query.order_by(Alert.created_at.desc()).limit(limit).all()
        return [a.to_dict() for a in alerts]

    @staticmethod
    def acknowledge_alert(alert_id: int) -> dict:
        alert = Alert.query.get(alert_id)
        if not alert:
            return {"success": False, "error": "Alert not found"}
        if alert.status == "OPEN":
            alert.status = "ACKNOWLEDGED"
            alert.acknowledged_at = datetime.utcnow()
            db.session.commit()
        return {"success": True, "alert": alert.to_dict()}

    @staticmethod
    def resolve_alert(alert_id: int) -> dict:
        alert = Alert.query.get(alert_id)
        if not alert:
            return {"success": False, "error": "Alert not found"}
        alert.status = "RESOLVED"
        alert.resolved_at = datetime.utcnow()
        db.session.commit()
        return {"success": True, "alert": alert.to_dict()}

