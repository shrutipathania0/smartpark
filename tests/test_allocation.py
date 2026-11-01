import pytest
from app import app
from database.models import db, ParkingSlot, ParkingSession
from services.allocation_service import AllocationService
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

def test_compatible_category_allocation(client):
    with app.app_context():
        # 1. Normal vehicle
        res1 = AllocationService.allocate_slot("DL01AB1234", Config.CATEGORY_NORMAL)
        assert res1["success"] is True
        assert res1["slot"]["category"] == Config.CATEGORY_NORMAL
        assert res1["slot"]["status"] == "RESERVED"
        assert res1["session"]["status"] == "ACTIVE_RESERVED"

        # 2. EV vehicle
        res2 = AllocationService.allocate_slot("MH02EV1001", Config.CATEGORY_EV)
        assert res2["success"] is True
        assert res2["slot"]["category"] == Config.CATEGORY_EV
        assert res2["slot"]["status"] == "RESERVED"

        # 3. Disabled vehicle
        res3 = AllocationService.allocate_slot("KA05MG8821", Config.CATEGORY_DISABLED)
        assert res3["success"] is True
        assert res3["slot"]["category"] == Config.CATEGORY_DISABLED
        assert res3["slot"]["status"] == "RESERVED"

def test_incompatible_category_rejection(client):
    with app.app_context():
        res = AllocationService.allocate_slot("HR26DK8888", "Helicopter Parking")
        assert res["success"] is False
        assert "Invalid parking category" in res["error"]

def test_duplicate_active_session_prevention(client):
    with app.app_context():
        res1 = AllocationService.allocate_slot("DL01AB1234", Config.CATEGORY_NORMAL)
        assert res1["success"] is True

        # Second entry attempt with same vehicle while first is active
        res2 = AllocationService.allocate_slot("DL01AB1234", Config.CATEGORY_NORMAL)
        assert res2["success"] is False
        assert "already has an active session" in res2["error"]

def test_category_full_rejection(client):
    with app.app_context():
        # Disabled category has 3 slots
        for i in range(1, 4):
            r = AllocationService.allocate_slot(f"DL01DIS{i:02d}", Config.CATEGORY_DISABLED)
            assert r["success"] is True

        # 4th disabled request must be rejected (never silently assigned to Normal or EV)
        r4 = AllocationService.allocate_slot("DL01DIS04", Config.CATEGORY_DISABLED)
        assert r4["success"] is False
        assert "No available slots in Disabled Parking" in r4["error"]

