"""Tests for grounded installed-government catalog ingestion."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from logic.government_catalog_loader import WikiPageEvidence, load_government_catalog_candidate
from logic.promotion_readiness_service import generate_promotion_readiness_report
from logic.root_database import connect


class GovernmentCatalogLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.game_root = root / "game"
        governments = self.game_root / "common" / "governments"
        governments.mkdir(parents=True)
        (governments / "00_governments.txt").write_text(
            "feudal_government = { primary_holding = castle_holding }\n"
            "tribal_government = { primary_holding = tribal_holding }\n",
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
                INSERT INTO reference.title_baseline_states
                (baseline_id, title_id, holder_status, liege_status, government_id,
                 government_status, development_status, capital_status, validation_status)
                VALUES ('baseline', 'c_test', 'no_declaration', 'no_declaration',
                        'feudal_government', 'declared', 'no_declaration',
                        'derived_first_barony', 'valid')
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
        self.government_evidence = WikiPageEvidence(
            "government",
            "https://ck3.paradoxwikis.com/Government",
            "https://ck3.paradoxwikis.com/index.php?title=Government&oldid=35874",
            "35874",
            retrieved,
            "1.19",
            "reviewed",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_loads_linked_wiki_provenance_and_validates_coverage(self) -> None:
        arguments = dict(
            game_root=self.game_root,
            reference_snapshot_id="snapshot",
            wiki_root=self.root_evidence,
            wiki_government=self.government_evidence,
            database_path=self.database_path,
        )
        load_government_catalog_candidate(**arguments)
        result = load_government_catalog_candidate(**arguments)
        report = generate_promotion_readiness_report("baseline", self.database_path)
        findings = {finding.code: finding for finding in report.findings}
        connection = connect(self.database_path)
        try:
            governments = connection.execute(
                "SELECT government_id, source_path, wiki_page_key FROM reference.governments ORDER BY government_id"
            ).fetchall()
            links = connection.execute(
                "SELECT from_page_key, to_page_key, link_text FROM source.wiki_page_links"
            ).fetchall()
            counts = connection.execute(
                "SELECT (SELECT count(*) FROM source.source_files), (SELECT count(*) FROM source.wiki_pages), (SELECT count(*) FROM reference.governments)"
            ).fetchone()
            connection.execute(
                "UPDATE reference.title_baseline_states SET government_id = 'missing_government'"
            )
        finally:
            connection.close()
        missing_report = generate_promotion_readiness_report("baseline", self.database_path)
        missing = {finding.code: finding for finding in missing_report.findings}

        self.assertEqual(2, result.government_count)
        self.assertEqual(
            [
                ("feudal_government", "common/governments/00_governments.txt", "government"),
                ("tribal_government", "common/governments/00_governments.txt", "government"),
            ],
            governments,
        )
        self.assertEqual([("wiki_root", "government", "Government")], links)
        self.assertEqual((1, 2, 2), counts)
        self.assertEqual("passed", findings["wiki_provenance"].classification)
        self.assertEqual("passed", findings["government_catalog"].classification)
        self.assertEqual("blocking", missing["government_catalog"].classification)
        self.assertEqual(1, missing["government_catalog"].subject_count)


if __name__ == "__main__":
    unittest.main()
