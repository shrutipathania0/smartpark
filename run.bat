@echo off
title SmartPark AI — Local Server Startup
echo ========================================================
echo        SMARTPARK AI — FACILITY MANAGEMENT SYSTEM
echo ========================================================
echo.

set VENV_PY=smartpark-env\Scripts\python.exe

if not exist "%VENV_PY%" (
    echo [ERROR] Virtual environment 'smartpark-env' was not found!
    echo Please install dependencies using:
    echo   python -m venv smartpark-env
    echo   smartpark-env\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo [INFO] Activating virtual environment...
call smartpark-env\Scripts\activate.bat

echo [INFO] Checking local directories and model weights...
if not exist "models\detector\best.pt" (
    echo [WARNING] Custom detector 'models\detector\best.pt' not found.
    echo Defaulting to pretrained lightweight YOLOv8n detector.
)

echo.
echo ========================================================
echo  SmartPark AI is starting on: http://127.0.0.1:8000
echo  - Portal Home:       http://127.0.0.1:8000/
echo  - Entry Machine:     http://127.0.0.1:8000/entry
echo  - Parking Grid:      http://127.0.0.1:8000/parking
echo  - Guard Dashboard:   http://127.0.0.1:8000/guard
echo  - Exit Machine:      http://127.0.0.1:8000/exit
echo.
echo  Default Guard Login: guard / smartpark2026
echo ========================================================
echo.

"%VENV_PY%" app.py
pause

