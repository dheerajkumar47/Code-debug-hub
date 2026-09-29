@echo off
REM BidSmith one-click start (Windows). Double-click this file.
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python is not installed. Install Python 3.11+ from https://www.python.org/downloads/
  echo IMPORTANT: tick "Add python.exe to PATH" during install, then run this file again.
  pause
  exit /b 1
)

if not exist .venv (
  echo Creating virtual environment...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
echo Installing requirements (first run only takes a minute)...
python -m pip install -q --disable-pip-version-check -r requirements.txt

set NEEDSETUP=0
if not exist .env set NEEDSETUP=1
if exist keys.txt set NEEDSETUP=1
if exist keys.txt.txt set NEEDSETUP=1
if "%NEEDSETUP%"=="1" (
  echo.
  echo === Setup: reading your keys ===
  python -m bidsmith setup
)

python -m bidsmith check
if errorlevel 1 (
  echo.
  echo Fix the lines marked with X above. To re-enter keys: python -m bidsmith setup
  pause
  exit /b 1
)

python -m bidsmith serve
pause
