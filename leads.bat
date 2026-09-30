@echo off
REM Finds real, qualified business leads from Google Maps. See docs\10-LEADS.md
cd /d "%~dp0"
if not exist .venv (
  echo Run start.bat once first.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python -m bidsmith leads
echo.
pause
