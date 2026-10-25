@echo off
title BuildPulse - Enterprise Construction Management System
cd /d "%~dp0"

echo ========================================================
echo        BUILDPULSE - CONSTRUCTION MANAGEMENT SYSTEM
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

echo [1/2] Verifying BuildPulse Database & Projects...
%PY_CMD% database_buildpulse.py

echo.
echo [2/2] Starting BuildPulse Server on Port 5001...
echo.
echo ========================================================
echo  Local PC Address     : http://127.0.0.1:5001
echo  Dashboard            : http://127.0.0.1:5001/dashboard
echo  Client Portal        : http://127.0.0.1:5001/client-portal
echo ========================================================
echo.
echo Opening browser...
start http://127.0.0.1:5001/
echo.
echo Server is running! Keep this window open.
echo Press Ctrl+C to stop.
echo.

set PORT=5001
%PY_CMD% app_buildpulse.py
pause
