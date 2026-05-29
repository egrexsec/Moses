from pathlib import Path
import zipfile


def create_zip_archive(files, archive_name="moses_stems.zip"):
    archive_path = Path(archive_name)

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in files:
            file_path = Path(file)

            if file_path.exists():
                zipf.write(file_path, arcname=file_path.name)

    return str(archive_path)
