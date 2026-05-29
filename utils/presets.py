EXPORT_PRESETS = {
    "Band Rehearsal": [
        "drums",
        "bass",
        "other"
    ],
    "Choir Pack": [
        "vocals",
        "other"
    ],
    "Bass Shed": [
        "bass"
    ],
    "Drummer Practice": [
        "drums"
    ],
    "MD Pack": [
        "vocals",
        "bass",
        "drums",
        "other"
    ]
}


def filter_stems_by_preset(categorized_stems, preset_name):
    allowed = EXPORT_PRESETS.get(preset_name, [])

    filtered = []

    for stem_type in allowed:
        filtered.extend(categorized_stems.get(stem_type, []))

    return filtered
