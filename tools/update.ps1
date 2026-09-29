# BidSmith updater. The repo is private, so the download goes through your browser (already logged in to GitHub).
# Keeps: .env (your keys), data\ (history), .venv\ (installed libraries).
param([string]$BotDir = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
$url  = 'https://github.com/dheerajkumar47/Code-debug-hub/archive/refs/heads/claude/funny-noether-d41u0f.zip'
$name = 'Code-debug-hub-claude-funny-noether-d41u0f*.zip'

try { $downloads = (New-Object -ComObject Shell.Application).Namespace('shell:Downloads').Self.Path } catch { $downloads = $null }
if (-not $downloads -or -not (Test-Path $downloads)) { $downloads = Join-Path $env:USERPROFILE 'Downloads' }

$started = Get-Date
Write-Host "Opening the download in your browser (you are logged in to GitHub there)..."
Start-Process $url
Write-Host "Waiting for the ZIP in $downloads  (up to 3 minutes)..."

$zip = $null
for ($i = 0; $i -lt 180 -and -not $zip; $i++) {
    Start-Sleep -Seconds 1
    $cand = Get-ChildItem -Path $downloads -Filter $name -File -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -ge $started.AddSeconds(-5) } |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($cand) {
        $size1 = $cand.Length; Start-Sleep -Seconds 2; $cand.Refresh()
        if ($cand.Length -eq $size1 -and $size1 -gt 0) { $zip = $cand.FullName }
    }
}
if (-not $zip) {
    Write-Host "No download arrived. If the browser asked where to save, save it to Downloads and run update.bat again."
    exit 1
}

$tmp = Join-Path $env:TEMP 'bidsmith_update'
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
Expand-Archive -Path $zip -DestinationPath $tmp -Force
$src = (Get-ChildItem $tmp -Directory | Select-Object -First 1).FullName
robocopy $src $BotDir /E /NFL /NDL /NJH /NJS /XD .venv data /XF .env keys.txt update.bat | Out-Null
if ($LASTEXITCODE -ge 8) { Write-Host "Copy failed (robocopy code $LASTEXITCODE)."; exit 1 }
Remove-Item $zip -Force -ErrorAction SilentlyContinue
Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Updated. Your keys and history were kept."
exit 0
