import json
import sqlite3
from pathlib import Path
from threading import Lock


DB_PATH = Path("moses.db")
_db_lock = Lock()


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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
