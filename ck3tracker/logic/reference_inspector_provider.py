"""Read-only candidate reference models for the visual inspection page."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from logic.promotion_readiness_service import get_latest_promotion_readiness_report
from logic.root_database import connect


TITLE_RANKS = ("empire", "kingdom", "duchy", "county", "barony")


def get_promotion_readiness(
    baseline_id: str,
    database_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """Return the latest immutable readiness report for visual review."""
    report = get_latest_promotion_readiness_report(baseline_id, database_path)
    if report is None:
        return None
    return {
        "report_id": report.report_id,
        "generated_at_utc": report.generated_at_utc,
        "overall_status": report.overall_status,
        "evidence_status": report.evidence_status,
        "evidence_detail": report.evidence_detail,
        "evidence_binding_count": len(report.evidence_bindings),
        "counts": report.counts,
        "findings": [
            {
                "code": finding.code,
                "classification": finding.classification,
                "subject_count": finding.subject_count,
                "summary": finding.summary,
                "detail": finding.detail,
            }
            for finding in report.findings
        ],
    }


def get_inspection_baselines(
    database_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Return candidate and promoted baselines for explicit inspection."""
    connection = connect(database_path)
    try:
        rows = connection.execute(
            """
            SELECT b.baseline_id, b.reference_snapshot_id, b.baseline_date,
                   b.label, b.support_status, b.historical_state_complete,
                   s.game_version, s.steam_build_id, s.review_status,
                   count(t.title_id) AS title_count,
                   count(t.title_id) FILTER (WHERE t.selectable) AS selectable_count
            FROM reference.baselines b
            JOIN source.reference_snapshots s USING (reference_snapshot_id)
            LEFT JOIN reference.titles t USING (baseline_id)
            GROUP BY ALL
            ORDER BY b.baseline_date, b.label
            """
        ).fetchall()
        columns = [column[0] for column in connection.description]
        return [dict(zip(columns, row, strict=True)) for row in rows]
    finally:
        connection.close()


def get_inspection_title_options(
    baseline_id: str,
    title_rank: str,
    database_path: str | Path | None = None,
) -> list[dict[str, str]]:
    """Return every title at a rank, including candidate warning records."""
    if title_rank not in TITLE_RANKS:
        raise ValueError(f"Unsupported title rank: {title_rank}")
    connection = connect(database_path)
    try:
        rows = connection.execute(
            """
            SELECT title_id, display_name, selectable
            FROM reference.titles
            WHERE baseline_id = ? AND title_rank = ?
            ORDER BY display_name, title_id
            """,
            [baseline_id, title_rank],
        ).fetchall()
        return [
            {
                "label": f"{display_name}  [{title_id}]"
                + ("  - warning" if not selectable else ""),
                "value": title_id,
            }
            for title_id, display_name, selectable in rows
        ]
    finally:
        connection.close()


