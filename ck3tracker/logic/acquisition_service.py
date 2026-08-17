"""Create run-state records when a county enters a playthrough."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from logic.run_state_store import load_table, replace_rows, update_county_lifecycle


TRIAL_BASE_PATH = Path(__file__).parents[1] / "data" / "trial" / "base_baronies.parquet"
TRIAL_STATE_DIR = TRIAL_BASE_PATH.parent


def create_county_acquisition_bundle(
    county_id: str,
    playthrough_id: str,
    ownership_scope: str,
    holder_type: str,
    observed_at: str,
) -> dict[str, pd.DataFrame]:
    """Create an acquisition event and ordered barony state rows for a county."""
    if ownership_scope not in {"domain", "realm"}:
        raise ValueError("ownership_scope must be 'domain' or 'realm'")
    if holder_type not in {"ruler", "vassal"}:
        raise ValueError("holder_type must be 'ruler' or 'vassal'")

    base_baronies = pd.read_parquet(TRIAL_BASE_PATH)
    county_baronies = base_baronies[base_baronies["county_id"] == county_id].copy()
    if county_baronies.empty:
        raise KeyError(f"Unknown base county: {county_id}")

    county_baronies = county_baronies.sort_values("slot_number").reset_index(drop=True)
    duchy_id = county_baronies.iloc[0]["duchy_id"]
    event_id = f"{playthrough_id}:{county_id}:acquired"

    acquisition_events = pd.DataFrame(
        [
            {
                "event_id": event_id,
                "playthrough_id": playthrough_id,
                "event_type": "county_acquired",
                "county_id": county_id,
                "duchy_id": duchy_id,
                "ownership_scope": ownership_scope,
                "holder_type": holder_type,
                "observed_at": observed_at,
                "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        ]
    )

    barony_state = county_baronies[
        [
            "barony_id",
            "county_id",
            "duchy_id",
            "slot_number",
            "slot_status",
            "holding_type",
            "is_county_capital",
            "is_open_barony_slot",
        ]
    ].copy()
    barony_state.insert(0, "playthrough_id", playthrough_id)
    barony_state["ownership_scope"] = ownership_scope
    barony_state["holder_type"] = holder_type
    barony_state["acquisition_event_id"] = event_id
    barony_state["observed_at"] = observed_at

    return {
        "acquisition_events": acquisition_events,
        "barony_state": barony_state,
    }


def record_county_acquisition(
    county_id: str,
    playthrough_id: str,
    ownership_scope: str,
    holder_type: str,
    observed_at: str,
) -> dict[str, pd.DataFrame]:
    """Persist an acquisition bundle to the trial parquet state tables."""
    bundle = create_county_acquisition_bundle(
        county_id=county_id,
        playthrough_id=playthrough_id,
        ownership_scope=ownership_scope,
        holder_type=holder_type,
        observed_at=observed_at,
    )
    replace_rows("acquisition_events", bundle["acquisition_events"], ["event_id"])
    replace_rows("barony_state", bundle["barony_state"], ["playthrough_id", "barony_id", "acquisition_event_id"])
    return {"acquisition_events": load_table("acquisition_events"), "barony_state": load_table("barony_state")}


def record_county_reclamation(
    county_id: str,
    playthrough_id: str,
    ownership_scope: str,
    holder_type: str,
    observed_at: str,
) -> dict[str, pd.DataFrame]:
    """Persist a reclaim event and reactivate the county without rewriting history."""
    bundle = create_county_acquisition_bundle(
        county_id=county_id,
        playthrough_id=playthrough_id,
        ownership_scope=ownership_scope,
        holder_type=holder_type,
        observed_at=observed_at,
    )
    event_id = f"{playthrough_id}:{county_id}:reclaimed"
    bundle["acquisition_events"]["event_id"] = event_id
    bundle["acquisition_events"]["event_type"] = "county_reclaimed"
    bundle["barony_state"]["acquisition_event_id"] = event_id

    replace_rows("acquisition_events", bundle["acquisition_events"], ["event_id"])
    replace_rows("barony_state", bundle["barony_state"], ["playthrough_id", "barony_id", "acquisition_event_id"])
    update_county_lifecycle(
        playthrough_id,
        county_id,
        "active",
        True,
        "Reclaimed by the player; reclaim event retained in acquisition history.",
    )
    return {
        "acquisition_events": load_table("acquisition_events"),
        "barony_state": load_table("barony_state"),
        "county_lifecycle": load_table("county_lifecycle"),
    }


def record_county_loss(
    county_id: str,
    playthrough_id: str,
    observed_at: str,
) -> pd.DataFrame:
    """Persist a county loss event and mark the county inactive without deleting history."""
    base_baronies = pd.read_parquet(TRIAL_BASE_PATH)
    county_baronies = base_baronies[base_baronies["county_id"] == county_id]
    if county_baronies.empty:
        raise KeyError(f"Unknown base county: {county_id}")

    event_id = f"{playthrough_id}:{county_id}:lost"
    event = pd.DataFrame([{
        "event_id": event_id,
        "playthrough_id": playthrough_id,
        "event_type": "county_lost",
        "county_id": county_id,
        "duchy_id": county_baronies.iloc[0]["duchy_id"],
        "ownership_scope": "realm",
        "holder_type": "unknown",
        "observed_at": observed_at,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    }])
    replace_rows("acquisition_events", event, ["event_id"])
    update_county_lifecycle(
        playthrough_id,
        county_id,
        "archived",
        False,
        "Lost by the player; historical observations retained for future recovery.",
    )
    return load_table("county_lifecycle")
