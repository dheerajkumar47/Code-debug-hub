@echo off
REM Opens a free, secure https link to your BidSmith dashboard that works on your phone anywhere
REM (Wi-Fi or mobile data). Keep start.bat running in its own window first. See docs\11-PHONE.md
cd /d "%~dp0"
if not exist data mkdir data
if not exist data\cloudflared.exe (
  echo Downloading Cloudflare Tunnel - one time only...
  powershell -NoProfile -Command "Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'data\cloudflared.exe'"
  if not exist data\cloudflared.exe (
    echo Download failed. Check your internet and try again.
    pause
    exit /b 1
  )
)
echo.
echo ================================================================
echo  Look below for a line with  https://....trycloudflare.com
echo  Open that link on your phone. Login: owner + your password.
echo  Keep this window AND the start.bat window open.
echo ================================================================
echo.
data\cloudflared.exe tunnel --no-autoupdate --url http://localhost:8000
pause
