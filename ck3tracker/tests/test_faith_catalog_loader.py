"""Tests for grounded installed-faith catalog ingestion."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from logic.faith_catalog_loader import WikiPageEvidence, load_faith_catalog_candidate
from logic.promotion_readiness_service import generate_promotion_readiness_report
from logic.root_database import connect


class FaithCatalogLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.game_root = root / "game"
        religions = self.game_root / "common" / "religion" / "religion_types"
        religions.mkdir(parents=True)
        (religions / "00_religions.txt").write_text(
            "christianity_religion = {\n"
            "  family = rf_abrahamic\n"
            "  faiths = {\n"
            "    catholic = { doctrine = doctrine_pluralism_righteous }\n"
            "    orthodox = { doctrine = doctrine_pluralism_righteous }\n"
            "  }\n"
            "}\n",
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
                (baseline_id, character_id, sex, sex_status, faith_id,
                 lifecycle_status, validation_status)
                VALUES ('baseline', 'character', 'male', 'declared', 'catholic',
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
        self.faith_evidence = WikiPageEvidence(
            "faith",
            "https://ck3.paradoxwikis.com/Faith",
            "https://ck3.paradoxwikis.com/index.php?title=Faith&oldid=35751",
            "35751",
            retrieved,
            "1.19",
            "reviewed",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_loads_parent_religion_wiki_provenance_and_coverage(self) -> None:
        arguments = dict(
            game_root=self.game_root,
            reference_snapshot_id="snapshot",
            wiki_root=self.root_evidence,
            wiki_faith=self.faith_evidence,
            database_path=self.database_path,
        )
        load_faith_catalog_candidate(**arguments)
        result = load_faith_catalog_candidate(**arguments)
        report = generate_promotion_readiness_report("baseline", self.database_path)
        findings = {finding.code: finding for finding in report.findings}
        connection = connect(self.database_path)
        try:
            faiths = connection.execute(
                "SELECT faith_id, religion_id, source_path, wiki_page_key FROM reference.faiths ORDER BY faith_id"
            ).fetchall()
            links = connection.execute(
                "SELECT from_page_key, to_page_key, link_text FROM source.wiki_page_links"
            ).fetchall()
            counts = connection.execute(
                "SELECT (SELECT count(*) FROM source.source_files), (SELECT count(*) FROM source.wiki_pages), (SELECT count(*) FROM reference.faiths)"
            ).fetchone()
            connection.execute(
                "UPDATE reference.character_baseline_states SET faith_id = 'missing_faith'"
            )
        finally:
            connection.close()
        missing_report = generate_promotion_readiness_report("baseline", self.database_path)
        missing = {finding.code: finding for finding in missing_report.findings}

        self.assertEqual(2, result.faith_count)
        self.assertEqual(
            [
                ("catholic", "christianity_religion", "common/religion/religion_types/00_religions.txt", "faith"),
                ("orthodox", "christianity_religion", "common/religion/religion_types/00_religions.txt", "faith"),
            ],
            faiths,
        )
        self.assertEqual([("wiki_root", "faith", "Faith")], links)
        self.assertEqual((1, 2, 2), counts)
        self.assertEqual("passed", findings["faith_wiki_provenance"].classification)
        self.assertEqual("passed", findings["faith_catalog"].classification)
        self.assertEqual("blocking", missing["faith_catalog"].classification)
        self.assertEqual(1, missing["faith_catalog"].subject_count)


if __name__ == "__main__":
    unittest.main()