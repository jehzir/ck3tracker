"""Tests for installed landed-title candidate loading and validation."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from logic.landed_titles_loader import load_landed_titles_candidate
from logic.root_database import connect


class LandedTitlesLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.game_root = root / "game"
        self.database_path = root / "tracker.duckdb"
        source = self.game_root / "common" / "landed_titles"
        source.mkdir(parents=True)
        (source / "00_titles.txt").write_text(
            """
e_world = {
    capital = c_ucinaa
    k_islands = {
        d_ruucuu = {
            c_ucinaa = {
                b_simajiri = { province = 1 }
            }
        }
    }
}
c_duplicate = { capital = c_ucinaa }
c_duplicate = { capital = c_other }
e_special = {
    d_special = {
        c_special = {
            b_special = { province = 2 }
        }
    }
}
""",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_loads_candidate_with_provenance_and_selectability(self) -> None:
        result = load_landed_titles_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            game_version="1.19.0.6",
            steam_build_id="23530548",
            database_path=self.database_path,
        )

        connection = connect(self.database_path)
        try:
            ucinaa = connection.execute(
                """
                SELECT parent_title_id, selectable, source_path, validation_status
                FROM reference.titles
                WHERE baseline_id = 'scribe_867' AND title_id = 'c_ucinaa'
                """
            ).fetchone()
            special = connection.execute(
                """
                SELECT selectable, validation_note
                FROM reference.titles
                WHERE baseline_id = 'scribe_867' AND title_id = 'b_special'
                """
            ).fetchone()
            statuses = connection.execute(
                """
                SELECT review_status,
                       (SELECT support_status FROM reference.baselines
                        WHERE baseline_id = 'scribe_867'),
                       (SELECT COUNT(*) FROM source.source_files
                        WHERE reference_snapshot_id = 'scribe_build')
                FROM source.reference_snapshots
                WHERE reference_snapshot_id = 'scribe_build'
                """
            ).fetchone()
            capitals = connection.execute(
                """
                SELECT title_id, declared_capital_title_id,
                       static_capital_title_id, static_capital_status
                FROM reference.titles
                WHERE title_id IN ('e_world', 'c_ucinaa', 'b_simajiri')
                ORDER BY title_id
                """
            ).fetchall()
        finally:
            connection.close()

        self.assertEqual(("d_ruucuu", True, "common/landed_titles/00_titles.txt", "valid"), ucinaa)
        self.assertEqual(False, special[0])
        self.assertIn("non-canonical", special[1])
        self.assertEqual(("candidate", "candidate", 1), statuses)
        self.assertEqual(
            [
                ("b_simajiri", None, None, "not_applicable"),
                ("c_ucinaa", None, "b_simajiri", "derived_first_barony"),
                ("e_world", "c_ucinaa", "c_ucinaa", "declared_static"),
            ],
            capitals,
        )
        self.assertEqual(10, result.title_count)

    def test_candidate_reload_is_idempotent(self) -> None:
        arguments = {
            "game_root": self.game_root,
            "reference_snapshot_id": "scribe_build",
            "baseline_id": "scribe_867",
            "game_version": "1.19.0.6",
            "steam_build_id": "23530548",
            "database_path": self.database_path,
        }
        load_landed_titles_candidate(**arguments)
        load_landed_titles_candidate(**arguments)

        connection = connect(self.database_path)
        try:
            counts = connection.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM reference.titles),
                    (SELECT COUNT(*) FROM source.source_files),
                    (SELECT COUNT(*) FROM source.parser_runs)
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual((10, 1, 2), counts)


if __name__ == "__main__":
    unittest.main()