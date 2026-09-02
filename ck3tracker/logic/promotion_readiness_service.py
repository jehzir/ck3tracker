"""Generate an auditable promotion-readiness report without promoting data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from uuid import uuid4

from logic.root_database import connect


EXPECTED_PARSERS = {
    "installed_bookmarks": "1.2.0",
    "installed_character_history": "1.8.0",
    "installed_cultures": "1.1.0",
    "installed_dynasties": "1.0.0",
    "installed_dynasty_houses": "1.0.0",
    "installed_faiths": "1.0.0",
    "installed_governments": "1.0.0",
    "installed_landed_titles": "1.0.0",
    "installed_localization_english": "1.0.0",
    "installed_title_history": "1.22.0",
}


@dataclass(frozen=True)
class ReadinessFinding:
    code: str
    classification: str
    subject_count: int
    summary: str
    detail: str


@dataclass(frozen=True)
class ReadinessEvidenceBinding:
    parser_name: str
    parser_run_id: str | None
    parser_version: str | None
    parser_status: str
    manifest_count: int
    manifest_digest: str


@dataclass(frozen=True)
class PromotionReadinessReport:
    report_id: str
    baseline_id: str
    reference_snapshot_id: str
    generated_at_utc: datetime
    overall_status: str
    findings: tuple[ReadinessFinding, ...]
    evidence_status: str
    evidence_detail: str
    evidence_bindings: tuple[ReadinessEvidenceBinding, ...]

    @property
    def counts(self) -> dict[str, int]:
        return {
            classification: sum(
                finding.classification == classification for finding in self.findings
            )
            for classification in (
                "blocking",
                "accepted_exception",
                "informational",
                "passed",
            )
        }


def generate_promotion_readiness_report(
    baseline_id: str,
    database_path: str | Path | None = None,
) -> PromotionReadinessReport:
    """Evaluate and persist one immutable report run for a candidate baseline."""
    connection = connect(database_path)
    generated_at = datetime.now(timezone.utc)
    report_id = f"{baseline_id}:readiness:{uuid4()}"
    try:
        connection.execute("BEGIN TRANSACTION")
        baseline = connection.execute(
            """
            SELECT b.reference_snapshot_id, b.support_status,
                   b.historical_state_complete, s.review_status,
                   s.game_version, s.steam_build_id
            FROM reference.baselines b
            JOIN source.reference_snapshots s USING (reference_snapshot_id)
            WHERE b.baseline_id = ?
            """,
            [baseline_id],
        ).fetchone()
        if baseline is None:
            raise ValueError(f"Unknown baseline: {baseline_id}")
        snapshot_id = str(baseline[0])
        evidence_bindings = _capture_evidence_bindings(connection, snapshot_id)
        findings = _evaluate(
            connection,
            baseline_id,
            snapshot_id,
            baseline,
            evidence_bindings,
        )
        overall_status = (
            "blocked"
            if any(finding.classification == "blocking" for finding in findings)
            else "ready_for_review"
        )
        report = PromotionReadinessReport(
            report_id,
            baseline_id,
            snapshot_id,
            generated_at,
            overall_status,
            tuple(findings),
            "current",
            "Report evidence matches the parser runs and manifests evaluated at generation.",
            evidence_bindings,
        )
        counts = report.counts

        connection.execute(
            """
            INSERT INTO reference.promotion_readiness_reports
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                report.report_id,
                report.baseline_id,
                report.reference_snapshot_id,
                report.generated_at_utc,
                report.overall_status,
                counts["blocking"],
                counts["accepted_exception"],
                counts["informational"],
                counts["passed"],
            ],
        )
        connection.executemany(
            """
            INSERT INTO reference.promotion_readiness_findings
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    report.report_id,
                    order,
                    finding.code,
                    finding.classification,
                    finding.subject_count,
                    finding.summary,
                    finding.detail,
                )
                for order, finding in enumerate(report.findings, 1)
            ],
        )
        connection.executemany(
            """
            INSERT INTO reference.promotion_readiness_evidence
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    report.report_id,
                    binding.parser_name,
                    binding.parser_run_id,
                    binding.parser_version,
                    binding.parser_status,
                    binding.manifest_count,
                    binding.manifest_digest,
                )
                for binding in report.evidence_bindings
            ],
        )
        connection.execute("COMMIT")
        return report
    except Exception:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        connection.close()


