from pathlib import Path


STEM_TYPES = [
    "vocals",
    "bass",
    "drums",
    "other",
    "guitar",
    "piano"
]


def categorize_stems(files):
    categorized = {}

    for stem_type in STEM_TYPES:
        categorized[stem_type] = []

    for file in files:
        lower = Path(file).name.lower()

        matched = False

        for stem_type in STEM_TYPES:
            if stem_type in lower:
                categorized[stem_type].append(file)
                matched = True
                break

        if not matched:
            categorized.setdefault("misc", []).append(file)

    return categorized
