@echo off
REM Creates azure-cloud-init.txt for running BidSmith 24/7 on an Azure VM. See docs\09-AZURE.md
cd /d "%~dp0"
if not exist .venv (
  echo Run start.bat once first.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python tools\make_azure_setup.py
echo.
pause
