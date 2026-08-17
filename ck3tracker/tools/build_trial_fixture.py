"""Build a small parquet fixture from the validated Mallorca and Kroumerie trials."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


OUTPUT_DIR = Path(__file__).parents[1] / "data" / "trial"
GAME_VERSION = "1.19.0.6 (Scribe)"
START_DATE = 867
SNAPSHOT = "dead_run_screenshot"
PLAYTHROUGH_ID = "trial_dead_run"


def build_tables() -> dict[str, pd.DataFrame]:
    playthroughs = pd.DataFrame(
        [
            {
                "playthrough_id": PLAYTHROUGH_ID,
                "challenge_id": "mallorca_domain_kroumerie_realm",
                "game_version": GAME_VERSION,
                "start_date": START_DATE,
                "lifecycle_state": "dead",
                "snapshot_label": SNAPSHOT,
            }
        ]
    )

    counties = pd.DataFrame(
        [
            {
                "playthrough_id": PLAYTHROUGH_ID,
                "county_id": "c_iviza",
                "duchy_id": "d_mallorca",
                "county_name": "Ibiza",
                "ownership_scope": "domain",
                "county_holder_type": "ruler",
                "control": 100,
                "development": 7,
                "popular_opinion": 34,
                "culture": "Catalan",
                "faith": "Mozarabism",
                "observed_at": SNAPSHOT,
            },
            {
                "playthrough_id": PLAYTHROUGH_ID,
                "county_id": "c_menorca",
                "duchy_id": "d_mallorca",
                "county_name": "Menorca",
                "ownership_scope": "domain",
                "county_holder_type": "ruler",
                "control": 100,
                "development": 4,
                "popular_opinion": 34,
                "culture": "Catalan",
                "faith": "Mozarabism",
                "observed_at": SNAPSHOT,
            },
            {
                "playthrough_id": PLAYTHROUGH_ID,
                "county_id": "c_mallorca",
                "duchy_id": "d_mallorca",
                "county_name": "Mayurqa",
                "ownership_scope": "domain",
                "county_holder_type": "ruler",
                "control": 100,
                "development": 7,
                "popular_opinion": 34,
                "culture": "Catalan",
                "faith": "Mozarabism",
                "observed_at": SNAPSHOT,
            },
            {
                "playthrough_id": PLAYTHROUGH_ID,
                "county_id": "c_annaba",
                "duchy_id": "d_kroumerie",
                "county_name": "Annaba",
                "ownership_scope": "realm",
                "county_holder_type": "vassal",
                "county_holder_name": "Wali Mezwar II",
                "county_holder_role": "Vassal and Champion",
                "control": 97,
                "development": 10,
                "popular_opinion": 20,
                "culture": "Baranis",
                "faith": "Ash'arism",
                "observed_at": SNAPSHOT,
            },
            {
                "playthrough_id": PLAYTHROUGH_ID,
                "county_id": "c_constantine",
                "duchy_id": "d_kroumerie",
                "county_name": "Constantine",
                "ownership_scope": "realm",
                "county_holder_type": "vassal",
                "county_holder_name": "Wali Thabit II",
                "county_holder_role": "Chancellor and Vassal",
                "control": 100,
                "development": 10,
                "popular_opinion": 20,
                "culture": "Baranis",
                "faith": "Ash'arism",
                "observed_at": SNAPSHOT,
            },
        ]
    )

    holdings = pd.DataFrame(
        [
            {
                "playthrough_id": PLAYTHROUGH_ID,
                "barony_id": "b_iviza",
                "county_id": "c_iviza",
                "duchy_id": "d_mallorca",
                "barony_name": "Ibiza",
                "holding_type": "castle",
                "holder_type": "ruler",
                "tax": 0.76,
                "loot": 6,
                "levies": 108,
                "supply_limit": 5337,
                "plague_resistance": 10,
                "garrison": 480,
                "fort_level": 4,
                "regular_building_slots": 2,
                "duchy_building_slots": 0,
                "is_county_capital": True,
                "observed_at": SNAPSHOT,
            },
            {
                "playthrough_id": PLAYTHROUGH_ID,
                "barony_id": "b_menorca",
                "county_id": "c_menorca",
                "duchy_id": "d_mallorca",
                "barony_name": "Menorca",
                "holding_type": "castle",
                "holder_type": "ruler",
                "tax": 0.80,
                "loot": 7,
                "levies": 107,
                "supply_limit": 4550,
                "plague_resistance": 10,
                "garrison": 300,
                "fort_level": 3,
                "regular_building_slots": 2,
                "duchy_building_slots": 0,
                "is_county_capital": True,
                "observed_at": SNAPSHOT,
            },
            {
                "playthrough_id": PLAYTHROUGH_ID,
                "barony_id": "b_alcudia",
                "county_id": "c_mallorca",
                "duchy_id": "d_mallorca",
                "barony_name": "Alcudia",
                "holding_type": "city",
                "holder_type": "ruler",
                "tax": 1.15,
                "loot": 9,
                "levies": 191,
                "supply_limit": 4727,
                "plague_resistance": 0,
                "garrison": None,
                "fort_level": None,
                "regular_building_slots": 2,
                "duchy_building_slots": 0,
                "is_county_capital": False,
                "observed_at": SNAPSHOT,
            },
            {
                "playthrough_id": PLAYTHROUGH_ID,
                "barony_id": "b_palma",
                "county_id": "c_mallorca",
                "duchy_id": "d_mallorca",
                "barony_name": "Palma",
                "holding_type": "castle",
                "holder_type": "ruler",
                "tax": 0.76,
                "loot": 6,
                "levies": 108,
                "supply_limit": 5337,
                "plague_resistance": 10,
                "garrison": 480,
                "fort_level": 4,
                "regular_building_slots": 2,
                "duchy_building_slots": 1,
                "is_county_capital": True,
                "observed_at": SNAPSHOT,
            },
            {
                "playthrough_id": PLAYTHROUGH_ID,
                "barony_id": "b_qasr-al-ifriqi",
                "county_id": "c_constantine",
                "duchy_id": "d_kroumerie",
                "barony_name": "Qasr-al-Ifriqi",
                "holding_type": "city",
                "holder_type": "vassal",
                "tax": 1.66,
                "loot": 20,
                "levies": 78,
                "supply_limit": 4550,
                "plague_resistance": 0,
                "garrison": None,
                "fort_level": None,
                "regular_building_slots": 2,
                "duchy_building_slots": 0,
                "is_county_capital": False,
                "observed_at": SNAPSHOT,
            },
            {
                "playthrough_id": PLAYTHROUGH_ID,
                "barony_id": "b_qalama",
                "county_id": "c_annaba",
                "duchy_id": "d_kroumerie",
                "barony_name": "Qalama",
                "holding_type": "city",
                "holder_type": "vassal",
                "tax": 1.42,
                "loot": 18,
                "levies": 154,
                "supply_limit": 4810,
                "plague_resistance": 5,
                "garrison": None,
                "fort_level": None,
                "regular_building_slots": 2,
                "duchy_building_slots": 0,
                "is_county_capital": False,
                "observed_at": SNAPSHOT,
            },
            {
                "playthrough_id": PLAYTHROUGH_ID,
                "barony_id": "b_constantine",
                "county_id": "c_constantine",
                "duchy_id": "d_kroumerie",
                "barony_name": "Constantine",
                "holding_type": "castle",
                "holder_type": "vassal",
                "tax": 2.10,
                "loot": 23,
                "levies": 183,
                "supply_limit": 4550,
                "plague_resistance": 10,
                "garrison": 400,
                "fort_level": 3,
                "regular_building_slots": 2,
                "duchy_building_slots": 0,
                "is_county_capital": True,
                "observed_at": SNAPSHOT,
            },
            {
                "playthrough_id": PLAYTHROUGH_ID,
                "barony_id": "b_tifash",
                "county_id": "c_constantine",
                "duchy_id": "d_kroumerie",
                "barony_name": "Tifash",
                "holding_type": "temple",
                "holder_type": "vassal",
                "tax": 1.83,
                "loot": 20,
                "levies": 52,
                "supply_limit": 4550,
                "plague_resistance": 16,
                "garrison": None,
                "fort_level": None,
                "regular_building_slots": 1,
                "duchy_building_slots": 0,
                "is_county_capital": False,
                "observed_at": SNAPSHOT,
            },
            {
                "playthrough_id": PLAYTHROUGH_ID,
                "barony_id": "b_tijis",
                "county_id": "c_constantine",
                "duchy_id": "d_kroumerie",
                "barony_name": "Tijis",
                "holding_type": "empty",
                "holder_type": "vassal",
                "tax": None,
                "loot": None,
                "levies": None,
                "supply_limit": 4550,
                "plague_resistance": 10,
                "garrison": None,
                "fort_level": None,
                "regular_building_slots": 0,
                "duchy_building_slots": 0,
                "is_county_capital": False,
                "observed_at": SNAPSHOT,
            },
            {
                "playthrough_id": PLAYTHROUGH_ID,
                "barony_id": "b_taburshiq",
                "county_id": "c_constantine",
                "duchy_id": "d_kroumerie",
                "barony_name": "Taburshiq",
                "holding_type": "empty",
                "holder_type": "vassal",
                "tax": None,
                "loot": None,
                "levies": None,
                "supply_limit": 4550,
                "plague_resistance": 10,
                "garrison": None,
                "fort_level": None,
                "regular_building_slots": 0,
                "duchy_building_slots": 0,
                "is_county_capital": False,
                "observed_at": SNAPSHOT,
            },
        ]
    )

    base_baronies = pd.DataFrame(
        [
            {"barony_id": "b_iviza", "county_id": "c_iviza", "duchy_id": "d_mallorca", "is_county_capital": True, "slot_number": 1, "slot_status": "occupied", "holding_type": "castle", "is_open_barony_slot": False},
            {"barony_id": "b_menorca", "county_id": "c_menorca", "duchy_id": "d_mallorca", "is_county_capital": True, "slot_number": 1, "slot_status": "occupied", "holding_type": "castle", "is_open_barony_slot": False},
            {"barony_id": "b_palma", "county_id": "c_mallorca", "duchy_id": "d_mallorca", "is_county_capital": True, "slot_number": 1, "slot_status": "occupied", "holding_type": "castle", "is_open_barony_slot": False},
            {"barony_id": "b_alcudia", "county_id": "c_mallorca", "duchy_id": "d_mallorca", "is_county_capital": False, "slot_number": 2, "slot_status": "occupied", "holding_type": "city", "is_open_barony_slot": False},
            {"barony_id": "b_annaba", "county_id": "c_annaba", "duchy_id": "d_kroumerie", "is_county_capital": True, "slot_number": 1, "slot_status": "occupied", "holding_type": "castle", "is_open_barony_slot": False},
            {"barony_id": "b_izan", "county_id": "c_annaba", "duchy_id": "d_kroumerie", "is_county_capital": False, "slot_number": 2, "slot_status": "occupied", "holding_type": "unknown", "is_open_barony_slot": False},
            {"barony_id": "b_qalama", "county_id": "c_annaba", "duchy_id": "d_kroumerie", "is_county_capital": False, "slot_number": 3, "slot_status": "occupied", "holding_type": "city", "is_open_barony_slot": False},
            {"barony_id": "b_constantine", "county_id": "c_constantine", "duchy_id": "d_kroumerie", "is_county_capital": True, "slot_number": 1, "slot_status": "occupied", "holding_type": "castle", "is_open_barony_slot": False},
            {"barony_id": "b_qasr-al-ifriqi", "county_id": "c_constantine", "duchy_id": "d_kroumerie", "is_county_capital": False, "slot_number": 2, "slot_status": "occupied", "holding_type": "city", "is_open_barony_slot": False},
            {"barony_id": "b_taburshiq", "county_id": "c_constantine", "duchy_id": "d_kroumerie", "is_county_capital": False, "slot_number": 5, "slot_status": "open", "holding_type": "empty", "is_open_barony_slot": True},
            {"barony_id": "b_tifash", "county_id": "c_constantine", "duchy_id": "d_kroumerie", "is_county_capital": False, "slot_number": 4, "slot_status": "occupied", "holding_type": "temple", "is_open_barony_slot": False},
            {"barony_id": "b_tijis", "county_id": "c_constantine", "duchy_id": "d_kroumerie", "is_county_capital": False, "slot_number": 3, "slot_status": "open", "holding_type": "empty", "is_open_barony_slot": True},
        ]
    )

    title_progress = pd.DataFrame(
        [
            {
                "playthrough_id": PLAYTHROUGH_ID,
                "title_id": "d_mallorca",
                "title_name": "Mallorca",
                "title_status": "held",
                "de_jure_county_count": 3,
                "domain_county_count": 3,
                "realm_county_count": 3,
                "creation_gold_cost": None,
                "observed_at": SNAPSHOT,
            },
            {
                "playthrough_id": PLAYTHROUGH_ID,
                "title_id": "d_kroumerie",
                "title_name": "Kroumerie",
                "title_status": "not_created",
                "de_jure_county_count": 2,
                "domain_county_count": 0,
                "realm_county_count": 2,
                "creation_gold_cost": 250,
                "observed_at": SNAPSHOT,
            },
        ]
    )

    return {
        "playthroughs": playthroughs,
        "county_observations": counties,
        "holding_observations": holdings,
        "base_baronies": base_baronies,
        "title_progress": title_progress,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, table in build_tables().items():
        table.to_parquet(OUTPUT_DIR / f"{name}.parquet", index=False)
        print(f"{name}: {len(table)} rows")
    print(f"output={OUTPUT_DIR}")


if __name__ == "__main__":
    main()
