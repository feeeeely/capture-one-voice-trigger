@echo off
REM One-time setup for Voice Trigger on Windows. Run once, then you're done.
setlocal
cd /d "%~dp0"

echo Voice Trigger for Capture One - setup
echo =====================================
echo.

REM --- 1. Find a suitable Python -------------------------------------
REM 3.10 minimum: pywin32 publishes no wheels below that.
set "PY="
call :trypy py -3.13
call :trypy py -3.12
call :trypy py -3.11
call :trypy py -3.10
call :trypy py -3
call :trypy python
if not defined PY goto nopython

for /f "delims=" %%V in ('%PY% --version 2^>^&1') do echo Found Python: %%V

REM --- 2. Virtual environment ----------------------------------------
if exist "venv\Scripts\python.exe" goto haveenv
echo Creating virtual environment...
%PY% -m venv venv
if errorlevel 1 goto venvfail
:haveenv

set "VPY=venv\Scripts\python.exe"

echo Installing packages...
%VPY% -m pip install --quiet --upgrade pip
REM 0.3.44 is pinned to match macOS; do not bump without testing there.
%VPY% -m pip install --quiet "vosk==0.3.44" sounddevice keyboard pywin32 psutil
if errorlevel 1 goto pipfail

REM --- 3. Speech model ------------------------------------------------
REM Override with:  set MODEL=vosk-model-small-de-0.15  before running.
if not defined MODEL set "MODEL=vosk-model-small-en-us-0.15"

if exist "%MODEL%" goto havemodel
echo Downloading speech model %MODEL% (about 45 MB)...
curl -fL -o model.zip "https://alphacephei.com/vosk/models/%MODEL%.zip"
if errorlevel 1 goto dlfail

tar -xf model.zip 2>nul
if not exist "%MODEL%" powershell -NoProfile -Command "Expand-Archive -Path 'model.zip' -DestinationPath '.' -Force"
if not exist "%MODEL%" goto unzipfail
del model.zip
goto modeldone
:havemodel
echo Speech model already present.
:modeldone

echo.
echo =====================================
echo Done.
echo.
echo STILL TO DO in Capture One:
echo   Edit ^> Edit Keyboard Shortcuts
echo   -^> Duplicate the default set, then SELECT it in the dropdown
echo   -^> 'Capture'                      -^>  Ctrl + Alt + Shift + A
echo   -^> 'Start/Stop Camera Autofocus'  -^>  Ctrl + Alt + Shift + F
echo.
echo Then double-click:  start.bat
echo =====================================
echo.
pause
exit /b 0

REM -------------------------------------------------------------------
:trypy
if defined PY goto :eof
%* -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 goto :eof
set "PY=%*"
goto :eof

:nopython
echo ERROR: Python 3.10 or newer is required, and none was found.
echo.
echo Install it from:
echo     https://www.python.org/downloads/
echo Tick "Add python.exe to PATH" during the install, then run this again.
echo.
pause
exit /b 1

:venvfail
echo ERROR: could not create the virtual environment.
echo Try deleting the "venv" folder and running this again.
echo.
pause
exit /b 1

:pipfail
echo ERROR: package installation failed. The messages above say why.
echo A company-managed PC may be blocking downloads from the internet.
echo.
pause
exit /b 1

:dlfail
echo ERROR: could not download the speech model.
echo Get %MODEL%.zip by hand from https://alphacephei.com/vosk/models
echo and unzip it into this folder, then run this again.
echo.
pause
exit /b 1

:unzipfail
echo ERROR: downloaded the model but could not unpack it.
echo Unzip model.zip into this folder by hand, then run this again.
echo.
pause
exit /b 1
