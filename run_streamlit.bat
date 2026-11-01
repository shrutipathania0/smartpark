@echo off
title SmartPark AI — Streamlit App Launcher
echo ========================================================
echo        SMARTPARK AI — STREAMLIT FACILITY SYSTEM
echo ========================================================
echo.

set VENV_PY=smartpark-env\Scripts\python.exe

if not exist "%VENV_PY%" (
    echo [ERROR] Virtual environment 'smartpark-env' was not found!
    echo Please run:
    echo   python -m venv smartpark-env
    echo   smartpark-env\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo [INFO] Starting SmartPark AI Streamlit App...
echo.
echo URL: http://localhost:8501
echo.

smartpark-env\Scripts\streamlit.exe run streamlit_app.py
pause

