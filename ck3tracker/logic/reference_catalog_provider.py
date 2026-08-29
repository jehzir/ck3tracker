"""Read models for promoted CK3 baselines and location selectors."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from logic.root_database import connect


TITLE_RANKS = {"empire", "kingdom", "duchy", "county", "barony"}


def get_supported_baselines(database_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Return reference baselines that are safe to offer for new runs."""
    connection = connect(database_path)
    try:
        cursor = connection.execute(
            """
            SELECT baseline_id, reference_snapshot_id, baseline_date, label, game_version
            FROM app.supported_baselines
            ORDER BY baseline_date, label
            """
        )
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    finally:
        connection.close()


def get_location_options(
    baseline_id: str,
    title_rank: str,
    parent_title_id: str | None = None,
    search: str | None = None,
    database_path: str | Path | None = None,
) -> list[dict[str, str | None]]:
    """Return localized title options for one step of a cascading selector."""
    if title_rank not in TITLE_RANKS:
        raise ValueError(f"Unsupported title rank: {title_rank}")

    clauses = ["baseline_id = ?", "title_rank = ?"]
    parameters: list[str] = [baseline_id, title_rank]
    if parent_title_id is not None:
        clauses.append("parent_title_id = ?")
        parameters.append(parent_title_id)
    if search:
        clauses.append("(display_name ILIKE ? OR title_id ILIKE ?)")
        term = f"%{search.strip()}%"
        parameters.extend([term, term])

    connection = connect(database_path)
    try:
        rows = connection.execute(
            f"""
            SELECT title_id, display_name, parent_title_id
            FROM app.reference_location_options
            WHERE {' AND '.join(clauses)}
            ORDER BY display_name, title_id
            """,
            parameters,
        ).fetchall()
        return [
            {"label": display_name, "value": title_id, "parent_title_id": parent_id}
            for title_id, display_name, parent_id in rows
        ]
    finally:
        connection.close()