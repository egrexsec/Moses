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

### 3. Start Moses

CPU mode:

```bash
docker compose -f docker/docker-compose.cpu.yml up --build
```

GPU mode:

```bash
docker compose -f docker/docker-compose.gpu.yml up --build
```

Then open:

```text
http://localhost:7860
```

---

## Current Status

Moses is packaged for Docker using container files inside the `docker/` directory.

Available runtimes:

| Runtime | File | Purpose |
|---|---|---|
| CPU | `docker/Containerfile.cpu` | Runs without GPU acceleration |
| GPU | `docker/Containerfile.gpu` | Uses PyTorch CUDA runtime for NVIDIA GPU acceleration |
| CPU Compose | `docker/docker-compose.cpu.yml` | CPU deployment stack |
| GPU Compose | `docker/docker-compose.gpu.yml` | GPU deployment stack |

The app runs on port:

```text
7860
```

Open after launch:

```text
http://localhost:7860
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

## Docker Installation — CPU Mode

Use this if you do not have an NVIDIA GPU or just want the simplest test run.

### Requirements

- Docker
- Docker Compose plugin

### Run

From the repository root:

```bash
docker compose -f docker/docker-compose.cpu.yml up --build
```

Then open:

```text
http://localhost:7860
```

### Stop

```bash
docker compose -f docker/docker-compose.cpu.yml down
```

---

## Docker Installation — GPU Mode

Use this if you have an NVIDIA GPU. This is strongly recommended for large Gospel tracks, choir-heavy songs, and batch processing.

### Requirements

- Docker
- Docker Compose plugin
- NVIDIA GPU
- NVIDIA drivers installed on the host
- NVIDIA Container Toolkit installed on the host

### Verify GPU on Host

```bash
nvidia-smi
```

If this fails, fix NVIDIA drivers before running Moses in GPU mode.

### Run

From the repository root:

```bash
docker compose -f docker/docker-compose.gpu.yml up --build
```

Then open:

```text
http://localhost:7860
```

### Stop

```bash
docker compose -f docker/docker-compose.gpu.yml down
```

---

## Updating Moses

Pull the latest changes:

```bash
git pull
```

Then rebuild:

```bash
docker compose -f docker/docker-compose.gpu.yml up --build
```

CPU users can replace the GPU compose file with:

```text
docker/docker-compose.cpu.yml
```

---

## Persistent Data

Docker Compose maps these folders from your local repo into the container:

```text
exports/
mixes/
workspaces/
cache/
logs/
```

That means your exports, workspace data, cache, and logs should survive container rebuilds.

---

## Local Python Installation

Use this for development or debugging.

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

Moses includes a bootstrap system that checks:

- Python version
- FFmpeg
- FFprobe
- Demucs
- PyTorch / CUDA
- NVIDIA driver visibility
- required folders
- SQLite database
- Demucs model readiness

Diagnostics are written to:

```text
logs/startup_diagnostics.json
```

---

## Ableton Workflow

Recommended workflow:

1. Upload a clean WAV/FLAC/ALAC song.
2. Split the song into stems.
3. Export using the Ableton-ready packaging flow.
4. Extract the ZIP.
5. Drag the WAV files into Ableton Live as separate tracks.

Expected export structure:

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

## Notes for First Release

The first release should stay focused on:

- upload song
- split stems
- export clean WAV files
- package for Ableton
- validate against Gospel tracks

Advanced workstation features such as timeline playback, distributed workers, and multi-user access should remain secondary until the core workflow is stable.

---

## Disclaimer

For personal learning, rehearsal, and ministry preparation only. Do not redistribute copyrighted stems without permission.
