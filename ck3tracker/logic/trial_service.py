"""Read-only summaries for the validated parquet trial fixture."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


TRIAL_DIR = Path(__file__).parents[1] / "data" / "trial"


def load_trial_tables() -> dict[str, pd.DataFrame]:
    """Load the trial parquet tables without mutating them."""
    table_names = (
        "playthroughs",
        "county_observations",
        "holding_observations",
        "base_baronies",
        "title_progress",
        "county_lifecycle",
    )
    return {
        name: pd.read_parquet(TRIAL_DIR / f"{name}.parquet")
        for name in table_names
    }


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
