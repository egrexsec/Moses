PRIORITY_LEVELS = {
    "urgent": 0,
    "high": 25,
    "normal": 50,
    "low": 75,
}

DEFAULT_PRIORITY = "normal"


def normalize_priority(priority):
    if not priority:
        return DEFAULT_PRIORITY

    priority = str(priority).lower().strip()

    if priority not in PRIORITY_LEVELS:
        return DEFAULT_PRIORITY

    return priority


def priority_score(priority):
    return PRIORITY_LEVELS[normalize_priority(priority)]
