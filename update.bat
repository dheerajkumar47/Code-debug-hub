@echo off
REM Update BidSmith. Your browser downloads the new version (the repo is private); keys and history are kept.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\update.ps1" -BotDir "%~dp0."
if errorlevel 1 (
  echo.
  echo Update did not finish. You can also download the ZIP yourself - see docs\08-STEP-BY-STEP.md
  pause
  exit /b 1
)
echo.
echo Starting BidSmith...
call "%~dp0start.bat"
