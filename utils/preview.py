from pathlib import Path


PREVIEW_STEMS = [
    "vocals",
    "bass",
    "drums",
    "other"
]


def get_preview_stems(files):
    previews = {}

    for file in files:
        lower = Path(file).name.lower()

        for stem in PREVIEW_STEMS:
            if stem in lower:
                previews[stem] = file

    return previews
