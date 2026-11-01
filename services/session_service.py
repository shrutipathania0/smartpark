from datetime import datetime
from database.models import db, ParkingSession, ParkingSlot, ParkingEvent
from services.pricing_service import PricingService
from services.billing_service import BillingService

class SessionService:
    @staticmethod
    def get_active_session_by_registration(registration_number: str) -> ParkingSession:
        """Find active session (ACTIVE_RESERVED or ACTIVE_PARKED) for vehicle."""
        clean_reg = registration_number.strip().upper().replace(" ", "").replace("-", "")
        return ParkingSession.query.filter(
            ParkingSession.registration_number == clean_reg,
            ParkingSession.status.in_(["ACTIVE_RESERVED", "ACTIVE_PARKED"])
        ).first()

    @staticmethod
    def get_session_by_ticket_id(ticket_id: str) -> ParkingSession:
        return ParkingSession.query.filter_by(ticket_id=ticket_id.strip()).first()

    @staticmethod
    def confirm_actual_parking(session_id: int) -> dict:
        """
        Transition vehicle from RESERVED to OCCUPIED when physical parking is verified.
        Saves pricing snapshot at this exact moment and records parked_start_time.
        """
        session = ParkingSession.query.get(session_id)
        if not session:
            return {"success": False, "error": f"Session #{session_id} not found."}

        if session.status != "ACTIVE_RESERVED":
            return {
                "success": False,
                "error": f"Session status is '{session.status}', expected 'ACTIVE_RESERVED'."
            }

        slot = ParkingSlot.query.get(session.slot_id)
        if not slot:
            return {"success": False, "error": f"Slot #{session.slot_id} not found."}

        # Record parked start time
        now = datetime.utcnow()
        session.parked_start_time = now
        session.status = "ACTIVE_PARKED"

        # Save pricing snapshot from current pricing rule
        current_pricing = PricingService.get_pricing_rule(session.parking_category)
        session.set_pricing_snapshot(current_pricing)

        # Update slot to OCCUPIED
        slot.status = "OCCUPIED"
        slot.updated_at = now

        event = ParkingEvent(
            session_id=session.id,
            event_type="VEHICLE_PARKED_OCCUPIED",
            details=f"Vehicle {session.registration_number} parked in slot {slot.slot_number}. Start time recorded."
        )
        db.session.add(event)
        db.session.commit()

        return {
            "success": True,
            "session": session.to_dict(),
            "slot": slot.to_dict()
        }

    @staticmethod
    def process_exit(session_id: int) -> dict:
        """
        Complete vehicle exit, calculate final billing using saved pricing snapshot,
        close session, and release assigned slot to VACANT.
        """
        session = ParkingSession.query.get(session_id)
        if not session:
            return {"success": False, "error": f"Session #{session_id} not found."}

        if session.status not in ["ACTIVE_RESERVED", "ACTIVE_PARKED"]:
            return {
                "success": False,
                "error": f"Cannot complete exit for session with status '{session.status}'."
            }

        now = datetime.utcnow()
        bill_info = BillingService.calculate_bill(session, exit_time=now)

        session.exit_time = now
        session.actual_duration_seconds = bill_info["actual_duration_seconds"]
        session.final_amount = bill_info["final_amount"]
        session.status = "COMPLETED"

        # Release slot
        slot = ParkingSlot.query.get(session.slot_id)
        if slot:
            slot.status = "VACANT"
            slot.current_session_id = None
            slot.previous_status = None
            slot.updated_at = now

        event = ParkingEvent(
            session_id=session.id,
            event_type="VEHICLE_EXIT_COMPLETED",
            details=f"Vehicle {session.registration_number} completed exit from slot {slot.slot_number if slot else 'N/A'}. Final fee: ₹{session.final_amount:.2f}."
        )
        db.session.add(event)
        db.session.commit()

        return {
            "success": True,
            "session": session.to_dict(),
            "bill": bill_info,
            "slot": slot.to_dict() if slot else None
        }

    @staticmethod
    def cancel_reservation(session_id: int, reason: str = "Driver cancelled entry") -> dict:
        """Cancels an unparked reservation and releases the slot to VACANT."""
        session = ParkingSession.query.get(session_id)
        if not session:
            return {"success": False, "error": f"Session #{session_id} not found."}

        if session.status != "ACTIVE_RESERVED":
            return {"success": False, "error": f"Cannot cancel session with status '{session.status}'."}

        session.status = "CANCELLED"
        slot = ParkingSlot.query.get(session.slot_id)
        if slot:
            slot.status = "VACANT"
            slot.current_session_id = None
            slot.previous_status = None

        event = ParkingEvent(
            session_id=session.id,
            event_type="RESERVATION_CANCELLED",
            details=f"Reservation {session.ticket_id} cancelled. Reason: {reason}."
        )
        db.session.add(event)
        db.session.commit()

        return {"success": True, "session": session.to_dict()}

