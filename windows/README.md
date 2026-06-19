# Moses Windows WSL Package

This folder contains the Windows bootstrap and launcher scripts for running Moses through WSL2 instead of Docker Desktop.

## Goal

Give Windows users a simple path:

```text
Install prerequisites
Launch Moses
Open http://localhost:7860
Split stems
Export WAV files
```

## Why WSL?

Moses depends on Python audio/AI tooling such as PyTorch, Torchaudio, Demucs, FFmpeg, and Gradio. WSL2 keeps that stack closer to Linux, where these tools are usually easier to install and run.

## Files

| File | Purpose |
|---|---|
| `install-wsl.ps1` | Installs/checks WSL, prepares Ubuntu, clones Moses, creates a virtual environment, installs FFmpeg and Python dependencies. |
| `launch-moses.ps1` | Starts Moses from Windows through WSL and opens the browser. |
| `Moses.cmd` | Double-click launcher for non-technical users. |

## First-time install

Open PowerShell as Administrator and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
.\windows\install-wsl.ps1
```

The script checks for WSL. If WSL is missing, it runs:

```powershell
wsl --install -d Ubuntu
```

Windows may require a reboot after WSL is installed.

## Launch Moses

After installation, double-click:

```text
windows\Moses.cmd
```

Or run:

```powershell
.\windows\launch-moses.ps1
```

The launcher starts Moses inside Ubuntu and opens:

```text
http://localhost:7860
```

## Default WSL paths

The installer clones Moses into:

```text
~/moses
```

Inside WSL this resolves to something like:

```text
/home/<linux-user>/moses
```

## CPU vs GPU

This WSL package defaults to CPU-safe installation. It does not install NVIDIA CUDA automatically.

For GPU acceleration, install NVIDIA Windows drivers with WSL CUDA support, then install the correct PyTorch CUDA build inside the Moses virtual environment.

## Troubleshooting

### WSL was just installed but Moses did not continue

Reboot Windows, then run the installer again.

### Browser opens but Moses does not load

Wait a few seconds, then refresh:

```text
http://localhost:7860
```

### FFmpeg errors

Run inside WSL:

```bash
sudo apt update
sudo apt install -y ffmpeg
```

### Reinstall Python dependencies

Run inside WSL:

```bash
cd ~/moses
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Packaging note

This is not yet a native Windows app. It is a Windows launcher and installer layer for a WSL-hosted Moses backend.
