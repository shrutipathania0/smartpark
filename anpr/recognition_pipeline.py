import time
import numpy as np
from database.models import db, RecognitionLog
from anpr.camera import CameraUtils
from anpr.detector import PlateDetector
from anpr.plate_cropper import PlateCropper
from anpr.ocr_engine import OCREngine
from anpr.plate_validator import PlateValidator
from config import Config

class ANPRPipeline:
    """
    Complete end-to-end Automatic Number Plate Recognition pipeline.
    Webcam Frame -> Plate Detection -> Cropping -> Preprocessing -> OCR -> Validation -> Confidence Tiering -> Audit Logging
    """

    def __init__(self, detector: PlateDetector = None, ocr_engine: OCREngine = None):
        self.detector = detector or PlateDetector()
        self.ocr_engine = ocr_engine or OCREngine(use_gpu=False)

    def process_frame(self, frame_bgr: np.ndarray, gate_type: str = "entry") -> dict:
        """
        Processes a single video/camera frame.
        Returns full structured recognition result dictionary.
        """
        start_time = time.time()
        if frame_bgr is None or frame_bgr.size == 0:
            return {
                "success": False,
                "error": "Empty or invalid frame provided.",
                "gate_type": gate_type
            }

        # 1. Detect plates in frame
        detections = self.detector.detect_plates(frame_bgr)

        best_crop = None
        best_bbox = None
        best_ocr = {
            "raw_text": "",
            "normalized_text": "",
            "confidence": 0.0,
            "is_valid": False,
            "format_type": "NONE"
        }
        det_conf = 0.0

        if detections:
            # Sort by detection confidence
            detections.sort(key=lambda d: d.get("confidence", 0.0), reverse=True)
            best_det = detections[0]
            best_bbox = best_det["bbox"]
            det_conf = best_det.get("confidence", 0.5)

            # 2. Crop plate
            best_crop = PlateCropper.crop_plate(frame_bgr, best_bbox, padding_pct=0.08)

            # 3. Run OCR on cropped plate
            if best_crop is not None:
                best_ocr = self.ocr_engine.recognize_plate(best_crop)
        else:
            # If no box detected, attempt OCR on central lower rectangular ROI (typical vehicle bumper position)
            h, w = frame_bgr.shape[:2]
            center_crop = frame_bgr[int(h * 0.3):int(h * 0.85), int(w * 0.15):int(w * 0.85)]
            best_ocr = self.ocr_engine.recognize_plate(center_crop)
            if best_ocr.get("is_valid"):
                best_crop = center_crop
                best_bbox = [int(w * 0.15), int(h * 0.3), int(w * 0.85), int(h * 0.85)]
                det_conf = 0.5

        # 4. Confidence evaluation & Tiering
        ocr_conf = float(best_ocr.get("confidence", 0.0))
        is_valid_format = bool(best_ocr.get("is_valid", False))

        # Combined confidence metric
        if det_conf > 0 and ocr_conf > 0:
            combined_conf = round(0.4 * det_conf + 0.6 * ocr_conf, 3)
        else:
            combined_conf = round(max(det_conf, ocr_conf), 3)

        # Tier assignment
        if combined_conf >= Config.HIGH_CONFIDENCE_THRESHOLD and is_valid_format:
            confidence_tier = "HIGH"
            action_recommendation = "AUTO_POPULATE"
        elif combined_conf >= Config.OCR_CONFIDENCE_THRESHOLD or is_valid_format:
            confidence_tier = "MEDIUM"
            action_recommendation = "REQUEST_CONFIRMATION"
        else:
            confidence_tier = "LOW"
            action_recommendation = "MANUAL_CORRECTION"

        # 5. Save capture image locally
        capture_path = CameraUtils.save_capture(frame_bgr, gate_type=gate_type)

        # 6. Encode cropped plate to base64 for UI display
        cropped_b64 = CameraUtils.encode_frame_to_base64(best_crop) if best_crop is not None else ""

        # 7. Save recognition audit log in DB
        try:
            log_entry = RecognitionLog(
                gate_type=gate_type.upper(),
                raw_ocr_text=best_ocr.get("raw_text", ""),
                normalized_registration_number=best_ocr.get("normalized_text", ""),
                confidence=combined_conf,
                image_path=capture_path,
                recognition_status=confidence_tier
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            print(f"Error logging recognition to database: {e}")

        total_latency_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "success": True,
            "gate_type": gate_type.upper(),
            "bbox": best_bbox,
            "detection_confidence": det_conf,
            "raw_text": best_ocr.get("raw_text", ""),
            "registration_number": best_ocr.get("normalized_text", ""),
            "ocr_confidence": ocr_conf,
            "combined_confidence": combined_conf,
            "confidence_tier": confidence_tier,
            "action_recommendation": action_recommendation,
            "is_valid_format": is_valid_format,
            "format_type": best_ocr.get("format_type", "NONE"),
            "cropped_plate_b64": cropped_b64,
            "capture_path": capture_path,
            "latency_ms": total_latency_ms
        }

