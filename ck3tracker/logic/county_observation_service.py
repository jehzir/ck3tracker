"""Validate and persist Bronze county observations as one DuckDB transaction."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd

from logic.run_state_store import connect


TRIAL_DIR = Path(__file__).parents[1] / "data" / "trial"


def record_county_observation(
    county_id: str,
    playthrough_id: str,
    control: float,
    development: float,
    popular_opinion: float,
    note: str | None,
    game_date: str,
    source: str,
) -> dict[str, str]:
    """Validate and append one county observation plus its transaction event."""
    counties = pd.read_parquet(TRIAL_DIR / "county_observations.parquet")
    if county_id not in set(counties["county_id"]):
        raise ValueError(f"Unknown county: {county_id}")
    if not game_date or not game_date.strip():
        raise ValueError("game_date is required")
    if not source or not source.strip():
        raise ValueError("source is required")
    for field_name, value in (
        ("control", control),
        ("development", development),
        ("popular_opinion", popular_opinion),
    ):
        if value is None or value < 0:
            raise ValueError(f"{field_name} cannot be negative or empty")
    if control > 100:
        raise ValueError("control cannot exceed 100")

    connection = connect()
    transaction_id = f"{playthrough_id}:county-observation:{uuid4()}"
    observation_id = f"{transaction_id}:observation"
    recorded_at_utc = datetime.now(timezone.utc).isoformat()
    try:
        active = connection.execute(
            "SELECT active_in_editor FROM county_lifecycle WHERE playthrough_id = ? AND county_id = ?",
            [playthrough_id, county_id],
        ).fetchone()
        if active is not None and not bool(active[0]):
            raise ValueError(f"Cannot observe inactive county: {county_id}")

        connection.execute("BEGIN TRANSACTION")
        connection.execute(
            "INSERT INTO transaction_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [transaction_id, playthrough_id, "county_observation_recorded", "county", county_id,
             game_date.strip(), recorded_at_utc, source.strip(), note],
        )
        connection.execute(
            "INSERT INTO county_state_observations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [observation_id, transaction_id, playthrough_id, county_id, control, development,
             popular_opinion, note, game_date.strip(), source.strip()],
        )
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()

    return {"transaction_id": transaction_id, "observation_id": observation_id}