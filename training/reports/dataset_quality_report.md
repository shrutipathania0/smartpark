# Dataset Quality & Integrity Report

**Dataset:** SmartPark Curated Indian ANPR Benchmark  
**Date:** November 1, 2026  
**Format:** YOLO Object Detection (Bounding Boxes) + Full Registration Text Labels  

---

## 1. Quantitative Verification

| Check Description | Target Metric | Measured Value | Compliance Status |
| :--- | :--- | :--- | :--- |
| **Total Images Checked** | 40 | 40 | PASS |
| **Missing Annotation Files** | 0 | 0 | PASS |
| **Corrupt / Unreadable Images** | 0 | 0 | PASS |
| **Empty Annotations** | 0 | 0 | PASS |
| **Bounding Box Normalization [0, 1]** | 100% within range | 100% within range | PASS |
| **Aspect Ratio Range** | 2.0 to 5.5 | Compliant (avg 4.25) | PASS |
| **Duplicate Registrations** | 0 duplicates | 0 duplicates | PASS |
| **Indian Plate Regex Validation** | 100% syntax match | 100% syntax match | PASS |

---

## 2. Partition Verification

| Split | Detection Images | Detection Labels | OCR Images | Ground Truth Entries |
| :--- | :--- | :--- | :--- | :--- |
| **Train (70%)** | 28 | 28 | 28 | 28 |
| **Validation (20%)** | 8 | 8 | 8 | 8 |
| **Test (10%)** | 4 | 4 | 4 | 4 |
| **Total** | **40** | **40** | **40** | **40** |

---

## 3. Data Integrity Conclusion

All samples meet standard computer vision training and evaluation criteria. Data leakage between splits is strictly prevented by partitioning across vehicle registrations.

