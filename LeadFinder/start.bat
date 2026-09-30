@echo off
REM Lead Finder: double-click to open the dashboard in your browser. Keep this window open while you use it.
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python is not installed. Install Python 3.11+ from https://www.python.org/downloads/
  pause
  exit /b 1
)
if not exist .venv (
  echo First run: setting up, about 1 minute...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install -q --disable-pip-version-check -r requirements.txt
if not exist .env (
  if exist ..\FreelancerBot\.env (
    copy ..\FreelancerBot\.env .env >nul
    echo Copied your keys from the FreelancerBot folder.
  ) else (
    copy .env.example .env >nul
  )
)
python -m leadfinder
pause
