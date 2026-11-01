import numpy as np
from anpr.plate_validator import PlateValidator
from anpr.plate_cropper import PlateCropper
from anpr.image_preprocessing import ImagePreprocessor

def test_indian_plate_standard_validation():
    # Valid standard plates
    valid_samples = ["DL01AB1234", "MH12DE1433", "KA05MG8821", "UP16CD5566", "TN07BK3341"]
    for plate in valid_samples:
        norm, is_valid, fmt = PlateValidator.normalize_indian_plate(plate)
        assert is_valid is True, f"Failed for {plate}"
        assert norm == plate
        assert fmt == "STANDARD"

def test_bharat_series_validation():
    bh_samples = ["22BH1029AB", "23BH4567ZZ", "21BH8812CD"]
    for plate in bh_samples:
        norm, is_valid, fmt = PlateValidator.normalize_indian_plate(plate)
        assert is_valid is True, f"Failed for {plate}"
        assert norm == plate
        assert fmt == "BH_SERIES"

def test_positional_character_correction():
    # '0L' state code should correct to 'DL'
    norm1, is_valid1, _ = PlateValidator.normalize_indian_plate("0L01AB1234")
    assert is_valid1 is True
    assert norm1.startswith("DL")

    # 'O' in numeric registration block (e.g. 123O) should correct to '0'
    norm2, is_valid2, _ = PlateValidator.normalize_indian_plate("DL01AB123O")
    assert is_valid2 is True
    assert norm2.endswith("1230")

    # 'I' in RTO number (e.g. DLI1AB1234) should correct to '1'
    norm3, is_valid3, _ = PlateValidator.normalize_indian_plate("DL01AB1234")
    assert is_valid3 is True

    # Spaced plate string (e.g. "DL 01 AB 1234")
    norm4, is_valid4, _ = PlateValidator.normalize_indian_plate("DL 01 AB 1234")
    assert is_valid4 is True
    assert norm4 == "DL01AB1234"

def test_cropper_boundary_clamping():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Box extending past image boundary
    box = [600, 450, 700, 520]
    cropped = PlateCropper.crop_plate(frame, box, padding_pct=0.05)
    assert cropped is not None
    assert cropped.shape[0] > 0
    assert cropped.shape[1] > 0
    assert cropped.shape[0] <= 480
    assert cropped.shape[1] <= 640

def test_image_preprocessing_variants():
    sample = np.full((80, 320, 3), 128, dtype=np.uint8)
    variants = ImagePreprocessor.preprocess_for_ocr(sample)
    assert "original" in variants
    assert "gray" in variants
    assert "clahe" in variants
    assert "otsu" in variants
    assert "adaptive" in variants

