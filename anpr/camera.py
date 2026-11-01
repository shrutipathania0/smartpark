import os
import base64
import uuid
from datetime import datetime
import numpy as np
from config import Config

class CameraUtils:
    """
    Utilities for decoding webcam frames, handling base64 payloads,
    and managing local capture storage.
    """

    @staticmethod
    def decode_base64_frame(data_uri: str) -> np.ndarray | None:
        """Decodes base64 data URI string into an OpenCV BGR numpy array."""
        try:
            import cv2
            if not data_uri:
                return None
            if "base64," in data_uri:
                _, encoded = data_uri.split("base64,", 1)
            else:
                encoded = data_uri

            img_bytes = base64.b64decode(encoded)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            print(f"Error decoding base64 frame: {e}")
            return None

    @staticmethod
    def encode_frame_to_base64(img_bgr: np.ndarray, format_ext: str = ".jpg") -> str:
        """Encodes OpenCV BGR image array into base64 data URI string."""
        try:
            import cv2
            if img_bgr is None or img_bgr.size == 0:
                return ""
            _, buffer = cv2.imencode(format_ext, img_bgr)
            b64_str = base64.b64encode(buffer).decode('utf-8')
            mime = "image/jpeg" if format_ext in [".jpg", ".jpeg"] else "image/png"
            return f"data:{mime};base64,{b64_str}"
        except Exception as e:
            print(f"Error encoding frame to base64: {e}")
            return ""

    @staticmethod
    def save_capture(img_bgr: np.ndarray, gate_type: str = "entry") -> str:
        """
        Saves captured frame into data/captures/{gate_type}/YYYY-MM-DD/
        Returns relative path suitable for database storage and web serving.
        """
        try:
            import cv2
            if img_bgr is None or img_bgr.size == 0:
                return ""

            today_str = datetime.utcnow().strftime("%Y-%m-%d")
            dest_dir = Config.CAPTURES_DIR / gate_type.lower() / today_str
            os.makedirs(dest_dir, exist_ok=True)

            unique_id = uuid.uuid4().hex[:8]
            filename = f"capture_{gate_type.lower()}_{datetime.utcnow().strftime('%H%M%S')}_{unique_id}.jpg"
            file_path = dest_dir / filename

            cv2.imwrite(str(file_path), img_bgr)
            rel_path = f"captures/{gate_type.lower()}/{today_str}/{filename}"
            return rel_path
        except Exception as e:
            print(f"Error saving capture image: {e}")
            return ""

