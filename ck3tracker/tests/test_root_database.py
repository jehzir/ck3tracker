"""Tests for root database schema bootstrap."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import duckdb

from logic.root_database import connect


class RootDatabaseTests(unittest.TestCase):
    def test_bootstraps_title_baseline_state_faith_boundary(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "tracker.duckdb"
            connection = connect(database_path)
            try:
                columns = connection.execute(
                    "DESCRIBE reference.title_baseline_state_faiths"
                ).fetchall()
                column_contract = {
                    row[0]: (row[1], row[2], row[3]) for row in columns
                }
                self.assertEqual(
                    {
                        "baseline_id": ("VARCHAR", "NO", "PRI"),
                        "title_id": ("VARCHAR", "NO", "PRI"),
                        "reference_snapshot_id": ("VARCHAR", "NO", None),
                        "faith_id": ("VARCHAR", "NO", None),
                        "effective_date": ("DATE", "NO", None),
                        "source_group": ("VARCHAR", "NO", None),
                        "source_declaration_order": ("BIGINT", "NO", None),
                        "validation_status": ("VARCHAR", "NO", None),
                        "validation_note": ("VARCHAR", "YES", None),
                    },
                    column_contract,
                )
                connection.execute(
                    """
                    INSERT INTO source.reference_snapshots
                    (reference_snapshot_id, game_version, map_profile, review_status)
                    VALUES ('snapshot', '1.19.0.6', 'default', 'candidate')
                    """
                )
                connection.execute(
                    """
                    INSERT INTO reference.baselines
                    (baseline_id, reference_snapshot_id, baseline_date, label,
                     support_status)
                    VALUES ('baseline', 'snapshot', '0867-01-01', '867', 'candidate')
                    """
                )
                connection.execute(
                    """
                    INSERT INTO reference.titles
                    (baseline_id, title_id, title_rank, display_name)
                    VALUES ('baseline', 'e_test', 'empire', 'Test Empire')
                    """
                )
                connection.execute(
                    """
                    INSERT INTO reference.faiths
                    VALUES ('snapshot', 'orthodox', 'christianity_religion',
                            'common/religion/faiths/test.txt', 1, 2, 1, '{}',
                            '1.0.0', 'faith', 'valid', NULL)
                    """
                )
                connection.execute(
                    """
                    INSERT INTO reference.title_baseline_state_faiths
                    VALUES ('baseline', 'e_test', 'snapshot', 'orthodox',
                            '0866-01-01', 'title_history', 1, 'valid', NULL)
                    """
                )
                with self.assertRaises(duckdb.ConstraintException):
                    connection.execute(
                        """
                        INSERT INTO reference.title_baseline_state_faiths
                        VALUES ('baseline', 'e_test', 'snapshot', 'orthodox',
                                '0866-01-01', 'title_history', 2, 'valid', NULL)
                        """
                    )
                with self.assertRaises(duckdb.ConstraintException):
                    connection.execute(
                        """
                        INSERT INTO reference.title_baseline_state_faiths
                        VALUES ('baseline', 'e_missing', 'snapshot', 'orthodox',
                                '0866-01-01', 'title_history', 2, 'valid', NULL)
                        """
                    )
                with self.assertRaises(duckdb.ConstraintException):
                    connection.execute(
                        """
                        INSERT INTO reference.title_baseline_state_faiths
                        VALUES ('baseline', 'e_test', 'snapshot', 'missing_faith',
                                '0866-01-01', 'title_history', 2, 'valid', NULL)
                        """
                    )
            finally:
                connection.close()

            connection = connect(database_path)
            try:
                self.assertEqual(
                    (1,),
                    connection.execute(
                        "SELECT count(*) FROM reference.title_baseline_state_faiths"
                    ).fetchone(),
                )
            finally:
                connection.close()

    def test_bootstraps_character_baseline_language_boundary(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "tracker.duckdb"
            connection = connect(database_path)
            try:
                columns = connection.execute(
                    "DESCRIBE reference.character_baseline_languages"
                ).fetchall()
                column_contract = {
                    row[0]: (row[1], row[2], row[3]) for row in columns
                }
                self.assertEqual(
                    {
                        "baseline_id": ("VARCHAR", "NO", "PRI"),
                        "character_id": ("VARCHAR", "NO", "PRI"),
                        "language_id": ("VARCHAR", "NO", "PRI"),
                        "knowledge_kind": ("VARCHAR", "NO", None),
                        "effective_date": ("DATE", "YES", None),
                        "source_group": ("VARCHAR", "NO", None),
                        "source_declaration_order": ("BIGINT", "YES", None),
                        "validation_status": ("VARCHAR", "NO", None),
                        "validation_note": ("VARCHAR", "YES", None),
                    },
                    column_contract,
                )

                connection.execute(
                    """
                    INSERT INTO reference.character_baseline_languages
                    (baseline_id, character_id, language_id, knowledge_kind,
                     source_group, validation_status)
                    VALUES ('baseline', 'character', 'language_test', 'native',
                            'culture', 'valid')
                    """
                )
                with self.assertRaises(duckdb.ConstraintException):
                    connection.execute(
                        """
                        INSERT INTO reference.character_baseline_languages
                        (baseline_id, character_id, language_id, knowledge_kind,
                         source_group, validation_status)
                        VALUES ('baseline', 'character', 'language_test',
                                'history_granted', 'title_history', 'valid')
                        """
                    )
            finally:
                connection.close()

    def test_bootstraps_character_baseline_court_state_boundary(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "tracker.duckdb"
            connection = connect(database_path)
            try:
                columns = connection.execute(
                    "DESCRIBE reference.character_baseline_court_states"
                ).fetchall()
                column_contract = {
                    row[0]: (row[1], row[2], row[3]) for row in columns
                }
                self.assertEqual(
                    {
                        "baseline_id": ("VARCHAR", "NO", "PRI"),
                        "character_id": ("VARCHAR", "NO", "PRI"),
                        "court_language_id": ("VARCHAR", "YES", None),
                        "court_language_effective_date": ("DATE", "YES", None),
                        "court_language_source_declaration_order": (
                            "BIGINT",
                            "YES",
                            None,
                        ),
                        "court_type_id": ("VARCHAR", "YES", None),
                        "court_type_effective_date": ("DATE", "YES", None),
                        "court_type_source_declaration_order": (
                            "BIGINT",
                            "YES",
                            None,
                        ),
                        "validation_status": ("VARCHAR", "NO", None),
                        "validation_note": ("VARCHAR", "YES", None),
                    },
                    column_contract,
                )

                connection.execute(
                    """
                    INSERT INTO reference.character_baseline_court_states
                    (baseline_id, character_id, validation_status)
                    VALUES ('baseline', 'character', 'valid')
                    """
                )
                with self.assertRaises(duckdb.ConstraintException):
                    connection.execute(
                        """
                        INSERT INTO reference.character_baseline_court_states
                        (baseline_id, character_id, validation_status)
                        VALUES ('baseline', 'character', 'valid')
                        """
                    )
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()