import pytest
import uuid
from datetime import datetime, timedelta
from app import app
from database.models import db, ParkingSession, ParkingSlot
from services.billing_service import BillingService
from services.pricing_service import PricingService
from config import Config

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        from database.database import seed_initial_data
        seed_initial_data()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

def create_dummy_session(duration_minutes: int, parked: bool = True):
    slot = ParkingSlot.query.first()
    start_time = datetime.utcnow() - timedelta(minutes=duration_minutes) if parked else None
    tkt_id = f"TKT-TEST-{uuid.uuid4().hex[:6]}"
    sess = ParkingSession(
        ticket_id=tkt_id,
        registration_number="DL01AB1234",
        parking_category=Config.CATEGORY_NORMAL,
        slot_id=slot.id,
        entry_time=start_time or datetime.utcnow(),
        parked_start_time=start_time,
        status="ACTIVE_PARKED" if parked else "ACTIVE_RESERVED"
    )
    db.session.add(sess)
    db.session.commit()
    return sess

def test_unparked_reservation_bill(client):
    with app.app_context():
        sess = create_dummy_session(45, parked=False)
        bill = BillingService.calculate_bill(sess)
        assert bill["final_amount"] == 0.0
        assert bill["actual_duration_seconds"] == 0
        assert bill["is_unparked_exit"] is True

def test_billing_boundaries(client):
    with app.app_context():
        now = datetime.utcnow()

        # 1. 30 minutes -> ₹0
        s30 = create_dummy_session(30)
        b30 = BillingService.calculate_bill(s30, exit_time=now)
        assert b30["final_amount"] == 0.0

        # 2. 60 minutes -> ₹0
        s60 = create_dummy_session(60)
        b60 = BillingService.calculate_bill(s60, exit_time=now)
        assert b60["final_amount"] == 0.0

        # 3. 65 minutes -> ₹0 (within 10-min grace)
        s65 = create_dummy_session(65)
        b65 = BillingService.calculate_bill(s65, exit_time=now)
        assert b65["final_amount"] == 0.0

        # 4. Exactly 70 minutes -> ₹0 (end of grace period)
        s70 = create_dummy_session(70)
        b70 = BillingService.calculate_bill(s70, exit_time=now)
        assert b70["final_amount"] == 0.0

        # 5. 71 minutes -> ₹50 (1 block of 2h started)
        s71 = create_dummy_session(71)
        b71 = BillingService.calculate_bill(s71, exit_time=now)
        assert b71["final_amount"] == 50.0
        assert b71["number_of_blocks"] == 1

        # 6. 2 hours 10 minutes (130 min = 70 min free + 60 min chargeable <= 120 min) -> ₹50
        s130 = create_dummy_session(130)
        b130 = BillingService.calculate_bill(s130, exit_time=now)
        assert b130["final_amount"] == 50.0
        assert b130["number_of_blocks"] == 1

        # 7. 4 hours 10 minutes (250 min = 70 min free + 180 min chargeable -> 2 blocks) -> ₹100
        s250 = create_dummy_session(250)
        b250 = BillingService.calculate_bill(s250, exit_time=now)
        assert b250["final_amount"] == 100.0
        assert b250["number_of_blocks"] == 2

def test_pricing_snapshot_immutability(client):
    with app.app_context():
        now = datetime.utcnow()
        # Session parked 80 minutes ago with snapshot saved at rate 50
        s = create_dummy_session(80)
        s.set_pricing_snapshot({
            "free_minutes": 60,
            "grace_minutes": 10,
            "charge_amount": 50.0,
            "billing_interval_minutes": 120,
            "rounding_policy": "CEIL"
        })
        db.session.commit()

        # Guard changes rate to ₹200 for future sessions
        PricingService.update_pricing_rule(Config.CATEGORY_NORMAL, 30, 5, 200.0, 60)

        # Existing session's bill MUST still use its saved snapshot (₹50)
        bill = BillingService.calculate_bill(s, exit_time=now)
        assert bill["final_amount"] == 50.0
        assert bill["rate_per_block"] == 50.0
