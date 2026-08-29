"""Tests for grounded installed dynasty-house catalog ingestion."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from logic.dynasty_house_catalog_loader import (
    WikiPageEvidence,
    load_dynasty_house_catalog_candidate,
)
from logic.promotion_readiness_service import generate_promotion_readiness_report
from logic.root_database import connect


class DynastyHouseCatalogLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.game_root = root / "game"
        self.houses = self.game_root / "common" / "dynasty_houses"
        self.houses.mkdir(parents=True)
        (self.houses / "00_dynasty_houses.txt").write_text(
            "12319 = { name = dynn_numeric dynasty = 25061 }\n"
            "house_symbolic = { name = dynn_symbolic dynasty = symbolic_dynasty }\n",
            encoding="utf-8-sig",
        )
        self.database_path = root / "tracker.duckdb"
        connection = connect(self.database_path)
        try:
            connection.execute(
                "INSERT INTO source.reference_snapshots VALUES ('snapshot', '1.19.0.6', '23530548', 'ck3', 'candidate', current_timestamp)"
            )
            connection.execute(
                "INSERT INTO reference.baselines VALUES ('baseline', 'snapshot', NULL, '0867-01-01', '867', 'candidate', false)"
            )
            connection.execute(
                """
                INSERT INTO reference.character_baseline_states
                (baseline_id, character_id, sex, sex_status, dynasty_house_id,
                 lifecycle_status, validation_status)
                VALUES ('baseline', 'character', 'male', 'declared', '12319',
                        'unknown', 'valid')
                """
            )
            connection.executemany(
                """
                INSERT INTO reference.dynasties
                (reference_snapshot_id, dynasty_id, source_path,
                 source_line_start, source_line_end, source_order, raw_script,
                 parser_version, wiki_page_key, validation_status)
                VALUES (?, ?, 'common/dynasties/test.txt', 1, 1, ?, '{}',
                        'test', 'dynasty', 'valid')
                """,
                [("snapshot", "25061", 1), ("snapshot", "symbolic_dynasty", 2)],
            )
        finally:
            connection.close()
        retrieved = datetime(2026, 8, 29, tzinfo=timezone.utc)
        self.dynasty_evidence = WikiPageEvidence(
            "dynasty",
            "https://ck3.paradoxwikis.com/Dynasty",
            "https://ck3.paradoxwikis.com/index.php?title=Dynasty&oldid=35828",
            "35828",
            retrieved,
            "1.19",
            "reviewed",
        )
        self.house_evidence = WikiPageEvidence(
            "house",
            "https://ck3.paradoxwikis.com/Dynasty#Houses",
            "https://ck3.paradoxwikis.com/index.php?title=Dynasty&oldid=35828#Houses",
            "35828",
            retrieved,
            "1.19",
            "reviewed",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _arguments(self) -> dict[str, object]:
        return {
            "game_root": self.game_root,
            "reference_snapshot_id": "snapshot",
            "wiki_dynasty": self.dynasty_evidence,
            "wiki_house": self.house_evidence,
            "database_path": self.database_path,
        }

    def test_loads_parent_dynasties_provenance_and_coverage(self) -> None:
        load_dynasty_house_catalog_candidate(**self._arguments())
        result = load_dynasty_house_catalog_candidate(**self._arguments())
        report = generate_promotion_readiness_report("baseline", self.database_path)
        findings = {finding.code: finding for finding in report.findings}
        connection = connect(self.database_path)
        try:
            houses = connection.execute(
                "SELECT dynasty_house_id, dynasty_id, source_path, wiki_page_key FROM reference.dynasty_houses ORDER BY source_order"
            ).fetchall()
            links = connection.execute(
                "SELECT from_page_key, to_page_key, link_text FROM source.wiki_page_links"
            ).fetchall()
            counts = connection.execute(
                "SELECT (SELECT count(*) FROM source.source_files), (SELECT count(*) FROM source.wiki_pages), (SELECT count(*) FROM reference.dynasty_houses)"
            ).fetchone()
            connection.execute(
                "UPDATE reference.character_baseline_states SET dynasty_house_id = 'missing_house'"
            )
        finally:
            connection.close()
        missing_report = generate_promotion_readiness_report("baseline", self.database_path)
        missing = {finding.code: finding for finding in missing_report.findings}

        self.assertEqual(2, result.dynasty_house_count)
        self.assertEqual(
            [
                ("12319", "25061", "common/dynasty_houses/00_dynasty_houses.txt", "house"),
                ("house_symbolic", "symbolic_dynasty", "common/dynasty_houses/00_dynasty_houses.txt", "house"),
            ],
            houses,
        )
        self.assertEqual([("dynasty", "house", "Houses")], links)
        self.assertEqual((1, 2, 2), counts)
        self.assertEqual("passed", findings["house_wiki_provenance"].classification)
        self.assertEqual("passed", findings["house_catalog"].classification)
        self.assertEqual("blocking", missing["house_catalog"].classification)
        self.assertEqual(1, missing["house_catalog"].subject_count)

    def test_rejects_duplicate_ids_without_replacing_loaded_rows(self) -> None:
        load_dynasty_house_catalog_candidate(**self._arguments())
        (self.houses / "01_duplicate.txt").write_text(
            "12319 = { name = dynn_duplicate dynasty = 25061 }\n",
            encoding="utf-8-sig",
        )

        with self.assertRaisesRegex(ValueError, "Duplicate dynasty-house ID: 12319"):
            load_dynasty_house_catalog_candidate(**self._arguments())

        self._assert_loaded_ids_unchanged()

    def test_rejects_unresolved_parent_without_replacing_loaded_rows(self) -> None:
        load_dynasty_house_catalog_candidate(**self._arguments())
        (self.houses / "00_dynasty_houses.txt").write_text(
            "12319 = { name = dynn_numeric dynasty = missing_dynasty }\n",
            encoding="utf-8-sig",
        )

        with self.assertRaisesRegex(ValueError, "Unresolved parent dynasty IDs: missing_dynasty"):
            load_dynasty_house_catalog_candidate(**self._arguments())

        self._assert_loaded_ids_unchanged()

    def _assert_loaded_ids_unchanged(self) -> None:
        connection = connect(self.database_path)
        try:
            house_ids = connection.execute(
                "SELECT dynasty_house_id FROM reference.dynasty_houses ORDER BY source_order"
            ).fetchall()
        finally:
            connection.close()
        self.assertEqual([("12319",), ("house_symbolic",)], house_ids)


if __name__ == "__main__":
    unittest.main()