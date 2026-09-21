"""Tests for installed nickname catalog ingestion."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from logic.nickname_catalog_loader import load_nickname_catalog_candidate
from logic.root_database import connect


class NicknameCatalogLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.game_root = root / "game"
        self.nickname_path = self.game_root / "common" / "nicknames" / "00_nicknames.txt"
        self.nickname_path.parent.mkdir(parents=True)
        self._write_valid_definitions()
        self.database_path = root / "tracker.duckdb"
        connection = connect(self.database_path)
        try:
            connection.execute(
                """
                INSERT INTO source.reference_snapshots
                VALUES ('snapshot', '1.19.0.6', '23530548', 'ck3',
                        'candidate', current_timestamp)
                """
            )
            connection.executemany(
                """
                INSERT INTO reference.localizations
                VALUES ('snapshot', 'english', ?, 0, ?, 'nicknames.yml', ?,
                        '1.0.0', 'valid')
                """,
                [
                    ("nick_default", "the Default", 1),
                    ("nick_explicit", "the Explicit", 2),
                ],
            )
        finally:
            connection.close()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _write_valid_definitions(self) -> None:
        self.nickname_path.write_text(
            "nick_default = {}\n"
            "nick_explicit = { is_bad = no is_prefix = yes }\n"
            "nick_the_bastard_rumoured = { is_bad = yes }\n",
            encoding="utf-8-sig",
        )

    def _load(self):
        return load_nickname_catalog_candidate(
            game_root=self.game_root,
            reference_snapshot_id="snapshot",
            database_path=self.database_path,
        )

    def test_loads_defaults_flags_orphan_provenance_and_is_idempotent(self) -> None:
        first = self._load()
        second = self._load()
        connection = connect(self.database_path)
        try:
            rows = connection.execute(
                """
                SELECT nickname_id, is_bad, is_prefix, display_name,
                       definition_source_path, definition_source_order,
                       localization_source_path, validation_status
                FROM reference.nicknames ORDER BY definition_source_order
                """
            ).fetchall()
            manifests = connection.execute(
                """
                SELECT relative_path, source_group, parser_run_id
                FROM source.source_files
                WHERE source_group = 'installed_nicknames'
                """
            ).fetchall()
            latest_run = connection.execute(
                """
                SELECT parser_version, status, row_count
                FROM source.parser_runs
                WHERE parser_name = 'installed_nicknames'
                ORDER BY started_at_utc DESC, parser_run_id DESC LIMIT 1
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(3, first.nickname_count)
        self.assertEqual((2, 1), (second.localized_count, second.reviewed_orphan_count))
        self.assertEqual(
            [
                ("nick_default", False, False, "the Default", "common/nicknames/00_nicknames.txt", 1, "nicknames.yml", "valid"),
                ("nick_explicit", False, True, "the Explicit", "common/nicknames/00_nicknames.txt", 2, "nicknames.yml", "valid"),
                ("nick_the_bastard_rumoured", True, False, None, "common/nicknames/00_nicknames.txt", 3, None, "reviewed_orphan"),
            ],
            rows,
        )
        self.assertEqual(
            [("common/nicknames/00_nicknames.txt", "installed_nicknames", second.parser_run_id)],
            manifests,
        )
        self.assertEqual(("1.0.0", "completed", 3), latest_run)
        self.assertNotEqual(first.parser_run_id, second.parser_run_id)

    def test_rejects_changed_or_used_orphan(self) -> None:
        cases = (
            (
                "changed",
                "nick_default = {}\n"
                "nick_explicit = { is_prefix = yes }\n"
                "nick_the_bastard_rumoured = { is_bad = yes is_prefix = yes }\n",
            ),
            ("used", None),
        )
        for name, definitions in cases:
            with self.subTest(name=name):
                self._write_valid_definitions()
                usage_path = self.game_root / "events" / "test.txt"
                if definitions is not None:
                    self.nickname_path.write_text(definitions, encoding="utf-8-sig")
                else:
                    usage_path.parent.mkdir(parents=True, exist_ok=True)
                    usage_path.write_text(
                        "give_nickname = nick_the_bastard_rumoured\n",
                        encoding="utf-8",
                    )
                with self.assertRaises(ValueError):
                    self._load()
                if usage_path.exists():
                    usage_path.unlink()

    def test_rejects_unresolved_duplicate_and_malformed_definitions(self) -> None:
        cases = (
            (
                "unresolved",
                "nick_missing = {}\n"
                "nick_the_bastard_rumoured = { is_bad = yes }\n",
            ),
            (
                "duplicate",
                "nick_default = {}\n"
                "nick_default = {}\n"
                "nick_the_bastard_rumoured = { is_bad = yes }\n",
            ),
            (
                "malformed",
                "nick_default = { is_bad = maybe }\n"
                "nick_the_bastard_rumoured = { is_bad = yes }\n",
            ),
        )
        for name, definitions in cases:
            with self.subTest(name=name):
                self.nickname_path.write_text(definitions, encoding="utf-8-sig")
                with self.assertRaises(ValueError):
                    self._load()

    def test_failure_preserves_prior_catalog_and_promoted_snapshot_rejects(self) -> None:
        self._load()
        connection = connect(self.database_path)
        try:
            before = connection.execute(
                "SELECT nickname_id, display_name FROM reference.nicknames ORDER BY nickname_id"
            ).fetchall()
        finally:
            connection.close()
        self.nickname_path.write_text(
            "nick_missing = {}\n"
            "nick_the_bastard_rumoured = { is_bad = yes }\n",
            encoding="utf-8-sig",
        )
        with self.assertRaises(ValueError):
            self._load()
        connection = connect(self.database_path)
        try:
            after = connection.execute(
                "SELECT nickname_id, display_name FROM reference.nicknames ORDER BY nickname_id"
            ).fetchall()
            connection.execute(
                "UPDATE source.reference_snapshots SET review_status = 'promoted'"
            )
        finally:
            connection.close()
        self._write_valid_definitions()
        with self.assertRaises(ValueError):
            self._load()
        self.assertEqual(before, after)

    def test_rejects_unknown_snapshot(self) -> None:
        with self.assertRaises(ValueError):
            load_nickname_catalog_candidate(
                game_root=self.game_root,
                reference_snapshot_id="missing",
                database_path=self.database_path,
            )


if __name__ == "__main__":
    unittest.main()