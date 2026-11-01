import pytest
from app import app
from database.models import db, ParkingSlot, Alert, SimulationEvent
from services.allocation_service import AllocationService
from services.parking_service import ParkingService
from services.alert_service import AlertService
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

def test_simulation_park_correctly_workflow(client):
    with app.app_context():
        alloc = AllocationService.allocate_slot("DL01AB1234", Config.CATEGORY_NORMAL)
        slot_id = alloc["slot"]["id"]

        res = ParkingService.simulate_park_correctly(slot_id=slot_id)
        assert res["success"] is True
        slot = ParkingSlot.query.get(slot_id)
        assert slot.status == "OCCUPIED"

def test_simulation_place_and_clear_object(client):
    with app.app_context():
        slot = ParkingSlot.query.first()
        slot_id = slot.id

        # 1. Place object
        res_place = ParkingService.simulate_place_object(slot_id, description="Maintenance barrier")
        assert res_place["success"] is True
        assert res_place["slot"]["status"] == "BLOCKED"

        slot = ParkingSlot.query.get(slot_id)
        assert slot.status == "BLOCKED"

        # Check alert created
        open_alerts = Alert.query.filter_by(slot_id=slot_id, status="OPEN").all()
        assert len(open_alerts) == 1
        alert_id = open_alerts[0].id

        # 2. Clear object
        res_clear = ParkingService.simulate_clear_object(slot_id)
        assert res_clear["success"] is True
        assert res_clear["slot"]["status"] == "VACANT"

        # Check alert is resolved
        alert = Alert.query.get(alert_id)
        assert alert.status == "RESOLVED"

def test_incident_simulation_alerts(client):
    with app.app_context():
        # Park incorrectly
        r1 = ParkingService.simulate_park_incorrectly(slot_id=1, registration_number="DL01AB9999")
        assert r1["success"] is True
        assert r1["alert"]["alert_type"] == "WRONG_PARKING"

        # Block lane
        r2 = ParkingService.simulate_block_lane(lane_id="Lane B")
        assert r2["success"] is True
        assert r2["alert"]["alert_type"] == "LANE_BLOCKAGE"

        # Cross parking
        r3 = ParkingService.simulate_cross_parking(slot_id=2, registration_number="MH12DE1234")
        assert r3["success"] is True
        assert r3["alert"]["alert_type"] == "CROSS_PARKING"

        # Occupy two spaces
        r4 = ParkingService.simulate_occupy_two_spaces("N-04", "N-05", "KA05GH7890")
        assert r4["success"] is True
        assert r4["alert"]["alert_type"] == "TWO_SPACES"

        # Wrong space
        r5 = ParkingService.simulate_wrong_space("N-01", "E-01", "UP16CD5566")
        assert r5["success"] is True

        open_alerts = AlertService.get_open_alerts()
        assert len(open_alerts) >= 5

def test_alert_lifecycle(client):
    with app.app_context():
        alert = AlertService.create_alert("ANPR_FAILURE", "WARNING", "Webcam disconnected")
        assert alert.status == "OPEN"

        # Acknowledge
        ack = AlertService.acknowledge_alert(alert.id)
        assert ack["success"] is True
        assert ack["alert"]["status"] == "ACKNOWLEDGED"

        # Resolve
        res = AlertService.resolve_alert(alert.id)
        assert res["success"] is True
        assert res["alert"]["status"] == "RESOLVED"

def test_simulation_reset(client):
    with app.app_context():
        # Reserve a slot and place an object
        AllocationService.allocate_slot("DL01AB1234", Config.CATEGORY_NORMAL)
        ParkingService.simulate_place_object(slot_id=2)

        # Reset simulation
        reset_res = ParkingService.simulate_reset()
        assert reset_res["success"] is True

        # All slots must be VACANT
        slots = ParkingSlot.query.all()
        for s in slots:
            assert s.status == "VACANT"
            assert s.current_session_id is None