def get_latest_promotion_readiness_report(
    baseline_id: str,
    database_path: str | Path | None = None,
) -> PromotionReadinessReport | None:
    """Return the newest persisted readiness report for a baseline."""
    connection = connect(database_path)
    try:
        row = connection.execute(
            """
            SELECT report_id, baseline_id, reference_snapshot_id,
                   generated_at_utc, overall_status
            FROM reference.promotion_readiness_reports
            WHERE baseline_id = ?
            ORDER BY generated_at_utc DESC, report_id DESC
            LIMIT 1
            """,
            [baseline_id],
        ).fetchone()
        if row is None:
            return None
        findings = connection.execute(
            """
            SELECT finding_code, classification, subject_count, summary, detail
            FROM reference.promotion_readiness_findings
            WHERE report_id = ?
            ORDER BY finding_order
            """,
            [row[0]],
        ).fetchall()
        evidence_rows = connection.execute(
            """
            SELECT parser_name, parser_run_id, parser_version, parser_status,
                   manifest_count, manifest_digest
            FROM reference.promotion_readiness_evidence
            WHERE report_id = ?
            ORDER BY parser_name
            """,
            [row[0]],
        ).fetchall()
        evidence_bindings = tuple(
            ReadinessEvidenceBinding(*evidence_row) for evidence_row in evidence_rows
        )
        current_bindings = _capture_evidence_bindings(connection, str(row[2]))
        evidence_status, evidence_detail = _compare_evidence_bindings(
            evidence_bindings,
            current_bindings,
        )
        return PromotionReadinessReport(
            str(row[0]),
            str(row[1]),
            str(row[2]),
            row[3],
            str(row[4]),
            tuple(ReadinessFinding(*finding) for finding in findings),
            evidence_status,
            evidence_detail,
            evidence_bindings,
        )
    finally:
        connection.close()


