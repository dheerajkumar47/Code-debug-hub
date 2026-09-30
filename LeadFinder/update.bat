@echo off
REM Lead Finder updater: downloads the latest version. Keeps .env (keys), data\ (results) and .venv\.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0update.ps1"
pause
