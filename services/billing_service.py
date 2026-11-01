import math
from datetime import datetime
from services.pricing_service import PricingService
from config import Config

class BillingService:
    @staticmethod
    def calculate_bill(session, exit_time: datetime = None) -> dict:
        """
        Calculate billing breakdown and final amount for a parking session.
        If the vehicle never parked (parked_start_time is None), bill is 0.
        Uses pricing_snapshot saved at parked_start_time if present.
        """
        if exit_time is None:
            exit_time = datetime.utcnow()

        # If vehicle was only reserved and never parked
        if not session.parked_start_time:
            return {
                "ticket_id": session.ticket_id,
                "registration_number": session.registration_number,
                "category": session.parking_category,
                "parked_start_time": None,
                "exit_time": exit_time.isoformat(),
                "actual_duration_seconds": 0,
                "total_duration_minutes": 0,
                "free_minutes": 60,
                "grace_minutes": 10,
                "total_free_minutes": 70,
                "chargeable_duration_minutes": 0,
                "billing_interval_minutes": 120,
                "number_of_blocks": 0,
                "rate_per_block": 50.0,
                "final_amount": 0.0,
                "final_amount_paise": 0,
                "is_unparked_exit": True,
                "status_message": "Vehicle exited without occupying slot. No fee charged."
            }

        # Calculate duration
        start_time = session.parked_start_time
        if exit_time < start_time:
            exit_time = start_time

        duration_seconds = int((exit_time - start_time).total_seconds())
        # Ceiling of seconds into full minutes or fractional minutes
        # In parking standards, any second into a minute counts as that minute:
        total_duration_minutes = math.ceil(duration_seconds / 60.0) if duration_seconds > 0 else 0

        # Retrieve pricing rule from session snapshot or pricing service
        pricing = session.get_pricing_snapshot()
        if not pricing:
            pricing = PricingService.get_pricing_rule(session.parking_category)

        free_minutes = int(pricing.get("free_minutes", 60))
        grace_minutes = int(pricing.get("grace_minutes", 10))
        total_free_threshold = free_minutes + grace_minutes
        charge_amount = float(pricing.get("charge_amount", 50.0))
        billing_interval = int(pricing.get("billing_interval_minutes", 120))
        rounding_policy = pricing.get("rounding_policy", "CEIL")

        if total_duration_minutes <= total_free_threshold:
            chargeable_minutes = 0
            number_of_blocks = 0
            final_amount_paise = 0
        else:
            chargeable_minutes = total_duration_minutes - total_free_threshold
            if rounding_policy == "CEIL":
                number_of_blocks = math.ceil(chargeable_minutes / billing_interval)
            elif rounding_policy == "FLOOR":
                number_of_blocks = math.floor(chargeable_minutes / billing_interval)
            else:
                number_of_blocks = math.ceil(chargeable_minutes / billing_interval)

            rate_in_paise = int(round(charge_amount * 100))
            final_amount_paise = number_of_blocks * rate_in_paise

        final_amount = round(final_amount_paise / 100.0, 2)

        return {
            "ticket_id": session.ticket_id,
            "registration_number": session.registration_number,
            "category": session.parking_category,
            "slot_number": session.slot.slot_number if session.slot else None,
            "parked_start_time": start_time.isoformat(),
            "exit_time": exit_time.isoformat(),
            "actual_duration_seconds": duration_seconds,
            "total_duration_minutes": total_duration_minutes,
            "free_minutes": free_minutes,
            "grace_minutes": grace_minutes,
            "total_free_minutes": total_free_threshold,
            "chargeable_duration_minutes": chargeable_minutes,
            "billing_interval_minutes": billing_interval,
            "number_of_blocks": number_of_blocks,
            "rate_per_block": charge_amount,
            "final_amount": final_amount,
            "final_amount_paise": final_amount_paise,
            "is_unparked_exit": False,
            "status_message": f"Charged ₹{final_amount:.2f} for {number_of_blocks} billing block(s)." if final_amount > 0 else "Complimentary parking within free period."
        }

