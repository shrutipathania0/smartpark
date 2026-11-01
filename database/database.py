import os
from werkzeug.security import generate_password_hash
from database.models import db, ParkingSlot, PricingRule, Guard
from config import Config

def init_db(app):
    if 'sqlalchemy' not in app.extensions:
        db.init_app(app)
    with app.app_context():
        # Ensure data folder exists
        os.makedirs(Config.BASE_DIR / 'data', exist_ok=True)
        os.makedirs(Config.CAPTURES_DIR / 'entry', exist_ok=True)
        os.makedirs(Config.CAPTURES_DIR / 'exit', exist_ok=True)
        os.makedirs(Config.LOGS_DIR, exist_ok=True)

        db.create_all()
        seed_initial_data()

def seed_initial_data():
    """Seeds default parking slots, pricing rules, and default guard account if not present."""
    # 1. Pricing Rules
    for category, rules in Config.DEFAULT_PRICING.items():
        existing_rule = PricingRule.query.filter_by(category=category).first()
        if not existing_rule:
            rule = PricingRule(
                category=category,
                free_minutes=rules["free_minutes"],
                grace_minutes=rules["grace_minutes"],
                charge_amount=rules["charge_amount"],
                billing_interval_minutes=rules["billing_interval_minutes"],
                rounding_policy=rules["rounding_policy"],
                updated_by="System Initializer"
            )
            db.session.add(rule)

    # 2. Parking Slots
    # Example: D-01..D-03 for Disabled, E-01..E-03 for EV, N-01..N-09 for Normal
    prefixes = {
        Config.CATEGORY_DISABLED: "D",
        Config.CATEGORY_EV: "E",
        Config.CATEGORY_NORMAL: "N"
    }

    for category, count in Config.DEFAULT_SLOT_COUNTS.items():
        prefix = prefixes.get(category, "P")
        for i in range(1, count + 1):
            slot_number = f"{prefix}-{i:02d}"
            existing_slot = ParkingSlot.query.filter_by(slot_number=slot_number).first()
            if not existing_slot:
                slot = ParkingSlot(
                    slot_number=slot_number,
                    category=category,
                    status="VACANT"
                )
                db.session.add(slot)

    # 3. Default Guard Account
    default_guard = Guard.query.filter_by(username="guard").first()
    if not default_guard:
        guard = Guard(
            username="guard",
            password_hash=generate_password_hash("smartpark2026"),
            full_name="Duty Officer"
        )
        db.session.add(guard)

    db.session.commit()

