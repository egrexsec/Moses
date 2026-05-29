from pathlib import Path
import shutil


EXPORT_ROOT = Path("exports")


def organize_song_outputs(song_name, stem_files):
    song_folder = EXPORT_ROOT / song_name
    song_folder.mkdir(parents=True, exist_ok=True)

    organized_files = []

    for stem_file in stem_files:
        source = Path(stem_file)
        destination = song_folder / source.name

        shutil.copy2(source, destination)

        organized_files.append(str(destination))

    return organized_files
