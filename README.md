# Moses

Local AI-powered stem separation workflow for rehearsal, ministry preparation, and Ableton-ready exports.

## Status note

**Recommended status: maintenance mode.**

The repository has a real local workflow and multiple utility modules, but it is currently best treated as a specialized personal tool rather than an actively expanding platform. The core value is clear: upload a track, run Demucs locally, export usable stems, and move those stems into rehearsal or production work.

## Project summary

Moses is a Gradio-based local application for splitting songs into stems with Demucs, organizing outputs, and packaging files for Ableton-oriented use. The codebase includes Docker paths for CPU and GPU usage plus utility modules for runtime checks, job tracking, exports, and playback helpers.

## Who it is for

- musicians preparing practice tracks
- church/ministry teams building rehearsal assets
- producers who want quick local stem separation
- users who want Ableton-friendly exports without a cloud dependency

## Problem it solves

When you need stems for rehearsal or arrangement work, many tools are cloud-first, subscription-based, or awkward to move into a DAW workflow. Moses focuses on a local path: separate, review, export, and bring the results into Ableton.

## Current status

What is confirmed in the repository today:
- a Gradio UI (`app.py`)
- background job handling for Demucs processing
- CPU/GPU runtime detection helpers
- Docker files for CPU and GPU paths
- Ableton export packaging under `utils/ableton_export.py`
- multiple support utilities for playback, queueing, diagnostics, and workspace behavior

What is **not** confirmed in this documentation refresh:
- a freshly re-validated end-to-end runtime on this machine
- current screenshots captured from a successful local run
- automated tests

## Features

- local Demucs-based stem separation workflow
- Gradio UI for upload, queueing, and result review
- CPU/GPU runtime detection helpers
- Docker-first startup path
- Ableton-ready export packaging with stem normalization and metadata output
- local-only workflow suitable for rehearsal preparation

## Screenshots / demo

Screenshots are intentionally omitted for now. The repository was inspected and its Docker/runtime paths were reviewed, but the full end-to-end UI workflow was not re-validated during this docs pass.

## Tech stack

- Python
- Gradio
- Demucs
- Docker / Docker Compose
- FFmpeg

## Quick start

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

## Usage

1. start the app locally
2. upload a song file
3. choose the model/profile that fits the quality/speed tradeoff
4. run separation
5. review the resulting stems
6. export the Ableton-ready output package
7. import the stems into Ableton on separate tracks

## Ableton workflow

Confirmed from the repo’s export helper:
- stems are copied into a per-song export structure
- normalized stem naming is applied
- metadata is written to `session_info.json`
- the export can be packaged as a zip for import/handoff

## Project structure

```text
app.py                    Main Gradio application
run.py                    Local launcher
utils/                    Processing, export, diagnostics, playback, and queue helpers
docker/                   CPU/GPU container definitions and compose variants
scripts/                  Runtime/setup helpers
docker-compose.yml        Default compose entrypoint
```

## Testing

There is no automated test suite in the repository today.

Practical validation for this repo should include:
- `docker compose config`
- Python syntax/compile checks
- a real sample-track processing test on the target runtime

## Deployment

Moses is intended for **local/self-hosted use**, not public internet deployment.

## Roadmap

See [ROADMAP.md](ROADMAP.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md).

## License

No `LICENSE` file is currently committed in this repository. Until one is added, the default legal position is **all rights reserved**.

## Disclaimer

Only process audio you have the right to use. Copyright, licensing, and ministry/media distribution rules still apply even when the workflow runs locally.

## Recommended alternatives

If you need a more polished or actively maintained stem-separation ecosystem, consider comparing Moses against current Demucs wrappers or other dedicated local stem tools before investing in new feature work here.
