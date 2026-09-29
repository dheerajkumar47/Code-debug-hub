@echo off
REM Re-enter or change your keys. Double-click this file.
cd /d "%~dp0"
if not exist .venv (
  echo Run start.bat once first.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
echo.
echo TIP: easiest is keys.txt in this folder (see docs\08-STEP-BY-STEP.md).
echo.
python -m bidsmith setup
python -m bidsmith check
echo.
echo If all lines are ticks, close this window and double-click start.bat
pause