def _capture_evidence_bindings(
    connection,
    snapshot_id: str,
) -> tuple[ReadinessEvidenceBinding, ...]:
    latest_runs = {
        str(row[0]): (str(row[1]), str(row[2]), str(row[3]))
        for row in connection.execute(
            """
            SELECT parser_name, parser_run_id, parser_version, status
            FROM (
                SELECT parser_name, parser_run_id, parser_version, status,
                       row_number() OVER (
                           PARTITION BY parser_name
                           ORDER BY started_at_utc DESC, parser_run_id DESC
                       ) AS run_order
                FROM source.parser_runs
                WHERE reference_snapshot_id = ?
            ) latest
            WHERE run_order = 1
            """,
            [snapshot_id],
        ).fetchall()
    }
    bindings: list[ReadinessEvidenceBinding] = []
    for parser_name in sorted(EXPECTED_PARSERS):
        manifest_rows = connection.execute(
            """
            SELECT relative_path, sha256, byte_size, modified_at_utc, parser_run_id
            FROM source.source_files
            WHERE reference_snapshot_id = ? AND source_group = ?
            ORDER BY relative_path
            """,
            [snapshot_id, parser_name],
        ).fetchall()
        manifest_payload = [
            [
                str(value) if value is not None else None
                for value in manifest_row
            ]
            for manifest_row in manifest_rows
        ]
        manifest_digest = sha256(
            json.dumps(
                manifest_payload,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        latest_run = latest_runs.get(parser_name)
        bindings.append(
            ReadinessEvidenceBinding(
                parser_name,
                latest_run[0] if latest_run else None,
                latest_run[1] if latest_run else None,
                latest_run[2] if latest_run else "missing",
                len(manifest_rows),
                manifest_digest,
            )
        )
    return tuple(bindings)


def _compare_evidence_bindings(
    stored: tuple[ReadinessEvidenceBinding, ...],
    current: tuple[ReadinessEvidenceBinding, ...],
) -> tuple[str, str]:
    if not stored:
        return "stale", "Legacy report has no parser-run or manifest bindings."
    stored_by_parser = {binding.parser_name: binding for binding in stored}
    changed = [
        binding.parser_name
        for binding in current
        if stored_by_parser.get(binding.parser_name) != binding
    ]
    if changed:
        return "stale", "Evidence changed for: " + ", ".join(changed) + "."
    return "current", "Report evidence matches the current parser runs and manifests."


def _evaluate(
    connection,
    baseline_id: str,
    snapshot_id: str,
    baseline,
    evidence_bindings: tuple[ReadinessEvidenceBinding, ...],
) -> list[ReadinessFinding]:
    findings: list[ReadinessFinding] = []

    def add(code: str, classification: str, count: int, summary: str, detail: str) -> None:
        findings.append(ReadinessFinding(code, classification, int(count), summary, detail))

    identity_complete = bool(baseline[4] and baseline[5])
    add(
        "build_identity",
        "passed" if identity_complete else "blocking",
        1 if identity_complete else 0,
        "Installed build identity is recorded" if identity_complete else "Installed build identity is incomplete",
        f"Game {baseline[4] or 'unknown'}, Steam build {baseline[5] or 'unknown'}.",
    )

    latest_parser_runs = {
        binding.parser_name: (
            binding.parser_run_id,
            binding.parser_version,
            binding.parser_status,
        )
        for binding in evidence_bindings
        if binding.parser_run_id is not None
    }
    parser_failures: list[str] = []
    for parser_name, expected_version in sorted(EXPECTED_PARSERS.items()):
        latest_run = latest_parser_runs.get(parser_name)
        if latest_run is None:
            parser_failures.append(f"{parser_name}: missing")
        elif latest_run[2] != "completed":
            parser_failures.append(
                f"{parser_name}: latest status {latest_run[2]}"
            )
        elif latest_run[1] != expected_version:
            parser_failures.append(
                f"{parser_name}: expected {expected_version}, latest {latest_run[1]}"
            )
    add(
        "required_parsers",
        "blocking" if parser_failures else "passed",
        len(parser_failures) if parser_failures else len(EXPECTED_PARSERS),
        "Required parser runs are not current" if parser_failures else "All required parser groups have current successful runs",
        "; ".join(parser_failures) if parser_failures else ", ".join(
            f"{name}@{version}" for name, version in sorted(EXPECTED_PARSERS.items())
        ),
    )

    manifest_bindings: dict[str, dict[str | None, int]] = {}
    for source_group, parser_run_id, manifest_count in connection.execute(
        """
        SELECT source_group, parser_run_id, count(*)
        FROM source.source_files
        WHERE reference_snapshot_id = ?
        GROUP BY source_group, parser_run_id
        """,
        [snapshot_id],
    ).fetchall():
        manifest_bindings.setdefault(str(source_group), {})[
            str(parser_run_id) if parser_run_id is not None else None
        ] = int(manifest_count)

    manifest_failures: list[str] = []
    manifest_counts: list[str] = []
    total_manifests = 0
    for parser_name in sorted(EXPECTED_PARSERS):
        bindings = manifest_bindings.get(parser_name, {})
        group_total = sum(bindings.values())
        total_manifests += group_total
        latest_run = latest_parser_runs.get(parser_name)
        if group_total == 0:
            manifest_failures.append(f"{parser_name}: missing")
            continue
        if latest_run is None:
            manifest_failures.append(f"{parser_name}: no latest parser run")
            continue
        matching_count = bindings.get(latest_run[0], 0)
        if matching_count != group_total:
            manifest_failures.append(
                f"{parser_name}: {matching_count} of {group_total} bound to latest run"
            )
            continue
        manifest_counts.append(f"{parser_name}: {group_total}")
    add(
        "source_manifests",
        "blocking" if manifest_failures else "passed",
        len(manifest_failures) if manifest_failures else total_manifests,
        "Source manifests are missing or stale" if manifest_failures else "All source manifests are bound to latest parser runs",
        "; ".join(manifest_failures) if manifest_failures else ", ".join(manifest_counts),
    )

    selectable_warnings = _count(
        connection,
        "SELECT count(*) FROM reference.titles WHERE baseline_id = ? AND selectable AND validation_status = 'warning'",
        [baseline_id],
    )
    add(
        "selectable_hierarchy",
        "blocking" if selectable_warnings else "passed",
        selectable_warnings,
        "Selectable hierarchy contains warnings" if selectable_warnings else "Every selectable title has a canonical parent chain",
        "Selectable locations must resolve Barony to County to Duchy to Kingdom to Empire.",
    )

    structural_exceptions = _count(
        connection,
        "SELECT count(*) FROM reference.titles WHERE baseline_id = ? AND NOT selectable AND validation_note LIKE 'non-canonical rank chain:%'",
        [baseline_id],
    )
    add(
        "nonselectable_structural_titles",
        "accepted_exception",
        structural_exceptions,
        "Noncanonical titles remain excluded from location selection",
        "These installed structural and noble-family records are retained but cannot start a playthrough.",
    )

    duplicate_titles = _count(
        connection,
        "SELECT count(*) FROM reference.titles WHERE baseline_id = ? AND validation_note = 'duplicate title declarations'",
        [baseline_id],
    )
    add(
        "duplicate_structural_titles",
        "accepted_exception" if duplicate_titles else "passed",
        duplicate_titles,
        "Nonselectable structural capital conflicts remain explicit" if duplicate_titles else "Structural title IDs are unique",
        "Conflicting noble-family declarations are retained, excluded from selection, and require no inferred winner.",
    )

    duplicate_history = _count(
        connection,
        """
        SELECT count(DISTINCT block.title_id)
        FROM source.title_history_blocks block
        JOIN reference.baselines baseline
          ON baseline.reference_snapshot_id = block.reference_snapshot_id
        WHERE baseline.baseline_id = ?
          AND block.duplicate_classification = 'conflicting_at_baseline'
        """,
        [baseline_id],
    )
    add(
        "duplicate_title_history",
        "blocking" if duplicate_history else "passed",
        duplicate_history,
        "Baseline-conflicting title histories require review" if duplicate_history else "Duplicate title histories do not conflict at this baseline",
        "Only distinct title IDs with conflicting baseline-effective singleton assignments block this date profile.",
    )

    opaque_title_states = _count(
        connection,
        "SELECT count(*) FROM reference.title_baseline_states WHERE baseline_id = ? AND validation_note LIKE '%not evaluated:%'",
        [baseline_id],
    )
    add(
        "opaque_title_history",
        "blocking" if opaque_title_states else "passed",
        opaque_title_states,
        "Baseline-effective title history remains uninterpreted" if opaque_title_states else "Baseline title history is fully interpreted",
        "Opaque effects and unsupported operations need scope review before promotion.",
    )

    duplicate_characters = _count(
        connection,
                """
                SELECT count(DISTINCT block.character_id)
                FROM source.character_history_blocks block
                JOIN reference.baselines baseline
                    ON baseline.reference_snapshot_id = block.reference_snapshot_id
                WHERE baseline.baseline_id = ?
                    AND block.duplicate_classification = 'conflicting_at_baseline'
                """,
        [baseline_id],
    )
    opaque_characters = _count(
        connection,
        "SELECT count(*) FROM reference.character_baseline_states WHERE baseline_id = ? AND validation_note LIKE '%not evaluated:%'",
        [baseline_id],
    )
    add(
        "character_history_review",
        "blocking" if duplicate_characters or opaque_characters else "passed",
        duplicate_characters + opaque_characters,
        "Character history requires review" if duplicate_characters or opaque_characters else "Character history is fully resolved",
        f"{duplicate_characters} duplicate IDs and {opaque_characters} baseline-effective opaque states.",
    )

    holder_conflicts = _count(
        connection,
        "SELECT count(*) FROM reference.title_holder_validations WHERE baseline_id = ? AND validation_status = 'warning'",
        [baseline_id],
    )
    add(
        "holder_lifecycle",
        "blocking" if holder_conflicts else "passed",
        holder_conflicts,
        "Holder lifecycle conflicts remain" if holder_conflicts else "Every title holder is alive at the baseline",
        "The current conflict is preserved with its title and character IDs in holder validation evidence.",
    )

    bookmark_links = _count(
        connection,
        "SELECT count(*) FROM reference.baseline_bookmarks WHERE baseline_id = ? AND validation_status = 'valid'",
        [baseline_id],
    )
    bookmark_warnings = _count(
        connection,
        """
        SELECT count(*)
        FROM reference.bookmark_featured_characters featured
        JOIN reference.baseline_bookmarks membership USING (bookmark_id)
        WHERE membership.baseline_id = ?
          AND featured.character_kind = 'featured'
          AND featured.validation_status = 'warning'
        """,
        [baseline_id],
    )
    add(
        "bookmark_profile",
        "passed" if bookmark_links and not bookmark_warnings else "blocking",
        bookmark_links,
        "Bookmark profile and featured rulers resolve" if bookmark_links and not bookmark_warnings else "Bookmark profile is incomplete",
        f"{bookmark_links} themed collections; {bookmark_warnings} unresolved direct featured rulers.",
    )

    unresolved_dlc_flags = [
        str(row[0])
        for row in connection.execute(
            """
            SELECT DISTINCT requirement.requirement_value
                        FROM reference.bookmark_dlc_requirements requirement
            LEFT JOIN reference.dlc_packages package
              ON package.reference_snapshot_id = requirement.reference_snapshot_id
             AND package.package_id = requirement.resolved_package_id
             AND package.validation_status = 'valid'
                        WHERE requirement.reference_snapshot_id = ?
              AND (requirement.resolution_status <> 'resolved'
                   OR requirement.resolved_package_id IS NULL
                   OR package.package_id IS NULL)
            ORDER BY requirement.requirement_value
            """,
                        [snapshot_id],
        ).fetchall()
    ]
    resolved_dlc_gates = _count(
        connection,
        """
        SELECT count(*)
                FROM reference.bookmark_dlc_requirements requirement
                WHERE requirement.reference_snapshot_id = ?
          AND requirement.resolution_status = 'resolved'
          AND requirement.resolved_package_id IS NOT NULL
        """,
                [snapshot_id],
    )
    add(
        "bookmark_dlc_resolution",
        "blocking" if unresolved_dlc_flags else "passed",
        len(unresolved_dlc_flags) if unresolved_dlc_flags else resolved_dlc_gates,
        "Bookmark DLC gates are unresolved" if unresolved_dlc_flags else "Every bookmark DLC gate resolves to an installed package",
        (
            ", ".join(unresolved_dlc_flags)
            if unresolved_dlc_flags
            else f"{resolved_dlc_gates} package-gated bookmark requirements; ungated bookmarks are core game."
        ),
    )

    unresolved_capitals = _count(
        connection,
        "SELECT count(*) FROM reference.title_baseline_states WHERE baseline_id = ? AND capital_status IN ('unresolved', 'not_evaluated')",
        [baseline_id],
    )
    add(
        "capital_resolution",
        "blocking" if unresolved_capitals else "passed",
        unresolved_capitals,
        "Capital resolution is incomplete" if unresolved_capitals else "Static and 867 historical capitals are resolved",
        "Resolved records retain declared, first-barony-derived, or history-override provenance.",
    )

    missing_localizations = _count(
        connection,
        """
        SELECT count(*)
        FROM reference.titles title
        JOIN reference.baselines baseline USING (baseline_id)
        LEFT JOIN reference.localizations label
          ON label.reference_snapshot_id = baseline.reference_snapshot_id
         AND label.language = 'english'
         AND label.localization_key = title.localization_key
        WHERE title.baseline_id = ? AND title.selectable
          AND label.localization_key IS NULL
        """,
        [baseline_id],
    )
    add(
        "selectable_localization",
        "blocking" if missing_localizations else "passed",
        missing_localizations,
        "Selectable titles are missing English labels" if missing_localizations else "Every selectable title has an English label",
        "Nonselectable placeholders do not block location selection.",
    )

    wiki_pages = _count(
        connection,
        """
        SELECT count(*) FROM source.wiki_pages
        WHERE reference_snapshot_id = ? AND page_key = 'government'
          AND canonical_url <> '' AND permanent_url <> '' AND revision_id <> ''
          AND retrieved_at_utc IS NOT NULL AND stated_game_version IS NOT NULL
          AND review_status = 'reviewed'
        """,
        [snapshot_id],
    )
    add(
        "wiki_provenance",
        "passed" if wiki_pages else "blocking",
        wiki_pages,
        "Reviewed Government wiki provenance is recorded" if wiki_pages else "Versioned Government wiki provenance is not loaded",
        "Promotion requires page URL, revision or permanent-link ID, retrieval time, stated version, and review status.",
    )

    unresolved_governments = _count(
        connection,
        """
        SELECT count(DISTINCT state.government_id)
        FROM reference.title_baseline_states state
        JOIN reference.baselines baseline USING (baseline_id)
        LEFT JOIN reference.governments government
          ON government.reference_snapshot_id = baseline.reference_snapshot_id
         AND government.government_id = state.government_id
         AND government.validation_status = 'valid'
        WHERE state.baseline_id = ? AND state.government_id IS NOT NULL
          AND government.government_id IS NULL
        """,
        [baseline_id],
    )
    add(
        "government_catalog",
        "blocking" if unresolved_governments else "passed",
        unresolved_governments,
        "Government IDs are unresolved" if unresolved_governments else "Every baseline government ID resolves",
        "Government coverage is validated by stable-ID joins against the snapshot-scoped installed catalog.",
    )

    culture_wiki_pages = _count(
        connection,
        """
        SELECT count(*) FROM source.wiki_pages
        WHERE reference_snapshot_id = ? AND page_key = 'culture'
          AND canonical_url <> '' AND permanent_url <> '' AND revision_id <> ''
          AND retrieved_at_utc IS NOT NULL AND stated_game_version IS NOT NULL
          AND review_status = 'reviewed'
        """,
        [snapshot_id],
    )
    add(
        "culture_wiki_provenance",
        "passed" if culture_wiki_pages else "blocking",
        culture_wiki_pages,
        "Reviewed Culture wiki provenance is recorded" if culture_wiki_pages else "Versioned Culture wiki provenance is not loaded",
        "Promotion requires page URL, revision or permanent-link ID, retrieval time, stated version, and review status.",
    )

    unresolved_cultures = _count(
        connection,
        """
        SELECT count(DISTINCT state.culture_id)
        FROM reference.character_baseline_states state
        JOIN reference.baselines baseline USING (baseline_id)
        LEFT JOIN reference.cultures culture
          ON culture.reference_snapshot_id = baseline.reference_snapshot_id
         AND culture.culture_id = state.culture_id
         AND culture.validation_status = 'valid'
        WHERE state.baseline_id = ? AND state.culture_id IS NOT NULL
          AND culture.culture_id IS NULL
        """,
        [baseline_id],
    )
    add(
        "culture_catalog",
        "blocking" if unresolved_cultures else "passed",
        unresolved_cultures,
        "Culture IDs are unresolved" if unresolved_cultures else "Every baseline culture ID resolves",
        "Culture coverage is validated by stable-ID joins against the snapshot-scoped installed catalog.",
    )

    faith_wiki_pages = _count(
        connection,
        """
        SELECT count(*) FROM source.wiki_pages
        WHERE reference_snapshot_id = ? AND page_key = 'faith'
          AND canonical_url <> '' AND permanent_url <> '' AND revision_id <> ''
          AND retrieved_at_utc IS NOT NULL AND stated_game_version IS NOT NULL
          AND review_status = 'reviewed'
        """,
        [snapshot_id],
    )
    add(
        "faith_wiki_provenance",
        "passed" if faith_wiki_pages else "blocking",
        faith_wiki_pages,
        "Reviewed Faith wiki provenance is recorded" if faith_wiki_pages else "Versioned Faith wiki provenance is not loaded",
        "Promotion requires page URL, revision or permanent-link ID, retrieval time, stated version, and review status.",
    )

    unresolved_faiths = _count(
        connection,
        """
        SELECT count(DISTINCT state.faith_id)
        FROM reference.character_baseline_states state
        JOIN reference.baselines baseline USING (baseline_id)
        LEFT JOIN reference.faiths faith
          ON faith.reference_snapshot_id = baseline.reference_snapshot_id
         AND faith.faith_id = state.faith_id
         AND faith.validation_status = 'valid'
        WHERE state.baseline_id = ? AND state.faith_id IS NOT NULL
          AND faith.faith_id IS NULL
        """,
        [baseline_id],
    )
    add(
        "faith_catalog",
        "blocking" if unresolved_faiths else "passed",
        unresolved_faiths,
        "Faith IDs are unresolved" if unresolved_faiths else "Every baseline faith ID resolves",
        "Faith coverage is validated by stable-ID joins against the snapshot-scoped installed catalog.",
    )

    dynasty_wiki_pages = _count(
        connection,
        """
        SELECT count(*) FROM source.wiki_pages
        WHERE reference_snapshot_id = ? AND page_key = 'dynasty'
          AND canonical_url <> '' AND permanent_url <> '' AND revision_id <> ''
          AND retrieved_at_utc IS NOT NULL AND stated_game_version IS NOT NULL
          AND review_status = 'reviewed'
        """,
        [snapshot_id],
    )
    add(
        "dynasty_wiki_provenance",
        "passed" if dynasty_wiki_pages else "blocking",
        dynasty_wiki_pages,
        "Reviewed Dynasty wiki provenance is recorded" if dynasty_wiki_pages else "Versioned Dynasty wiki provenance is not loaded",
        "Promotion requires page URL, revision or permanent-link ID, retrieval time, stated version, and review status.",
    )

    unresolved_dynasties = _count(
        connection,
        """
        SELECT count(DISTINCT state.dynasty_id)
        FROM reference.character_baseline_states state
        JOIN reference.baselines baseline USING (baseline_id)
        LEFT JOIN reference.dynasties dynasty
          ON dynasty.reference_snapshot_id = baseline.reference_snapshot_id
         AND dynasty.dynasty_id = state.dynasty_id
         AND dynasty.validation_status = 'valid'
        WHERE state.baseline_id = ? AND state.dynasty_id IS NOT NULL
          AND dynasty.dynasty_id IS NULL
        """,
        [baseline_id],
    )
    add(
        "dynasty_catalog",
        "blocking" if unresolved_dynasties else "passed",
        unresolved_dynasties,
        "Dynasty IDs are unresolved" if unresolved_dynasties else "Every baseline dynasty ID resolves",
        "Dynasty coverage is validated by stable-ID joins against the snapshot-scoped installed catalog.",
    )

    house_wiki_pages = _count(
        connection,
        """
        SELECT count(*) FROM source.wiki_pages
        WHERE reference_snapshot_id = ? AND page_key = 'house'
          AND canonical_url <> '' AND permanent_url <> '' AND revision_id <> ''
          AND retrieved_at_utc IS NOT NULL AND stated_game_version IS NOT NULL
          AND review_status = 'reviewed'
        """,
        [snapshot_id],
    )
    add(
        "house_wiki_provenance",
        "passed" if house_wiki_pages else "blocking",
        house_wiki_pages,
        "Reviewed House wiki provenance is recorded" if house_wiki_pages else "Versioned House wiki provenance is not loaded",
        "Promotion requires page URL, revision or permanent-link ID, retrieval time, stated version, and review status.",
    )

    unresolved_houses = _count(
        connection,
        """
        SELECT count(DISTINCT state.dynasty_house_id)
        FROM reference.character_baseline_states state
        JOIN reference.baselines baseline USING (baseline_id)
        LEFT JOIN reference.dynasty_houses house
          ON house.reference_snapshot_id = baseline.reference_snapshot_id
         AND house.dynasty_house_id = state.dynasty_house_id
         AND house.validation_status = 'valid'
        WHERE state.baseline_id = ? AND state.dynasty_house_id IS NOT NULL
          AND house.dynasty_house_id IS NULL
        """,
        [baseline_id],
    )
    add(
        "house_catalog",
        "blocking" if unresolved_houses else "passed",
        unresolved_houses,
        "Dynasty-house IDs are unresolved" if unresolved_houses else "Every baseline dynasty-house ID resolves",
        "House coverage is validated by stable-ID joins against the snapshot-scoped installed catalog.",
    )

    add(
        "promotion_gate",
        "informational",
        0,
        "Promotion remains an explicit operation",
        f"Current statuses: snapshot={baseline[3]}, baseline={baseline[1]}, historical_state_complete={str(baseline[2]).lower()}.",
    )
    return findings


def _count(connection, query: str, parameters: list[object] | None = None) -> int:
    return int(connection.execute(query, parameters or []).fetchone()[0])