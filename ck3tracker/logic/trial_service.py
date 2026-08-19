"""Read-only summaries for the validated parquet trial fixture."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from logic.run_state_store import load_table


TRIAL_DIR = Path(__file__).parents[1] / "data" / "trial"


def load_trial_tables() -> dict[str, pd.DataFrame]:
    """Load the trial parquet tables without mutating them."""
    parquet_tables = (
        "playthroughs",
        "county_observations",
        "holding_observations",
        "base_baronies",
        "title_progress",
    )
    tables = {
        name: pd.read_parquet(TRIAL_DIR / f"{name}.parquet")
        for name in parquet_tables
    }
    tables.update({name: load_table(name) for name in (
        "county_lifecycle",
        "acquisition_events",
        "barony_state",
        "transaction_events",
        "barony_observations",
    )})
    tables["holding_observations"] = _with_latest_barony_observations(tables)
    return tables


def _with_latest_barony_observations(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Project the latest DuckDB barony observations over immutable Parquet values."""
    holdings = tables["holding_observations"].copy()
    observations = tables["barony_observations"]
    if observations.empty:
        return holdings
    holding_records = holdings.to_dict("records")
    holding_columns = list(holdings.columns)
    latest = observations.sort_values("observed_at").drop_duplicates("barony_id", keep="last")
    base = tables["base_baronies"].set_index("barony_id")
    for observation in latest.to_dict("records"):
        matches = [index for index, row in enumerate(holding_records) if row["barony_id"] == observation["barony_id"]]
        if matches:
            row = holding_records[matches[-1]]
            for field in ("holding_type", "holder_type", "tax", "levies", "plague_resistance", "observed_at"):
                if observation.get(field) is not None:
                    row[field] = observation[field]
            continue
        base_row = base.loc[observation["barony_id"]].to_dict()
        row = {column: None for column in holdings.columns}
        row.update({
            "playthrough_id": observation["playthrough_id"],
            "barony_id": observation["barony_id"],
            "county_id": observation["county_id"],
            "duchy_id": observation["duchy_id"],
            "barony_name": observation["barony_name"],
            "holding_type": observation["holding_type"],
            "holder_type": observation["holder_type"],
            "tax": observation["tax"],
            "levies": observation["levies"],
            "plague_resistance": observation["plague_resistance"],
            "is_county_capital": base_row["is_county_capital"],
            "observed_at": observation["observed_at"],
        })
        holding_records.append(row)
    return pd.DataFrame(holding_records, columns=holding_columns)


def get_active_trial_counties(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return counties currently active in the trial editor without deleting history."""
    counties = tables["county_observations"]
    lifecycle = tables.get("county_lifecycle")
    if lifecycle is None:
        return counties
    archived_ids = lifecycle[~lifecycle["active_in_editor"]]["county_id"]
    return counties[~counties["county_id"].isin(archived_ids)]


def get_trial_summary(playthrough_id: str = "trial_dead_run") -> dict:
    """Return Domain, Realm, holding, and title summaries for one trial run."""
    tables = load_trial_tables()
    playthroughs = tables["playthroughs"]
    counties = tables["county_observations"]
    holdings = tables["holding_observations"]
    base_baronies = tables["base_baronies"]
    titles = tables["title_progress"]

    run = playthroughs[playthroughs["playthrough_id"] == playthrough_id]
    if run.empty:
        raise KeyError(f"Unknown trial playthrough: {playthrough_id}")

    run_counties = counties[counties["playthrough_id"] == playthrough_id]
    run_holdings = holdings[holdings["playthrough_id"] == playthrough_id]
    occupied_holdings = run_holdings[run_holdings["holding_type"] != "empty"]
    run_titles = titles[titles["playthrough_id"] == playthrough_id]

    title_summaries = []
    for title in run_titles.to_dict("records"):
        title_holdings = occupied_holdings[occupied_holdings["duchy_id"] == title["title_id"]]
        title_counties = run_counties[run_counties["duchy_id"] == title["title_id"]]
        title_base_baronies = base_baronies[base_baronies["duchy_id"] == title["title_id"]]
        title_summaries.append(
            {
                "title_id": title["title_id"],
                "title_name": title["title_name"],
                "title_status": title["title_status"],
                "de_jure_county_count": int(title["de_jure_county_count"]),
                "domain_county_count": int(title["domain_county_count"]),
                "realm_county_count": int(title["realm_county_count"]),
                "domain_barony_count": int(
                    (title_holdings["holder_type"] == "ruler").sum()
                ),
                "realm_barony_count": int(len(title_holdings)),
                "base_barony_count": int(len(title_base_baronies)),
                "observed_county_count": int(len(title_counties)),
                "creation_gold_cost": title["creation_gold_cost"],
            }
        )

    return {
        "playthrough": run.iloc[0].to_dict(),
        "titles": title_summaries,
        "county_count": int(len(run_counties)),
        "domain_county_count": int(
            (run_counties["ownership_scope"] == "domain").sum()
        ),
        "realm_county_count": int(len(run_counties)),
        "domain_barony_count": int(
            (run_holdings["holder_type"] == "ruler").sum()
        ),
        "realm_barony_count": int(len(occupied_holdings)),
        "base_barony_count": int(len(base_baronies[base_baronies["duchy_id"] == "d_kroumerie"])),
        "base_baronies": base_baronies.to_dict("records"),
        "county_observations": run_counties.to_dict("records"),
        "holding_observations": run_holdings.to_dict("records"),
    }


def validate_trial_summary(summary: dict) -> bool:
    """Return whether the Mallorca/Kroumerie proof assertions still hold."""
    if summary["playthrough"]["game_version"] != "1.19.0.6 (Scribe)":
        return False
    if summary["domain_county_count"] != 3 or summary["realm_county_count"] != 5:
        return False
    if summary["domain_barony_count"] != 4 or summary["realm_barony_count"] != 8:
        return False

    titles = {title["title_id"]: title for title in summary["titles"]}
    mallorca = titles.get("d_mallorca")
    kroumerie = titles.get("d_kroumerie")
    if mallorca is None or kroumerie is None:
        return False
    if mallorca["domain_county_count"] != 3 or mallorca["domain_barony_count"] != 4:
        return False
    if kroumerie["domain_county_count"] != 0 or kroumerie["realm_county_count"] != 2:
        return False
    if kroumerie["realm_barony_count"] != 4:
        return False
    if kroumerie["title_status"] != "not_created":
        return False

    palma = next(
        (holding for holding in summary["holding_observations"] if holding["barony_id"] == "b_palma"),
        None,
    )
    return palma is not None and palma["duchy_building_slots"] == 1
