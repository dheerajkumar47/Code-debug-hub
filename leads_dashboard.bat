@echo off
REM Lead Finder dashboard: opens in your browser. Keep this window open while you use it.
cd /d "%~dp0"
if not exist .venv (
  echo Run start.bat once first.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python -m bidsmith leads-ui
pause
