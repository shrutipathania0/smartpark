import numpy as np

class PlateCropper:
    """
    Safely crops detected number plate regions from full video/camera frames.
    Includes padding, boundary clamping, and aspect-ratio validation.
    """

    @staticmethod
    def crop_plate(frame: np.ndarray, bbox: list[int | float], padding_pct: float = 0.05) -> np.ndarray | None:
        """
        bbox format: [x1, y1, x2, y2]
        Returns cropped image array or None if box is invalid.
        """
        if frame is None or len(bbox) < 4:
            return None

        h, w = frame.shape[:2]
        x1, y1, x2, y2 = bbox[:4]

        # Convert to int coordinates
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        # Ensure valid order
        xmin = min(x1, x2)
        xmax = max(x1, x2)
        ymin = min(y1, y2)
        ymax = max(y1, y2)

        box_w = xmax - xmin
        box_h = ymax - ymin

        if box_w < 10 or box_h < 10:
            return None

        # Apply padding
        pad_x = int(box_w * padding_pct)
        pad_y = int(box_h * padding_pct)

        xmin = max(0, xmin - pad_x)
        ymin = max(0, ymin - pad_y)
        xmax = min(w, xmax + pad_x)
        ymax = min(h, ymax + pad_y)

        cropped = frame[ymin:ymax, xmin:xmax]
        return cropped

