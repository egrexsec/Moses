import pandas as pd

from utils.projects import (
    add_project_item,
    create_project,
    get_project,
    list_projects,
)


def create_workspace_project(name, description, project_type):
    if not name:
        return "Project name is required.", ""

    project = create_project(
        name=name,
        description=description or "",
        project_type=project_type or "rehearsal"
    )

    return (
        f"Created project: {project['name']}",
        project["project_id"]
    )


def projects_dataframe():
    projects = list_projects()

    if not projects:
        return pd.DataFrame(
            columns=[
                "Project ID",
                "Name",
                "Type",
                "Description",
                "Workspace"
            ]
        )

    rows = []

    for project in projects:
        rows.append({
            "Project ID": project["project_id"],
            "Name": project["name"],
            "Type": project["project_type"],
            "Description": project["description"],
            "Workspace": project["workspace_path"],
        })

    return pd.DataFrame(rows)


def add_song_to_project(project_id, title, source_path, notes, song_order):
    if not project_id:
        return "Project ID is required."

    if not title:
        return "Song title is required."

    add_project_item(
        project_id=project_id,
        title=title,
        source_path=source_path or "",
        notes=notes or "",
        song_order=int(song_order or 0)
    )

    return f"Added song to project: {title}"


def project_detail_text(project_id):
    if not project_id:
        return "No project selected."

    data = get_project(project_id)
    project = data.get("project")

    if not project:
        return "Project not found."

    lines = [
        f"Project: {project['name']}",
        f"Type: {project['project_type']}",
        f"Workspace: {project['workspace_path']}",
        "",
        "Setlist:"
    ]

    items = data.get("items", [])
    jobs = data.get("jobs", [])

    if not items:
        lines.append("- No songs added yet.")
    else:
        for item in items:
            lines.append(
                f"{item['song_order']}. {item['title']} — {item.get('notes') or ''}"
            )

    lines.extend([
        "",
        "Linked Jobs:"
    ])

    if not jobs:
        lines.append("- No jobs linked yet.")
    else:
        for job in jobs:
            lines.append(
                f"- {job['song_name']} | {job['status']} | {job['progress']}%"
            )

    return "\n".join(lines)
