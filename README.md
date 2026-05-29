# Moses

AI-powered local stem splitter for Gospel music using Demucs.

## Vision

Moses is a private local-first application designed to:

- Split Gospel songs into stems
- Create rehearsal/practice tracks
- Isolate bass, vocals, drums, and instruments
- Help musicians learn parts by ear
- Support choir and worship team preparation

## Planned Stack

- Python
- Demucs
- Gradio GUI
- FFmpeg
- PyTorch

## Planned Features

- Drag-and-drop song upload
- 2-stem and 4-stem separation
- Bass practice mode
- Choir rehearsal mode
- GPU acceleration (CUDA)
- Batch song processing
- Export presets
- Desktop packaging

## Initial Setup

```bash
python -m venv venv
venv\\Scripts\\activate
pip install demucs gradio
```

## Roadmap

### Phase 1
- Basic local GUI
- Single-song splitting
- Export WAV stems

### Phase 2
- Batch processing
- GPU optimization
- Preset workflow modes

### Phase 3
- Desktop application builds
- DAW integration helpers
- AI-assisted stem cleanup

## Disclaimer

For personal learning, rehearsal, and ministry preparation only.
Do not redistribute copyrighted stems without permission.
