"""Tests for root database schema bootstrap."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import duckdb

from logic.root_database import connect


class RootDatabaseTests(unittest.TestCase):
    def test_bootstraps_character_nickname_storage_boundary(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "tracker.duckdb"
            connection = connect(database_path)
            try:
                nickname_columns = {
                    row[0]: (row[1], row[2], row[3])
                    for row in connection.execute(
                        "DESCRIBE reference.nicknames"
                    ).fetchall()
                }
                event_columns = {
                    row[0]: (row[1], row[2], row[3])
                    for row in connection.execute(
                        "DESCRIBE reference.character_nickname_events"
                    ).fetchall()
                }
                state_columns = {
                    row[0]: (row[1], row[2], row[3])
                    for row in connection.execute(
                        "DESCRIBE reference.character_baseline_nickname_states"
                    ).fetchall()
                }
                self.assertEqual(
                    {
                        "reference_snapshot_id": ("VARCHAR", "NO", "PRI"),
                        "nickname_id": ("VARCHAR", "NO", "PRI"),
                        "is_bad": ("BOOLEAN", "NO", None),
                        "is_prefix": ("BOOLEAN", "NO", None),
                        "localization_language": ("VARCHAR", "NO", None),
                        "localization_key": ("VARCHAR", "NO", None),
                        "display_name": ("VARCHAR", "NO", None),
                        "definition_source_path": ("VARCHAR", "NO", None),
                        "definition_source_line_start": ("INTEGER", "NO", None),
                        "definition_source_line_end": ("INTEGER", "NO", None),
                        "definition_source_order": ("BIGINT", "NO", None),
                        "raw_script": ("VARCHAR", "NO", None),
                        "localization_source_path": ("VARCHAR", "NO", None),
                        "localization_source_line": ("INTEGER", "NO", None),
                        "parser_version": ("VARCHAR", "NO", None),
                        "validation_status": ("VARCHAR", "NO", None),
                        "validation_note": ("VARCHAR", "YES", None),
                    },
                    nickname_columns,
                )
                self.assertEqual(
                    {
                        "reference_snapshot_id": ("VARCHAR", "NO", "PRI"),
                        "character_id": ("VARCHAR", "NO", "PRI"),
                        "source_group": ("VARCHAR", "NO", "PRI"),
                        "source_declaration_order": ("BIGINT", "NO", "PRI"),
                        "source_operation_order": ("INTEGER", "NO", "PRI"),
                        "effective_date": ("VARCHAR", "NO", None),
                        "event_kind": ("VARCHAR", "NO", None),
                        "nickname_id": ("VARCHAR", "YES", None),
                        "source_path": ("VARCHAR", "NO", None),
                        "source_line_start": ("INTEGER", "NO", None),
                        "source_line_end": ("INTEGER", "NO", None),
                        "validation_status": ("VARCHAR", "NO", None),
                        "validation_note": ("VARCHAR", "YES", None),
                    },
                    event_columns,
                )
                self.assertEqual(
                    {
                        "baseline_id": ("VARCHAR", "NO", "PRI"),
                        "character_id": ("VARCHAR", "NO", "PRI"),
                        "reference_snapshot_id": ("VARCHAR", "NO", None),
                        "active_nickname_id": ("VARCHAR", "YES", None),
                        "last_event_kind": ("VARCHAR", "NO", None),
                        "effective_date": ("VARCHAR", "NO", None),
                        "source_group": ("VARCHAR", "NO", None),
                        "source_declaration_order": ("BIGINT", "NO", None),
                        "source_operation_order": ("INTEGER", "NO", None),
                        "validation_status": ("VARCHAR", "NO", None),
                        "validation_note": ("VARCHAR", "YES", None),
                    },
                    state_columns,
                )

                connection.execute(
                    """
                    INSERT INTO source.reference_snapshots
                    (reference_snapshot_id, game_version, map_profile, review_status)
                    VALUES
                        ('snapshot', '1.19.0.6', 'default', 'candidate'),
                        ('other_snapshot', '1.19.0.6', 'default', 'candidate')
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
                    INSERT INTO reference.character_baseline_states
                    (baseline_id, character_id, sex, sex_status, lifecycle_status,
                     validation_status)
                    VALUES ('baseline', 'character', 'male', 'defaulted', 'alive',
                            'valid')
                    """
                )
                connection.execute(
                    """
                    INSERT INTO source.character_history_declarations
                    (reference_snapshot_id, declaration_order, character_id,
                     effective_date, operation_order, operation_key, value_kind,
                     scalar_value, raw_script, source_path, source_line_start,
                     source_line_end, encoding_name, parser_version,
                     resolution_status)
                    VALUES
                        ('snapshot', 1, 'character', '0860-01-01', 1,
                         'give_nickname', 'scalar', 'nick_test',
                         'give_nickname = nick_test', 'history/test.txt', 10, 10,
                         'utf-8', '1.8.0', 'preserved'),
                        ('snapshot', 2, 'character', '0861-01-01', 1,
                         'remove_nickname', 'scalar', 'yes',
                         'remove_nickname = yes', 'history/test.txt', 11, 11,
                         'utf-8', '1.8.0', 'preserved')
                    """
                )
                connection.execute(
                    """
                    INSERT INTO reference.localizations
                    VALUES ('snapshot', 'english', 'nick_test', 0, 'the Test',
                            'localization/english/test.yml', 1, '1.0.0',
                            'resolved')
                    """
                )
                connection.execute(
                    """
                    INSERT INTO reference.nicknames
                    VALUES ('snapshot', 'nick_test', false, false, 'english',
                            'nick_test', 'the Test', 'common/nicknames/test.txt',
                            1, 3, 1, '{}', 'localization/english/test.yml', 1,
                            '1.0.0', 'valid', NULL)
                    """
                )
                with self.assertRaises(duckdb.ConstraintException):
                    connection.execute(
                        """
                        INSERT INTO reference.nicknames
                        VALUES ('other_snapshot', 'nick_other', false, false,
                                'english', 'nick_test', 'the Test',
                                'common/nicknames/test.txt', 1, 3, 1, '{}',
                                'localization/english/test.yml', 1, '1.0.0',
                                'invalid', NULL)
                        """
                    )
                connection.execute(
                    """
                    INSERT INTO reference.character_nickname_events
                    VALUES
                        ('snapshot', 'character', 'character_history', 1, 1,
                         '0860-01-01', 'set', 'nick_test', 'history/test.txt',
                         10, 10, 'valid', NULL),
                        ('snapshot', 'character', 'character_history', 2, 1,
                         '0861-01-01', 'clear', NULL, 'history/test.txt',
                         11, 11, 'valid', NULL)
                    """
                )
                self.assertEqual(
                    (2,),
                    connection.execute(
                        "SELECT count(*) FROM reference.character_nickname_events"
                    ).fetchone(),
                )
                connection.execute(
                    """
                    INSERT INTO reference.character_baseline_nickname_states
                    VALUES ('baseline', 'character', 'snapshot', NULL, 'clear',
                            '0861-01-01', 'character_history', 2, 1, 'valid', NULL)
                    """
                )
                connection.execute(
                    "DELETE FROM reference.character_baseline_nickname_states"
                )
                invalid_scalar_states = (
                    """
                    INSERT INTO reference.character_baseline_nickname_states
                    VALUES ('baseline', 'character', 'snapshot', NULL, 'set',
                            '0861-01-01', 'character_history', 2, 1, 'invalid',
                            NULL)
                    """,
                    """
                    INSERT INTO reference.character_baseline_nickname_states
                    VALUES ('baseline', 'character', 'snapshot', 'nick_test',
                            'clear', '0860-01-01', 'character_history', 1, 1,
                            'invalid', NULL)
                    """,
                )
                for statement in invalid_scalar_states:
                    with self.assertRaises(duckdb.ConstraintException):
                        connection.execute(statement)
                connection.execute(
                    """
                    INSERT INTO reference.character_baseline_nickname_states
                    VALUES ('baseline', 'character', 'snapshot', NULL, 'clear',
                            '0861-01-01', 'character_history', 2, 1, 'valid', NULL)
                    """
                )

                invalid_events = (
                    """
                    INSERT INTO reference.character_nickname_events
                    VALUES ('snapshot', 'character', 'character_history', 1, 2,
                            '0860-01-01', 'set', NULL, 'history/test.txt', 10, 10,
                            'invalid', NULL)
                    """,
                    """
                    INSERT INTO reference.character_nickname_events
                    VALUES ('snapshot', 'character', 'character_history', 2, 2,
                            '0861-01-01', 'clear', 'nick_test', 'history/test.txt',
                            11, 11, 'invalid', NULL)
                    """,
                    """
                    INSERT INTO reference.character_nickname_events
                    VALUES ('snapshot', 'character', 'character_history', 1, 3,
                            '0860-01-01', 'set', 'nick_missing', 'history/test.txt',
                            10, 10, 'invalid', NULL)
                    """,
                    """
                    INSERT INTO reference.character_nickname_events
                    VALUES ('other_snapshot', 'character', 'character_history',
                            1, 1, '0860-01-01', 'set', 'nick_test',
                            'history/test.txt', 10, 10, 'invalid', NULL)
                    """,
                )
                for statement in invalid_events:
                    with self.assertRaises(duckdb.ConstraintException):
                        connection.execute(statement)

                invalid_states = (
                    """
                    INSERT INTO reference.character_baseline_nickname_states
                    VALUES ('missing_baseline', 'character', 'snapshot',
                            'nick_test', 'set', '0860-01-01',
                            'character_history', 1, 1, 'invalid', NULL)
                    """,
                    """
                    INSERT INTO reference.character_baseline_nickname_states
                    VALUES ('baseline', 'missing_character', 'snapshot',
                            'nick_test', 'set', '0860-01-01',
                            'character_history', 1, 1, 'invalid', NULL)
                    """,
                )
                for statement in invalid_states:
                    with self.assertRaises(duckdb.ConstraintException):
                        connection.execute(statement)
            finally:
                connection.close()

            connection = connect(database_path)
            try:
                self.assertEqual(
                    (1, 2, 1),
                    connection.execute(
                        """
                        SELECT
                            (SELECT count(*) FROM reference.nicknames),
                            (SELECT count(*)
                             FROM reference.character_nickname_events),
                            (SELECT count(*)
                             FROM reference.character_baseline_nickname_states)
                        """
                    ).fetchone(),
                )
            finally:
                connection.close()

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