def get_baseline_bookmarks(
    baseline_id: str,
    database_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Return themed recommendation collections attached to a date profile."""
    connection = connect(database_path)
    try:
        rows = connection.execute(
            """
            SELECT bookmark.bookmark_id,
                   COALESCE(label.display_value, bookmark.bookmark_id) AS display_name,
                   bookmark.effective_start_date,
                   count(character.character_ordinal) FILTER
                       (WHERE character.character_kind = 'featured') AS featured_count,
                   COALESCE(
                       string_agg(
                           DISTINCT CASE
                               WHEN requirement.resolution_status = 'resolved'
                               THEN package.display_name || ' [' || package.package_id || ']'
                               ELSE requirement.requirement_value || ' [unresolved]'
                           END,
                           ', '
                       ),
                       'Core game'
                   ) AS dlc_requirements,
                   membership.validation_status,
                   membership.validation_note
            FROM reference.baseline_bookmarks membership
            JOIN reference.baselines baseline USING (baseline_id)
            JOIN reference.bookmarks bookmark
              ON bookmark.reference_snapshot_id = baseline.reference_snapshot_id
             AND bookmark.bookmark_id = membership.bookmark_id
            LEFT JOIN reference.localizations label
              ON label.reference_snapshot_id = bookmark.reference_snapshot_id
             AND label.language = 'english'
             AND label.localization_key = bookmark.localization_key
            LEFT JOIN reference.bookmark_featured_characters character
              ON character.reference_snapshot_id = bookmark.reference_snapshot_id
             AND character.bookmark_id = bookmark.bookmark_id
            LEFT JOIN reference.bookmark_dlc_requirements requirement
              ON requirement.reference_snapshot_id = bookmark.reference_snapshot_id
             AND requirement.bookmark_id = bookmark.bookmark_id
                        LEFT JOIN reference.dlc_packages package
                            ON package.reference_snapshot_id = requirement.reference_snapshot_id
                         AND package.package_id = requirement.resolved_package_id
            WHERE membership.baseline_id = ?
            GROUP BY ALL
            ORDER BY display_name, bookmark.bookmark_id
            """,
            [baseline_id],
        ).fetchall()
        columns = [column[0] for column in connection.description]
        return [dict(zip(columns, row, strict=True)) for row in rows]
    finally:
        connection.close()


def get_title_inspection(
    baseline_id: str,
    title_id: str,
    database_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """Return hierarchy, baseline state, holder, children, and provenance."""
    connection = connect(database_path)
    try:
        cursor = connection.execute(
            """
            SELECT t.title_id, t.display_name, t.title_rank, t.parent_title_id,
                   t.selectable, t.source_path, t.source_line,
                   t.validation_status AS hierarchy_validation_status,
                   t.validation_note AS hierarchy_validation_note,
                   b.baseline_date, b.support_status, b.historical_state_complete,
                   s.reference_snapshot_id, s.game_version, s.steam_build_id,
                   COALESCE(adjudication.adjudicated_holder_character_id,
                            ts.holder_character_id) AS holder_character_id,
                   ts.holder_character_id AS declared_holder_character_id,
                   adjudication.evidence_kind AS holder_evidence_kind,
                   adjudication.evidence_path AS holder_evidence_path,
                   adjudication.evidence_sha256 AS holder_evidence_sha256,
                   ts.holder_status, ts.liege_title_id,
                   ts.liege_status, ts.government_id, ts.government_status,
                   ts.development_level, ts.development_status,
                   ts.capital_title_id, ts.capital_status,
                   ts.validation_status AS history_validation_status,
                   ts.validation_note AS history_validation_note,
                   dj.de_jure_liege_title_id,
                   dj.de_jure_liege_status,
                   dj.effective_date AS de_jure_effective_date,
                   dj.source_declaration_order AS de_jure_source_declaration_order,
                   hv.declaration_status AS holder_declaration_status,
                   hv.uniqueness_status AS holder_uniqueness_status,
                   hv.lifecycle_status AS holder_lifecycle_status,
                   hv.validation_status AS holder_validation_status,
                   hv.validation_note AS holder_validation_note,
                   cs.display_name AS holder_name, cs.sex AS holder_sex,
                   cs.sex_status AS holder_sex_status, cs.culture_id,
                   cs.faith_id, cs.faith_source_key, cs.dynasty_id,
                   cs.dynasty_house_id, cs.birth_date, cs.death_date,
                   cs.validation_status AS character_validation_status,
                   cs.validation_note AS character_validation_note
            FROM reference.titles t
            JOIN reference.baselines b USING (baseline_id)
            JOIN source.reference_snapshots s USING (reference_snapshot_id)
            LEFT JOIN reference.title_baseline_states ts
              ON ts.baseline_id = t.baseline_id AND ts.title_id = t.title_id
            LEFT JOIN reference.title_holder_validations hv
              ON hv.baseline_id = t.baseline_id AND hv.title_id = t.title_id
                        LEFT JOIN reference.title_holder_adjudications adjudication
                            ON adjudication.baseline_id = t.baseline_id
                         AND adjudication.title_id = t.title_id
                         AND adjudication.review_status = 'reviewed'
                        LEFT JOIN reference.title_baseline_de_jure_lieges dj
                            ON dj.baseline_id = t.baseline_id AND dj.title_id = t.title_id
            LEFT JOIN reference.character_baseline_states cs
              ON cs.baseline_id = t.baseline_id
                         AND cs.character_id = COALESCE(
                                        adjudication.adjudicated_holder_character_id,
                                        ts.holder_character_id
                                 )
            WHERE t.baseline_id = ? AND t.title_id = ?
            """,
            [baseline_id, title_id],
        )
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [column[0] for column in cursor.description]
        result = dict(zip(columns, row, strict=True))
        result["chain"] = _title_chain(connection, baseline_id, title_id)
        result["children"] = _title_children(connection, baseline_id, title_id)
        result["history_blocks"] = _title_history_blocks(
            connection, result["reference_snapshot_id"], title_id
        )
        result["laws"] = _title_laws(connection, baseline_id, title_id)
        result["warnings"] = _warnings(result)
        return result
    finally:
        connection.close()


def _title_chain(connection, baseline_id: str, title_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        WITH RECURSIVE chain AS (
            SELECT title_id, display_name, title_rank, parent_title_id,
                   selectable, 0 AS depth
            FROM reference.titles
            WHERE baseline_id = ? AND title_id = ?
            UNION ALL
            SELECT parent.title_id, parent.display_name, parent.title_rank,
                   parent.parent_title_id, parent.selectable, chain.depth + 1
            FROM reference.titles parent
            JOIN chain ON parent.title_id = chain.parent_title_id
            WHERE parent.baseline_id = ?
        )
        SELECT title_id, display_name, title_rank, selectable
        FROM chain ORDER BY depth DESC
        """,
        [baseline_id, title_id, baseline_id],
    ).fetchall()
    return [
        {
            "title_id": row[0],
            "display_name": row[1],
            "title_rank": row[2],
            "selectable": row[3],
        }
        for row in rows
    ]


