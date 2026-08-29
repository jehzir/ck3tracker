"""Tests for confirmed-before-write CK3 save baseline proposals."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZIP_DEFLATED, ZipFile

from logic.root_database import connect
from logic.save_baseline_proposal_service import (
    confirm_save_baseline,
    propose_save_baseline,
)
from tests.test_ck3_save_reader import IDENTITY_GAMESTATE


class SaveBaselineProposalServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        directory = Path(self.temporary_directory.name)
        self.database_path = directory / "tracker.duckdb"
        self.save_path = directory / "example.ck3"
        with ZipFile(self.save_path, "w", ZIP_DEFLATED) as archive:
            archive.writestr("gamestate", IDENTITY_GAMESTATE)
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
                    ("e_japan", "empire", None, "Japan"),
                    ("k_ryukyu", "kingdom", "e_japan", "Ryukyu"),
                    ("d_ruucuu", "duchy", "k_ryukyu", "Ruucuu"),
                    ("c_ucinaa", "county", "d_ruucuu", "Ucinaa"),
                    ("b_simajiri", "barony", "c_ucinaa", "Simajiri"),
                ],
            )
        finally:
            connection.close()

    def test_proposal_matches_promoted_baseline_without_writing(self) -> None:
        proposal = propose_save_baseline(
            self.save_path,
            database_path=self.database_path,
        )

        connection = connect(self.database_path)
        try:
            playthrough_count = connection.execute(
                "SELECT COUNT(*) FROM journal.playthroughs"
            ).fetchone()[0]
        finally:
            connection.close()

        self.assertEqual("scribe", proposal.reference_snapshot_id)
        self.assertEqual("scribe_867", proposal.baseline_id)
        self.assertEqual(date(867, 1, 1), proposal.baseline_date)
        self.assertEqual(date(867, 1, 18), proposal.save_game_date)
        self.assertEqual("c_ucinaa", proposal.primary_title_id)
        self.assertEqual("b_simajiri", proposal.starting_barony_id)
        self.assertEqual("c_ucinaa", proposal.starting_county_id)
        self.assertEqual(0, playthrough_count)

    def test_confirmation_creates_one_atomic_playthrough(self) -> None:
        proposal = propose_save_baseline(
            self.save_path,
            database_path=self.database_path,
        )

        transaction_id = confirm_save_baseline(
            proposal,
            playthrough_id="ucinaa_run",
            database_path=self.database_path,
        )

        connection = connect(self.database_path)
        try:
            context = connection.execute(
                """
                SELECT ruler_character_id, starting_county_id, starting_barony_id
                FROM app.playthrough_context
                WHERE playthrough_id = 'ucinaa_run'
                """
            ).fetchone()
            event_count = connection.execute(
                """
                SELECT COUNT(*) FROM journal.transaction_events
                WHERE transaction_id = ? AND event_type = 'playthrough_created'
                """,
                [transaction_id],
            ).fetchone()[0]
        finally:
            connection.close()

        self.assertEqual(("37862", "c_ucinaa", "b_simajiri"), context)
        self.assertEqual(1, event_count)

    def test_rejects_title_missing_from_reference_without_writing(self) -> None:
        connection = connect(self.database_path)
        try:
            connection.execute(
                """
                DELETE FROM reference.titles
                WHERE baseline_id = 'scribe_867' AND title_id = 'c_ucinaa'
                """
            )
        finally:
            connection.close()

        with self.assertRaisesRegex(ValueError, "absent from.*c_ucinaa"):
            propose_save_baseline(self.save_path, database_path=self.database_path)

        connection = connect(self.database_path)
        try:
            count = connection.execute(
                "SELECT COUNT(*) FROM journal.playthroughs"
            ).fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(0, count)


if __name__ == "__main__":
    unittest.main()