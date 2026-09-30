# Lead Finder updater. Downloads the repo ZIP and copies only the LeadFinder folder here.
# Keeps: .env (your keys), data\ (results), .venv\ (installed libraries).
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$url  = 'https://github.com/dheerajkumar47/Code-debug-hub/archive/refs/heads/claude/funny-noether-d41u0f.zip'
$tmp  = Join-Path $env:TEMP 'leadfinder_update'
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
New-Item -ItemType Directory -Path $tmp | Out-Null
$zip = Join-Path $tmp 'repo.zip'
Write-Host "Downloading the latest Lead Finder..."
Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $zip
Expand-Archive -Path $zip -DestinationPath $tmp -Force
$src = Join-Path (Get-ChildItem $tmp -Directory | Select-Object -First 1).FullName 'LeadFinder'
if (-not (Test-Path $src)) { Write-Host "LeadFinder folder not found in the download."; exit 1 }
robocopy $src $here /E /NFL /NDL /NJH /NJS /XD .venv data /XF .env | Out-Null
if ($LASTEXITCODE -ge 8) { Write-Host "Copy failed (robocopy code $LASTEXITCODE)."; exit 1 }
Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Updated. Your keys and results were kept."
exit 0
