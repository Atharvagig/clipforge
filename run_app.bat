@echo off
title ClipForgeAI Launcher
echo ==========================================
echo       Starting ClipForgeAI Desktop
echo ==========================================
echo.
"C:\Users\atharva tripathi\AppData\Local\Programs\Python\Python312\python.exe" -m clipforge.main
if %ERRORLEVEL% neq 0 (
    echo.
    echo Application exited with error code %ERRORLEVEL%
    pause
)
