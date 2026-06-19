# Moses Windows WSL Installer
# Run from PowerShell as Administrator for first-time WSL setup.

param(
    [string]$Distro = "Ubuntu",
    [string]$RepoUrl = "https://github.com/egrexsec/Moses.git",
    [string]$InstallDir = "~/moses"
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

function Test-WslInstalled {
    return Test-Command "wsl.exe"
}

function Test-DistroInstalled {
    param([string]$Name)
    $distros = & wsl.exe --list --quiet 2>$null
    return ($distros -contains $Name)
}

Write-Step "Checking WSL"

if (-not (Test-WslInstalled)) {
    Write-Host "WSL is not available on this system. Attempting to install WSL with $Distro."
    & wsl.exe --install -d $Distro
    Write-Host "WSL installation was started. Reboot Windows if prompted, then run this installer again."
    exit 0
}

if (-not (Test-DistroInstalled -Name $Distro)) {
    Write-Host "$Distro is not installed. Installing $Distro through WSL."
    & wsl.exe --install -d $Distro
    Write-Host "If Windows asks for a reboot or Ubuntu asks for first-time account setup, complete that and run this installer again."
    exit 0
}

Write-Step "Preparing Ubuntu packages"

$bootstrap = @'
set -e
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip ffmpeg build-essential curl
'@

& wsl.exe -d $Distro -- bash -lc $bootstrap

Write-Step "Cloning or updating Moses"

$setupRepo = @"
set -e
if [ ! -d "$InstallDir/.git" ]; then
  rm -rf "$InstallDir"
  git clone "$RepoUrl" "$InstallDir"
else
  cd "$InstallDir"
  git pull --ff-only
fi
"@

& wsl.exe -d $Distro -- bash -lc $setupRepo

Write-Step "Creating Python virtual environment and installing dependencies"

$setupPython = @"
set -e
cd "$InstallDir"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python utils/bootstrap.py || true
"@

& wsl.exe -d $Distro -- bash -lc $setupPython

Write-Step "Creating local Windows shortcut launcher"

$launcherPath = Join-Path $PSScriptRoot "Moses.cmd"
$launcherContent = @"
@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0launch-moses.ps1"
"@
Set-Content -Path $launcherPath -Value $launcherContent -Encoding ASCII

Write-Host "`nMoses WSL installation complete." -ForegroundColor Green
Write-Host "Launch Moses with: windows\Moses.cmd"
Write-Host "Moses will open at: http://localhost:7860"
