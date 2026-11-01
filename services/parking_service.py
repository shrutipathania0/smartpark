from datetime import datetime
from database.models import db, ParkingSlot, ParkingSession, SimulationEvent, Alert, ParkingEvent
from services.session_service import SessionService
from services.alert_service import AlertService
from config import Config

class ParkingService:
    @staticmethod
    def get_all_slots() -> list:
        slots = ParkingSlot.query.order_by(ParkingSlot.slot_number.asc()).all()
        return [s.to_dict() for s in slots]

    @staticmethod
    def get_slot_by_id(slot_id: int) -> dict:
        slot = ParkingSlot.query.get(slot_id)
        return slot.to_dict() if slot else None

    # --- 1. Park Correctly ---
    @staticmethod
    def simulate_park_correctly(slot_id: int = None, registration_number: str = None) -> dict:
        slot = None
        session = None

        if slot_id:
            slot = ParkingSlot.query.get(slot_id)
            if slot and slot.current_session_id:
                session = ParkingSession.query.get(slot.current_session_id)
        elif registration_number:
            session = SessionService.get_active_session_by_registration(registration_number)
            if session:
                slot = ParkingSlot.query.get(session.slot_id)

        if not slot or not session:
            # Fallback: find first slot that is RESERVED
            slot = ParkingSlot.query.filter_by(status="RESERVED").first()
            if slot and slot.current_session_id:
                session = ParkingSession.query.get(slot.current_session_id)

        if not slot or not session:
            return {"success": False, "error": "No reserved slot/vehicle found to park correctly. Create an entry reservation first."}

        # Transition to OCCUPIED via SessionService
        result = SessionService.confirm_actual_parking(session.id)
        if result["success"]:
            sim_ev = SimulationEvent(
                event_type="PARK_CORRECTLY",
                slot_id=slot.id,
                registration_number=session.registration_number,
                details=f"Vehicle {session.registration_number} parked properly in assigned slot {slot.slot_number}."
            )
            db.session.add(sim_ev)
            db.session.commit()

        return result

    # --- 2. Place Object / Block Space ---
    @staticmethod
    def simulate_place_object(slot_id: int, description: str = "Debris / Construction cone blocking slot") -> dict:
        slot = ParkingSlot.query.get(slot_id)
        if not slot:
            return {"success": False, "error": f"Slot #{slot_id} not found."}

        if slot.status == "BLOCKED":
            return {"success": False, "error": f"Slot {slot.slot_number} is already blocked."}

        slot.previous_status = slot.status
        slot.status = "BLOCKED"
        slot.updated_at = datetime.utcnow()

        # Create alert for guard
        alert = AlertService.create_alert(
            alert_type="OBJECT_OBSTRUCTION",
            severity="WARNING",
            description=f"Physical obstruction detected in slot {slot.slot_number}: {description}",
            slot_id=slot.id
        )

        sim_ev = SimulationEvent(
            event_type="PLACE_OBJECT",
            slot_id=slot.id,
            details=f"Object placed in slot {slot.slot_number}. Slot set to BLOCKED."
        )
        db.session.add(sim_ev)
        db.session.commit()

        return {"success": True, "slot": slot.to_dict(), "alert": alert.to_dict()}

    # --- 3. Park Incorrectly ---
    @staticmethod
    def simulate_park_incorrectly(slot_id: int, registration_number: str = "DL01AB9999") -> dict:
        slot = ParkingSlot.query.get(slot_id)
        if not slot:
            return {"success": False, "error": f"Slot #{slot_id} not found."}

        alert = AlertService.create_alert(
            alert_type="WRONG_PARKING",
            severity="WARNING",
            description=f"Vehicle {registration_number} parked improperly in slot {slot.slot_number} without valid alignment.",
            registration_number=registration_number,
            slot_id=slot.id
        )

        sim_ev = SimulationEvent(
            event_type="PARK_INCORRECTLY",
            slot_id=slot.id,
            registration_number=registration_number,
            details=f"Vehicle {registration_number} parked incorrectly in slot {slot.slot_number}."
        )
        db.session.add(sim_ev)
        db.session.commit()

        return {"success": True, "alert": alert.to_dict()}

    # --- 4. Block Driving Lane ---
    @staticmethod
    def simulate_block_lane(lane_id: str = "Main Entry Lane A") -> dict:
        alert = AlertService.create_alert(
            alert_type="LANE_BLOCKAGE",
            severity="CRITICAL",
            description=f"Obstruction or stalled vehicle blocking transit in {lane_id}!",
            lane_id=lane_id
        )

        sim_ev = SimulationEvent(
            event_type="BLOCK_LANE",
            details=f"Driving {lane_id} blocked."
        )
        db.session.add(sim_ev)
        db.session.commit()

        return {"success": True, "alert": alert.to_dict()}

    # --- 5. Cross Parking ---
    @staticmethod
    def simulate_cross_parking(slot_id: int, registration_number: str = "MH12DE1234") -> dict:
        slot = ParkingSlot.query.get(slot_id)
        if not slot:
            return {"success": False, "error": f"Slot #{slot_id} not found."}

        alert = AlertService.create_alert(
            alert_type="CROSS_PARKING",
            severity="WARNING",
            description=f"Vehicle {registration_number} cross-parked diagonally across boundary lines of slot {slot.slot_number}.",
            registration_number=registration_number,
            slot_id=slot.id
        )

        sim_ev = SimulationEvent(
            event_type="CROSS_PARKING",
            slot_id=slot.id,
            registration_number=registration_number,
            details=f"Cross parking violation by {registration_number} in slot {slot.slot_number}."
        )
        db.session.add(sim_ev)
        db.session.commit()

        return {"success": True, "alert": alert.to_dict()}

    # --- 6. Occupy Two Spaces ---
    @staticmethod
    def simulate_occupy_two_spaces(slot1_number: str = "N-04", slot2_number: str = "N-05", registration_number: str = "KA05GH7890") -> dict:
        slot1 = ParkingSlot.query.filter_by(slot_number=slot1_number).first()
        slot2 = ParkingSlot.query.filter_by(slot_number=slot2_number).first()

        alert = AlertService.create_alert(
            alert_type="TWO_SPACES",
            severity="CRITICAL",
            description=f"Vehicle {registration_number} straddling both slots {slot1_number} and {slot2_number} simultaneously!",
            registration_number=registration_number,
            slot_id=slot1.id if slot1 else None
        )

        sim_ev = SimulationEvent(
            event_type="OCCUPY_TWO_SPACES",
            registration_number=registration_number,
            details=f"Vehicle {registration_number} straddles {slot1_number} and {slot2_number}."
        )
        db.session.add(sim_ev)
        db.session.commit()

        return {"success": True, "alert": alert.to_dict()}

    # --- 7. Wrong Space / Wrong Category Parking ---
    @staticmethod
    def simulate_wrong_space(assigned_slot_number: str, occupied_slot_number: str, registration_number: str) -> dict:
        assigned_slot = ParkingSlot.query.filter_by(slot_number=assigned_slot_number).first()
        occupied_slot = ParkingSlot.query.filter_by(slot_number=occupied_slot_number).first()

        desc = f"Vehicle {registration_number} assigned to {assigned_slot_number} ({assigned_slot.category if assigned_slot else 'N/A'}) but detected occupying {occupied_slot_number} ({occupied_slot.category if occupied_slot else 'N/A'})!"

        alert = AlertService.create_alert(
            alert_type="WRONG_CATEGORY_PARKING" if (assigned_slot and occupied_slot and assigned_slot.category != occupied_slot.category) else "WRONG_SPACE_PARKING",
            severity="CRITICAL",
            description=desc,
            registration_number=registration_number,
            slot_id=occupied_slot.id if occupied_slot else None
        )

        sim_ev = SimulationEvent(
            event_type="WRONG_SPACE",
            registration_number=registration_number,
            details=desc
        )
        db.session.add(sim_ev)
        db.session.commit()

        return {"success": True, "alert": alert.to_dict()}

    # --- 8. Clear Object ---
    @staticmethod
    def simulate_clear_object(slot_id: int) -> dict:
        slot = ParkingSlot.query.get(slot_id)
        if not slot:
            return {"success": False, "error": f"Slot #{slot_id} not found."}

        if slot.status != "BLOCKED":
            return {"success": False, "error": f"Slot {slot.slot_number} is not blocked."}

        # Restore to previous status if valid, else VACANT
        restored_status = slot.previous_status if slot.previous_status in ["VACANT", "RESERVED", "OCCUPIED"] else "VACANT"
        # If restored status is RESERVED or OCCUPIED but current_session_id is invalid or missing, default to VACANT
        if restored_status in ["RESERVED", "OCCUPIED"]:
            if not slot.current_session_id:
                restored_status = "VACANT"
            else:
                session = ParkingSession.query.get(slot.current_session_id)
                if not session or session.status not in ["ACTIVE_RESERVED", "ACTIVE_PARKED"]:
                    restored_status = "VACANT"
                    slot.current_session_id = None

        slot.status = restored_status
        slot.previous_status = None
        slot.updated_at = datetime.utcnow()

        # Resolve open alerts for this slot
        alerts = Alert.query.filter_by(slot_id=slot.id, alert_type="OBJECT_OBSTRUCTION", status="OPEN").all()
        for a in alerts:
            a.status = "RESOLVED"
            a.resolved_at = datetime.utcnow()

        sim_ev = SimulationEvent(
            event_type="CLEAR_OBJECT",
            slot_id=slot.id,
            details=f"Obstruction cleared from slot {slot.slot_number}. Restored to {restored_status}."
        )
        db.session.add(sim_ev)
        db.session.commit()

        return {"success": True, "slot": slot.to_dict()}

    # --- 9. Reset Simulation ---
    @staticmethod
    def simulate_reset() -> dict:
        """Restores demo parking slots to clean VACANT state while preserving historical records."""
        slots = ParkingSlot.query.all()
        for s in slots:
            s.status = "VACANT"
            s.previous_status = None
            s.current_session_id = None
            s.updated_at = datetime.utcnow()

        # Complete any open active sessions as cancelled
        active_sessions = ParkingSession.query.filter(ParkingSession.status.in_(["ACTIVE_RESERVED", "ACTIVE_PARKED"])).all()
        for sess in active_sessions:
            sess.status = "CANCELLED"
            sess.exit_time = datetime.utcnow()

        # Resolve all open alerts
        open_alerts = Alert.query.filter_by(status="OPEN").all()
        for al in open_alerts:
            al.status = "RESOLVED"
            al.resolved_at = datetime.utcnow()

        sim_ev = SimulationEvent(
            event_type="RESET_SIMULATION",
            details="Simulation state reset to default vacant layout."
        )
        db.session.add(sim_ev)
        db.session.commit()

        return {"success": True, "message": "Simulation reset successfully."}

