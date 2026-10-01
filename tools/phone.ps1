# Phone link for the BidSmith dashboard (free Cloudflare quick tunnel). Called by phone.bat.
# Checks the bot is running, starts the tunnel, prints the link big and copies it to the clipboard.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$exe  = Join-Path $root 'data\cloudflared.exe'
$log  = Join-Path $root 'data\phone-tunnel-quic.log'
New-Item -ItemType Directory -Force -Path (Join-Path $root 'data') | Out-Null

function Say($text, $color = 'Gray') { Write-Host $text -ForegroundColor $color }

# 1. The bot must be running, otherwise the link opens an error page.
try {
    Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 5 | Out-Null
    Say 'OK  BidSmith is running.' 'Green'
} catch {
    Say ''
    Say 'BidSmith is NOT running.' 'Red'
    Say 'Double-click start.bat first, wait until it says "Application startup complete", then run phone.bat again.' 'Yellow'
    exit 1
}

# 2. Download Cloudflare Tunnel once.
if (-not (Test-Path $exe)) {
    Say 'Downloading Cloudflare Tunnel (one time only)...'
    try {
        Invoke-WebRequest -UseBasicParsing -OutFile $exe `
            -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe'
    } catch {
        Say 'Download failed. Check your internet and try again.' 'Red'
        exit 1
    }
}

# 3. Start the tunnel; if the fast connection (QUIC) is blocked on this network, retry with HTTP/2.
function Start-Tunnel($protocol) {
    $script:log = Join-Path $root "data\phone-tunnel-$protocol.log"
    if (Test-Path $script:log) { Remove-Item $script:log -Force -ErrorAction SilentlyContinue }
    # Same console window (closing the window stops the tunnel); its messages go to the log file.
    $argList = "tunnel --no-autoupdate --protocol $protocol --url http://127.0.0.1:8000"
    return Start-Process -FilePath $exe -ArgumentList $argList -PassThru -NoNewWindow -RedirectStandardError $script:log
}

# Stop a tunnel left over from an earlier run, so only one link is active.
Get-Process -Name cloudflared -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -eq $exe } | Stop-Process -Force -ErrorAction SilentlyContinue

function Wait-Link($proc) {
    for ($i = 0; $i -lt 45; $i++) {
        Start-Sleep -Seconds 1
        if ($proc.HasExited) { return $null }
        if (Test-Path $script:log) {
            $m = Select-String -Path $script:log -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' -ErrorAction SilentlyContinue |
                 Select-Object -First 1
            $ok = Select-String -Path $script:log -Pattern 'Registered tunnel connection' -Quiet -ErrorAction SilentlyContinue
            if ($m -and $ok) { return $m.Matches[0].Value }
        }
    }
    return $null
}

Say 'Creating your phone link (up to 45 seconds)...'
$proc = Start-Tunnel 'quic'
$link = Wait-Link $proc
if (-not $link) {
    if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
    Say 'Fast connection blocked on this network, trying the standard one...' 'Yellow'
    $proc = Start-Tunnel 'http2'
    $link = Wait-Link $proc
}
if (-not $link) {
    if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
    Say ''
    Say 'Could not create the link. Last lines of the log (send a screenshot of this):' 'Red'
    if (Test-Path $script:log) { Get-Content $script:log -Tail 15 }
    exit 1
}

try { Set-Clipboard -Value $link } catch {}
Say ''
Say '==================================================================' 'Cyan'
Say '  YOUR PHONE LINK (also copied, paste it in WhatsApp to yourself):' 'Cyan'
Say ''
Say "     $link" 'Green'
Say ''
Say '  Login: owner + your dashboard password (DASHBOARD_PASSWORD in .env)' 'Cyan'
Say '  Keep THIS window and the start.bat window open.' 'Cyan'
Say '  The link changes every time you start phone.bat.' 'Cyan'
Say '==================================================================' 'Cyan'
Say ''
Say 'Running... close this window to stop the phone link.'
Wait-Process -Id $proc.Id
Say 'The tunnel stopped. Run phone.bat again for a new link.' 'Yellow'
