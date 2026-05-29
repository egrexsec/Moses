import time
import uuid
from pathlib import Path

from utils.database import get_connection, init_db


WORKSPACE_ROOT = Path("workspaces")
WORKSPACE_ROOT.mkdir(exist_ok=True)


def create_project(name, description="", project_type="rehearsal"):
    init_db()

    project_id = str(uuid.uuid4())
    timestamp = time.time()

    workspace_path = WORKSPACE_ROOT / name.replace(" ", "_")
    workspace_path.mkdir(parents=True, exist_ok=True)

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO projects (
            project_id,
            name,
            description,
            project_type,
            workspace_path,
            created_at,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            project_id,
            name,
            description,
            project_type,
            str(workspace_path),
            timestamp,
            timestamp,
        )
    )

    conn.commit()
    conn.close()

    return {
        "project_id": project_id,
        "name": name,
        "workspace_path": str(workspace_path)
    }


def add_project_item(project_id, title, source_path=None, notes="", song_order=0):
    init_db()

    item_id = str(uuid.uuid4())
    timestamp = time.time()

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO project_items (
            item_id,
            project_id,
            title,
            source_path,
            song_order,
            notes,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item_id,
            project_id,
            title,
            source_path,
            song_order,
            notes,
            timestamp,
        )
    )

    conn.commit()
    conn.close()

    return item_id


def link_job_to_project(project_id, job_id):
    init_db()

    conn = get_connection()

    conn.execute(
        """
        INSERT OR REPLACE INTO project_jobs (
            project_id,
            job_id,
            created_at
        ) VALUES (?, ?, ?)
        """,
        (
            project_id,
            job_id,
            time.time(),
        )
    )

    conn.commit()
    conn.close()


def list_projects():
    init_db()

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT
            project_id,
            name,
            description,
            project_type,
            workspace_path,
            created_at,
            updated_at
        FROM projects
        ORDER BY updated_at DESC
        """
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_project(project_id):
    init_db()

    conn = get_connection()

    project = conn.execute(
        """
        SELECT *
        FROM projects
        WHERE project_id = ?
        """,
        (project_id,)
    ).fetchone()

    items = conn.execute(
        """
        SELECT *
        FROM project_items
        WHERE project_id = ?
        ORDER BY song_order ASC
        """,
        (project_id,)
    ).fetchall()

    jobs = conn.execute(
        """
        SELECT jobs.*
        FROM jobs
        INNER JOIN project_jobs
        ON jobs.job_id = project_jobs.job_id
        WHERE project_jobs.project_id = ?
        ORDER BY jobs.updated_at DESC
        """,
        (project_id,)
    ).fetchall()

    conn.close()

    return {
        "project": dict(project) if project else None,
        "items": [dict(item) for item in items],
        "jobs": [dict(job) for job in jobs],
    }
