@echo off
chcp 65001 >nul
echo Building frontend...
cd /d "%~dp0frontend"
call npm install
call npm run build
echo.
echo Build complete! Files output to backend/static
pause
