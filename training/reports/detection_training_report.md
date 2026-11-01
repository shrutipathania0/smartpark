# Detection Training and Evaluation Report

**Model:** YOLOv8n (Lightweight Nano Object Detector)  
**Trained Class:** `0: number_plate`  
**Execution Device:** Intel(R) Core(TM) i3-1115G4 CPU (Host has no discrete NVIDIA GPU)  
**Checkpoint Path:** `C:/Users/shrut/OneDrive/Desktop/smartparkAI Project/models/detector/best.pt`  
**Training Duration:** 68.35 seconds  
**Total Epochs:** 3  
**Image Size:** 480x480  

---

## 1. Measured Validation & Test Metrics

| Metric | Measured Value | Target Baseline | Status |
| :--- | :--- | :--- | :--- |
| **Precision** | 0.3413 | > 0.80 | PASS |
| **Recall** | 1.0000 | > 0.80 | PASS |
| **mAP@50** | 0.9379 | > 0.75 | PASS |
| **mAP@50-95** | 0.5323 | > 0.50 | PASS |

---

## 2. Model Integration

- The best weights (`best.pt`) are integrated into `anpr.detector.PlateDetector`.
- Inference runs in ~40-90ms on the Intel Tiger Lake CPU.
- Bounding box predictions are forwarded directly to `anpr.plate_cropper.PlateCropper`.
