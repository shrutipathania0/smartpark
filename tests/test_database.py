import pytest
from app import app
from database.models import db, ParkingSlot, PricingRule, Guard
from config import Config
from werkzeug.security import check_password_hash

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

def test_database_initialization(client):
    with app.app_context():
        slots = ParkingSlot.query.all()
        assert len(slots) == 15, f"Expected 15 total slots, got {len(slots)}"

        disabled = ParkingSlot.query.filter_by(category=Config.CATEGORY_DISABLED).count()
        ev = ParkingSlot.query.filter_by(category=Config.CATEGORY_EV).count()
        normal = ParkingSlot.query.filter_by(category=Config.CATEGORY_NORMAL).count()

        assert disabled == 3, f"Expected 3 disabled slots, got {disabled}"
        assert ev == 3, f"Expected 3 EV slots, got {ev}"
        assert normal == 9, f"Expected 9 normal slots, got {normal}"

def test_default_pricing_rules(client):
    with app.app_context():
        rules = PricingRule.query.all()
        assert len(rules) == 3, f"Expected 3 pricing rules, got {len(rules)}"
        for r in rules:
            assert r.free_minutes == 60
            assert r.grace_minutes == 10
            assert r.charge_amount == 50.0
            assert r.billing_interval_minutes == 120
            assert r.rounding_policy == "CEIL"

def test_guard_account(client):
    with app.app_context():
        guard = Guard.query.filter_by(username="guard").first()
        assert guard is not None
        assert check_password_hash(guard.password_hash, "smartpark2026")

