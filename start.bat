@echo off
REM Double-click to start the voice trigger.
cd /d "%~dp0"

if exist "venv\Scripts\python.exe" goto run
echo Setup has not been run yet.
echo Run setup.bat first (see README).
echo.
pause
exit /b 1

:run
venv\Scripts\python.exe voice_trigger.py
echo.
pause
