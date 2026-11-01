import numpy as np

class ImagePreprocessor:
    """
    Provides image preprocessing techniques for number plate recognition:
    - Grayscale conversion
    - Noise filtering
    - Contrast Enhancement (CLAHE)
    - Adaptive Thresholding
    - Deskewing and sharpening
    """

    @staticmethod
    def preprocess_for_ocr(image_bgr: np.ndarray) -> dict:
        """
        Preprocesses a cropped number plate image to generate optimal representations for OCR.
        Returns a dictionary with raw, grayscale, clahe_enhanced, and binary thresholded variants.
        """
        import cv2

        variants = {}
        variants["original"] = image_bgr

        # 1. Grayscale
        if len(image_bgr.shape) == 3:
            gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        else:
            gray = image_bgr.copy()
        variants["gray"] = gray

        # 2. Resize to optimal height (e.g. 100px) while maintaining aspect ratio
        h, w = gray.shape[:2]
        if h > 0 and w > 0:
            target_h = 100
            scale = target_h / float(h)
            target_w = int(w * scale)
            resized = cv2.resize(gray, (target_w, target_h), interpolation=cv2.INTER_CUBIC)
        else:
            resized = gray
        variants["resized"] = resized

        # 3. Bilateral filter to smooth noise while preserving character edges
        denoised = cv2.bilateralFilter(resized, 9, 75, 75)
        variants["denoised"] = denoised

        # 4. CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        variants["clahe"] = enhanced

        # 5. Adaptive Thresholding (Otsu & Gaussian)
        _, otsu = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants["otsu"] = otsu

        adaptive = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        variants["adaptive"] = adaptive

        return variants

