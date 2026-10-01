@echo off
REM Opens a free, secure https link to your BidSmith dashboard that works on your phone anywhere
REM (Wi-Fi or mobile data). Start start.bat first. See docs\11-PHONE.md
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\phone.ps1"
pause
