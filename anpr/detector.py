import os
import time
from pathlib import Path
import numpy as np
from config import Config

class PlateDetector:
    """
    YOLO-based Number Plate Detector with fallback heuristic detection.
    Detects rectangular vehicle number plates in image/video frames.
    """

    def __init__(self, model_path: Path | str = None, conf_threshold: float = 0.35):
        self.model_path = Path(model_path) if model_path else Config.DETECTOR_MODEL_PATH
        self.conf_threshold = conf_threshold
        self._model = None
        self._initialized = False

    def _get_model(self):
        if not self._initialized:
            try:
                from ultralytics import YOLO
                if self.model_path.exists():
                    print(f"Loading custom trained YOLO plate detector from {self.model_path}")
                    self._model = YOLO(str(self.model_path))
                else:
                    # Fallback to standard lightweight YOLOv8n
                    print("Custom model weights not found yet. Using pretrained lightweight YOLOv8n.")
                    self._model = YOLO("yolov8n.pt")
                self._initialized = True
            except Exception as e:
                print(f"Detector initialization note: {e}. Fallback contour detector will be active.")
                self._model = None
                self._initialized = True
        return self._model

    def detect_plates(self, frame_bgr: np.ndarray) -> list[dict]:
        """
        Detects number plate bounding boxes in the input frame.
        Returns list of dicts: [
            {"bbox": [x1, y1, x2, y2], "confidence": float, "class": "number_plate"}
        ]
        """
        start_time = time.time()
        if frame_bgr is None or frame_bgr.size == 0:
            return []

        h, w = frame_bgr.shape[:2]
        model = self._get_model()

        detections = []

        if model is not None:
            try:
                # Run inference on CPU
                results = model.predict(source=frame_bgr, conf=self.conf_threshold, verbose=False, device='cpu')
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        coords = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                        conf = float(box.conf[0].item())
                        cls_id = int(box.cls[0].item())

                        detections.append({
                            "bbox": [int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3])],
                            "confidence": round(conf, 3),
                            "class": "number_plate",
                            "inference_time_ms": round((time.time() - start_time) * 1000, 2)
                        })
            except Exception as ex:
                print(f"YOLO inference error: {ex}")

        # If YOLO found detections, return them
        if detections:
            return detections

        # Fallback heuristic: Contour & Aspect Ratio analysis for rectangular plate regions
        fallback_boxes = self._detect_candidate_plate_contours(frame_bgr)
        return fallback_boxes

    def _detect_candidate_plate_contours(self, frame_bgr: np.ndarray) -> list[dict]:
        """Heuristic fallback to detect high-contrast rectangular plate regions."""
        try:
            import cv2
            h, w = frame_bgr.shape[:2]
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            blur = cv2.bilateralFilter(gray, 11, 17, 17)
            edged = cv2.Canny(blur, 30, 200)

            contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

            candidates = []
            for c in contours:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.02 * peri, True)
                # Plate typically has 4 vertices (quadrilateral)
                if len(approx) == 4:
                    x, y, bw, bh = cv2.boundingRect(c)
                    aspect_ratio = float(bw) / float(bh) if bh > 0 else 0
                    # Standard Indian plate aspect ratio is between 2.0 and 5.5
                    area = bw * bh
                    if 2.0 <= aspect_ratio <= 5.5 and area > 1200:
                        candidates.append({
                            "bbox": [x, y, x + bw, y + bh],
                            "confidence": 0.55,
                            "class": "candidate_plate_contour"
                        })
                        if len(candidates) >= 2:
                            break
            return candidates
        except Exception:
            return []

