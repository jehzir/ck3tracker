"""Record reviewed runtime holder evidence without rewriting installed history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from pathlib import Path

from logic.ck3_save_reader import read_save_baseline_identity, read_save_metadata
from logic.root_database import connect


@dataclass(frozen=True)
class HolderAdjudicationResult:
    baseline_id: str
    title_id: str
    declared_holder_character_id: str
    adjudicated_holder_character_id: str
    save_player_character_id: int
    evidence_sha256: str


def record_immediate_save_holder_adjudication(
    *,
    save_path: str | Path,
    baseline_id: str,
    title_id: str,
    resolved_character_id: str,
    review_note: str,
    database_path: str | Path | None = None,
) -> HolderAdjudicationResult:
    """Validate and record one player-owned title observed at the baseline instant."""
    path = Path(save_path).resolve()
    metadata = read_save_metadata(path)
    identity = read_save_baseline_identity(path)
    digest = sha256(path.read_bytes()).hexdigest()
    observed_date = _ck3_date(metadata.game_date)

    connection = connect(database_path)
    try:
        baseline = connection.execute(
            """
            SELECT baseline.baseline_date, snapshot.game_version,
                   baseline.support_status, snapshot.review_status
            FROM reference.baselines baseline
            JOIN source.reference_snapshots snapshot USING (reference_snapshot_id)
            WHERE baseline.baseline_id = ?
            """,
            [baseline_id],
        ).fetchone()
        if baseline is None:
            raise ValueError(f"Unknown baseline: {baseline_id}")
        if baseline[2] == "promoted" or baseline[3] == "promoted":
            raise ValueError("Promoted reference evidence cannot be adjudicated")
        if observed_date != baseline[0]:
            raise ValueError(
                f"Save date {observed_date} does not match baseline date {baseline[0]}"
            )
        if metadata.game_version != baseline[1]:
            raise ValueError(
                f"Save version {metadata.game_version} does not match {baseline[1]}"
            )
        if title_id not in identity.domain_title_ids:
            raise ValueError(f"Observed title is not in the player's saved domain: {title_id}")

        title = connection.execute(
            """
            SELECT title.title_rank, state.holder_character_id
            FROM reference.titles title
            JOIN reference.title_baseline_states state USING (baseline_id, title_id)
            WHERE title.baseline_id = ? AND title.title_id = ?
            """,
            [baseline_id, title_id],
        ).fetchone()
        if title is None or title[1] is None:
            raise ValueError(f"Title lacks an installed holder declaration: {title_id}")
        declared_holder_id = str(title[1])

        primary_holder = connection.execute(
            """
            SELECT holder_character_id FROM reference.title_baseline_states
            WHERE baseline_id = ? AND title_id = ?
            """,
            [baseline_id, identity.primary_title_id],
        ).fetchone()
        if primary_holder is None or primary_holder[0] != resolved_character_id:
            raise ValueError(
                "Resolved character does not match the installed holder of the saved primary title"
            )

        character = connection.execute(
            """
            SELECT state.lifecycle_status,
                   count(block.source_block_order) FILTER (
                       WHERE block.duplicate_classification = 'conflicting_at_baseline'
                   )
            FROM reference.character_baseline_states state
            JOIN reference.baselines baseline USING (baseline_id)
            LEFT JOIN source.character_history_blocks block
              ON block.reference_snapshot_id = baseline.reference_snapshot_id
             AND block.character_id = state.character_id
            WHERE state.baseline_id = ? AND state.character_id = ?
            GROUP BY state.lifecycle_status
            """,
            [baseline_id, resolved_character_id],
        ).fetchone()
        if character is None or character[0] != "alive_at_baseline" or character[1] != 0:
            raise ValueError("Resolved character is not unique and alive at the baseline")

        validation_note = (
            f"{review_note}; installed declaration retained as {declared_holder_id}"
        )
        connection.execute("BEGIN TRANSACTION")
        connection.execute(
            """
            INSERT OR REPLACE INTO reference.title_holder_adjudications
            (baseline_id, title_id, declared_holder_character_id,
             adjudicated_holder_character_id, evidence_kind, evidence_path,
             evidence_sha256, evidence_game_version, evidence_date,
             save_player_character_id, review_status, review_note)
            VALUES (?, ?, ?, ?, 'immediate_save', ?, ?, ?, ?, ?, 'reviewed', ?)
            """,
            [
                baseline_id,
                title_id,
                declared_holder_id,
                resolved_character_id,
                str(path),
                digest,
                metadata.game_version,
                observed_date,
                identity.player_character_id,
                review_note,
            ],
        )
        connection.execute(
            """
            INSERT OR REPLACE INTO reference.title_holder_validations
            (baseline_id, title_id, holder_character_id, declaration_status,
             uniqueness_status, lifecycle_status, validation_status, validation_note)
            VALUES (?, ?, ?, 'runtime_adjudicated', 'unique',
                    'alive_at_baseline', 'valid', ?)
            """,
            [baseline_id, title_id, resolved_character_id, validation_note],
        )
        connection.execute("COMMIT")
    except Exception:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        connection.close()

    return HolderAdjudicationResult(
        baseline_id,
        title_id,
        declared_holder_id,
        resolved_character_id,
        identity.player_character_id,
        digest,
    )


def _ck3_date(value: str) -> date:
    parts = value.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid CK3 save date: {value}")
    return date(*(int(part) for part in parts))