"""Tests for snapshot-scoped installed title localization loading."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from logic.landed_titles_loader import load_landed_titles_candidate
from logic.root_database import connect
from logic.title_localization_loader import load_title_localizations_candidate


class TitleLocalizationLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.game_root = root / "game"
        self.database_path = root / "tracker.duckdb"
        titles = self.game_root / "common" / "landed_titles"
        titles.mkdir(parents=True)
        (titles / "00_titles.txt").write_text(
            """
e_world = {
    k_islands = {
        d_ruucuu = {
            c_ucinaa = {
                b_simajiri = { province = 1 }
                b_missing = { province = 2 }
            }
        }
    }
}
""",
            encoding="utf-8",
        )
        localization = self.game_root / "localization" / "english"
        localization.mkdir(parents=True)
        (localization / "a_titles_l_english.yml").write_text(
            'l_english:\n c_ucinaa:0 "Old Ucinaa"\n b_simajiri:0 "Simajiri"\n',
            encoding="utf-8-sig",
        )
        (localization / "z_override_l_english.yml").write_text(
            'l_english:\n c_ucinaa:1 "Ucinaa"\n d_ruucuu:0 "Ruucuu"\n quote_key:0 "The "Quoted" Name"\n',
            encoding="utf-8-sig",
        )
        (localization / "header_only_l_english.yml").write_text(
            "l_english:\n",
            encoding="utf-8-sig",
        )
        load_landed_titles_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            game_version="1.19.0.6",
            steam_build_id="23530548",
            database_path=self.database_path,
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_resolves_conflict_with_provenance_and_updates_title_labels(self) -> None:
        result = load_title_localizations_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            database_path=self.database_path,
        )

        connection = connect(self.database_path)
        try:
            declarations = connection.execute(
                """
                SELECT display_value, relative_path, is_winner, resolution_status
                FROM source.localization_declarations
                WHERE localization_key = 'c_ucinaa'
                ORDER BY declaration_order
                """
            ).fetchall()
            titles = connection.execute(
                """
                SELECT title_id, localization_key, display_name
                FROM reference.titles
                WHERE title_id IN ('c_ucinaa', 'b_simajiri', 'b_missing')
                ORDER BY title_id
                """
            ).fetchall()
            state = connection.execute(
                """
                SELECT s.review_status, b.support_status, b.historical_state_complete
                FROM source.reference_snapshots s
                JOIN reference.baselines b USING (reference_snapshot_id)
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(
            [
                ("Old Ucinaa", "localization/english/a_titles_l_english.yml", False, "review_required"),
                ("Ucinaa", "localization/english/z_override_l_english.yml", True, "review_required"),
            ],
            declarations,
        )
        self.assertEqual(
            [
                ("b_missing", "b_missing", "Missing"),
                ("b_simajiri", "b_simajiri", "Simajiri"),
                ("c_ucinaa", "c_ucinaa", "Ucinaa"),
            ],
            titles,
        )
        self.assertEqual(("candidate", "candidate", False), state)
        self.assertEqual(5, result.declaration_count)
        self.assertEqual(4, result.localization_count)
        self.assertEqual(1, result.conflict_count)

    def test_candidate_reload_is_idempotent(self) -> None:
        arguments = {
            "game_root": self.game_root,
            "reference_snapshot_id": "scribe_build",
            "database_path": self.database_path,
        }
        load_title_localizations_candidate(**arguments)
        load_title_localizations_candidate(**arguments)

        connection = connect(self.database_path)
        try:
            counts = connection.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM source.localization_declarations),
                    (SELECT COUNT(*) FROM reference.localizations),
                    (SELECT COUNT(*) FROM source.source_files),
                    (SELECT COUNT(*) FROM source.parser_runs)
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual((5, 4, 4, 3), counts)


if __name__ == "__main__":
    unittest.main()