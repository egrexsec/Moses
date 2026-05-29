# Moses

AI-powered local stem splitter for Gospel music using Demucs.

Moses is designed for a simple first-release workflow:

```text
Upload Song
→ Split Vocals / Instruments / Stems
→ Export Ableton-ready WAV files
→ Import into Ableton Live
```

---

## Quick Start

### 1. Install Requirements

Install:

- Git
- Docker Desktop or Docker Engine
- Docker Compose plugin

GPU users additionally need:

- NVIDIA GPU
- NVIDIA drivers
- NVIDIA Container Toolkit

---

### 2. Clone The Repository

```bash
git clone https://github.com/egrexsec/moses.git
```

Enter the project directory:

```bash
cd moses
```

---

### 3. Detect Recommended Runtime

Moses now includes automatic runtime detection.

Run:

```bash
bash scripts/setup_runtime.sh
```

This validates:

- Docker
- NVIDIA GPU visibility
- Docker GPU runtime support
- CUDA container access

It also recommends:

- GPU runtime
OR
- CPU runtime

based on your system.

Detection logs are written to:

```text
logs/runtime_gpu_detection.json
```

---

### 4. Start Moses

Recommended startup:

```bash
docker compose up --build
```

Then open:

```text
http://localhost:7860
```

---

## Current Status

Moses is packaged for Docker using:

| Runtime | File | Purpose |
|---|---|---|
| Default Runtime | `docker-compose.yml` | Simplified GPU-first startup |
| CPU Runtime | `docker/Containerfile.cpu` | CPU-only runtime |
| GPU Runtime | `docker/Containerfile.gpu` | CUDA GPU runtime |
| CPU Compose | `docker/docker-compose.cpu.yml` | Explicit CPU deployment |
| GPU Compose | `docker/docker-compose.gpu.yml` | Explicit GPU deployment |

The app runs on:

```text
http://localhost:7860
```

---

## Automatic GPU Runtime Detection

Moses now includes:

```text
utils/runtime_gpu_detect.py
```

This automatically checks:

- NVIDIA GPU visibility
- `nvidia-smi`
- Docker GPU runtime support
- CUDA container accessibility
- recommended runtime mode

Run manually:

```bash
python utils/runtime_gpu_detect.py
```

Example output:

```text
Recommended Startup:
docker compose up --build
```

or:

```text
Recommended Startup:
docker compose -f docker/docker-compose.cpu.yml up --build
```

---

## Recommended Upload Files

Best formats:

- WAV, preferably 24-bit
- FLAC
- ALAC

Acceptable:

- High bitrate MP3, preferably 320 kbps

Avoid:

- Low bitrate MP3
- YouTube-ripped audio
- clipped/distorted recordings

For best Gospel stem quality, use the cleanest stereo mix available.

---

## Default Docker Installation

The root `docker-compose.yml` automatically uses the GPU runtime:

```text
docker/Containerfile.gpu
```

Recommended launch:

```bash
docker compose up --build
```

Stop:

```bash
docker compose down
```

---

## CPU-Only Mode

Use this if:

- no NVIDIA GPU exists
- CUDA is unavailable
- debugging CPU-only workflows

Run:

```bash
docker compose -f docker/docker-compose.cpu.yml up --build
```

Stop:

```bash
docker compose -f docker/docker-compose.cpu.yml down
```

---

## Explicit GPU Mode

Use this if you want the dedicated GPU compose file.

### Verify GPU

```bash
nvidia-smi
```

### Start

```bash
docker compose -f docker/docker-compose.gpu.yml up --build
```

### Stop

```bash
docker compose -f docker/docker-compose.gpu.yml down
```

---

## Updating Moses

Pull latest updates:

```bash
git pull
```

Then rebuild:

```bash
docker compose up --build
```

---

## Persistent Data

Docker maps these folders outside the container:

```text
exports/
mixes/
workspaces/
cache/
logs/
models/
data/
```

Your:

- exports
- model cache
- logs
- workspaces
- SQLite database

should survive rebuilds.

---

## Local Python Installation

Use this for development/debugging.

### Create Virtual Environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:

```bash
python -m venv venv
source venv/bin/activate
```

### Install Requirements

```bash
pip install -r requirements.txt
```

### Run Bootstrap Diagnostics

```bash
python utils/bootstrap.py
```

### Start Moses

```bash
python run.py
```

Open:

```text
http://localhost:7860
```

---

## Bootstrap Diagnostics

Moses validates:

- Python version
- FFmpeg
- FFprobe
- Demucs
- CUDA
- NVIDIA drivers
- required folders
- SQLite database
- Demucs model readiness

Diagnostics output:

```text
logs/startup_diagnostics.json
```

---

## Ableton Workflow

Recommended workflow:

1. Upload clean WAV/FLAC/ALAC audio.
2. Split stems.
3. Export Ableton-ready package.
4. Extract ZIP.
5. Drag WAV stems into Ableton Live.

Expected structure:

```text
exports/ableton/SongName/
├── Stems/
│   ├── Vocals.wav
│   ├── Drums.wav
│   ├── Bass.wav
│   ├── Other.wav
│   └── Instrumental.wav
└── Metadata/
    └── session_info.json
```

---

## Notes For First Release

V1 should remain focused on:

- upload song
- split stems
- export clean WAV files
- package for Ableton
- validate against Gospel tracks

Advanced workstation systems should remain secondary until the core workflow is stable.

---

## Disclaimer

For personal learning, rehearsal, and ministry preparation only.

Do not redistribute copyrighted stems without permission.
