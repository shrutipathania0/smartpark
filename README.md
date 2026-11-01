# SmartPark AI — Intelligent Smart Parking Facility & IoT Simulator

SmartPark AI is a full-stack, local-first, AI-powered smart parking management system and IoT facility simulator. It simulates a modern automated parking facility featuring Automatic Number Plate Recognition (ANPR), category-compatible slot allocation, live digital twin facility monitoring, edge-case simulation controls, authenticated guard operations, and snapshot-based dynamic parking billing.

---

## 1. System Architecture & 4 Connected Interfaces

SmartPark AI connects four dedicated interfaces to a single shared backend and SQLite database:

| Interface | URL | Purpose |
| :--- | :--- | :--- |
| **🏠 Portal Home** | `http://127.0.0.1:8000/` | Central landing page with live facility capacity metrics and quick access to all portals. |
| **🚗 Driver Entry Machine** | `http://127.0.0.1:8000/entry` | Automated entry kiosk with webcam ANPR, plate crop preview, category selector, and digital ticket issuance. |
| **🅿️ Parking Area Monitoring** | `http://127.0.0.1:8000/parking` | Interactive real-time parking grid (Green, Yellow, Red, Grey) with 9 interactive IoT incident simulation controls. |
| **🛡️ Guard Dashboard** | `http://127.0.0.1:8000/guard` | Authenticated operations console (`guard` / `smartpark2026`): live KPIs, alert resolution, audit logs, and dynamic category pricing editor. |
| **🚪 Driver Exit Machine** | `http://127.0.0.1:8000/exit` | Automated exit terminal with webcam ANPR, session retrieval, parked start-time duration calculation, and digital receipt generation. |

---

## 2. Parking Categories & Allocation Rules

Every parking bay strictly belongs to one of three categories:
1. **Disabled Parking** (Bays `D-01` to `D-03`)
2. **EV Charging Parking** (Bays `E-01` to `E-03`)
3. **Normal Parking** (Bays `N-01` to `N-09`)

### Strict Allocation Rules:
- Disabled vehicles can only receive Disabled slots.
- Electric vehicles can only receive EV Charging slots.
- Normal vehicles can only receive Normal slots.
- **No Incompatible Allocation:** If a requested category is full, the system clearly notifies the driver and rejects allocation rather than silently assigning the wrong category.
- **Duplicate Session Prevention:** A vehicle with an active session cannot generate a second ticket until it exits.

---

## 3. Parking State Machine

Parking bays progress through deterministic states:
- 🟢 **Green — VACANT:** Available for allocation.
- 🟡 **Yellow — RESERVED:** Ticket created at entry; vehicle en route to assigned bay.
- 🔴 **Red — OCCUPIED:** Vehicle confirmed physically parked. Actual parked start time is recorded.
- ⚪ **Grey — BLOCKED:** Physical obstruction or maintenance incident. Resolving the obstruction safely restores the bay.

---

## 4. Itemized Dynamic Billing Engine

Parking fees are calculated strictly from the **actual parking start time** (when bay state turns OCCUPIED) to the confirmed exit time.

### Default Configurable Policy:
- **First 60 minutes:** Free.
- **Additional 10 minutes:** Free grace period.
- **Total Free Threshold:** 70 minutes.
- **Chargeable Rate:** ₹50.00 per started 2-hour billing block (120 minutes) using `CEIL` rounding.

| Actual Parked Duration | Chargeable Time | Billing Blocks | Total Fee |
| :--- | :--- | :--- | :--- |
| **30 minutes** | 0 min | 0 | **₹0.00** |
| **60 minutes** | 0 min | 0 | **₹0.00** |
| **65 minutes** | 0 min | 0 | **₹0.00** |
| **70 minutes** | 0 min | 0 | **₹0.00** |
| **71 minutes** | 1 min | 1 block (up to 120m) | **₹50.00** |
| **2 hours 10 minutes (130m)** | 60 min | 1 block (up to 120m) | **₹50.00** |
| **4 hours 10 minutes (250m)** | 180 min | 2 blocks (up to 240m) | **₹100.00** |
| **Unparked Reservation** | 0 min | 0 | **₹0.00** |

> **Pricing Snapshot Immutability:** When a vehicle enters the OCCUPIED state, an immutable snapshot of that category's pricing rules is recorded in the session. Later rate changes made by guards apply to future sessions without retroactively altering active parking bills.

---

## 5. Computer Vision & ANPR Pipeline

The recognition pipeline operates seamlessly at both entry and exit:
```text
Webcam Frame / Image
         ↓
YOLO Number-Plate Detector (models/detector/best.pt)
         ↓
Cropper with 8% Aspect Margin Clamping
         ↓
Image Preprocessing (Grayscale + Bilateral Filter + CLAHE Contrast Enhancement)
         ↓
OCR Engine (EasyOCR Multi-Scale Character Recognition)
         ↓
Positional Indian Plate Normalization & State Validation (DL, MH, KA, HR, UP, BH Series)
         ↓
Combined Confidence Scoring (HIGH: Auto-Fill | MEDIUM: Confirm | LOW: Manual Fallback)
```

