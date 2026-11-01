# Dataset Inventory & Research Report

**Project:** SmartPark AI  
**Research Date:** November 1, 2026  
**Target:** Indian Vehicle Automatic Number Plate Recognition (ANPR)  

---

## 1. Public Dataset Sources Researched

| Dataset Name | Source / Repository | Total Samples | Bounding Box Available | Text Labels Available | Licence / Terms | Selected Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Kaggle Indian Number Plates** | `kaggle.com/datasets/dataturks/vehicle-number-plate-detection` | 237 images | Yes (JSON bounding boxes) | Partial OCR | Open Data / CC-BY 4.0 | Evaluated |
| **Roboflow Indian License Plates** | `universe.roboflow.com/indian-plates/indian-car-plates` | 1,200+ images | Yes (YOLO v8 format) | Bounding box only | CC-BY 4.0 | Evaluated |
| **ANPRIND Character Dataset** | `mendeley.com/datasets/indian-number-plates` | 1,000+ crops | Bounding box crops | Character labels | Research Use | Evaluated |
| **SmartPark Indian ANPR Benchmark** | Local Curated & Standardized Synthesis | 40 multi-state samples | Yes (YOLO normalized txt) | Full ground-truth registration CSV | Open Source MIT | **Active Curated Benchmark** |

---

## 2. Dataset Partitioning

The curated benchmark dataset adheres strictly to independent data splits with zero leakage across vehicle identities:

```text
training/datasets/
│
├── detection/
│   ├── images/
│   │   ├── train/ (70% - 28 samples)
│   │   ├── val/   (20% - 8 samples)
│   │   └── test/  (10% - 4 samples)
│   ├── labels/
│   │   ├── train/
│   │   ├── val/
│   │   └── test/
│   └── data.yaml
│
└── recognition/
    ├── images/
    ├── labels.csv
    ├── train.csv
    ├── val.csv
    └── test.csv
```

---

## 3. Plate Variety & Regional Representation

The benchmark covers realistic Indian registration formats:
- **Private White Plates:** Delhi (`DL`), Maharashtra (`MH`), Karnataka (`KA`), Tamil Nadu (`TN`), Uttar Pradesh (`UP`), Haryana (`HR`), Gujarat (`GJ`), Rajasthan (`RJ`), West Bengal (`WB`), Kerala (`KL`), Andhra Pradesh (`AP`), Telangana (`TS`), Madhya Pradesh (`MP`), Chandigarh (`CH`), Punjab (`PB`).
- **Electric Vehicle (EV) Green Plates:** `MH02EV1001`, `DL03EV2020`, `KA03EV3344`, `TS09EV5566`, `TN09EV7788`, `UP14EV9900`.
- **Commercial Yellow Plates:** `DL1TA4500`, `MH01TC8899`, `KA04TB1234`, `HR55T9999`.
- **Bharat (BH) Series Plates:** `22BH1029AB`, `23BH4567ZZ`, `21BH8812CD`, `24BH3344EF`.

