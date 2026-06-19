# Moses Windows WSL Launcher

param(
    [string]$Distro = "Ubuntu",
    [string]$InstallDir = "~/moses",
    [int]$Port = 7860,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Test-Command {
    param([string]$Name)
    $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

if (-not (Test-Command "wsl.exe")) {
    Write-Host "WSL is not installed. Run windows\install-wsl.ps1 first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

$distros = & wsl.exe --list --quiet 2>$null
if (-not ($distros -contains $Distro)) {
    Write-Host "$Distro is not installed. Run windows\install-wsl.ps1 first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Step "Checking Moses installation"

$check = @"
if [ ! -f "$InstallDir/run.py" ]; then
  echo "Moses was not found at $InstallDir"
  exit 2
fi
if [ ! -f "$InstallDir/.venv/bin/activate" ]; then
  echo "Moses virtual environment was not found at $InstallDir/.venv"
  exit 3
fi
"@

& wsl.exe -d $Distro -- bash -lc $check

if ($LASTEXITCODE -ne 0) {
    Write-Host "Moses is not fully installed. Run windows\install-wsl.ps1 first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit $LASTEXITCODE
}

Write-Step "Starting Moses in WSL"

$launch = @"
cd "$InstallDir"
source .venv/bin/activate
python run.py
"@

$process = Start-Process -FilePath "wsl.exe" -ArgumentList @("-d", $Distro, "--", "bash", "-lc", $launch) -PassThru -WindowStyle Normal

Start-Sleep -Seconds 6

$url = "http://localhost:$Port"

if (-not $NoBrowser) {
    Write-Step "Opening $url"
    Start-Process $url
}

Write-Host "`nMoses is starting in a WSL terminal window." -ForegroundColor Green
Write-Host "If the page is not ready yet, wait a few more seconds and refresh: $url"
Write-Host "Close the WSL terminal window to stop Moses."
