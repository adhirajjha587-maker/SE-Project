@echo off
title Balaji Medical - Public Internet Sharing
cd /d "%~dp0"

echo ========================================================
echo     BALAJI MEDICAL - PUBLIC INTERNET TUNNEL
echo ========================================================
echo.
echo Connecting to public tunnel for external devices/clients...
echo (If disconnected, this window will automatically reconnect)
echo.

:loop
echo Connecting...
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=15 -o ServerAliveCountMax=3 -i "%USERPROFILE%\.ssh\id_ed25519" -R 80:127.0.0.1:5000 nokey@localhost.run
echo.
echo Tunnel connection ended. Reconnecting in 3 seconds...
timeout /t 3 /nobreak >nul
goto loop
