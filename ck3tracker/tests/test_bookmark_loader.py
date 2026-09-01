"""Tests for bookmark collection ingestion and baseline date-profile mapping."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from logic.bookmark_loader import load_bookmarks_candidate
from logic.root_database import connect


class BookmarkLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.game_root = root / "game"
        self.database_path = root / "tracker.duckdb"
        source = self.game_root / "common" / "bookmarks"
        for folder in ("groups", "bookmarks", "challenge_characters"):
            (source / folder).mkdir(parents=True)
            (source / folder / f"_{folder}.info").write_text("info", encoding="utf-8")
        (source / "groups" / "00_bookmark_groups.txt").write_text(
            "bm_group_867 = { default_start_date = 867.1.1 }",
            encoding="utf-8-sig",
        )
        (source / "bookmarks" / "00_bookmarks.txt").write_text(
            """
bm_867_one = {
  group = bm_group_867
  is_playable = yes
  character = {
    name = one_name history_id = person_one title = c_one type = male
    character = { name = relation_name history_id = related_one relation = sibling }
  }
}
bm_867_two = {
  start_date = 867.1.1 group = bm_group_867 is_playable = yes
  requires_dlc_flag = test_dlc
  character = { name = two_name history_id = person_two title = c_two type = female }
}
""",
            encoding="utf-8-sig",
        )
        (source / "challenge_characters" / "00_challenge_characters.txt").write_text(
            "challenge_test = { start_date = 867.1.1 character = { history_id = person_one } }",
            encoding="utf-8-sig",
        )
        royal_court_descriptor = self.game_root / "dlc" / "dlc004_ep1" / "dlc004.dlc"
        royal_court_descriptor.parent.mkdir(parents=True)
        royal_court_descriptor.write_text(
            '''name = "The Royal Court"
path = "dlc/dlc004_ep1"
steam_id = "1303182"
pops_id = "ck3_dlc004_ep1"
msgr_id = "9PDMBMV4J906"
''',
            encoding="utf-8",
        )
        connection = connect(self.database_path)
        try:
            connection.execute(
                "INSERT INTO source.reference_snapshots VALUES ('snapshot', '1.0', '1', 'ck3', 'candidate', current_timestamp)"
            )
            connection.execute(
                "INSERT INTO reference.baselines VALUES ('baseline', 'snapshot', 'bm_867', '0867-01-01', '867', 'candidate', false)"
            )
            for title_id in ("c_one", "c_two"):
                connection.execute(
                    "INSERT INTO reference.titles (baseline_id, title_id, title_rank, display_name) VALUES ('baseline', ?, 'county', ?)",
                    [title_id, title_id],
                )
            for character_id in ("person_one", "person_two"):
                connection.execute(
                    """
                    INSERT INTO reference.character_baseline_states
                    (baseline_id, character_id, sex, sex_status, lifecycle_status,
                     validation_status) VALUES ('baseline', ?, 'male',
                     'inferred_default', 'alive_at_baseline', 'valid')
                    """,
                    [character_id],
                )
            for key in ("one_name", "two_name"):
                connection.execute(
                    """
                    INSERT INTO reference.localizations
                    VALUES ('snapshot', 'english', ?, NULL, ?, 'test.yml', 1,
                            'test', 'valid')
                    """,
                    [key, key],
                )
        finally:
            connection.close()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_links_all_same_date_bookmarks_without_synthetic_identity(self) -> None:
        result = load_bookmarks_candidate(
            game_root=self.game_root,
            reference_snapshot_id="snapshot",
            baseline_id="baseline",
            database_path=self.database_path,
        )
        connection = connect(self.database_path)
        try:
            baseline = connection.execute(
                "SELECT bookmark_id, support_status, historical_state_complete FROM reference.baselines"
            ).fetchone()
            links = connection.execute(
                "SELECT bookmark_id FROM reference.baseline_bookmarks ORDER BY bookmark_id"
            ).fetchall()
            characters = connection.execute(
                """
                SELECT bookmark_id, character_ordinal, parent_character_ordinal,
                       character_kind, validation_status
                FROM reference.bookmark_featured_characters
                ORDER BY bookmark_id, character_ordinal
                """
            ).fetchall()
            dlc = connection.execute(
                "SELECT bookmark_id, requirement_value, resolution_status FROM reference.bookmark_dlc_requirements"
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual((None, "candidate", False), baseline)
        self.assertEqual([("bm_867_one",), ("bm_867_two",)], links)
        self.assertEqual(
            [
                ("bm_867_one", 1, None, "featured", "valid"),
                ("bm_867_one", 2, 1, "related", "valid"),
                ("bm_867_two", 1, None, "featured", "valid"),
            ],
            characters,
        )
        self.assertEqual(("bm_867_two", "test_dlc", "raw_flag"), dlc)
        self.assertEqual(2, result.baseline_bookmark_count)

    def test_candidate_reload_is_idempotent(self) -> None:
        arguments = {
            "game_root": self.game_root,
            "reference_snapshot_id": "snapshot",
            "baseline_id": "baseline",
            "database_path": self.database_path,
        }
        load_bookmarks_candidate(**arguments)
        load_bookmarks_candidate(**arguments)
        connection = connect(self.database_path)
        try:
            counts = connection.execute(
                """
                SELECT
                  (SELECT count(*) FROM reference.bookmark_groups),
                  (SELECT count(*) FROM reference.bookmarks),
                  (SELECT count(*) FROM reference.baseline_bookmarks),
                  (SELECT count(*) FROM reference.bookmark_featured_characters),
                  (SELECT count(*) FROM source.parser_runs)
                """
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual((1, 2, 2, 3, 2), counts)

    def test_resolves_reviewed_feature_to_installed_package(self) -> None:
        bookmark_path = self.game_root / "common" / "bookmarks" / "bookmarks" / "00_bookmarks.txt"
        bookmark_path.write_text(
            bookmark_path.read_text(encoding="utf-8-sig").replace(
                "requires_dlc_flag = test_dlc",
                "requires_dlc_flag = landless_adventurer",
            ),
            encoding="utf-8-sig",
        )
        descriptor = self.game_root / "dlc" / "dlc014_ep3" / "dlc014.dlc"
        descriptor.parent.mkdir(parents=True)
        descriptor.write_text(
            '''name = "Roads to Power"
path = "dlc/dlc014_ep3"
steam_id = "2671070"
pops_id = "ck3_dlc014_ep3"
msgr_id = "9PHT1PQ17BJ1"
''',
            encoding="utf-8",
        )

        load_bookmarks_candidate(
            game_root=self.game_root,
            reference_snapshot_id="snapshot",
            baseline_id="baseline",
            database_path=self.database_path,
        )
        connection = connect(self.database_path)
        try:
            requirement = connection.execute(
                """
                SELECT requirement_value, resolution_status, resolved_package_id
                FROM reference.bookmark_dlc_requirements
                """
            ).fetchone()
            package = connection.execute(
                """
                SELECT package_id, display_name, steam_id, pops_id,
                       wiki_revision_id, validation_status
                FROM reference.dlc_packages
                WHERE package_id = 'dlc014_ep3'
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(
            ("landless_adventurer", "resolved", "dlc014_ep3"), requirement
        )
        self.assertEqual(
            (
                "dlc014_ep3",
                "Roads to Power",
                "2671070",
                "ck3_dlc014_ep3",
                "33550",
                "valid",
            ),
            package,
        )

    def test_loads_required_royal_court_feature_without_bookmark_requirement(self) -> None:
        load_bookmarks_candidate(
            game_root=self.game_root,
            reference_snapshot_id="snapshot",
            baseline_id="baseline",
            database_path=self.database_path,
        )
        connection = connect(self.database_path)
        try:
            mapping = connection.execute(
                """
                SELECT mapping.feature_flag, mapping.package_id,
                       mapping.review_status, package.display_name,
                       package.steam_id, package.pops_id,
                       package.wiki_revision_id, package.validation_status
                FROM reference.dlc_feature_mappings mapping
                JOIN reference.dlc_packages package
                  ON package.reference_snapshot_id = mapping.reference_snapshot_id
                 AND package.package_id = mapping.package_id
                WHERE mapping.reference_snapshot_id = 'snapshot'
                  AND mapping.feature_flag = 'royal_court'
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(
            (
                "royal_court",
                "dlc004_ep1",
                "reviewed",
                "The Royal Court",
                "1303182",
                "ck3_dlc004_ep1",
                "35819",
                "valid",
            ),
            mapping,
        )


if __name__ == "__main__":
    unittest.main()