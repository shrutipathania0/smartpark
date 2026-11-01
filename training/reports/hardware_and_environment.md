# Phase 1: Hardware and Environment Report

**Project:** SmartPark AI  
**Inspection Date:** November 1, 2026  
**Operating System:** Windows 11 Home / Pro (Build 10.0.26200, 64-bit AMD64)  
**Host Hardware Model:** Intel 11th Gen Laptop Architecture  

---

## 1. Hardware Inspection

| Component | Detected Specification | Notes |
| :--- | :--- | :--- |
| **Processor (CPU)** | 11th Gen Intel(R) Core(TM) i3-1115G4 @ 3.00GHz | 2 Cores, 4 Logical Processors, Tiger Lake architecture |
| **System Memory (RAM)** | 7.75 GB Total (~8 GB physical) | ~0.80 GB to 1.5 GB currently available depending on background tasks |
| **Primary GPU** | Intel(R) UHD Graphics (PCI VEN 8086, DEV 9A78) | Integrated graphics processor |
| **Dedicated NVIDIA GPU** | **Not Present / Not Installed** | Registry and PnP hardware discovery confirmed no discrete NVIDIA GPU or CUDA-capable card on this host |
| **Storage (Drive C:)** | 475.67 GB Total \| **313.52 GB Available Free Space** | Ample disk capacity for models, datasets, database, captures, and logs |
| **Camera Hardware** | Realtek USB Camera (Hardware ID: USB\VID_0BDA&PID_5830) | Status: OK, functional for live video streaming & frame capture |

---

## 2. Software & Python Environment

| Component | Status / Version | Notes |
| :--- | :--- | :--- |
| **Base Python** | Python 3.12.4 (64-bit MSC v.1940) | Located at `C:\Users\shrut\AppData\Local\Programs\Python\Python312\python.exe` |
| **Virtual Environment Target** | `smartpark-env` | Isolated virtual environment using Python 3.12 |
| **PyTorch Architecture** | CPU / OpenVINO / ONNX-ready | PyTorch CPU build selected; provides reliable inference without CUDA crashes |
| **Internet Connectivity** | Active (HTTP 200 to PyPI, GitHub, Hugging Face) | Sandbox commands requiring downloads will use external network elevation |

---

## 3. Engineering Decisions & Constraints

1. **Lightweight Model Strategy:**
   - Because the machine has an Intel Core i3-1115G4 CPU with 8 GB RAM and integrated Intel UHD Graphics, heavy deep learning models (like YOLOv8x or full Transformer OCR pipelines) would risk out-of-memory (OOM) or high inference latencies (>3000ms).
   - We will select lightweight, high-efficiency models:
     - **Detector:** Pretrained and fine-tuned lightweight YOLO (YOLOv8n / YOLO11n / custom plate detector) with 320x320 or 640x640 resolution, ensuring ~50-100ms inference time on CPU.
     - **OCR Pipeline:** High-precision EasyOCR with optimized text normalization, adaptive thresholding preprocessing, and Indian format regular expressions.
     - Optional OpenVINO/ONNX runtime acceleration for Intel Tiger Lake if needed.

2. **Webcam & Processing Architecture:**
   - In-browser client-side frame throttling (capturing candidate frames every 500ms to 1s) to prevent overwhelming the local CPU.
   - Dual-mode recognition: live webcam stream with auto-capture + manual snapshot capture + sample image test suite for demonstration flexibility.

