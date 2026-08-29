"""Tests for classified, non-promoting readiness reports."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from logic.promotion_readiness_service import (
    EXPECTED_PARSERS,
    generate_promotion_readiness_report,
    get_latest_promotion_readiness_report,
)
from logic.root_database import connect


class PromotionReadinessServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "tracker.duckdb"
        connection = connect(self.database_path)
        try:
            connection.execute(
                "INSERT INTO source.reference_snapshots VALUES ('snapshot', '1.0', '100', 'ck3', 'candidate', current_timestamp)"
            )
            connection.execute(
                "INSERT INTO reference.baselines VALUES ('baseline', 'snapshot', NULL, '0867-01-01', '867', 'candidate', false)"
            )
            for parser in (
                "installed_bookmarks",
                "installed_character_history",
                "installed_landed_titles",
                "installed_localization_english",
                "installed_title_history",
            ):
                connection.execute(
                    """
                    INSERT INTO source.parser_runs
                    VALUES (?, 'snapshot', ?, '1', 'completed', current_timestamp,
                            current_timestamp, 1, 0, NULL)
                    """,
                    [f"run:{parser}", parser],
                )
            connection.execute(
                """
                INSERT INTO reference.titles
                (baseline_id, title_id, title_rank, display_name, selectable,
                 localization_key, validation_status)
                VALUES ('baseline', 'c_test', 'county', 'Test', true,
                        'c_test', 'valid')
                """
            )
            connection.execute(
                "INSERT INTO reference.localizations VALUES ('snapshot', 'english', 'c_test', NULL, 'Test', 'test.yml', 1, '1', 'valid')"
            )
            connection.execute(
                """
                INSERT INTO reference.title_baseline_states
                (baseline_id, title_id, holder_status, liege_status,
                 government_status, development_status, capital_title_id,
                 capital_status, validation_status)
                VALUES ('baseline', 'c_test', 'declared', 'no_declaration',
                        'declared', 'derived', 'b_test',
                        'derived_first_barony', 'valid')
                """
            )
            connection.execute(
                """
                INSERT INTO reference.title_holder_validations
                VALUES ('baseline', 'c_test', 'dead_character', 'declared',
                        'unique', 'dead_at_baseline', 'warning',
                        'holder lifecycle is dead_at_baseline')
                """
            )
            connection.execute(
                "INSERT INTO reference.bookmark_groups VALUES ('snapshot', 'group', '0867-01-01', 'group', 'valid', NULL)"
            )
            connection.execute(
                "INSERT INTO reference.bookmarks VALUES ('snapshot', 'bookmark', 'group', NULL, '0867-01-01', true, false, NULL, 'bookmark', 'bookmark_desc', 'valid', NULL)"
            )
            connection.execute(
                "INSERT INTO reference.baseline_bookmarks VALUES ('baseline', 'bookmark', 'valid', NULL)"
            )
        finally:
            connection.close()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_report_classifies_blockers_without_promoting(self) -> None:
        report = generate_promotion_readiness_report(
            "baseline", database_path=self.database_path
        )
        findings = {finding.code: finding for finding in report.findings}

        self.assertEqual("blocked", report.overall_status)
        self.assertEqual("blocking", findings["holder_lifecycle"].classification)
        self.assertEqual(1, findings["holder_lifecycle"].subject_count)
        self.assertEqual("passed", findings["bookmark_profile"].classification)
        self.assertEqual("passed", findings["bookmark_dlc_resolution"].classification)
        self.assertEqual("passed", findings["capital_resolution"].classification)
        self.assertEqual("passed", findings["duplicate_title_history"].classification)
        self.assertEqual("blocking", findings["wiki_provenance"].classification)

        latest = get_latest_promotion_readiness_report(
            "baseline", database_path=self.database_path
        )
        connection = connect(self.database_path)
        try:
            state = connection.execute(
                """
                SELECT s.review_status, b.support_status,
                       b.historical_state_complete,
                       (SELECT count(*) FROM app.supported_baselines)
                FROM source.reference_snapshots s
                JOIN reference.baselines b USING (reference_snapshot_id)
                """
            ).fetchone()
        finally:
            connection.close()
        self.assertIsNotNone(latest)
        self.assertEqual(report.report_id, latest.report_id)
        self.assertEqual("current", latest.evidence_status)
        self.assertEqual(len(EXPECTED_PARSERS), len(latest.evidence_bindings))
        self.assertEqual(("candidate", "candidate", False, 0), state)

    def test_new_parser_run_makes_prior_report_stale_without_mutation(self) -> None:
        self._replace_with_current_parser_runs()
        report = generate_promotion_readiness_report(
            "baseline", database_path=self.database_path
        )
        connection = connect(self.database_path)
        try:
            stored_before = connection.execute(
                """
                SELECT parser_name, parser_run_id, manifest_count, manifest_digest
                FROM reference.promotion_readiness_evidence
                WHERE report_id = ? ORDER BY parser_name
                """,
                [report.report_id],
            ).fetchall()
            connection.execute(
                """
                INSERT INTO source.parser_runs
                VALUES ('run:bookmarks:new', 'snapshot', 'installed_bookmarks',
                        '1.1.0', 'completed', TIMESTAMP '2001-01-01',
                        TIMESTAMP '2001-01-01', 1, 0, NULL)
                """
            )
            connection.execute(
                """
                UPDATE source.source_files
                SET parser_run_id = 'run:bookmarks:new', sha256 = 'new-hash'
                WHERE source_group = 'installed_bookmarks'
                """
            )
        finally:
            connection.close()

        stale = get_latest_promotion_readiness_report(
            "baseline", database_path=self.database_path
        )
        connection = connect(self.database_path)
        try:
            stored_after = connection.execute(
                """
                SELECT parser_name, parser_run_id, manifest_count, manifest_digest
                FROM reference.promotion_readiness_evidence
                WHERE report_id = ? ORDER BY parser_name
                """,
                [report.report_id],
            ).fetchall()
        finally:
            connection.close()

        self.assertIsNotNone(stale)
        self.assertEqual("stale", stale.evidence_status)
        self.assertEqual(
            "Evidence changed for: installed_bookmarks.",
            stale.evidence_detail,
        )
        self.assertEqual(stored_before, stored_after)

    def test_manifest_hash_change_makes_prior_report_stale(self) -> None:
        self._replace_with_current_parser_runs()
        report = generate_promotion_readiness_report(
            "baseline", database_path=self.database_path
        )
        connection = connect(self.database_path)
        try:
            connection.execute(
                """
                UPDATE source.source_files SET sha256 = 'changed-hash'
                WHERE source_group = 'installed_faiths'
                """
            )
        finally:
            connection.close()

        stale = get_latest_promotion_readiness_report(
            "baseline", database_path=self.database_path
        )

        self.assertIsNotNone(stale)
        self.assertEqual("stale", stale.evidence_status)
        self.assertEqual(
            "Evidence changed for: installed_faiths.",
            stale.evidence_detail,
        )

    def test_requires_each_expected_version_on_the_latest_run(self) -> None:
        self._replace_with_current_parser_runs()
        current_report = generate_promotion_readiness_report(
            "baseline", database_path=self.database_path
        )
        current = {finding.code: finding for finding in current_report.findings}
        self.assertEqual("passed", current["required_parsers"].classification)
        self.assertEqual(len(EXPECTED_PARSERS), current["required_parsers"].subject_count)
        self.assertIn("installed_character_history@1.4.0", current["required_parsers"].detail)
        self.assertEqual("passed", current["source_manifests"].classification)
        self.assertEqual(len(EXPECTED_PARSERS), current["source_manifests"].subject_count)

        connection = connect(self.database_path)
        try:
            connection.execute(
                """
                INSERT INTO source.parser_runs
                VALUES ('run:bookmarks:failed', 'snapshot', 'installed_bookmarks',
                        '1.0.0', 'failed', TIMESTAMP '2001-01-01',
                        TIMESTAMP '2001-01-01', NULL, NULL, 'parse failed')
                """
            )
        finally:
            connection.close()
        failed_report = generate_promotion_readiness_report(
            "baseline", database_path=self.database_path
        )
        failed = {finding.code: finding for finding in failed_report.findings}
        self.assertEqual("blocking", failed["required_parsers"].classification)
        self.assertEqual(1, failed["required_parsers"].subject_count)
        self.assertEqual(
            "installed_bookmarks: latest status failed",
            failed["required_parsers"].detail,
        )
        self.assertEqual("blocking", failed["source_manifests"].classification)
        self.assertEqual(
            "installed_bookmarks: 0 of 1 bound to latest run",
            failed["source_manifests"].detail,
        )

        connection = connect(self.database_path)
        try:
            connection.execute(
                "DELETE FROM source.parser_runs WHERE parser_run_id = 'run:bookmarks:failed'"
            )
            connection.execute(
                """
                INSERT INTO source.parser_runs
                VALUES ('run:bookmarks:obsolete', 'snapshot', 'installed_bookmarks',
                        '0.9.0', 'completed', TIMESTAMP '2002-01-01',
                        TIMESTAMP '2002-01-01', 1, 0, NULL)
                """
            )
        finally:
            connection.close()
        obsolete_report = generate_promotion_readiness_report(
            "baseline", database_path=self.database_path
        )
        obsolete = {finding.code: finding for finding in obsolete_report.findings}
        self.assertEqual("blocking", obsolete["required_parsers"].classification)
        self.assertEqual(1, obsolete["required_parsers"].subject_count)
        self.assertEqual(
            "installed_bookmarks: expected 1.1.0, latest 0.9.0",
            obsolete["required_parsers"].detail,
        )
        self.assertEqual("blocking", obsolete["source_manifests"].classification)
        self.assertEqual(
            "installed_bookmarks: 0 of 1 bound to latest run",
            obsolete["source_manifests"].detail,
        )

    def test_missing_manifest_group_blocks_without_rewriting_evidence(self) -> None:
        self._replace_with_current_parser_runs()
        connection = connect(self.database_path)
        try:
            connection.execute(
                "DELETE FROM source.source_files WHERE source_group = 'installed_faiths'"
            )
        finally:
            connection.close()

        report = generate_promotion_readiness_report(
            "baseline", database_path=self.database_path
        )
        findings = {finding.code: finding for finding in report.findings}
        connection = connect(self.database_path)
        try:
            manifest_count = connection.execute(
                "SELECT count(*) FROM source.source_files"
            ).fetchone()[0]
        finally:
            connection.close()

        self.assertEqual("blocking", findings["source_manifests"].classification)
        self.assertEqual(1, findings["source_manifests"].subject_count)
        self.assertEqual("installed_faiths: missing", findings["source_manifests"].detail)
        self.assertEqual(len(EXPECTED_PARSERS) - 1, manifest_count)

    def test_unresolved_bookmark_dlc_flag_blocks_without_mutation(self) -> None:
        connection = connect(self.database_path)
        try:
            connection.execute(
                """
                INSERT INTO reference.bookmark_dlc_requirements
                (reference_snapshot_id, bookmark_id, requirement_kind,
                 requirement_value, resolution_status, validation_note,
                 resolved_package_id)
                VALUES ('snapshot', 'bookmark', 'requires_dlc_flag',
                        'unknown_feature', 'raw_flag',
                        'No reviewed mapping exists', NULL)
                """
            )
        finally:
            connection.close()

        report = generate_promotion_readiness_report(
            "baseline", database_path=self.database_path
        )
        finding = {item.code: item for item in report.findings}["bookmark_dlc_resolution"]
        connection = connect(self.database_path)
        try:
            requirement = connection.execute(
                """
                SELECT requirement_value, resolution_status, resolved_package_id
                FROM reference.bookmark_dlc_requirements
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual("blocking", finding.classification)
        self.assertEqual(1, finding.subject_count)
        self.assertEqual("unknown_feature", finding.detail)
        self.assertEqual(("unknown_feature", "raw_flag", None), requirement)

    def _replace_with_current_parser_runs(self) -> None:
        connection = connect(self.database_path)
        try:
            connection.execute("DELETE FROM source.parser_runs")
            connection.execute("DELETE FROM source.source_files")
            connection.executemany(
                """
                INSERT INTO source.parser_runs
                VALUES (?, 'snapshot', ?, ?, 'completed', TIMESTAMP '2000-01-01',
                        TIMESTAMP '2000-01-01', 1, 0, NULL)
                """,
                [
                    (f"run:{parser_name}:current", parser_name, parser_version)
                    for parser_name, parser_version in EXPECTED_PARSERS.items()
                ],
            )
            connection.executemany(
                """
                INSERT INTO source.source_files
                (reference_snapshot_id, relative_path, source_group, byte_size,
                 modified_at_utc, sha256, parser_run_id)
                VALUES ('snapshot', ?, ?, 1, TIMESTAMP '2000-01-01', 'hash', ?)
                """,
                [
                    (
                        f"common/{parser_name}.txt",
                        parser_name,
                        f"run:{parser_name}:current",
                    )
                    for parser_name in EXPECTED_PARSERS
                ],
            )
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()