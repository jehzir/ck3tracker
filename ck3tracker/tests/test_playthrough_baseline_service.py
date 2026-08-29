"""Focused tests for baseline selection and playthrough creation."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from logic.playthrough_baseline_service import create_playthrough_baseline
from logic.reference_catalog_provider import get_location_options, get_supported_baselines
from logic.root_database import connect


class PlaythroughBaselineServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "tracker.duckdb"
        self._seed_reference_data()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _seed_reference_data(self) -> None:
        connection = connect(self.database_path)
        try:
            connection.execute(
                """
                INSERT INTO source.reference_snapshots
                (reference_snapshot_id, game_version, map_profile, review_status)
                VALUES ('scribe', '1.19.0.6', 'ck3', 'promoted')
                """
            )
            connection.execute(
                """
                INSERT INTO reference.baselines
                (baseline_id, reference_snapshot_id, bookmark_id, baseline_date,
                 label, support_status, historical_state_complete)
                VALUES ('scribe_867', 'scribe', 'bm_867', DATE '0867-01-01',
                        '867', 'promoted', true)
                """
            )
            connection.executemany(
                """
                INSERT INTO reference.titles
                (baseline_id, title_id, title_rank, parent_title_id, display_name)
                VALUES ('scribe_867', ?, ?, ?, ?)
                """,
                [
                    ("e_scandinavia", "empire", None, "Scandinavia"),
                    ("k_finland", "kingdom", "e_scandinavia", "Finland"),
                    ("d_finland", "duchy", "k_finland", "Finland"),
                    ("c_nyland", "county", "d_finland", "Nyland"),
                    ("b_porvoo", "barony", "c_nyland", "Porvoo"),
                ],
            )
        finally:
            connection.close()

    def test_lists_only_promoted_baselines_and_filtered_locations(self) -> None:
        baselines = get_supported_baselines(self.database_path)
        counties = get_location_options(
            "scribe_867", "county", "d_finland", "nyl", self.database_path
        )

        self.assertEqual(["scribe_867"], [row["baseline_id"] for row in baselines])
        self.assertEqual(["c_nyland"], [row["value"] for row in counties])

    def test_creates_playthrough_context_and_event_atomically(self) -> None:
        transaction_id = create_playthrough_baseline(
            playthrough_id="finland_run",
            reference_snapshot_id="scribe",
            baseline_id="scribe_867",
            starting_title_id="b_porvoo",
            ruler_name="Example Ruler",
            source="manual_test",
            database_path=self.database_path,
        )

        connection = connect(self.database_path)
        try:
            context = connection.execute(
                """
                SELECT starting_empire_id, starting_kingdom_id, starting_duchy_id,
                       starting_county_id, starting_barony_id
                FROM app.playthrough_context
                WHERE playthrough_id = 'finland_run'
                """
            ).fetchone()
            event = connection.execute(
                """
                SELECT event_type, transaction_id
                FROM journal.transaction_events
                WHERE playthrough_id = 'finland_run'
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(
            ("e_scandinavia", "k_finland", "d_finland", "c_nyland", "b_porvoo"),
            context,
        )
        self.assertEqual(("playthrough_created", transaction_id), event)

    def test_rejects_unsupported_baseline_without_partial_rows(self) -> None:
        with self.assertRaisesRegex(ValueError, "not promoted"):
            create_playthrough_baseline(
                playthrough_id="invalid_run",
                reference_snapshot_id="other_snapshot",
                baseline_id="scribe_867",
                starting_title_id="c_nyland",
                ruler_name="Example Ruler",
                database_path=self.database_path,
            )

        connection = connect(self.database_path)
        try:
            count = connection.execute(
                "SELECT COUNT(*) FROM journal.playthroughs"
            ).fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(0, count)

    def test_duplicate_playthrough_rolls_back_baseline_and_event(self) -> None:
        arguments = {
            "playthrough_id": "duplicate_run",
            "reference_snapshot_id": "scribe",
            "baseline_id": "scribe_867",
            "starting_title_id": "c_nyland",
            "ruler_name": "Example Ruler",
            "database_path": self.database_path,
        }
        create_playthrough_baseline(**arguments)

        with self.assertRaises(Exception):
            create_playthrough_baseline(**arguments)

        connection = connect(self.database_path)
        try:
            counts = connection.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM journal.playthroughs),
                    (SELECT COUNT(*) FROM journal.playthrough_baselines),
                    (SELECT COUNT(*) FROM journal.transaction_events)
                """
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual((1, 1, 1), counts)


if __name__ == "__main__":
    unittest.main()