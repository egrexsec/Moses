from pathlib import Path
import json
import shutil
import zipfile

ABLETON_EXPORT_DIR = Path("exports/ableton")
ABLETON_EXPORT_DIR.mkdir(parents=True, exist_ok=True)

ABLETON_STEM_ORDER = [
    "vocals",
    "drums",
    "bass",
    "other",
    "instrumental",
]


def sanitize_name(name):
    return "_".join(str(name).strip().split())



def create_ableton_project_structure(song_name):
    safe_name = sanitize_name(song_name)

    project_dir = ABLETON_EXPORT_DIR / safe_name
    stems_dir = project_dir / "Stems"
    metadata_dir = project_dir / "Metadata"

    stems_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    return {
        "project_dir": project_dir,
        "stems_dir": stems_dir,
        "metadata_dir": metadata_dir,
    }



def normalize_stem_filename(stem_name):
    stem_name = stem_name.lower().strip()

    aliases = {
        "no_vocals": "instrumental",
        "accompaniment": "instrumental",
        "vox": "vocals",
    }

    return aliases.get(stem_name, stem_name)



def copy_stems_for_ableton(song_name, stem_files):
    structure = create_ableton_project_structure(song_name)

    exported = {}

    for stem_path in stem_files:
        stem_path = Path(stem_path)

        if not stem_path.exists():
            continue

        stem_name = normalize_stem_filename(stem_path.stem)

        output_name = f"{stem_name.title()}.wav"
        output_path = structure["stems_dir"] / output_name

        shutil.copy2(stem_path, output_path)

        exported[stem_name] = str(output_path)

    return {
        "structure": structure,
        "exported": exported,
    }



def write_ableton_metadata(song_name, exported_stems, bpm=None, key=None):
    structure = create_ableton_project_structure(song_name)

    metadata = {
        "song_name": song_name,
        "bpm": bpm,
        "musical_key": key,
        "stems": exported_stems,
        "ableton_ready": True,
        "notes": [
            "All stems are aligned from start position.",
            "Import all WAV files into Ableton on separate tracks.",
            "Warping should remain aligned across stems.",
        ],
    }

    metadata_path = structure["metadata_dir"] / "session_info.json"

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=4)

    return str(metadata_path)



def create_ableton_zip(song_name):
    structure = create_ableton_project_structure(song_name)

    zip_path = structure["project_dir"].with_suffix(".zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in structure["project_dir"].rglob("*"):
            if file_path.is_file():
                zipf.write(
                    file_path,
                    arcname=file_path.relative_to(structure["project_dir"])
                )

    return str(zip_path)



def package_ableton_export(song_name, stem_files, bpm=None, key=None):
    export_result = copy_stems_for_ableton(song_name, stem_files)

    metadata_path = write_ableton_metadata(
        song_name,
        export_result["exported"],
        bpm=bpm,
        key=key,
    )

    zip_path = create_ableton_zip(song_name)

    return {
        "project_directory": str(export_result["structure"]["project_dir"]),
        "metadata_file": metadata_path,
        "zip_file": zip_path,
        "stems": export_result["exported"],
    }
