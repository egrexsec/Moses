import json
import os
import sqlite3
import tempfile
from pathlib import Path
from threading import Lock


DEFAULT_DB_PATH = "data/moses.db"
_db_lock = Lock()
_resolved_db_path = None
_last_db_error = None


def candidate_db_paths():
    paths = []

    env_path = os.getenv("MOSES_DB_PATH")

    if env_path:
        paths.append(Path(env_path))

    paths.extend([
        Path(DEFAULT_DB_PATH),
        Path("/app/data/moses.db"),
        Path(tempfile.gettempdir()) / "moses.db",
    ])

    unique_paths = []
    seen = set()

    for path in paths:
        resolved = str(path)
        if resolved not in seen:
            unique_paths.append(path)
            seen.add(resolved)

    return unique_paths


def path_is_writable(db_path):
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        test_file = db_path.parent / ".moses_write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return True, ""
    except Exception as exc:
        return False, str(exc)


def resolve_db_path():
    global _resolved_db_path, _last_db_error

    if _resolved_db_path is not None:
        return _resolved_db_path

    errors = []

    for db_path in candidate_db_paths():
        writable, error = path_is_writable(db_path)

        if not writable:
            errors.append(f"{db_path}: {error}")
            continue

        try:
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.execute("CREATE TABLE IF NOT EXISTS db_healthcheck (id INTEGER PRIMARY KEY)")
            conn.commit()
            conn.close()
            _resolved_db_path = db_path
            _last_db_error = None
            return _resolved_db_path
        except Exception as exc:
            errors.append(f"{db_path}: {exc}")

    _last_db_error = " | ".join(errors) if errors else "No database paths were tested."
    raise RuntimeError(f"Unable to find writable SQLite database path. {_last_db_error}")


def get_db_path():
    return resolve_db_path()


def get_db_status():
    try:
        db_path = resolve_db_path()
        return {
            "ok": True,
            "path": str(db_path),
            "error": "",
        }
    except Exception as exc:
        return {
            "ok": False,
            "path": "",
            "error": str(exc),
        }


def get_connection():
    db_path = resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _db_lock:
        conn = get_connection()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                song_name TEXT,
                audio_file TEXT,
                model TEXT,
                mode TEXT,
                export_preset TEXT,
                status TEXT,
                progress INTEGER,
                message TEXT,
                outputs TEXT,
                zip_file TEXT,
                practice_track TEXT,
                vocal_preview TEXT,
                waveform_image TEXT,
                spectrogram_image TEXT,
                band_mix TEXT,
                metadata TEXT,
                error TEXT,
                created_at REAL,
                updated_at REAL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                project_type TEXT,
                workspace_path TEXT,
                created_at REAL,
                updated_at REAL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_items (
                item_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT,
                source_path TEXT,
                song_order INTEGER,
                notes TEXT,
                created_at REAL,
                FOREIGN KEY(project_id) REFERENCES projects(project_id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_jobs (
                project_id TEXT NOT NULL,
                job_id TEXT NOT NULL,
                created_at REAL,
                PRIMARY KEY(project_id, job_id),
                FOREIGN KEY(project_id) REFERENCES projects(project_id),
                FOREIGN KEY(job_id) REFERENCES jobs(job_id)
            )
            """
        )

        conn.commit()
        conn.close()


def upsert_job(job):
    init_db()

    with _db_lock:
        conn = get_connection()
        conn.execute(
            """
            INSERT INTO jobs (
                job_id, song_name, audio_file, model, mode, export_preset,
                status, progress, message, outputs, zip_file, practice_track,
                vocal_preview, waveform_image, spectrogram_image, band_mix,
                metadata, error, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                song_name=excluded.song_name,
                audio_file=excluded.audio_file,
                model=excluded.model,
                mode=excluded.mode,
                export_preset=excluded.export_preset,
                status=excluded.status,
                progress=excluded.progress,
                message=excluded.message,
                outputs=excluded.outputs,
                zip_file=excluded.zip_file,
                practice_track=excluded.practice_track,
                vocal_preview=excluded.vocal_preview,
                waveform_image=excluded.waveform_image,
                spectrogram_image=excluded.spectrogram_image,
                band_mix=excluded.band_mix,
                metadata=excluded.metadata,
                error=excluded.error,
                updated_at=excluded.updated_at
            """,
            (
                job.job_id,
                job.song_name,
                job.audio_file,
                job.model,
                job.mode,
                job.export_preset,
                job.status,
                job.progress,
                job.message,
                json.dumps(job.outputs),
                job.zip_file,
                job.practice_track,
                job.vocal_preview,
                job.waveform_image,
                getattr(job, "spectrogram_image", None),
                job.band_mix,
                job.metadata,
                job.error,
                job.created_at,
                job.updated_at,
            )
        )
        conn.commit()
        conn.close()


def fetch_recent_jobs(limit=20):
    init_db()

    with _db_lock:
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT job_id, song_name, status, progress, message, created_at, updated_at
            FROM jobs
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()
        conn.close()

    return [dict(row) for row in rows]


def update_job_status(job_id, status, message=""):
    init_db()

    with _db_lock:
        conn = get_connection()
        conn.execute(
            """
            UPDATE jobs
            SET status = ?, message = ?
            WHERE job_id = ?
            """,
            (status, message, job_id)
        )
        conn.commit()
        conn.close()
