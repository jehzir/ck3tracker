"""Tests for grounded installed-dynasty catalog ingestion."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from logic.dynasty_catalog_loader import WikiPageEvidence, load_dynasty_catalog_candidate
from logic.promotion_readiness_service import generate_promotion_readiness_report
from logic.root_database import connect


class DynastyCatalogLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.game_root = root / "game"
        dynasties = self.game_root / "common" / "dynasties"
        dynasties.mkdir(parents=True)
        (dynasties / "00_dynasties.txt").write_text(
            "2 = { name = dynn_numeric culture = italian }\n"
            "custom_dynasty = { name = dynn_symbolic culture = norman }\n",
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
                (baseline_id, character_id, sex, sex_status, dynasty_id,
                 lifecycle_status, validation_status)
                VALUES ('baseline', 'character', 'male', 'declared', '2',
                        'unknown', 'valid')
                """
            )
        finally:
            connection.close()
        retrieved = datetime(2026, 8, 29, tzinfo=timezone.utc)
        self.root_evidence = WikiPageEvidence(
            "wiki_root",
            "https://ck3.paradoxwikis.com/Crusader_Kings_III_Wiki",
            "https://ck3.paradoxwikis.com/index.php?title=Crusader_Kings_III_Wiki&oldid=32094",
            "32094",
            retrieved,
            None,
            "reviewed",
        )
        self.dynasty_evidence = WikiPageEvidence(
            "dynasty",
            "https://ck3.paradoxwikis.com/Dynasty",
            "https://ck3.paradoxwikis.com/index.php?title=Dynasty&oldid=35828",
            "35828",
            retrieved,
            "1.19",
            "reviewed",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_loads_wiki_provenance_and_stable_id_coverage(self) -> None:
        arguments = dict(
            game_root=self.game_root,
            reference_snapshot_id="snapshot",
            wiki_root=self.root_evidence,
            wiki_dynasty=self.dynasty_evidence,
            database_path=self.database_path,
        )
        load_dynasty_catalog_candidate(**arguments)
        result = load_dynasty_catalog_candidate(**arguments)
        report = generate_promotion_readiness_report("baseline", self.database_path)
        findings = {finding.code: finding for finding in report.findings}
        connection = connect(self.database_path)
        try:
            dynasties = connection.execute(
                "SELECT dynasty_id, source_path, wiki_page_key FROM reference.dynasties ORDER BY source_order"
            ).fetchall()
            links = connection.execute(
                "SELECT from_page_key, to_page_key, link_text FROM source.wiki_page_links"
            ).fetchall()
            counts = connection.execute(
                "SELECT (SELECT count(*) FROM source.source_files), (SELECT count(*) FROM source.wiki_pages), (SELECT count(*) FROM reference.dynasties)"
            ).fetchone()
            connection.execute(
                "UPDATE reference.character_baseline_states SET dynasty_id = 'missing_dynasty'"
            )
        finally:
            connection.close()
        missing_report = generate_promotion_readiness_report("baseline", self.database_path)
        missing = {finding.code: finding for finding in missing_report.findings}

        self.assertEqual(2, result.dynasty_count)
        self.assertEqual(
            [
                ("2", "common/dynasties/00_dynasties.txt", "dynasty"),
                ("custom_dynasty", "common/dynasties/00_dynasties.txt", "dynasty"),
            ],
            dynasties,
        )
        self.assertEqual([("wiki_root", "dynasty", "Dynasty")], links)
        self.assertEqual((1, 2, 2), counts)
        self.assertEqual("passed", findings["dynasty_wiki_provenance"].classification)
        self.assertEqual("passed", findings["dynasty_catalog"].classification)
        self.assertEqual("blocking", missing["dynasty_catalog"].classification)
        self.assertEqual(1, missing["dynasty_catalog"].subject_count)

    def test_rejects_duplicate_ids_without_replacing_loaded_rows(self) -> None:
        arguments = dict(
            game_root=self.game_root,
            reference_snapshot_id="snapshot",
            wiki_root=self.root_evidence,
            wiki_dynasty=self.dynasty_evidence,
            database_path=self.database_path,
        )
        load_dynasty_catalog_candidate(**arguments)
        duplicate_path = self.game_root / "common" / "dynasties" / "01_duplicate.txt"
        duplicate_path.write_text("2 = { name = dynn_duplicate }\n", encoding="utf-8-sig")

        with self.assertRaisesRegex(ValueError, "Duplicate dynasty ID: 2"):
            load_dynasty_catalog_candidate(**arguments)

        connection = connect(self.database_path)
        try:
            dynasty_ids = connection.execute(
                "SELECT dynasty_id FROM reference.dynasties ORDER BY source_order"
            ).fetchall()
        finally:
            connection.close()
        self.assertEqual([("2",), ("custom_dynasty",)], dynasty_ids)


if __name__ == "__main__":
    unittest.main()