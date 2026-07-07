# Moses

Local AI-powered stem separation workflow for worship practice and Ableton-ready exports.

> **Status: Archived / no longer actively maintained.**
> Moses was originally built as a personal local stem-separation workflow for worship practice and Ableton-ready exports. Since my current workflow now uses worship backing tracks, this project is no longer needed and is preserved as a learning and portfolio reference.

## What Moses does

Moses is a local Gradio-based app for separating songs into stems with Demucs, organizing the outputs, and exporting files that are easier to move into an Ableton workflow.

Confirmed in the repository:
- Gradio UI in `app.py`
- Docker-based local runtime
- CPU and GPU compose variants
- utility modules for exports, runtime checks, and processing helpers

## Why it existed

The project existed to support a local workflow for:
- worship practice preparation
- stem-based rehearsal use
- quick Ableton-ready exports without depending on a cloud service

## Current archive status

This repository is preserved as a completed personal learning and portfolio project.

It is **not** being actively developed or maintained.

## Quick start

If you still want to run it locally, these paths remain documented in the repo:

### Default Docker path

```bash
docker compose up --build
```

Open `http://localhost:7860`.

### CPU-specific path

```bash
docker compose -f docker/docker-compose.cpu.yml up --build
```

### GPU-specific path

```bash
docker compose -f docker/docker-compose.gpu.yml up --build
```

## Copyright disclaimer

Only process audio you have the right to use. Copyright, licensing, and ministry/media distribution rules still apply even when the workflow runs locally.

## License

No `LICENSE` file is currently committed in this repository. Until one is added, the default legal position is **all rights reserved**.
