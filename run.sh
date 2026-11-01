#!/usr/bin/env bash
# SmartPark AI — Unix Startup Script

set -e

echo "========================================================"
echo "       SMARTPARK AI — FACILITY MANAGEMENT SYSTEM"
echo "========================================================"

if [ -f "smartpark-env/bin/python" ]; then
    PYTHON_CMD="smartpark-env/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "[ERROR] Python 3 executable not found!"
    exit 1
fi

echo "[INFO] Starting SmartPark AI on http://127.0.0.1:8000"
echo "Default Guard Login: guard / smartpark2026"

$PYTHON_CMD app.py

