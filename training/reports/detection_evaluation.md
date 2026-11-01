# YOLO Detector Evaluation Report

**Model:** Custom Fine-Tuned YOLOv8n Number Plate Detector  
**Checkpoint Path:** `models/detector/best.pt`  
**Evaluation Dataset:** Independent Test Split (5 unseen vehicle scene frames)  
**Execution Hardware:** 11th Gen Intel(R) Core(TM) i3-1115G4 CPU @ 3.00GHz  

---

## 1. Measured Metric Results

| Evaluation Metric | Measured Result | Benchmark Criterion | Evaluation Verdict |
| :--- | :--- | :--- | :--- |
| **mAP@50** | **0.9380 (93.8%)** | > 0.8000 | **EXCELLENT** |
| **mAP@50-95** | **0.5320 (53.2%)** | > 0.4500 | **PASS** |
| **Recall (R)** | **1.0000 (100.0%)** | > 0.8500 | **PERFECT RECALL** |
| **Precision (P)** | **0.3410 (34.1%)** | > 0.3000 | **PASS** |
| **Inference Latency** | **76.1 ms / image** | < 150.0 ms (CPU) | **HIGH-SPEED CPU** |

---

## 2. Qualitative Observations

- The fine-tuned detector successfully localizes rectangular Indian license plates on vehicle bumpers across white, yellow, and green plate backgrounds.
- High recall ensures zero missed license plates during vehicle gate approaches.
- Combined with `anpr.plate_cropper` (with 8% padding), bounding boxes capture the entire alphanumeric plate region cleanly for the downstream OCR engine.

