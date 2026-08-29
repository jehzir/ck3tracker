"""Build a confirmed-before-write playthrough proposal from a CK3 save."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re

from logic.ck3_save_reader import read_save_baseline_identity, read_save_metadata
from logic.playthrough_baseline_service import (
    create_playthrough_baseline,
    resolve_title_chain,
)
from logic.root_database import connect


@dataclass(frozen=True)
class SaveBaselineProposal:
    """Read-only preview of a save matched to a promoted reference baseline."""

    source_path: Path
    reference_snapshot_id: str
    baseline_id: str
    baseline_date: date
    save_game_date: date
    game_version: str
    ruler_name: str
    ruler_character_id: str
    primary_title_id: str
    realm_capital_title_id: str
    domain_title_ids: tuple[str, ...]
    starting_empire_id: str | None
    starting_kingdom_id: str | None
    starting_duchy_id: str | None
    starting_county_id: str
    starting_barony_id: str


def propose_save_baseline(
    save_path: str | Path,
    *,
    reference_snapshot_id: str | None = None,
    baseline_id: str | None = None,
    database_path: str | Path | None = None,
) -> SaveBaselineProposal:
    """Validate a selected save against references without writing journal rows."""
    metadata = read_save_metadata(save_path)
    identity = read_save_baseline_identity(save_path)
    save_game_date = _parse_ck3_date(metadata.game_date)

    connection = connect(database_path)
    try:
        clauses = ["game_version = ?", "baseline_date <= ?"]
        parameters: list[object] = [metadata.game_version, save_game_date]
        if reference_snapshot_id is not None:
            clauses.append("reference_snapshot_id = ?")
            parameters.append(reference_snapshot_id)
        if baseline_id is not None:
            clauses.append("baseline_id = ?")
            parameters.append(baseline_id)

        candidates = connection.execute(
            f"""
            SELECT reference_snapshot_id, baseline_id, baseline_date
            FROM app.supported_baselines
            WHERE {' AND '.join(clauses)}
            ORDER BY baseline_date DESC, reference_snapshot_id, baseline_id
            """,
            parameters,
        ).fetchall()
        if not candidates:
            raise ValueError(
                "No promoted reference baseline matches the save version and date"
            )
        newest_date = candidates[0][2]
        newest_candidates = [row for row in candidates if row[2] == newest_date]
        if len(newest_candidates) != 1:
            raise ValueError(
                "Multiple promoted baselines match; select a reference snapshot explicitly"
            )
        matched_snapshot_id, matched_baseline_id, matched_baseline_date = (
            newest_candidates[0]
        )

        title_ids = set(identity.domain_title_ids)
        title_ids.add(identity.primary_title_id)
        title_ids.add(identity.realm_capital_title_id)
        for title_id in sorted(title_ids):
            row = connection.execute(
                """
                SELECT 1
                FROM reference.titles
                WHERE baseline_id = ? AND title_id = ?
                """,
                [matched_baseline_id, title_id],
            ).fetchone()
            if row is None:
                raise ValueError(
                    f"Save title is absent from the matched reference baseline: {title_id}"
                )

        chain = resolve_title_chain(
            connection,
            matched_baseline_id,
            identity.realm_capital_title_id,
        )
        county_id = chain.get("county")
        barony_id = chain.get("barony")
        if county_id is None or barony_id is None:
            raise ValueError("Save realm capital does not resolve to a county and barony")

        return SaveBaselineProposal(
            source_path=identity.source_path,
            reference_snapshot_id=matched_snapshot_id,
            baseline_id=matched_baseline_id,
            baseline_date=matched_baseline_date,
            save_game_date=save_game_date,
            game_version=metadata.game_version,
            ruler_name=metadata.player_name,
            ruler_character_id=str(identity.player_character_id),
            primary_title_id=identity.primary_title_id,
            realm_capital_title_id=identity.realm_capital_title_id,
            domain_title_ids=identity.domain_title_ids,
            starting_empire_id=chain.get("empire"),
            starting_kingdom_id=chain.get("kingdom"),
            starting_duchy_id=chain.get("duchy"),
            starting_county_id=county_id,
            starting_barony_id=barony_id,
        )
    finally:
        connection.close()


def confirm_save_baseline(
    proposal: SaveBaselineProposal,
    *,
    playthrough_id: str,
    database_path: str | Path | None = None,
) -> str:
    """Create a playthrough only after the proposal has been reviewed."""
    return create_playthrough_baseline(
        playthrough_id=playthrough_id,
        reference_snapshot_id=proposal.reference_snapshot_id,
        baseline_id=proposal.baseline_id,
        starting_title_id=proposal.starting_barony_id,
        ruler_name=proposal.ruler_name,
        ruler_character_id=proposal.ruler_character_id,
        source="confirmed_ck3_save",
        database_path=database_path,
    )


def _parse_ck3_date(value: str) -> date:
    match = re.fullmatch(r"(\d{1,4})\.(\d{1,2})\.(\d{1,2})", value)
    if match is None:
        raise ValueError(f"Invalid CK3 game date: {value}")
    year, month, day = (int(part) for part in match.groups())
    return date(year, month, day)