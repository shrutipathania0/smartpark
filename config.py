import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.getenv("SECRET_KEY", "smartpark-ai-super-secret-key-change-in-production-2026")
    
    db_file = (BASE_DIR / 'data' / 'smartpark.db').as_posix()
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or f"sqlite:///{db_file}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 8000))

    # Storage paths
    CAPTURES_DIR = BASE_DIR / os.getenv("CAPTURES_DIR", "data/captures")
    LOGS_DIR = BASE_DIR / os.getenv("LOGS_DIR", "data/logs")
    MODELS_DIR = BASE_DIR / "models"
    DETECTOR_MODEL_PATH = BASE_DIR / os.getenv("DETECTOR_MODEL_PATH", "models/detector/best.pt")

    # Categories
    CATEGORY_DISABLED = "Disabled Parking"
    CATEGORY_EV = "EV Charging Parking"
    CATEGORY_NORMAL = "Normal Parking"
    VALID_CATEGORIES = [CATEGORY_DISABLED, CATEGORY_EV, CATEGORY_NORMAL]

    # Slot count defaults
    DEFAULT_SLOT_COUNTS = {
        CATEGORY_DISABLED: int(os.getenv("DISABLED_SLOTS", 3)),
        CATEGORY_EV: int(os.getenv("EV_SLOTS", 3)),
        CATEGORY_NORMAL: int(os.getenv("NORMAL_SLOTS", 9)),
    }

    # ANPR Confidence thresholds
    OCR_CONFIDENCE_THRESHOLD = float(os.getenv("OCR_CONFIDENCE_THRESHOLD", 0.50))
    HIGH_CONFIDENCE_THRESHOLD = float(os.getenv("HIGH_CONFIDENCE_THRESHOLD", 0.75))

    # Default Pricing Policy
    DEFAULT_PRICING = {
        CATEGORY_DISABLED: {
            "free_minutes": 60,
            "grace_minutes": 10,
            "charge_amount": 50.00,
            "billing_interval_minutes": 120,
            "rounding_policy": "CEIL"
        },
        CATEGORY_EV: {
            "free_minutes": 60,
            "grace_minutes": 10,
            "charge_amount": 50.00,
            "billing_interval_minutes": 120,
            "rounding_policy": "CEIL"
        },
        CATEGORY_NORMAL: {
            "free_minutes": 60,
            "grace_minutes": 10,
            "charge_amount": 50.00,
            "billing_interval_minutes": 120,
            "rounding_policy": "CEIL"
        }
    }
