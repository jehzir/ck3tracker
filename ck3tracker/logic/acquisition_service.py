"""Create run-state records when a county enters a playthrough."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


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
    TRIAL_STATE_DIR.mkdir(parents=True, exist_ok=True)

    event_path = TRIAL_STATE_DIR / "acquisition_events.parquet"
    state_path = TRIAL_STATE_DIR / "barony_state.parquet"
    existing_events = pd.read_parquet(event_path) if event_path.exists() else pd.DataFrame()
    existing_state = pd.read_parquet(state_path) if state_path.exists() else pd.DataFrame()

    events = pd.concat([existing_events, bundle["acquisition_events"]], ignore_index=True)
    states = pd.concat([existing_state, bundle["barony_state"]], ignore_index=True)
    events = events.drop_duplicates(subset=["event_id"], keep="last")
    states = states.drop_duplicates(subset=["playthrough_id", "barony_id", "acquisition_event_id"], keep="last")
    events.to_parquet(event_path, index=False)
    states.to_parquet(state_path, index=False)

    return {
        "acquisition_events": events,
        "barony_state": states,
    }


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

    event_path = TRIAL_STATE_DIR / "acquisition_events.parquet"
    state_path = TRIAL_STATE_DIR / "barony_state.parquet"
    lifecycle_path = TRIAL_STATE_DIR / "county_lifecycle.parquet"
    existing_events = pd.read_parquet(event_path) if event_path.exists() else pd.DataFrame()
    existing_state = pd.read_parquet(state_path) if state_path.exists() else pd.DataFrame()
    events = pd.concat([existing_events, bundle["acquisition_events"]], ignore_index=True)
    states = pd.concat([existing_state, bundle["barony_state"]], ignore_index=True)
    events = events.drop_duplicates(subset=["event_id"], keep="last")
    states = states.drop_duplicates(subset=["playthrough_id", "barony_id", "acquisition_event_id"], keep="last")
    events.to_parquet(event_path, index=False)
    states.to_parquet(state_path, index=False)

    lifecycle = pd.read_parquet(lifecycle_path) if lifecycle_path.exists() else pd.DataFrame()
    match = (lifecycle["playthrough_id"] == playthrough_id) & (lifecycle["county_id"] == county_id)
    lifecycle.loc[match, "lifecycle_state"] = "active"
    lifecycle.loc[match, "active_in_editor"] = True
    lifecycle.loc[match, "reason"] = "Reclaimed by the player; reclaim event retained in acquisition history."
    lifecycle.to_parquet(lifecycle_path, index=False)
    return {"acquisition_events": events, "barony_state": states, "county_lifecycle": lifecycle}
