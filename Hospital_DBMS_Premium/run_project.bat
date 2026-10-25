@echo off
title MediCore Hospital Suite - Premium
echo.
echo ===============================================
echo       MEDICORE HOSPITAL SUITE
echo ===============================================
echo.
if not exist venv (
  echo [1/3] Creating Python virtual environment...
  py -m venv venv
) else (
  echo [1/3] Virtual environment already exists.
)
call venv\Scripts\activate
echo [2/3] Installing required package...
python -m pip install -r requirements.txt
echo [3/3] Starting hospital system...
echo.
echo Open http://127.0.0.1:5000 in your browser.
echo Press CTRL+C to stop the server.
echo.
python app.py
pause
