@echo off
REM Update BidSmith to the latest version. Keeps your keys (.env) and history (data folder).
cd /d "%~dp0"
echo Downloading the latest BidSmith...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$zip = Join-Path $env:TEMP 'bidsmith_update.zip'; $tmp = Join-Path $env:TEMP 'bidsmith_update';" ^
  "Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/dheerajkumar47/Code-debug-hub/archive/refs/heads/claude/funny-noether-d41u0f.zip' -OutFile $zip;" ^
  "if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force };" ^
  "Expand-Archive -Path $zip -DestinationPath $tmp -Force;" ^
  "$src = (Get-ChildItem $tmp -Directory | Select-Object -First 1).FullName;" ^
  "robocopy $src . /E /NFL /NDL /NJH /NJS /XD .venv data /XF .env keys.txt update.bat | Out-Null;" ^
  "Write-Host 'Updated. Your keys and history were kept.'"
if errorlevel 1 (
  echo Update failed - check your internet connection and try again.
  pause
  exit /b 1
)
echo.
echo Starting BidSmith...
call "%~dp0start.bat"