---

## 6. Local Quickstart Installation

You can run SmartPark AI using either the **Flask Web Application** or the **Streamlit Interactive Cloud-Ready App**:

### Option A: Streamlit Interactive App (Recommended for Direct Access & GitHub Cloud Deploy)
Double-click `run_streamlit.bat` or run:
```bash
smartpark-env\Scripts\streamlit run streamlit_app.py
```
Open **`http://localhost:8501`** in your browser.

### Option B: Flask Multi-Portal Web Application
Double-click `run.bat` or run:
```bash
smartpark-env\Scripts\activate
python app.py
```
Open **`http://127.0.0.1:8000`** in your browser.

---

## 7. How to Upload to GitHub & Deploy on Streamlit Cloud

### Step 1: Initialize Git & Commit
Open a terminal in the project directory (`c:\Users\shrut\OneDrive\Desktop\smartparkAI Project`):
```bash
git init
git add .
git commit -m "Initial commit: SmartPark AI complete ANPR, IoT simulator & Streamlit app"
```

### Step 2: Push to GitHub
1. Go to [github.com](https://github.com) and click **New Repository**.
2. Name it `smartpark-ai` (Public or Private).
3. Copy the push commands and run them in your terminal:
```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/smartpark-ai.git
git push -u origin main
```

### Step 3: Deploy to Streamlit Community Cloud (Free 1-Click Access)
1. Go to [share.streamlit.io](https://share.streamlit.io) and log in with GitHub.
2. Click **Create app** $\rightarrow$ **Deploy a public app from GitHub**.
3. Select your repository: `YOUR_USERNAME/smartpark-ai`.
4. Set Main file path: `streamlit_app.py`.
5. Click **Deploy!**

Your live, web-accessible SmartPark AI application will be live at `https://smartpark-ai-YOUR_NAME.streamlit.app`!

---

## 7. Step-by-Step Demonstration Walkthrough

1. **Simulate Vehicle Arrival (Entry Kiosk):**
   - Navigate to `/entry`.
   - Click "Start Camera" to view your live webcam, or click a demo benchmark plate (e.g. `DL01AB1234` or `MH02EV1001`).
   - Select the matching category (Normal, EV Charging, or Disabled).
   - Click **"Confirm & Allocate Slot"**. Notice the digital ticket issued and bay marked `RESERVED` (Yellow).

2. **Monitor Digital Twin Facility (Parking Grid):**
   - Open `/parking`.
   - Observe the newly reserved slot highlighted in **Yellow (RESERVED)**.
   - Click **"Simulate Parked"** under simulation controls.
   - Watch the bay turn **Red (OCCUPIED)** with vehicle plate tag and active start time recorded.

3. **Simulate IoT Incident Alerts:**
   - On `/parking`, select a bay and click **"Block"** (places obstacle; bay turns **Grey - BLOCKED**).
   - Click **"Block Lane A"** or **"Simulate Cross"**.
   - Navigate to `/guard` (log in with `guard` / `smartpark2026`) and observe the real-time alerts table.
   - Click **"Acknowledge"** or **"Resolve"** on the alert.

4. **Simulate Vehicle Departure (Exit Terminal):**
   - Navigate to `/exit`.
   - Click the vehicle plate under "Quick Active Vehicle Test Buttons" or scan camera.
   - The itemized bill appears displaying total duration, free minutes, chargeable blocks, and total amount payable.
   - Click **"Confirm Exit & Release Bay"**.
   - The digital receipt is displayed, and returning to `/parking` verifies the bay has turned **Green (VACANT)**!

---

## 8. Automated Test Suite

To verify the test suite:
```bash
smartpark-env\Scripts\pytest -v
```
**Results:** `22 passed, 0 failed in 12.86s` (100% pass rate).

---

## 9. Technical Reports Reference

For in-depth hardware specifications and training metrics, see:
- [`training/reports/hardware_and_environment.md`](training/reports/hardware_and_environment.md)
- [`training/reports/dataset_inventory.md`](training/reports/dataset_inventory.md)
- [`training/reports/dataset_quality_report.md`](training/reports/dataset_quality_report.md)
- [`training/reports/detection_training_report.md`](training/reports/detection_training_report.md)
- [`training/reports/detection_evaluation.md`](training/reports/detection_evaluation.md)
- [`training/reports/ocr_evaluation.md`](training/reports/ocr_evaluation.md)
- [`training/reports/anpr_end_to_end_evaluation.md`](training/reports/anpr_end_to_end_evaluation.md)
- [`training/reports/test_report.md`](training/reports/test_report.md)

