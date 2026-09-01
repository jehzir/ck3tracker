"""Tests for grounded installed-culture catalog ingestion."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from logic.culture_catalog_loader import WikiPageEvidence, load_culture_catalog_candidate
from logic.promotion_readiness_service import generate_promotion_readiness_report
from logic.root_database import connect


class CultureCatalogLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.game_root = root / "game"
        cultures = self.game_root / "common" / "culture" / "cultures"
        cultures.mkdir(parents=True)
        (cultures / "00_cultures.txt").write_text(
            "norse = { ethos = ethos_bellicose language = language_norse }\n"
            "irish = { ethos = ethos_courtly language = language_goidelic }\n",
            encoding="utf-8-sig",
        )
        pillars = self.game_root / "common" / "culture" / "pillars"
        pillars.mkdir(parents=True)
        (pillars / "00_language.txt").write_text(
            "language_norse = { type = language color = norse }\n"
            "language_goidelic = { type = language color = irish }\n",
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
                (baseline_id, character_id, sex, sex_status, culture_id,
                 lifecycle_status, validation_status)
                VALUES ('baseline', 'character', 'male', 'declared', 'norse',
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
        self.culture_evidence = WikiPageEvidence(
            "culture",
            "https://ck3.paradoxwikis.com/Culture",
            "https://ck3.paradoxwikis.com/index.php?title=Culture&oldid=35845",
            "35845",
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
            wiki_culture=self.culture_evidence,
            database_path=self.database_path,
        )
        load_culture_catalog_candidate(**arguments)
        result = load_culture_catalog_candidate(**arguments)
        report = generate_promotion_readiness_report("baseline", self.database_path)
        findings = {finding.code: finding for finding in report.findings}
        connection = connect(self.database_path)
        try:
            cultures = connection.execute(
                "SELECT culture_id, source_path, wiki_page_key FROM reference.cultures ORDER BY culture_id"
            ).fetchall()
            languages = connection.execute(
                """
                SELECT language_id, source_path
                FROM reference.languages ORDER BY language_id
                """
            ).fetchall()
            native_languages = connection.execute(
                """
                SELECT culture_id, language_id, source_path,
                       source_declaration_order
                FROM reference.culture_native_languages ORDER BY culture_id
                """
            ).fetchall()
            links = connection.execute(
                "SELECT from_page_key, to_page_key, link_text FROM source.wiki_page_links"
            ).fetchall()
            counts = connection.execute(
                "SELECT (SELECT count(*) FROM source.source_files), (SELECT count(*) FROM source.wiki_pages), (SELECT count(*) FROM reference.cultures)"
            ).fetchone()
            connection.execute(
                "UPDATE reference.character_baseline_states SET culture_id = 'missing_culture'"
            )
        finally:
            connection.close()
        missing_report = generate_promotion_readiness_report("baseline", self.database_path)
        missing = {finding.code: finding for finding in missing_report.findings}

        self.assertEqual(2, result.culture_count)
        self.assertEqual(
            [
                ("irish", "common/culture/cultures/00_cultures.txt", "culture"),
                ("norse", "common/culture/cultures/00_cultures.txt", "culture"),
            ],
            cultures,
        )
        self.assertEqual([("wiki_root", "culture", "Culture")], links)
        self.assertEqual((2, 2, 2), counts)
        self.assertEqual(
            [
                ("language_goidelic", "common/culture/pillars/00_language.txt"),
                ("language_norse", "common/culture/pillars/00_language.txt"),
            ],
            languages,
        )
        self.assertEqual(
            [
                ("irish", "language_goidelic",
                 "common/culture/cultures/00_cultures.txt", 2),
                ("norse", "language_norse",
                 "common/culture/cultures/00_cultures.txt", 1),
            ],
            native_languages,
        )
        self.assertEqual("passed", findings["culture_wiki_provenance"].classification)
        self.assertEqual("passed", findings["culture_catalog"].classification)
        self.assertEqual("blocking", missing["culture_catalog"].classification)
        self.assertEqual(1, missing["culture_catalog"].subject_count)

    def test_rejects_unresolved_native_language_before_replacing_catalog(self) -> None:
        load_culture_catalog_candidate(
            game_root=self.game_root,
            reference_snapshot_id="snapshot",
            wiki_root=self.root_evidence,
            wiki_culture=self.culture_evidence,
            database_path=self.database_path,
        )
        culture_path = (
            self.game_root / "common" / "culture" / "cultures" / "00_cultures.txt"
        )
        culture_path.write_text(
            "norse = { language = language_missing }\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "Unresolved native language"):
            load_culture_catalog_candidate(
                game_root=self.game_root,
                reference_snapshot_id="snapshot",
                wiki_root=self.root_evidence,
                wiki_culture=self.culture_evidence,
                database_path=self.database_path,
            )

        connection = connect(self.database_path)
        try:
            counts = connection.execute(
                """
                SELECT (SELECT count(*) FROM reference.cultures),
                       (SELECT count(*) FROM reference.languages),
                       (SELECT count(*) FROM reference.culture_native_languages)
                """
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual((2, 2, 2), counts)


if __name__ == "__main__":
    unittest.main()