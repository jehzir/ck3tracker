"""Validate and persist Bronze barony observations as one DuckDB transaction."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd

from logic.run_state_store import connect


TRIAL_DIR = Path(__file__).parents[1] / "data" / "trial"


def record_barony_observation(
    barony_id: str,
    playthrough_id: str,
    holder_type: str,
    tax: float | None,
    levies: float | None,
    plague_resistance: float | None,
    note: str | None,
    game_date: str,
    source: str,
) -> dict[str, str]:
    """Validate and append one barony observation plus its transaction event."""
    base = pd.read_parquet(TRIAL_DIR / "base_baronies.parquet")
    target_rows = base[base["barony_id"] == barony_id]
    if target_rows.empty:
        raise ValueError(f"Unknown barony: {barony_id}")
    target = target_rows.iloc[0].to_dict()
    if bool(target["is_open_barony_slot"]):
        raise ValueError(f"Cannot observe open barony slot: {barony_id}")
    if holder_type not in {"ruler", "vassal"}:
        raise ValueError("holder_type must be 'ruler' or 'vassal'")
    if not game_date or not game_date.strip():
        raise ValueError("game_date is required")
    if not source or not source.strip():
        raise ValueError("source is required")

    for field_name, value in (("tax", tax), ("levies", levies), ("plague_resistance", plague_resistance)):
        if value is not None and value < 0:
            raise ValueError(f"{field_name} cannot be negative")

    connection = connect()
    transaction_id = f"{playthrough_id}:barony-observation:{uuid4()}"
    observation_id = f"{transaction_id}:observation"
    recorded_at_utc = datetime.now(timezone.utc).isoformat()
    try:
        active = connection.execute(
            "SELECT active_in_editor FROM county_lifecycle WHERE playthrough_id = ? AND county_id = ?",
            [playthrough_id, target["county_id"]],
        ).fetchone()
        if active is not None and not bool(active[0]):
            raise ValueError(f"Cannot observe inactive county: {target['county_id']}")

        connection.execute("BEGIN TRANSACTION")
        connection.execute(
            """
            INSERT INTO transaction_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                transaction_id,
                playthrough_id,
                "barony_observation_recorded",
                "barony",
                barony_id,
                game_date.strip(),
                recorded_at_utc,
                source.strip(),
                note,
            ],
        )
        connection.execute(
            """
            INSERT INTO barony_observations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                observation_id,
                transaction_id,
                playthrough_id,
                barony_id,
                target["county_id"],
                target["duchy_id"],
                target.get("barony_name", barony_id),
                target["holding_type"],
                holder_type,
                tax,
                levies,
                plague_resistance,
                note,
                game_date.strip(),
                source.strip(),
            ],
        )
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()

    return {"transaction_id": transaction_id, "observation_id": observation_id}