def _title_children(connection, baseline_id: str, title_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT title_id, display_name, title_rank, selectable,
               validation_status, validation_note
        FROM reference.titles
        WHERE baseline_id = ? AND parent_title_id = ?
        ORDER BY display_name, title_id
        """,
        [baseline_id, title_id],
    ).fetchall()
    return [
        {
            "title_id": row[0],
            "display_name": row[1],
            "title_rank": row[2],
            "selectable": row[3],
            "validation_status": row[4],
            "validation_note": row[5],
        }
        for row in rows
    ]


def _title_history_blocks(
    connection, reference_snapshot_id: str, title_id: str
) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT source_block_order, source_path, duplicate_classification,
               baseline_conflict_fields, resolution_status, is_winner
        FROM source.title_history_blocks
        WHERE reference_snapshot_id = ? AND title_id = ?
        ORDER BY source_block_order
        """,
        [reference_snapshot_id, title_id],
    ).fetchall()
    return [
        {
            "source_block_order": row[0],
            "source_path": row[1],
            "duplicate_classification": row[2],
            "baseline_conflict_fields": row[3],
            "resolution_status": row[4],
            "is_winner": row[5],
        }
        for row in rows
    ]


def _title_laws(
    connection, baseline_id: str, title_id: str
) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT active.law_order, active.law_id, definition.law_group_id,
               active.effective_date, active.source_declaration_order,
               definition.source_path, definition.source_line_start,
               definition.source_line_end, active.validation_status,
               active.validation_note
        FROM reference.title_baseline_laws active
        JOIN reference.baselines baseline USING (baseline_id)
        JOIN reference.law_definitions definition
          ON definition.reference_snapshot_id = baseline.reference_snapshot_id
         AND definition.law_id = active.law_id
        WHERE active.baseline_id = ? AND active.title_id = ?
        ORDER BY active.law_order
        """,
        [baseline_id, title_id],
    ).fetchall()
    columns = [column[0] for column in connection.description]
    return [dict(zip(columns, row, strict=True)) for row in rows]


def _warnings(result: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for prefix, status_key, note_key in (
        ("Hierarchy", "hierarchy_validation_status", "hierarchy_validation_note"),
        ("Title history", "history_validation_status", "history_validation_note"),
        ("Holder", "holder_validation_status", "holder_validation_note"),
        ("Character", "character_validation_status", "character_validation_note"),
    ):
        if result.get(status_key) == "warning":
            warnings.append(f"{prefix}: {result.get(note_key) or 'review required'}")
    if result.get("capital_status") == "not_evaluated":
        warnings.append("Capital: static and scripted capital resolution is not loaded yet")
    return warnings