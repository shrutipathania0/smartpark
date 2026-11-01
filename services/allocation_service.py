import uuid
from datetime import datetime
from database.models import db, ParkingSlot, ParkingSession, ParkingEvent
from services.pricing_service import PricingService
from config import Config

class AllocationService:
    @staticmethod
    def get_availability_summary() -> dict:
        """Returns total, vacant, reserved, occupied, and blocked counts overall and by category."""
        slots = ParkingSlot.query.all()
        summary = {
            "total_slots": len(slots),
            "vacant": 0,
            "reserved": 0,
            "occupied": 0,
            "blocked": 0,
            "by_category": {
                Config.CATEGORY_DISABLED: {"total": 0, "vacant": 0, "reserved": 0, "occupied": 0, "blocked": 0},
                Config.CATEGORY_EV: {"total": 0, "vacant": 0, "reserved": 0, "occupied": 0, "blocked": 0},
                Config.CATEGORY_NORMAL: {"total": 0, "vacant": 0, "reserved": 0, "occupied": 0, "blocked": 0}
            }
        }

        for slot in slots:
            status_lower = slot.status.lower()
            if status_lower in summary:
                summary[status_lower] += 1
            cat = slot.category
            if cat in summary["by_category"]:
                summary["by_category"][cat]["total"] += 1
                if status_lower in summary["by_category"][cat]:
                    summary["by_category"][cat][status_lower] += 1

        return summary

    @staticmethod
    def allocate_slot(registration_number: str, category: str) -> dict:
        """
        Allocates a compatible VACANT slot for the requested category.
        Enforces strict category matching and prevents duplicate active sessions.
        """
        # 1. Validate category
        if category not in Config.VALID_CATEGORIES:
            return {
                "success": False,
                "error": f"Invalid parking category: {category}. Must be one of {Config.VALID_CATEGORIES}."
            }

        # Normalize registration number
        clean_reg = registration_number.strip().upper().replace(" ", "").replace("-", "")
        if not clean_reg:
            return {"success": False, "error": "Registration number cannot be empty."}

        # 2. Check for duplicate active session
        existing_session = ParkingSession.query.filter(
            ParkingSession.registration_number == clean_reg,
            ParkingSession.status.in_(["ACTIVE_RESERVED", "ACTIVE_PARKED"])
        ).first()

        if existing_session:
            return {
                "success": False,
                "error": f"Vehicle {clean_reg} already has an active session (Ticket: {existing_session.ticket_id}) in slot {existing_session.slot.slot_number if existing_session.slot else 'N/A'}."
            }

        # 3. Find first VACANT slot in exact category
        # Using with_for_update if supported or deterministic query within transaction
        slot = ParkingSlot.query.filter_by(category=category, status="VACANT").order_by(ParkingSlot.slot_number.asc()).first()

        if not slot:
            return {
                "success": False,
                "error": f"No available slots in {category}. All slots are currently reserved, occupied, or blocked."
            }

        # 4. Generate unique Ticket ID
        date_str = datetime.utcnow().strftime("%Y%m%d")
        unique_suffix = uuid.uuid4().hex[:6].upper()
        ticket_id = f"TKT-{date_str}-{unique_suffix}"

        # 5. Create Session (status ACTIVE_RESERVED)
        session = ParkingSession(
            ticket_id=ticket_id,
            registration_number=clean_reg,
            parking_category=category,
            slot_id=slot.id,
            entry_time=datetime.utcnow(),
            status="ACTIVE_RESERVED"
        )
        db.session.add(session)
        db.session.flush()  # to obtain session.id

        # 6. Update Slot status to RESERVED and link session
        slot.status = "RESERVED"
        slot.current_session_id = session.id
        slot.updated_at = datetime.utcnow()

        # Log event
        event = ParkingEvent(
            session_id=session.id,
            event_type="TICKET_CREATED_SLOT_RESERVED",
            details=f"Slot {slot.slot_number} reserved for {clean_reg} ({category}) under ticket {ticket_id}."
        )
        db.session.add(event)

        db.session.commit()

        return {
            "success": True,
            "session": session.to_dict(),
            "slot": slot.to_dict()
        }

