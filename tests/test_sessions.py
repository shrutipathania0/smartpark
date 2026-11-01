import pytest
from app import app
from database.models import db, ParkingSlot, ParkingSession
from services.allocation_service import AllocationService
from services.session_service import SessionService
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

def test_full_session_lifecycle(client):
    with app.app_context():
        # 1. Ticket created at entry
        alloc = AllocationService.allocate_slot("DL01AB1234", Config.CATEGORY_NORMAL)
        assert alloc["success"] is True
        sess_id = alloc["session"]["id"]
        slot_id = alloc["slot"]["id"]

        slot = ParkingSlot.query.get(slot_id)
        assert slot.status == "RESERVED"
        assert slot.current_session_id == sess_id

        # 2. Vehicle parks physically
        park_res = SessionService.confirm_actual_parking(sess_id)
        assert park_res["success"] is True
        assert park_res["session"]["status"] == "ACTIVE_PARKED"
        assert park_res["slot"]["status"] == "OCCUPIED"

        slot = ParkingSlot.query.get(slot_id)
        assert slot.status == "OCCUPIED"

        # 3. Vehicle exits
        exit_res = SessionService.process_exit(sess_id)
        assert exit_res["success"] is True
        assert exit_res["session"]["status"] == "COMPLETED"
        assert exit_res["slot"]["status"] == "VACANT"
        assert exit_res["slot"]["current_session_id"] is None

        # Slot is now available for new vehicle
        slot = ParkingSlot.query.get(slot_id)
        assert slot.status == "VACANT"
        assert slot.current_session_id is None

def test_cancel_unparked_reservation(client):
    with app.app_context():
        alloc = AllocationService.allocate_slot("MH12DE1433", Config.CATEGORY_EV)
        sess_id = alloc["session"]["id"]
        slot_id = alloc["slot"]["id"]

        # Cancel reservation before parking
        cancel_res = SessionService.cancel_reservation(sess_id, reason="Driver chose not to park")
        assert cancel_res["success"] is True
        assert cancel_res["session"]["status"] == "CANCELLED"

        slot = ParkingSlot.query.get(slot_id)
        assert slot.status == "VACANT"
        assert slot.current_session_id is None

