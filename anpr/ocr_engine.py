import os
import sys
import time
import numpy as np

# Prevent Windows charmap crashes on progress bars
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
from anpr.image_preprocessing import ImagePreprocessor
from anpr.plate_validator import PlateValidator

class OCREngine:
    """
    OCR recognition engine using EasyOCR with multi-stage image preprocessing,
    text normalization, and fallback mechanisms for Indian license plates.
    """

    def __init__(self, use_gpu: bool = False, languages: list = None):
        self.use_gpu = use_gpu
        self.languages = languages or ['en']
        self._reader = None
        self._initialized = False

    def _get_reader(self):
        if not self._initialized:
            try:
                import easyocr
                # Initialize reader on CPU or GPU based on availability
                self._reader = easyocr.Reader(self.languages, gpu=self.use_gpu)
                self._initialized = True
            except Exception as e:
                print(f"Warning: EasyOCR reader initialization failed ({e}). Fallback mode active.")
                self._reader = None
                self._initialized = True
        return self._reader

    def recognize_plate(self, plate_image: np.ndarray) -> dict:
        """
        Runs OCR on plate crop using multiple preprocessing variants.
        Selects the candidate with highest validation score and OCR confidence.
        """
        start_time = time.time()
        if plate_image is None or plate_image.size == 0:
            return {
                "raw_text": "",
                "normalized_text": "",
                "confidence": 0.0,
                "is_valid": False,
                "format_type": "NONE",
                "inference_time_ms": 0.0,
                "best_variant": "none"
            }

        reader = self._get_reader()

        # Generate preprocessed variants
        try:
            variants = ImagePreprocessor.preprocess_for_ocr(plate_image)
        except Exception:
            variants = {"original": plate_image}

        candidates = []

        if reader is not None:
            # Test key variants: original, clahe, and gray
            for var_name in ["clahe", "original", "gray"]:
                img = variants.get(var_name)
                if img is None:
                    continue
                try:
                    # easyocr readtext
                    results = reader.readtext(img, detail=1, paragraph=False)
                    if results:
                        # Combine text fragments
                        combined_text = "".join([res[1] for res in results])
                        # Average confidence
                        confs = [res[2] for res in results if len(res) > 2]
                        avg_conf = float(np.mean(confs)) if confs else 0.5

                        norm_text, is_valid, fmt = PlateValidator.normalize_indian_plate(combined_text)
                        score = avg_conf + (0.5 if is_valid else 0.0)

                        candidates.append({
                            "raw_text": combined_text,
                            "normalized_text": norm_text,
                            "confidence": avg_conf,
                            "is_valid": is_valid,
                            "format_type": fmt,
                            "score": score,
                            "best_variant": var_name
                        })
                except Exception as ex:
                    print(f"OCR variant {var_name} evaluation note: {ex}")

        # If candidates exist, sort by score descending
        if candidates:
            candidates.sort(key=lambda c: c["score"], reverse=True)
            best = candidates[0]
            inference_ms = round((time.time() - start_time) * 1000, 2)
            best["inference_time_ms"] = inference_ms
            return best

        # Fallback if EasyOCR failed or returned empty:
        # Check if plate has high-contrast contours or test fallback
        inference_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "raw_text": "",
            "normalized_text": "",
            "confidence": 0.0,
            "is_valid": False,
            "format_type": "UNRECOGNIZED",
            "inference_time_ms": inference_ms,
            "best_variant": "none"
        }
