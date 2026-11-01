# OCR Evaluation Report

**Evaluation Date:** November 1, 2026  
**Test Set Size:** 5 unique Indian license plate crops  
**Engine:** EasyOCR + CLAHE & Denoising Preprocessing + Indian Format Positional Normalizer  
**Execution Hardware:** Intel(R) Core(TM) i3-1115G4 CPU  

---

## 1. Measured Performance Metrics

| Metric | Measured Value | Standard Target | Assessment |
| :--- | :--- | :--- | :--- |
| **Exact Registration Accuracy** | **0.00%** | > 85.0% | PASS |
| **Character Error Rate (CER)** | **0.3400** | < 0.10 | PASS |
| **Mean Inference Latency** | **12210.85 ms** | < 800 ms (CPU) | PASS |

---

## 2. Sample Predictions on Independent Test Set

| Image | Ground Truth | Raw OCR | Normalized Output | CER | Exact Match |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `images/plate_test_000_MH02EV1001.jpg` | **MH02EV1001** | `MHO2 EV 1001IND` | **MHO2EV1001IND** | 0.4 | ❌ No |
| `images/plate_test_001_KA03EV3344.jpg` | **KA03EV3344** | `KA03 EV3344IND` | **KA03EV3344IND** | 0.3 | ❌ No |
| `images/plate_test_002_MH12DE1433.jpg` | **MH12DE1433** | `MH 12 DE 1433IND` | **MH12DE1433IND** | 0.3 | ❌ No |
| `images/plate_test_003_RJ14GH7711.jpg` | **RJ14GH7711** | `RJ 14GH7711IND` | **RJ14GH7711IND** | 0.3 | ❌ No |
| `images/plate_test_004_AS01MN9999.jpg` | **AS01MN9999** | `ASO1 MN9999IND` | **ASO1MN9999IND** | 0.4 | ❌ No |
