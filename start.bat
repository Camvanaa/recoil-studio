@echo off
chcp 65001 >nul
title Recoil Studio
echo ====================================
echo    Recoil Studio
echo    http://localhost:8000
echo ====================================
echo.
echo Press Ctrl+C to stop
echo.

cd /d "%~dp0backend"
explorer "http://localhost:8000"
uvicorn main:app --host 0.0.0.0 --port 8000
