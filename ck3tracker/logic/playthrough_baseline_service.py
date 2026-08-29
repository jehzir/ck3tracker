"""Create a playthrough from a promoted CK3 reference baseline."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from uuid import uuid4

from logic.root_database import connect


PARENT_RANK = {
    "barony": "county",
    "county": "duchy",
    "duchy": "kingdom",
    "kingdom": "empire",
    "empire": None,
}


def create_playthrough_baseline(
    *,
    playthrough_id: str,
    reference_snapshot_id: str,
    baseline_id: str,
    starting_title_id: str,
    ruler_name: str,
    ruler_character_id: str | None = None,
    source: str = "manual",
    database_path: str | Path | None = None,
) -> str:
    """Atomically create a run, its resolved title chain, and journal event."""
    required = {
        "playthrough_id": playthrough_id,
        "reference_snapshot_id": reference_snapshot_id,
        "baseline_id": baseline_id,
        "starting_title_id": starting_title_id,
        "ruler_name": ruler_name,
        "source": source,
    }
    for field_name, value in required.items():
        if not value or not value.strip():
            raise ValueError(f"{field_name} is required")

    connection = connect(database_path)
    try:
        baseline = connection.execute(
            """
            SELECT baseline_date
            FROM app.supported_baselines
            WHERE baseline_id = ? AND reference_snapshot_id = ?
            """,
            [baseline_id, reference_snapshot_id],
        ).fetchone()
        if baseline is None:
            raise ValueError("Baseline is not promoted for the selected reference snapshot")

        title_chain = resolve_title_chain(connection, baseline_id, starting_title_id)
        transaction_id = f"{playthrough_id}:created:{uuid4()}"
        baseline_date: date = baseline[0]

        connection.execute("BEGIN TRANSACTION")
        connection.execute(
            """
            INSERT INTO journal.playthroughs (
                playthrough_id, reference_snapshot_id, baseline_id,
                ruler_character_id, ruler_name, lifecycle_state
            ) VALUES (?, ?, ?, ?, ?, 'active')
            """,
            [
                playthrough_id,
                reference_snapshot_id,
                baseline_id,
                ruler_character_id,
                ruler_name.strip(),
            ],
        )
        connection.execute(
            """
            INSERT INTO journal.playthrough_baselines (
                playthrough_id, transaction_id, baseline_date, starting_title_id,
                starting_empire_id, starting_kingdom_id, starting_duchy_id,
                starting_county_id, starting_barony_id, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                playthrough_id,
                transaction_id,
                baseline_date,
                starting_title_id,
                title_chain.get("empire"),
                title_chain.get("kingdom"),
                title_chain.get("duchy"),
                title_chain.get("county"),
                title_chain.get("barony"),
                source.strip(),
            ],
        )
        connection.execute(
            """
            INSERT INTO journal.transaction_events (
                transaction_id, playthrough_id, event_type, scope,
                target_id, observed_at, source, note
            ) VALUES (?, ?, 'playthrough_created', 'playthrough', ?, ?, ?, ?)
            """,
            [
                transaction_id,
                playthrough_id,
                starting_title_id,
                baseline_date,
                source.strip(),
                f"Baseline {baseline_id}",
            ],
        )
        connection.execute("COMMIT")
        return transaction_id
    except Exception:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        connection.close()


def resolve_title_chain(connection, baseline_id: str, starting_title_id: str) -> dict[str, str]:
    """Resolve and validate a selectable title's complete parent chain."""
    chain: dict[str, str] = {}
    current_id: str | None = starting_title_id

    while current_id is not None:
        row = connection.execute(
            """
            SELECT title_rank, parent_title_id
            FROM reference.titles
            WHERE baseline_id = ? AND title_id = ? AND selectable
            """,
            [baseline_id, current_id],
        ).fetchone()
        if row is None:
            raise ValueError(f"Unknown or non-selectable title: {current_id}")

        title_rank, parent_title_id = row
        if title_rank in chain:
            raise ValueError(f"Invalid title hierarchy at rank: {title_rank}")
        if title_rank not in PARENT_RANK:
            raise ValueError(f"Unsupported title rank: {title_rank}")
        chain[title_rank] = current_id

        expected_parent_rank = PARENT_RANK[title_rank]
        if expected_parent_rank is None:
            if parent_title_id is not None:
                raise ValueError("Empire title cannot have a parent title")
            break
        if parent_title_id is None:
            raise ValueError(f"Incomplete title hierarchy above: {current_id}")

        parent = connection.execute(
            """
            SELECT title_rank
            FROM reference.titles
            WHERE baseline_id = ? AND title_id = ? AND selectable
            """,
            [baseline_id, parent_title_id],
        ).fetchone()
        if parent is None or parent[0] != expected_parent_rank:
            raise ValueError(f"Invalid parent for title: {current_id}")
        current_id = parent_title_id

    return chain