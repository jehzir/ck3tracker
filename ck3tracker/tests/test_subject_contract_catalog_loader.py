"""Tests for installed subject-contract catalog ingestion."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import logic.subject_contract_catalog_loader as loader
from logic.root_database import connect


class SubjectContractCatalogLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.game_root = root / "game"
        self.contract_root = (
            self.game_root / "common" / "subject_contracts" / "contracts"
        )
        self.contract_root.mkdir(parents=True)
        self._write_valid_game()
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
                VALUES ('snapshot', 'english', ?, 0, ?, 'contracts.yml', ?,
                        '1.0.0', 'valid')
                """,
                [
                    (stable_id, f"Label {stable_id}", line)
                    for line, stable_id in enumerate(self.localized_ids, 1)
                ],
            )
        finally:
            connection.close()

        contract_types, _ = loader._parse_installed_definitions(
            self.game_root, self.contract_root
        )
        self.original_exception_hashes = loader.EXPECTED_EXCEPTION_SHA256
        loader.EXPECTED_EXCEPTION_SHA256 = {
            item.contract_type_id: sha256(item.raw_script.encode()).hexdigest()
            for item in contract_types
            if item.contract_type_id in loader.REVIEWED_NONLOCALIZED_TYPES
        }

    def tearDown(self) -> None:
        loader.EXPECTED_EXCEPTION_SHA256 = self.original_exception_hashes
        self.temporary_directory.cleanup()

    def _write_valid_game(self) -> None:
        definitions: dict[str, list[str]] = {
            "herder.txt": [
                "herder_government_obligations = { obligation_levels = { default = { herd = { value = 0 } tax = { value = 0 } } } }"
            ],
            "japan_administrative.txt": [
                "japan_administrative_salary = { display_mode = tree obligation_levels = { "
                "salary_very_low = {} salary_low = { parent = salary_very_low } "
                "salary_medium = { parent = salary_low default = yes } "
                "salary_high = { parent = salary_medium } "
                "salary_very_high = { parent = salary_high } } }"
            ],
            "meritocratic.txt": [
                "meritocratic_tribute_gold = { display_mode = tree obligation_levels = { "
                "meritocratic_tributary_tax_none = { tax = 0 } "
                "meritocratic_tributary_tax_low = { default = yes parent = meritocratic_tributary_tax_none } "
                "meritocratic_tributary_tax_normal = { parent = meritocratic_tributary_tax_low } "
                "meritocratic_tributary_tax_high = { parent = meritocratic_tributary_tax_normal } } }",
                "meritocratic_tribute_prestige = { display_mode = tree obligation_levels = { "
                "meritocratic_prestige_transfer_none = { prestige = 0 } "
                "meritocratic_prestige_transfer_low = { default = yes parent = meritocratic_prestige_transfer_none } "
                "meritocratic_prestige_transfer_normal = { default = yes parent = meritocratic_prestige_transfer_low } "
                "meritocratic_prestige_transfer_high = { parent = meritocratic_prestige_transfer_normal } } }",
            ],
            "special_contracts.txt": [
                "ai_standard_liege_desire = 3",
                "ai_standard_vassal_desire = 3",
                "iqta_special_rights = { display_mode = checkbox obligation_levels = { "
                "iqta_special_rights_default = { default = yes } "
                "iqta_special_rights_granted = { parent = iqta_special_rights_default } } }",
                "ghazi_special_rights = { display_mode = checkbox obligation_levels = { "
                "ghazi_special_rights_default = { default = yes } "
                "ghazi_special_rights_granted = { parent = ghazi_special_rights_default } } }",
            ],
        }
        for index in range(11):
            definitions[f"filler_{index:02d}.txt"] = []
        for index in range(58):
            level_count = 4 if index < 2 else 3
            levels = " ".join(
                f"level_{index:02d}_{level_index} = {{"
                + (" default = no" if level_index == 0 else "")
                + " }"
                for level_index in range(level_count)
            )
            definitions[f"filler_{index % 11:02d}.txt"].append(
                f"contract_{index:02d} = {{ obligation_levels = {{ {levels} }} }}"
            )
        for filename, blocks in definitions.items():
            (self.contract_root / filename).write_text(
                "\n".join(blocks) + "\n", encoding="utf-8-sig"
            )

        evidence = {
            self.game_root
            / "common"
            / "subject_contracts"
            / "groups"
            / "subject_contract_groups.txt": (
                "herder_vassal = { contracts = { herder_government_obligations } }\n"
            ),
            self.game_root
            / "common"
            / "governments"
            / "00_government_types.txt": (
                "herder_government = { vassal_contract_group = herder_vassal }\n"
            ),
            self.game_root
            / "common"
            / "character_interactions"
            / "00_modifiy_vassal_contract.txt": (
                "is_shown = { vassal_contract_has_modifiable_obligations = yes }\n"
            ),
            self.game_root
            / "localization"
            / "english"
            / "government_l_english.yml": (
                "herder_government_vassals_label: \"Herder [obligations|E] cannot be adjusted\"\n"
            ),
        }
        for path, text in evidence.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

        all_types = {f"contract_{index:02d}" for index in range(58)}
        all_levels = {
            f"level_{index:02d}_{level_index}"
            for index in range(58)
            for level_index in range(4 if index < 2 else 3)
        }
        all_levels.update(
            {
                "default",
                "salary_very_low",
                "salary_low",
                "salary_medium",
                "salary_high",
                "salary_very_high",
            }
        )
        self.localized_ids = sorted(all_types | all_levels)

    def _load(self):
        return loader.load_subject_contract_catalog_candidate(
            game_root=self.game_root,
            reference_snapshot_id="snapshot",
            database_path=self.database_path,
        )

    def test_loads_complete_catalog_provenance_defaults_and_is_idempotent(self) -> None:
        first = self._load()
        second = self._load()
        connection = connect(self.database_path)
        try:
            counts = connection.execute(
                """
                SELECT count(*), count(DISTINCT contract_type_id),
                       count(*) FILTER (WHERE validation_status <> 'valid'),
                       count(*) FILTER (WHERE obligation_localization_key IS NOT NULL)
                FROM reference.subject_contract_obligations
                """
            ).fetchone()
            prestige_defaults = connection.execute(
                """
                SELECT obligation_id, is_default
                FROM reference.subject_contract_obligations
                WHERE contract_type_id = 'meritocratic_tribute_prestige'
                ORDER BY level_index
                """
            ).fetchall()
            manifests = connection.execute(
                """
                SELECT count(*), count(DISTINCT parser_run_id)
                FROM source.source_files
                WHERE source_group = 'installed_subject_contracts'
                """
            ).fetchone()
            latest_run = connection.execute(
                """
                SELECT parser_version, status, row_count
                FROM source.parser_runs
                WHERE parser_name = 'installed_subject_contracts'
                ORDER BY started_at_utc DESC, parser_run_id DESC LIMIT 1
                """
            ).fetchone()
            raw_marker = connection.execute(
                """
                SELECT is_default, raw_script, definition_source_path,
                       definition_source_order
                FROM reference.subject_contract_obligations
                WHERE contract_type_id = 'contract_00'
                  AND obligation_id = 'level_00_0'
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual((64, 194, 182, 18), (
            first.type_count,
            first.obligation_count,
            first.localized_obligation_count,
            first.reviewed_nonlocalized_count,
        ))
        self.assertEqual((194, 64, 18, 182), counts)
        self.assertEqual(
            [
                ("meritocratic_prestige_transfer_none", False),
                ("meritocratic_prestige_transfer_low", True),
                ("meritocratic_prestige_transfer_normal", True),
                ("meritocratic_prestige_transfer_high", False),
            ],
            prestige_defaults,
        )
        self.assertEqual((15, 1), manifests)
        self.assertEqual(("1.0.0", "completed", 194), latest_run)
        self.assertEqual(second.parser_run_id, connection_parser_run(self.database_path))
        self.assertFalse(raw_marker[0])
        self.assertIn("default = no", raw_marker[1])
        self.assertEqual("common/subject_contracts/contracts/filler_00.txt", raw_marker[2])
        self.assertGreater(raw_marker[3], 0)

    def test_rejects_exception_definition_consumer_localization_and_evidence_drift(self) -> None:
        cases = ("definition", "consumer", "localization", "evidence")
        for case in cases:
            with self.subTest(case=case):
                if case == "definition":
                    path = self.contract_root / "herder.txt"
                    path.write_text(
                        path.read_text(encoding="utf-8-sig").replace("value = 0", "value = 1", 1),
                        encoding="utf-8-sig",
                    )
                elif case == "consumer":
                    path = self.game_root / "events" / "test.txt"
                    path.parent.mkdir(parents=True)
                    path.write_text("use = meritocratic_tribute_gold\n", encoding="utf-8")
                elif case == "localization":
                    connection = connect(self.database_path)
                    try:
                        connection.execute(
                            """
                            INSERT INTO reference.localizations
                            VALUES ('snapshot', 'english', 'meritocratic_tribute_gold',
                                    0, 'Gold Tribute', 'new.yml', 1, '1.0.0', 'valid')
                            """
                        )
                    finally:
                        connection.close()
                else:
                    path = (
                        self.game_root
                        / "common"
                        / "character_interactions"
                        / "00_modifiy_vassal_contract.txt"
                    )
                    path.write_text("changed = yes\n", encoding="utf-8")
                with self.assertRaises(ValueError):
                    self._load()
                self.tearDown()
                self.setUp()

    def test_rejects_corpus_and_grammar_drift(self) -> None:
        cases = ("count", "duplicate", "default")
        for case in cases:
            with self.subTest(case=case):
                path = self.contract_root / "filler_00.txt"
                text = path.read_text(encoding="utf-8-sig")
                if case == "count":
                    text = text.replace("contract_00", "removed_contract_00", 1)
                    text = text.replace("obligation_levels", "renamed_levels", 1)
                elif case == "duplicate":
                    text += "contract_01 = { obligation_levels = { other = {} } }\n"
                else:
                    text = text.replace("default = no", "default = maybe", 1)
                path.write_text(text, encoding="utf-8-sig")
                with self.assertRaises(ValueError):
                    self._load()
                self.tearDown()
                self.setUp()

    def test_failure_preserves_prior_catalog_and_promoted_snapshot_rejects(self) -> None:
        self._load()
        connection = connect(self.database_path)
        try:
            before = connection.execute(
                """
                SELECT contract_type_id, obligation_id, validation_status
                FROM reference.subject_contract_obligations
                ORDER BY contract_type_id, level_index
                """
            ).fetchall()
            connection.execute(
                """
                DELETE FROM reference.localizations
                WHERE localization_key = 'contract_00'
                """
            )
        finally:
            connection.close()
        with self.assertRaises(ValueError):
            self._load()
        connection = connect(self.database_path)
        try:
            after = connection.execute(
                """
                SELECT contract_type_id, obligation_id, validation_status
                FROM reference.subject_contract_obligations
                ORDER BY contract_type_id, level_index
                """
            ).fetchall()
            connection.execute(
                "UPDATE source.reference_snapshots SET review_status = 'promoted'"
            )
        finally:
            connection.close()
        with self.assertRaises(ValueError):
            self._load()
        self.assertEqual(before, after)

    def test_rejects_unknown_snapshot(self) -> None:
        with self.assertRaises(ValueError):
            loader.load_subject_contract_catalog_candidate(
                game_root=self.game_root,
                reference_snapshot_id="missing",
                database_path=self.database_path,
            )


def connection_parser_run(database_path: Path) -> str:
    connection = connect(database_path)
    try:
        return str(
            connection.execute(
                """
                SELECT parser_run_id FROM source.source_files
                WHERE source_group = 'installed_subject_contracts' LIMIT 1
                """
            ).fetchone()[0]
        )
    finally:
        connection.close()


if __name__ == "__main__":
    unittest.main()
