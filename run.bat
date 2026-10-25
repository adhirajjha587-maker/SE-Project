@echo off
title Balaji Medical - Pharmacy Management System
cd /d "%~dp0"

echo ========================================================
echo        BALAJI MEDICAL - PHARMACY STORE SERVER
echo ========================================================
echo.

set PY_CMD=
where py >nul 2>nul
if %errorlevel% equ 0 (
    set PY_CMD=py
) else if exist "C:\Users\Adhiraj\AppData\Local\Programs\Python\Python313\python.exe" (
    set PY_CMD="C:\Users\Adhiraj\AppData\Local\Programs\Python\Python313\python.exe"
) else (
    set PY_CMD=python
)

echo [1/2] Verifying Database & Medicines Catalog...
%PY_CMD% database.py

echo.
echo [2/2] Starting Balaji Medical Server...
echo.
echo ========================================================
echo  Local PC Address     : http://127.0.0.1:5000
echo  Same Wi-Fi (Mobiles) : http://10.225.176.19:5000
echo ========================================================
echo.
echo Opening browser...
start http://127.0.0.1:5000/
echo.
echo Server is running! Keep this window open.
echo Press Ctrl+C to stop.
echo.

%PY_CMD% app.py
pause
