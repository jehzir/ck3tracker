"""Tests for candidate title-history replay and provenance."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from logic.landed_titles_loader import load_landed_titles_candidate
from logic.reference_inspector_provider import get_title_inspection
from logic.root_database import connect
from logic.title_history_loader import load_title_history_candidate


class TitleHistoryLoaderTests(unittest.TestCase):
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
                b_simajiri = { }
                b_other = { }
            }
            c_duplicate = { b_duplicate = { } }
            c_future = { b_future = { } }
            c_additive = { b_additive = { } }
        }
    }
}
""",
            encoding="utf-8",
        )
        history = self.game_root / "history" / "titles"
        history.mkdir(parents=True)
        (history / "titles.txt").write_text(
            """
c_ucinaa = {
  1066.1.1 = { holder = future_holder }
  867.1.1 = { change_development_level = 4 holder = first_holder }
  700.1.1 = { government = tribal_government }
  867.1.1 = {
    change_development_level = 2
    holder = final_holder
    effect = { set_variable = test }
  }
}
d_ruucuu = { 700.1.1 = { liege = 0 } }
k_islands = { 867.1.1 = { holder = 0 } }
b_other = { 867.1.1 = { effect = { set_capital_barony = yes } } }
e_world = { 867.1.1 = { effect = { set_capital_county = title:c_ucinaa } } }
b_simajiri = {
    867.1.1 = {
        effect = {
            if = {
                limit = { game_start_date = 1066.9.15 }
                set_capital_barony = yes
            }
        }
    }
}
c_duplicate = { 867.1.1 = { holder = first government = tribal_government } }
c_duplicate = { 867.1.1 = { holder = second government = tribal_government } }
c_future = { 1066.1.1 = { holder = first } }
c_future = { 1066.1.1 = { holder = second } }
c_additive = { 700.1.1 = { holder = first } }
c_additive = { 800.1.1 = { government = tribal_government } }
""",
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

    def test_replays_dates_and_preserves_unknown_operations(self) -> None:
        result = load_title_history_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            database_path=self.database_path,
        )
        connection = connect(self.database_path)
        try:
            ucinaa = connection.execute(
                """
                SELECT holder_character_id, holder_status, government_id,
                       development_level, validation_status, validation_note
                FROM reference.title_baseline_states
                WHERE baseline_id = 'scribe_867' AND title_id = 'c_ucinaa'
                """
            ).fetchone()
            explicit = connection.execute(
                """
                SELECT title_id, holder_character_id, holder_status,
                       liege_title_id, liege_status
                FROM reference.title_baseline_states
                WHERE title_id IN ('k_islands', 'd_ruucuu') ORDER BY title_id
                """
            ).fetchall()
            effect = connection.execute(
                """
                SELECT value_kind, raw_script, resolution_status
                FROM source.title_history_declarations
                WHERE operation_key = 'effect'
                """
            ).fetchone()
            state = connection.execute(
                """
                SELECT s.review_status, b.support_status, b.historical_state_complete
                FROM source.reference_snapshots s
                JOIN reference.baselines b USING (reference_snapshot_id)
                """
            ).fetchone()
            capitals = connection.execute(
                """
                SELECT title_id, capital_title_id, capital_status,
                       capital_source_event_sequence IS NOT NULL
                FROM reference.title_baseline_states
                WHERE title_id IN ('e_world', 'c_ucinaa', 'b_simajiri')
                ORDER BY title_id
                """
            ).fetchall()
            duplicate_blocks = connection.execute(
                """
                SELECT title_id, duplicate_classification,
                       baseline_conflict_fields, count(*)
                FROM source.title_history_blocks
                WHERE duplicate_classification <> 'unique'
                GROUP BY ALL ORDER BY title_id
                """
            ).fetchall()
            duplicate_state = connection.execute(
                """
                SELECT holder_character_id, holder_status, government_id,
                       government_status, validation_status, validation_note
                FROM reference.title_baseline_states
                WHERE title_id = 'c_duplicate'
                """
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual(
            ("final_holder", "declared", "tribal_government", 6, "warning", "not evaluated: effect"),
            ucinaa,
        )
        self.assertEqual(
            [
                ("d_ruucuu", None, "no_declaration", None, "explicit_independent"),
                ("k_islands", None, "explicit_unheld", None, "no_declaration"),
            ],
            explicit,
        )
        self.assertEqual(("block", "{ set_variable = test }", "preserved"), effect)
        self.assertEqual(("candidate", "candidate", False), state)
        self.assertEqual(
            [
                ("b_simajiri", None, "not_applicable", False),
                ("c_ucinaa", "b_other", "history_set_capital_barony", True),
                ("e_world", "c_ucinaa", "history_set_capital_county", True),
            ],
            capitals,
        )
        self.assertEqual(
            [
                ("c_additive", "additive_nonconflicting", None, 2),
                ("c_duplicate", "conflicting_at_baseline", "holder", 2),
                ("c_future", "conflicting_after_baseline", None, 2),
            ],
            duplicate_blocks,
        )
        self.assertEqual(
            (None, "ambiguous_duplicate", "tribal_government", "declared", "warning",
             "baseline-conflicting duplicate title declarations: holder"),
            duplicate_state,
        )
        self.assertEqual(20, result.declaration_count)
        self.assertEqual(19, result.event_count)
        self.assertEqual(9, result.state_count)

    def test_holder_ignore_head_of_faith_requirement_replaces_and_clears_holder(self) -> None:
        history = self.game_root / "history" / "titles" / "titles.txt"
        history.write_text(
            """
    k_islands = {
        700.1.1 = { holder = ordinary_holder }
        800.1.1 = { holder_ignore_head_of_faith_requirement = bypass_holder }
    }
    d_ruucuu = {
        700.1.1 = { holder_ignore_head_of_faith_requirement = first_bypass_holder }
        800.1.1 = { holder_ignore_head_of_faith_requirement = 0 }
    }
    """,
            encoding="utf-8",
        )

        load_title_history_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            database_path=self.database_path,
        )
        connection = connect(self.database_path)
        try:
            states = connection.execute(
                """
                    SELECT title_id, holder_character_id, holder_status,
                           validation_status, validation_note
                    FROM reference.title_baseline_states
                    WHERE baseline_id = 'scribe_867'
                        AND title_id IN ('k_islands', 'd_ruucuu')
                    ORDER BY title_id
                """
            ).fetchall()
            declarations = connection.execute(
                """
                    SELECT title_id, scalar_value, resolution_status, raw_script
                    FROM source.title_history_declarations
                    WHERE operation_key = 'holder_ignore_head_of_faith_requirement'
                    ORDER BY declaration_order
                """
            ).fetchall()
            events = connection.execute(
                """
                    SELECT title_id, event_type, text_value, validation_status,
                           validation_note
                    FROM reference.title_history_events
                    WHERE event_type = 'holder_ignore_head_of_faith_requirement'
                    ORDER BY event_sequence
                """
            ).fetchall()
        finally:
            connection.close()

        self.assertEqual(
            [
                ("d_ruucuu", None, "explicit_unheld", "valid", None),
                (
                    "k_islands",
                    "bypass_holder",
                    "declared_ignore_head_of_faith_requirement",
                    "valid",
                    None,
                ),
            ],
            states,
        )
        self.assertEqual(
            [
                (
                    "k_islands",
                    "bypass_holder",
                    "normalized",
                    "bypass_holder",
                ),
                (
                    "d_ruucuu",
                    "first_bypass_holder",
                    "normalized",
                    "first_bypass_holder",
                ),
                ("d_ruucuu", "0", "normalized", "0"),
            ],
            declarations,
        )
        self.assertEqual(
            [
                (
                    "d_ruucuu",
                    "holder_ignore_head_of_faith_requirement",
                    "first_bypass_holder",
                    "valid",
                    "holder assigned with head-of-faith eligibility bypass",
                ),
                (
                    "k_islands",
                    "holder_ignore_head_of_faith_requirement",
                    "bypass_holder",
                    "valid",
                    "holder assigned with head-of-faith eligibility bypass",
                ),
                (
                    "d_ruucuu",
                    "holder_ignore_head_of_faith_requirement",
                    "0",
                    "valid",
                    "explicit title clear with head-of-faith eligibility bypass",
                ),
            ],
            events,
        )

    def test_title_name_override_replaces_and_reset_restores_default_name(self) -> None:
        history = self.game_root / "history" / "titles" / "titles.txt"
        history.write_text(
            """
k_islands = { 700.1.1 = { name = CUSTOM_ISLANDS } }
d_ruucuu = {
    700.1.1 = { name = OLD_RUUCUU }
    800.1.1 = { reset_name = yes }
}
c_future = { 700.1.1 = { name = MISSING_NAME_KEY } }
""",
            encoding="utf-8",
        )
        connection = connect(self.database_path)
        try:
            connection.executemany(
                """
                INSERT INTO reference.localizations
                VALUES ('scribe_build', 'english', ?, 0, ?, 'test_l_english.yml',
                        ?, '1.0.0', 'valid')
                """,
                [
                    ("CUSTOM_ISLANDS", "Custom Islands", 1),
                    ("OLD_RUUCUU", "Old Ruucuu", 2),
                ],
            )
        finally:
            connection.close()

        load_title_history_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            database_path=self.database_path,
        )
        connection = connect(self.database_path)
        try:
            names = connection.execute(
                """
                SELECT title_id, localization_key, display_name, name_status,
                       effective_date, source_declaration_order
                FROM reference.title_baseline_name_overrides
                WHERE baseline_id = 'scribe_867'
                ORDER BY title_id
                """
            ).fetchall()
            states = connection.execute(
                """
                SELECT title_id, validation_status, validation_note
                FROM reference.title_baseline_states
                WHERE baseline_id = 'scribe_867'
                    AND title_id IN ('k_islands', 'd_ruucuu', 'c_future')
                ORDER BY title_id
                """
            ).fetchall()
            declarations = connection.execute(
                """
                SELECT title_id, operation_key, resolution_status
                FROM source.title_history_declarations
                WHERE operation_key IN ('name', 'reset_name')
                ORDER BY declaration_order
                """
            ).fetchall()
            events = connection.execute(
                """
                SELECT title_id, event_type, text_value, validation_status,
                       validation_note
                FROM reference.title_history_events
                WHERE event_type IN ('title_name_override_set', 'title_name_override_reset')
                ORDER BY event_sequence
                """
            ).fetchall()
        finally:
            connection.close()

        self.assertEqual(
            [
                ("d_ruucuu", None, None, "explicit_default", date(800, 1, 1), 3),
                (
                    "k_islands",
                    "CUSTOM_ISLANDS",
                    "Custom Islands",
                    "declared",
                    date(700, 1, 1),
                    1,
                ),
            ],
            names,
        )
        self.assertEqual(
            [
                ("c_future", "warning", "not evaluated: name"),
                ("d_ruucuu", "valid", None),
                ("k_islands", "valid", None),
            ],
            states,
        )
        self.assertEqual(
            [
                ("k_islands", "name", "normalized"),
                ("d_ruucuu", "name", "normalized"),
                ("d_ruucuu", "reset_name", "normalized"),
                ("c_future", "name", "preserved"),
            ],
            declarations,
        )
        self.assertEqual(
            [
                (
                    "k_islands",
                    "title_name_override_set",
                    "CUSTOM_ISLANDS",
                    "valid",
                    "display_name=Custom Islands",
                ),
                (
                    "d_ruucuu",
                    "title_name_override_set",
                    "OLD_RUUCUU",
                    "valid",
                    "display_name=Old Ruucuu",
                ),
                (
                    "d_ruucuu",
                    "title_name_override_reset",
                    None,
                    "valid",
                    "default title localization restored",
                ),
            ],
            events,
        )
        inspection = get_title_inspection(
            "scribe_867", "k_islands", self.database_path
        )
        self.assertEqual("CUSTOM_ISLANDS", inspection["name_override_localization_key"])
        self.assertEqual("Custom Islands", inspection["name_override_display_name"])
        self.assertEqual("declared", inspection["name_override_status"])

    def test_exact_set_title_name_effect_reuses_name_override_projection(self) -> None:
        history = self.game_root / "history" / "titles" / "titles.txt"
        history.write_text(
            """
d_ruucuu = {
  700.1.1 = { effect = { set_title_name = CUSTOM_RUUCUU } }
}
k_islands = {
  700.1.1 = {
    effect = { set_title_name = CUSTOM_ISLANDS set_variable = altered }
  }
}
c_ucinaa = {
  700.1.1 = { effect = { set_title_name = MISSING_NAME_KEY } }
}
""",
            encoding="utf-8",
        )
        connection = connect(self.database_path)
        try:
            connection.executemany(
                """
                INSERT INTO reference.localizations
                VALUES ('scribe_build', 'english', ?, 0, ?, 'test_l_english.yml',
                        ?, '1.0.0', 'valid')
                """,
                [
                    ("CUSTOM_RUUCUU", "Custom Ruucuu", 1),
                    ("CUSTOM_ISLANDS", "Custom Islands", 2),
                ],
            )
        finally:
            connection.close()

        load_title_history_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            database_path=self.database_path,
        )
        connection = connect(self.database_path)
        try:
            names = connection.execute(
                """
                SELECT title_id, localization_key, display_name, name_status,
                       effective_date, source_declaration_order
                FROM reference.title_baseline_name_overrides
                WHERE baseline_id = 'scribe_867'
                """
            ).fetchall()
            declarations = connection.execute(
                """
                SELECT title_id, resolution_status, raw_script
                FROM source.title_history_declarations
                WHERE operation_key = 'effect'
                ORDER BY declaration_order
                """
            ).fetchall()
            states = connection.execute(
                """
                SELECT title_id, validation_status, validation_note
                FROM reference.title_baseline_states
                WHERE baseline_id = 'scribe_867'
                  AND title_id IN ('d_ruucuu', 'k_islands', 'c_ucinaa')
                ORDER BY title_id
                """
            ).fetchall()
            event = connection.execute(
                """
                SELECT title_id, event_type, text_value, validation_note
                FROM reference.title_history_events
                WHERE event_type = 'title_name_override_set'
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(
            [
                (
                    "d_ruucuu", "CUSTOM_RUUCUU", "Custom Ruucuu", "declared",
                    date(700, 1, 1), 1,
                )
            ],
            names,
        )
        self.assertEqual("normalized", declarations[0][1])
        self.assertIn("set_title_name", declarations[0][2])
        self.assertEqual("preserved", declarations[1][1])
        self.assertEqual("preserved", declarations[2][1])
        self.assertEqual(
            [
                ("c_ucinaa", "warning", "not evaluated: effect"),
                ("d_ruucuu", "valid", None),
                ("k_islands", "warning", "not evaluated: effect"),
            ],
            states,
        )
        self.assertEqual(
            (
                "d_ruucuu", "title_name_override_set", "CUSTOM_RUUCUU",
                "display_name=Custom Ruucuu",
            ),
            event,
        )

    def test_candidate_reload_is_idempotent(self) -> None:
        arguments = {
            "game_root": self.game_root,
            "reference_snapshot_id": "scribe_build",
            "baseline_id": "scribe_867",
            "database_path": self.database_path,
        }
        load_title_history_candidate(**arguments)
        load_title_history_candidate(**arguments)
        connection = connect(self.database_path)
        try:
            counts = connection.execute(
                """
                SELECT
                  (SELECT count(*) FROM source.title_history_declarations),
                  (SELECT count(*) FROM reference.title_history_events),
                  (SELECT count(*) FROM reference.title_baseline_states),
                  (SELECT count(*) FROM source.parser_runs)
                """
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual((20, 19, 9, 3), counts)

    def test_later_source_file_resolves_duplicate_title_block(self) -> None:
        history = self.game_root / "history" / "titles"
        (history / "z_override.txt").write_text(
            """
c_duplicate = {
  867.1.1 = { holder = override government = nomad_government }
}
""",
            encoding="utf-8",
        )

        load_title_history_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            database_path=self.database_path,
        )
        connection = connect(self.database_path)
        try:
            blocks = connection.execute(
                """
                SELECT source_path, duplicate_classification,
                       baseline_conflict_fields, resolution_status, is_winner
                FROM source.title_history_blocks
                WHERE title_id = 'c_duplicate'
                ORDER BY source_block_order
                """
            ).fetchall()
            state = connection.execute(
                """
                SELECT holder_character_id, holder_status, government_id,
                       government_status, validation_status, validation_note
                FROM reference.title_baseline_states
                WHERE baseline_id = 'scribe_867' AND title_id = 'c_duplicate'
                """
            ).fetchone()
            provenance = connection.execute(
                """
                SELECT page_key, revision_id, review_status
                FROM source.wiki_pages
                WHERE reference_snapshot_id = 'scribe_build'
                  AND page_key = 'title_history_load_order'
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(
            [
                ("history/titles/titles.txt", "resolved_by_source_order", "government,holder", "superseded", False),
                ("history/titles/titles.txt", "resolved_by_source_order", "government,holder", "superseded", False),
                ("history/titles/z_override.txt", "resolved_by_source_order", "government,holder", "winner", True),
            ],
            blocks,
        )
        self.assertEqual(
            ("override", "declared", "nomad_government", "declared", "valid", None),
            state,
        )
        self.assertEqual(
            ("title_history_load_order", "35725", "reviewed"), provenance
        )

    def test_installed_tgp_package_makes_gated_destruction_a_noop(self) -> None:
        history = self.game_root / "history" / "titles"
        (history / "tgp_titles.txt").write_text(
            """
k_islands = {
  867.1.1 = {
    effect = { destroy_landless_title_no_tgp_dlc_effect = { DATE = 867.1.1 } }
  }
}
""",
            encoding="utf-8",
        )
        effects = self.game_root / "common" / "scripted_effects"
        effects.mkdir(parents=True)
        (effects / "10_dlc_tgp_scripted_effects.txt").write_text(
            """
destroy_landless_title_no_tgp_dlc_effect = {
  if = {
    limit = {
      NOT = { has_dlc_feature = all_under_heaven }
      game_start_date = $DATE$
    }
    holder ?= {
      empty_treasury_when_abandoning_landed_life_effect = yes
      destroy_title = prev
    }
  }
}
""",
            encoding="utf-8",
        )
        triggers = self.game_root / "common" / "scripted_triggers"
        triggers.mkdir(parents=True)
        (triggers / "00_has_dlc_scripted_triggers.txt").write_text(
            "has_tgp_dlc_trigger = { has_dlc_feature = all_under_heaven }\n",
            encoding="utf-8",
        )
        load_title_history_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            database_path=self.database_path,
        )
        connection = connect(self.database_path)
        try:
            unresolved = connection.execute(
                """
                SELECT state.validation_status, declaration.resolution_status
                FROM reference.title_baseline_states state
                JOIN source.title_history_declarations declaration
                  ON declaration.reference_snapshot_id = 'scribe_build'
                 AND declaration.title_id = state.title_id
                 AND declaration.operation_key = 'effect'
                WHERE state.baseline_id = 'scribe_867'
                  AND state.title_id = 'k_islands'
                """
            ).fetchone()
            connection.execute(
                """
                INSERT INTO reference.dlc_packages
                VALUES ('scribe_build', 'dlc022_ep4', 'All Under Heaven', NULL,
                        NULL, NULL, 'dlc/dlc022_ep4/dlc022.dlc', 'hash',
                        'https://example.test/wiki?oldid=1', '1', 'valid', NULL)
                """
            )
            connection.execute(
                """
                INSERT INTO reference.dlc_feature_mappings
                VALUES ('scribe_build', 'all_under_heaven', 'dlc022_ep4',
                        'reviewed', 'test evidence')
                """
            )
        finally:
            connection.close()

        self.assertEqual(("warning", "preserved"), unresolved)
        load_title_history_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            database_path=self.database_path,
        )
        connection = connect(self.database_path)
        try:
            state = connection.execute(
                """
                SELECT validation_status, validation_note
                FROM reference.title_baseline_states
                WHERE baseline_id = 'scribe_867' AND title_id = 'k_islands'
                """
            ).fetchone()
            declaration = connection.execute(
                """
                SELECT resolution_status
                FROM source.title_history_declarations
                WHERE title_id = 'k_islands' AND operation_key = 'effect'
                """
            ).fetchone()
            event = connection.execute(
                """
                SELECT event_type, text_value, validation_status,
                       validation_note, required_game_start_date
                FROM reference.title_history_events
                WHERE title_id = 'k_islands' AND event_type = 'dlc_gated_noop'
                """
            ).fetchone()
            evidence_paths = connection.execute(
                """
                SELECT relative_path
                FROM source.source_files
                WHERE reference_snapshot_id = 'scribe_build'
                  AND source_group = 'installed_title_history'
                  AND relative_path LIKE 'common/%'
                ORDER BY relative_path
                """
            ).fetchall()
        finally:
            connection.close()

        self.assertEqual(("valid", None), state)
        self.assertEqual(("normalized",), declaration)
        self.assertEqual(
            (
                "dlc_gated_noop",
                "all_under_heaven",
                "valid",
                "installed dlc022_ep4 makes destruction condition false",
                "0867-01-01",
            ),
            event,
        )
        self.assertEqual(
            [
                ("common/scripted_effects/10_dlc_tgp_scripted_effects.txt",),
                ("common/scripted_triggers/00_has_dlc_scripted_triggers.txt",),
            ],
            evidence_paths,
        )

    def test_installed_roads_to_power_package_makes_exact_destruction_a_noop(self) -> None:
                history = self.game_root / "history" / "titles" / "titles.txt"
                history.write_text(
                        """
k_islands = {
    867.1.1 = {
        effect = { destroy_landless_title_no_dlc_effect = { DATE = 867.1.1 } }
    }
}
c_future = {
    867.1.1 = {
        effect = {
            set_variable = test
            destroy_landless_title_no_dlc_effect = { DATE = 867.1.1 }
        }
    }
}
""",
                        encoding="utf-8",
                )
                effects = self.game_root / "common" / "scripted_effects"
                effects.mkdir(parents=True)
                (effects / "07_dlc_ep3_scripted_effects.txt").write_text(
                        """
destroy_landless_title_no_dlc_effect = {
    if = {
        limit = {
            NOT = { has_dlc_feature = roads_to_power }
            game_start_date = $DATE$
        }
        holder ?= {
            empty_treasury_when_abandoning_landed_life_effect = yes
            destroy_title = prev
        }
    }
}
""",
                        encoding="utf-8",
                )
                connection = connect(self.database_path)
                try:
                        connection.execute(
                                """
                                INSERT INTO reference.dlc_packages
                                VALUES ('scribe_build', 'dlc014_ep3', 'Roads to Power', NULL,
                                                NULL, NULL, 'dlc/dlc014_ep3/dlc014.dlc', 'hash',
                                                'https://example.test/wiki?oldid=1', '1', 'valid', NULL)
                                """
                        )
                        connection.execute(
                                """
                                INSERT INTO reference.dlc_feature_mappings
                                VALUES ('scribe_build', 'roads_to_power', 'dlc014_ep3',
                                                'reviewed', 'test evidence')
                                """
                        )
                finally:
                        connection.close()

                load_title_history_candidate(
                        game_root=self.game_root,
                        reference_snapshot_id="scribe_build",
                        baseline_id="scribe_867",
                        database_path=self.database_path,
                )
                connection = connect(self.database_path)
                try:
                        states = connection.execute(
                                """
                                SELECT title_id, validation_status, validation_note
                                FROM reference.title_baseline_states
                                WHERE baseline_id = 'scribe_867'
                                    AND title_id IN ('k_islands', 'c_future')
                                ORDER BY title_id
                                """
                        ).fetchall()
                        declarations = connection.execute(
                                """
                                SELECT title_id, resolution_status
                                FROM source.title_history_declarations
                                WHERE operation_key = 'effect'
                                    AND title_id IN ('k_islands', 'c_future')
                                ORDER BY title_id
                                """
                        ).fetchall()
                        event = connection.execute(
                                """
                                SELECT title_id, event_type, text_value, validation_note,
                                             required_game_start_date
                                FROM reference.title_history_events
                                WHERE event_type = 'dlc_gated_noop'
                                """
                        ).fetchone()
                finally:
                        connection.close()

                self.assertEqual(
                        [
                                ("c_future", "warning", "not evaluated: effect"),
                                ("k_islands", "valid", None),
                        ],
                        states,
                )
                self.assertEqual(
                        [("c_future", "preserved"), ("k_islands", "normalized")],
                        declarations,
                )
                self.assertEqual(
                        (
                                "k_islands",
                                "dlc_gated_noop",
                                "roads_to_power",
                                "installed dlc014_ep3 makes destruction condition false",
                                "0867-01-01",
                        ),
                        event,
                )

    def test_installed_roads_to_power_makes_exact_government_fallback_a_noop(self) -> None:
        history = self.game_root / "history" / "titles" / "titles.txt"
        history.write_text(
            """
k_islands = {
    867.1.1 = {
        holder = holder_1
        effect = {
            if = {
                limit = {
                    exists = holder
                    NOT = { has_dlc_feature = roads_to_power }
                }
                holder = {
                    empty_treasury_when_abandoning_landed_life_effect = yes
                    change_government = feudal_government
                }
            }
        }
    }
}
c_future = {
    867.1.1 = {
        holder = holder_2
        effect = {
            if = {
                limit = {
                    exists = holder
                    NOT = { has_dlc_feature = roads_to_power }
                }
                holder = {
                    empty_treasury_when_abandoning_landed_life_effect = yes
                    change_government = feudal_government
                    set_variable = altered
                }
            }
        }
    }
}
""",
            encoding="utf-8",
        )
        connection = connect(self.database_path)
        try:
            connection.execute(
                """
                INSERT INTO reference.dlc_packages
                VALUES ('scribe_build', 'dlc014_ep3', 'Roads to Power', NULL,
                        NULL, NULL, 'dlc/dlc014_ep3/dlc014.dlc', 'hash',
                        'https://example.test/wiki?oldid=1', '1', 'valid', NULL)
                """
            )
            connection.execute(
                """
                INSERT INTO reference.dlc_feature_mappings
                VALUES ('scribe_build', 'roads_to_power', 'dlc014_ep3',
                        'reviewed', 'test evidence')
                """
            )
        finally:
            connection.close()

        load_title_history_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            database_path=self.database_path,
        )
        connection = connect(self.database_path)
        try:
            states = connection.execute(
                """
                SELECT title_id, validation_status, validation_note
                FROM reference.title_baseline_states
                WHERE baseline_id = 'scribe_867'
                    AND title_id IN ('k_islands', 'c_future')
                ORDER BY title_id
                """
            ).fetchall()
            declarations = connection.execute(
                """
                SELECT title_id, resolution_status
                FROM source.title_history_declarations
                WHERE operation_key = 'effect'
                    AND title_id IN ('k_islands', 'c_future')
                ORDER BY title_id
                """
            ).fetchall()
            event = connection.execute(
                """
                SELECT title_id, event_type, text_value, validation_note
                FROM reference.title_history_events
                WHERE event_type = 'dlc_gated_conditional_noop'
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(
            [
                ("c_future", "warning", "not evaluated: effect"),
                ("k_islands", "valid", None),
            ],
            states,
        )
        self.assertEqual(
            [("c_future", "preserved"), ("k_islands", "normalized")],
            declarations,
        )
        self.assertEqual(
            (
                "k_islands",
                "dlc_gated_conditional_noop",
                "roads_to_power",
                "installed dlc014_ep3 makes government fallback condition false",
            ),
            event,
        )

    def test_materializes_exact_royal_court_state_at_execution_holder(self) -> None:
        history = self.game_root / "history" / "titles" / "titles.txt"
        history.write_text(
            """
k_islands = {
    700.1.1 = { holder = language_holder }
    800.1.1 = { effect = { if = {
        limit = { exists = holder has_dlc_feature = royal_court }
        holder = { set_court_language = language_chinese }
    } } }
    850.1.1 = { holder = type_holder }
    860.1.1 = { effect = { if = {
        limit = { exists = holder has_dlc_feature = royal_court }
        holder = { set_court_type = court_scholarly }
    } } }
    867.1.1 = { holder = final_holder }
}
c_future = {
    800.1.1 = { holder = learning_holder }
    801.1.1 = { effect = { if = {
        limit = { exists = holder has_dlc_feature = royal_court }
        holder = {
            set_court_language = language_greek
            if = {
                limit = { NOT = { knows_court_language_of = this } }
                learn_court_language_of = this
            }
        }
    } } }
}
c_additive = {
    800.1.1 = { holder = native_holder }
    801.1.1 = { effect = { if = {
        limit = { exists = holder has_dlc_feature = royal_court }
        holder = {
            set_court_language = language_iranian
            if = {
                limit = { NOT = { knows_court_language_of = this } }
                learn_court_language_of = this
            }
        }
    } } }
}
d_ruucuu = {
    800.1.1 = { holder = unresolved_holder }
    801.1.1 = { effect = { if = {
        limit = { exists = holder has_dlc_feature = royal_court }
        holder = { set_court_language = language_missing }
    } } }
}
k_balhae = {
    800.1.1 = { holder = excluded_holder }
    801.1.1 = { effect = { if = {
        limit = { exists = holder has_dlc_feature = royal_court }
        holder = { set_court_language = language_chinese }
    } } }
}
""",
            encoding="utf-8",
        )
        connection = connect(self.database_path)
        try:
            connection.execute(
                """
                INSERT INTO reference.dlc_packages
                VALUES ('scribe_build', 'dlc004_ep1', 'The Royal Court', NULL,
                        NULL, NULL, 'dlc/dlc004_ep1/dlc004.dlc', 'hash',
                        'https://example.test/wiki?oldid=1', '1', 'valid', NULL)
                """
            )
            connection.execute(
                """
                INSERT INTO reference.dlc_feature_mappings
                VALUES ('scribe_build', 'royal_court', 'dlc004_ep1',
                        'reviewed', 'test evidence')
                """
            )
            for order, language_id in enumerate(
                ("language_chinese", "language_greek", "language_iranian"),
                start=1,
            ):
                connection.execute(
                    """
                    INSERT INTO reference.languages
                    VALUES ('scribe_build', ?, 'common/culture/pillars/test.txt',
                            1, 1, ?, '{}', '1.1.0', 'valid', NULL)
                    """,
                    [language_id, order],
                )
            connection.execute(
                """
                INSERT INTO reference.character_baseline_languages
                VALUES ('scribe_867', 'native_holder', 'language_iranian',
                        'native', NULL, 'culture', 1, 'valid', NULL)
                """
            )
        finally:
            connection.close()

        arguments = dict(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            database_path=self.database_path,
        )
        load_title_history_candidate(**arguments)
        load_title_history_candidate(**arguments)
        connection = connect(self.database_path)
        try:
            court_states = connection.execute(
                """
                SELECT character_id, court_language_id,
                       court_language_effective_date,
                       court_language_source_declaration_order,
                       court_type_id, court_type_effective_date,
                       court_type_source_declaration_order
                FROM reference.character_baseline_court_states
                ORDER BY character_id
                """
            ).fetchall()
            declarations = connection.execute(
                """
                SELECT title_id, resolution_status
                FROM source.title_history_declarations
                WHERE operation_key = 'effect'
                ORDER BY title_id
                """
            ).fetchall()
            title_states = connection.execute(
                """
                SELECT title_id, validation_status
                FROM reference.title_baseline_states
                WHERE title_id IN ('k_islands', 'c_future', 'c_additive', 'd_ruucuu')
                ORDER BY title_id
                """
            ).fetchall()
            languages = connection.execute(
                """
                SELECT character_id, language_id, knowledge_kind, source_group,
                       source_declaration_order
                FROM reference.character_baseline_languages
                ORDER BY character_id, language_id
                """
            ).fetchall()
            learning_events = connection.execute(
                """
                SELECT title_id, event_type, text_value, validation_note
                FROM reference.title_history_events
                WHERE event_type IN ('court_language_learned',
                                     'court_language_learning_noop')
                ORDER BY title_id
                """
            ).fetchall()
        finally:
            connection.close()

        self.assertEqual(
            [
                ("language_holder", "language_chinese", date(800, 1, 1), 2,
                 None, None, None),
                ("learning_holder", "language_greek", date(801, 1, 1), 7,
                 None, None, None),
                ("native_holder", "language_iranian", date(801, 1, 1), 9,
                 None, None, None),
                ("type_holder", None, None, None,
                 "court_scholarly", date(860, 1, 1), 4),
            ],
            court_states,
        )
        self.assertEqual(
            [
                ("c_additive", "normalized"),
                ("c_future", "normalized"),
                ("d_ruucuu", "preserved"),
                ("k_balhae", "preserved"),
                ("k_islands", "normalized"),
                ("k_islands", "normalized"),
            ],
            declarations,
        )
        self.assertEqual(
            [
                ("c_additive", "valid"),
                ("c_future", "valid"),
                ("d_ruucuu", "warning"),
                ("k_islands", "valid"),
            ],
            title_states,
        )
        self.assertEqual(
            [
                ("learning_holder", "language_greek", "history_granted",
                 "title_history", 7),
                ("native_holder", "language_iranian", "native", "culture", 1),
            ],
            languages,
        )
        self.assertEqual(
            [
                ("c_additive", "court_language_learning_noop", "language_iranian",
                 "holder=native_holder; already_known"),
                ("c_future", "court_language_learned", "language_greek",
                 "holder=learning_holder; history_granted"),
            ],
            learning_events,
        )

    def test_historical_adventurer_body_is_fully_replayed(self) -> None:
                history = self.game_root / "history" / "titles" / "titles.txt"
                history.write_text(
                        """
k_islands = {
    867.1.1 = {
        holder = holder_1
        succession_laws = { landless_adventurer_succession_law }
        effect = {
            create_landless_adventurer_title_history_effect = yes
            set_variable = { name = adventurer_creation_reason value = flag:historical }
            destroy_landless_title_no_dlc_effect = { DATE = 867.1.1 }
        }
    }
}
""",
                        encoding="utf-8",
                )
                laws = self.game_root / "common" / "laws"
                laws.mkdir(parents=True)
                (laws / "00_succession_laws.txt").write_text(
                        "succession_order_laws = {\n"
                        "  landless_adventurer_succession_law = { }\n"
                        "}\n",
                        encoding="utf-8",
                )
                effects = self.game_root / "common" / "scripted_effects"
                effects.mkdir(parents=True)
                (effects / "07_dlc_ep3_scripted_effects.txt").write_text(
                        """
create_landless_adventurer_title_history_effect = {
    holder ?= {
        if = {
            limit = { NOT = { has_realm_law = landless_adventurer_succession_law } }
            add_realm_law = landless_adventurer_succession_law
        }
    }
}
destroy_landless_title_no_dlc_effect = {
    if = {
        limit = {
            NOT = { has_dlc_feature = roads_to_power }
            game_start_date = $DATE$
        }
        holder ?= {
            empty_treasury_when_abandoning_landed_life_effect = yes
            destroy_title = prev
        }
    }
}
""",
                        encoding="utf-8",
                )
                connection = connect(self.database_path)
                try:
                        connection.execute(
                                """
                                INSERT INTO reference.dlc_packages
                                VALUES ('scribe_build', 'dlc014_ep3', 'Roads to Power', NULL,
                                                NULL, NULL, 'dlc/dlc014_ep3/dlc014.dlc', 'hash',
                                                'https://example.test/wiki?oldid=1', '1', 'valid', NULL)
                                """
                        )
                        connection.execute(
                                """
                                INSERT INTO reference.dlc_feature_mappings
                                VALUES ('scribe_build', 'roads_to_power', 'dlc014_ep3',
                                                'reviewed', 'test evidence')
                                """
                        )
                finally:
                        connection.close()

                load_title_history_candidate(
                        game_root=self.game_root,
                        reference_snapshot_id="scribe_build",
                        baseline_id="scribe_867",
                        database_path=self.database_path,
                )
                connection = connect(self.database_path)
                try:
                        state = connection.execute(
                                """
                                SELECT validation_status, validation_note
                                FROM reference.title_baseline_states
                                WHERE baseline_id = 'scribe_867' AND title_id = 'k_islands'
                                """
                        ).fetchone()
                        variable = connection.execute(
                                """
                                SELECT variable_name, value_kind, text_value, effective_date
                                FROM reference.title_baseline_variables
                                WHERE baseline_id = 'scribe_867' AND title_id = 'k_islands'
                                """
                        ).fetchone()
                        events = connection.execute(
                                """
                                SELECT event_type, text_value, validation_note
                                FROM reference.title_history_events
                                WHERE title_id = 'k_islands'
                                    AND event_type IN ('landless_adventurer_history_initialized',
                                                                         'title_variable_set', 'dlc_gated_noop')
                                ORDER BY event_sequence
                                """
                        ).fetchall()
                        declaration = connection.execute(
                                """
                                SELECT resolution_status, raw_script
                                FROM source.title_history_declarations
                                WHERE title_id = 'k_islands' AND operation_key = 'effect'
                                """
                        ).fetchone()
                finally:
                        connection.close()

                self.assertEqual(("valid", None), state)
                self.assertEqual(
                        ("adventurer_creation_reason", "flag", "historical", date(867, 1, 1)),
                        variable,
                )
                self.assertEqual(
                        [
                                (
                                        "landless_adventurer_history_initialized",
                                        "landless_adventurer_succession_law",
                                        "explicit title law makes helper idempotent",
                                ),
                                ("title_variable_set", "adventurer_creation_reason=historical", "value_kind=flag"),
                                (
                                        "dlc_gated_noop",
                                        "roads_to_power",
                                        "installed dlc014_ep3 makes destruction condition false",
                                ),
                        ],
                        events,
                )
                self.assertEqual("normalized", declaration[0])
                self.assertIn("create_landless_adventurer_title_history_effect", declaration[1])

    def test_two_field_historical_adventurer_body_omits_destruction_event(self) -> None:
                history = self.game_root / "history" / "titles" / "titles.txt"
                history.write_text(
                        """
k_islands = {
    866.1.1 = {
        holder = holder_1
        succession_laws = { landless_adventurer_succession_law }
        effect = {
            create_landless_adventurer_title_history_effect = yes
            set_variable = { name = adventurer_creation_reason value = flag:historical }
        }
    }
}
d_ruucuu = {
    866.1.1 = {
        holder = holder_1
        succession_laws = { landless_adventurer_succession_law }
        effect = {
            create_landless_adventurer_title_history_effect = yes
            set_variable = { name = adventurer_creation_reason value = flag:historical }
            set_variable = { name = altered value = yes }
        }
    }
}
""",
                        encoding="utf-8",
                )
                laws = self.game_root / "common" / "laws"
                laws.mkdir(parents=True)
                (laws / "00_succession_laws.txt").write_text(
                        "succession_order_laws = {\n"
                        "  landless_adventurer_succession_law = { }\n"
                        "}\n",
                        encoding="utf-8",
                )
                effects = self.game_root / "common" / "scripted_effects"
                effects.mkdir(parents=True)
                (effects / "07_dlc_ep3_scripted_effects.txt").write_text(
                        """
create_landless_adventurer_title_history_effect = {
    holder ?= {
        if = {
            limit = { NOT = { has_realm_law = landless_adventurer_succession_law } }
            add_realm_law = landless_adventurer_succession_law
        }
    }
}
destroy_landless_title_no_dlc_effect = {
    if = {
        limit = {
            NOT = { has_dlc_feature = roads_to_power }
            game_start_date = $DATE$
        }
        holder ?= {
            empty_treasury_when_abandoning_landed_life_effect = yes
            destroy_title = prev
        }
    }
}
""",
                        encoding="utf-8",
                )
                connection = connect(self.database_path)
                try:
                        connection.execute(
                                """
                                INSERT INTO reference.dlc_packages
                                VALUES ('scribe_build', 'dlc014_ep3', 'Roads to Power', NULL,
                                                NULL, NULL, 'dlc/dlc014_ep3/dlc014.dlc', 'hash',
                                                'https://example.test/wiki?oldid=1', '1', 'valid', NULL)
                                """
                        )
                        connection.execute(
                                """
                                INSERT INTO reference.dlc_feature_mappings
                                VALUES ('scribe_build', 'roads_to_power', 'dlc014_ep3',
                                                'reviewed', 'test evidence')
                                """
                        )
                finally:
                        connection.close()

                load_title_history_candidate(
                        game_root=self.game_root,
                        reference_snapshot_id="scribe_build",
                        baseline_id="scribe_867",
                        database_path=self.database_path,
                )
                connection = connect(self.database_path)
                try:
                        events = connection.execute(
                                """
                                SELECT event_type
                                FROM reference.title_history_events
                                WHERE title_id = 'k_islands'
                                  AND event_type IN ('landless_adventurer_history_initialized',
                                                     'title_variable_set', 'dlc_gated_noop')
                                ORDER BY event_sequence
                                """
                        ).fetchall()
                        variable = connection.execute(
                                """
                                SELECT value_kind, text_value
                                FROM reference.title_baseline_variables
                                WHERE baseline_id = 'scribe_867' AND title_id = 'k_islands'
                                    AND variable_name = 'adventurer_creation_reason'
                                """
                        ).fetchone()
                        declarations = connection.execute(
                                """
                                SELECT title_id, resolution_status
                                FROM source.title_history_declarations
                                WHERE operation_key = 'effect'
                                ORDER BY declaration_order
                                """
                        ).fetchall()
                finally:
                        connection.close()

                self.assertEqual(
                        [
                                ("landless_adventurer_history_initialized",),
                                ("title_variable_set",),
                        ],
                        events,
                )
                self.assertEqual(("flag", "historical"), variable)
                self.assertEqual(
                        [("k_islands", "normalized"), ("d_ruucuu", "preserved")],
                        declarations,
                )

    def test_exact_ceremonial_title_variable_requires_resolved_title(self) -> None:
                history = self.game_root / "history" / "titles" / "titles.txt"
                history.write_text(
                        """
c_ucinaa = {
    500.1.1 = {
        effect = {
            set_variable = { name = ceremonial_title value = title:e_world }
        }
    }
}
d_ruucuu = {
    500.1.1 = {
        effect = {
            set_variable = { name = ceremonial_title value = title:e_world }
            set_variable = { name = altered value = yes }
        }
    }
}
k_islands = {
    500.1.1 = {
        effect = {
            set_variable = { name = ceremonial_title value = title:e_missing }
        }
    }
}
""",
                        encoding="utf-8",
                )

                load_title_history_candidate(
                        game_root=self.game_root,
                        reference_snapshot_id="scribe_build",
                        baseline_id="scribe_867",
                        database_path=self.database_path,
                )
                connection = connect(self.database_path)
                try:
                        variables = connection.execute(
                                """
                                SELECT title_id, variable_name, value_kind, text_value,
                                             source_declaration_order
                                FROM reference.title_baseline_variables
                                WHERE baseline_id = 'scribe_867'
                                ORDER BY title_id
                                """
                        ).fetchall()
                        events = connection.execute(
                                """
                                SELECT title_id, event_type, text_value, validation_note
                                FROM reference.title_history_events
                                WHERE event_type = 'title_variable_set'
                                ORDER BY event_sequence
                                """
                        ).fetchall()
                        declarations = connection.execute(
                                """
                                SELECT title_id, resolution_status
                                FROM source.title_history_declarations
                                WHERE operation_key = 'effect'
                                ORDER BY declaration_order
                                """
                        ).fetchall()
                finally:
                        connection.close()

                self.assertEqual(
                        [("c_ucinaa", "ceremonial_title", "title", "e_world", 1)],
                        variables,
                )
                self.assertEqual(
                        [("c_ucinaa", "title_variable_set", "ceremonial_title=e_world",
                            "value_kind=title")],
                        events,
                )
                self.assertEqual(
                        [
                                ("c_ucinaa", "normalized"),
                                ("d_ruucuu", "preserved"),
                                ("k_islands", "preserved"),
                        ],
                        declarations,
                )

    def test_exact_chrysanthemum_title_law_body_is_fully_replayed(self) -> None:
        titles = self.game_root / "common" / "landed_titles" / "00_titles.txt"
        titles.write_text(
                        """
e_world = {
    k_chrysanthemum_throne = {
        d_chrysanthemum = { c_chrysanthemum = { b_chrysanthemum = { } } }
    }
    k_islands = { d_ruucuu = { c_ucinaa = { b_simajiri = { } } } }
}
""",
            encoding="utf-8",
        )
        load_landed_titles_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            game_version="1.19.0.6",
            steam_build_id="23530548",
            database_path=self.database_path,
        )
        history = self.game_root / "history" / "titles" / "titles.txt"
        history.write_text(
            """
k_chrysanthemum_throne = {
  867.1.1 = { effect = {
    add_title_law = single_heir_succession_law
    destroy_landless_title_no_tgp_dlc_effect = { DATE = 867.1.1 }
  } }
}
k_islands = {
  867.1.1 = { effect = {
    add_title_law = single_heir_succession_law
    destroy_landless_title_no_tgp_dlc_effect = { DATE = 867.1.1 }
  } }
}
d_ruucuu = {
  867.1.1 = { effect = {
    destroy_landless_title_no_tgp_dlc_effect = { DATE = 867.1.1 }
    add_title_law = single_heir_succession_law
  } }
}
""",
            encoding="utf-8",
        )
        laws = self.game_root / "common" / "laws"
        laws.mkdir(parents=True)
        (laws / "00_succession_laws.txt").write_text(
                        """
succession_order_laws = {
    single_heir_succession_law = {
        succession = { order_of_succession = inheritance }
    }
}
""",
            encoding="utf-8",
        )
        effects = self.game_root / "common" / "scripted_effects"
        effects.mkdir(parents=True)
        (effects / "10_dlc_tgp_scripted_effects.txt").write_text(
            """
destroy_landless_title_no_tgp_dlc_effect = {
  if = {
    limit = {
      NOT = { has_dlc_feature = all_under_heaven }
      game_start_date = $DATE$
    }
    holder ?= {
      empty_treasury_when_abandoning_landed_life_effect = yes
      destroy_title = prev
    }
  }
}
""",
            encoding="utf-8",
        )
        triggers = self.game_root / "common" / "scripted_triggers"
        triggers.mkdir(parents=True)
        (triggers / "00_has_dlc_scripted_triggers.txt").write_text(
            "has_tgp_dlc_trigger = { has_dlc_feature = all_under_heaven }\n",
            encoding="utf-8",
        )
        connection = connect(self.database_path)
        try:
            connection.execute(
                """
                INSERT INTO reference.dlc_packages
                VALUES ('scribe_build', 'dlc022_ep4', 'All Under Heaven', NULL,
                        NULL, NULL, 'dlc/dlc022_ep4/dlc022.dlc', 'hash',
                        'https://example.test/wiki?oldid=1', '1', 'valid', NULL)
                """
            )
            connection.execute(
                """
                INSERT INTO reference.dlc_feature_mappings
                VALUES ('scribe_build', 'all_under_heaven', 'dlc022_ep4',
                        'reviewed', 'test evidence')
                """
            )
        finally:
            connection.close()

        arguments = dict(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            database_path=self.database_path,
        )
        load_title_history_candidate(**arguments)
        load_title_history_candidate(**arguments)
        connection = connect(self.database_path)
        try:
            laws = connection.execute(
                """
                SELECT title_id, law_order, law_id, effective_date,
                       source_declaration_order
                FROM reference.title_baseline_laws
                ORDER BY title_id, law_order
                """
            ).fetchall()
            events = connection.execute(
                """
                SELECT event_type, text_value, required_game_start_date
                FROM reference.title_history_events
                WHERE title_id = 'k_chrysanthemum_throne'
                ORDER BY event_sequence
                """
            ).fetchall()
            declarations = connection.execute(
                """
                SELECT title_id, resolution_status
                FROM source.title_history_declarations
                WHERE operation_key = 'effect'
                ORDER BY title_id
                """
            ).fetchall()
            states = connection.execute(
                """
                SELECT title_id, validation_status
                FROM reference.title_baseline_states
                WHERE title_id IN ('k_chrysanthemum_throne', 'k_islands', 'd_ruucuu')
                ORDER BY title_id
                """
            ).fetchall()
        finally:
            connection.close()

        self.assertEqual(
            [("k_chrysanthemum_throne", 1, "single_heir_succession_law",
              date(867, 1, 1), 1)],
            laws,
        )
        self.assertEqual(
            [
                ("title_law_added", "single_heir_succession_law", None),
                ("dlc_gated_noop", "all_under_heaven", "0867-01-01"),
            ],
            events,
        )
        self.assertEqual(
            [
                ("d_ruucuu", "preserved"),
                ("k_chrysanthemum_throne", "normalized"),
                ("k_islands", "preserved"),
            ],
            declarations,
        )
        self.assertEqual(
            [
                ("k_chrysanthemum_throne", "valid"),
                ("k_islands", "warning"),
            ],
            states,
        )

    def test_exact_e_japan_court_and_administrative_variable_body_replays(self) -> None:
                titles = self.game_root / "common" / "landed_titles" / "00_titles.txt"
                titles.write_text(
                        """
e_world = {
    e_japan = { k_japan = { d_japan = { c_japan = { b_japan = { } } } } }
    k_chrysanthemum_throne = {
        d_chrysanthemum = { c_chrysanthemum = { b_chrysanthemum = { } } }
    }
    k_islands = { d_ruucuu = { c_ucinaa = { b_simajiri = { } } } }
}
""",
                        encoding="utf-8",
                )
                load_landed_titles_candidate(
                        game_root=self.game_root,
                        reference_snapshot_id="scribe_build",
                        baseline_id="scribe_867",
                        game_version="1.19.0.6",
                        steam_build_id="23530548",
                        database_path=self.database_path,
                )
                history = self.game_root / "history" / "titles" / "titles.txt"
                exact_body = """
        if = {
            limit = { exists = holder has_dlc_feature = royal_court }
            holder = { set_court_language = language_chinese }
        }
        if = {
            limit = { has_tgp_dlc_trigger = yes }
            set_variable = {
                name = administrative_ui_special_title
                value = title:k_chrysanthemum_throne
            }
        }
"""
                history.write_text(
                        f"""
e_japan = {{
    858.1.1 = {{ holder = japanese_holder }}
    867.1.1 = {{ effect = {{{exact_body}  }} }}
}}
k_islands = {{
    858.1.1 = {{ holder = wrong_title_holder }}
    867.1.1 = {{ effect = {{{exact_body}  }} }}
}}
d_ruucuu = {{
    858.1.1 = {{ holder = reversed_holder }}
    867.1.1 = {{ effect = {{
        if = {{
            limit = {{ has_tgp_dlc_trigger = yes }}
            set_variable = {{
                name = administrative_ui_special_title
                value = title:k_chrysanthemum_throne
            }}
        }}
        if = {{
            limit = {{ exists = holder has_dlc_feature = royal_court }}
            holder = {{ set_court_language = language_chinese }}
        }}
    }} }}
}}
""",
                        encoding="utf-8",
                )
                effects = self.game_root / "common" / "scripted_effects"
                effects.mkdir(parents=True)
                (effects / "10_dlc_tgp_scripted_effects.txt").write_text(
                        """
destroy_landless_title_no_tgp_dlc_effect = {
    if = {
        limit = {
            NOT = { has_dlc_feature = all_under_heaven }
            game_start_date = $DATE$
        }
        holder ?= {
            empty_treasury_when_abandoning_landed_life_effect = yes
            destroy_title = prev
        }
    }
}
""",
                        encoding="utf-8",
                )
                triggers = self.game_root / "common" / "scripted_triggers"
                triggers.mkdir(parents=True)
                (triggers / "00_has_dlc_scripted_triggers.txt").write_text(
                        "has_tgp_dlc_trigger = { has_dlc_feature = all_under_heaven }\n",
                        encoding="utf-8",
                )
                connection = connect(self.database_path)
                try:
                        connection.execute(
                                """
                                INSERT INTO reference.languages
                                VALUES ('scribe_build', 'language_chinese', 'common/culture/test.txt',
                                                1, 1, 1, '{}', '1.1.0', 'valid', NULL)
                                """
                        )
                        for package_id, name, feature, path in (
                                ('dlc004_ep1', 'The Royal Court', 'royal_court',
                                 'dlc/dlc004_ep1/dlc004.dlc'),
                                ('dlc022_ep4', 'All Under Heaven', 'all_under_heaven',
                                 'dlc/dlc022_ep4/dlc022.dlc'),
                        ):
                                connection.execute(
                                        """
                                        INSERT INTO reference.dlc_packages
                                        VALUES ('scribe_build', ?, ?, NULL, NULL, NULL, ?, 'hash',
                                                        'https://example.test/wiki?oldid=1', '1', 'valid', NULL)
                                        """,
                                        [package_id, name, path],
                                )
                                connection.execute(
                                        """
                                        INSERT INTO reference.dlc_feature_mappings
                                        VALUES ('scribe_build', ?, ?, 'reviewed', 'test evidence')
                                        """,
                                        [feature, package_id],
                                )
                finally:
                        connection.close()

                arguments = dict(
                        game_root=self.game_root,
                        reference_snapshot_id="scribe_build",
                        baseline_id="scribe_867",
                        database_path=self.database_path,
                )
                load_title_history_candidate(**arguments)
                load_title_history_candidate(**arguments)
                connection = connect(self.database_path)
                try:
                        variables = connection.execute(
                                """
                                SELECT title_id, variable_name, value_kind, text_value,
                                             source_declaration_order
                                FROM reference.title_baseline_variables
                                ORDER BY title_id, variable_name
                                """
                        ).fetchall()
                        events = connection.execute(
                                """
                                SELECT event_type, text_value, validation_note
                                FROM reference.title_history_events
                                WHERE title_id = 'e_japan'
                                    AND event_type IN ('court_language_set',
                                                       'title_variable_set')
                                ORDER BY event_sequence
                                """
                        ).fetchall()
                        declarations = connection.execute(
                                """
                                SELECT title_id, resolution_status
                                FROM source.title_history_declarations
                                WHERE operation_key = 'effect'
                                ORDER BY title_id
                                """
                        ).fetchall()
                        court_state = connection.execute(
                                """
                                SELECT character_id, court_language_id,
                                             court_language_source_declaration_order
                                FROM reference.character_baseline_court_states
                                ORDER BY character_id
                                """
                        ).fetchall()
                        personal_languages = connection.execute(
                                "SELECT count(*) FROM reference.character_baseline_languages"
                        ).fetchone()
                finally:
                        connection.close()

                self.assertEqual(
                        [("e_japan", "administrative_ui_special_title", "title",
                            "k_chrysanthemum_throne", 2)],
                        variables,
                )
                self.assertEqual(
                        [
                                ("court_language_set", "language_chinese",
                                 "holder=japanese_holder; installed royal_court"),
                                ("title_variable_set",
                                 "administrative_ui_special_title=k_chrysanthemum_throne",
                                 "value_kind=title"),
                        ],
                        events,
                )
                self.assertEqual(
                        [
                                ("d_ruucuu", "preserved"),
                                ("e_japan", "normalized"),
                                ("k_islands", "preserved"),
                        ],
                        declarations,
                )
                self.assertEqual(
                        [
                                ("japanese_holder", "language_chinese", 2),
                                ("reversed_holder", "language_chinese", 6),
                                ("wrong_title_holder", "language_chinese", 4),
                        ],
                        court_state,
                )
                self.assertEqual((0,), personal_languages)

    def test_exact_byzantine_administrative_state_faith_body_replays(self) -> None:
                titles = self.game_root / "common" / "landed_titles" / "00_titles.txt"
                titles.write_text(
                        """
e_world = {
    e_byzantium = { k_byzantium = { d_byzantium = { c_byzantium = { b_byzantium = { } } } } }
    k_islands = { d_ruucuu = { c_ucinaa = { b_simajiri = { } } } }
}
""",
                        encoding="utf-8",
                )
                load_landed_titles_candidate(
                        game_root=self.game_root,
                        reference_snapshot_id="scribe_build",
                        baseline_id="scribe_867",
                        game_version="1.19.0.6",
                        steam_build_id="23530548",
                        database_path=self.database_path,
                )
                exact_effect = """
    effect = {
        if = {
            limit = {
                exists = holder
                holder = { has_government = administrative_government }
            }
            set_state_faith = faith:orthodox
        }
        if = {
            limit = { exists = holder has_dlc_feature = royal_court }
            holder = { set_court_type = court_intrigue }
        }
        if = {
            limit = {
                exists = holder
                NOT = { has_dlc_feature = roads_to_power }
            }
            holder = {
                change_government = feudal_government
                add_realm_law_skip_effects = single_heir_succession_law
            }
        }
    }
"""
                history = self.game_root / "history" / "titles" / "titles.txt"
                history.write_text(
                        f"""
e_byzantium = {{
    800.1.1 = {{ holder = byzantine_holder }}
    866.1.1 = {{ government = administrative_government {exact_effect} }}
}}
k_islands = {{
    800.1.1 = {{ holder = wrong_title_holder }}
    866.1.1 = {{ government = administrative_government {exact_effect} }}
}}
""",
                        encoding="utf-8",
                )
                effects = self.game_root / "common" / "scripted_effects"
                effects.mkdir(parents=True)
                (effects / "07_dlc_ep3_scripted_effects.txt").write_text(
                        """
destroy_landless_title_no_dlc_effect = {
    if = {
        limit = {
            NOT = { has_dlc_feature = roads_to_power }
            game_start_date = $DATE$
        }
        holder ?= {
            empty_treasury_when_abandoning_landed_life_effect = yes
            destroy_title = prev
        }
    }
}
""",
                        encoding="utf-8",
                )
                connection = connect(self.database_path)
                try:
                        connection.execute(
                                """
                                INSERT INTO reference.faiths VALUES
                                ('scribe_build', 'orthodox', 'christianity_religion',
                                 'common/religion/faiths/test.txt', 1, 2, 1, '{}', '1.0.0',
                                 'faith', 'valid', NULL)
                                """
                        )
                        connection.execute(
                                """
                                INSERT INTO reference.character_baseline_states VALUES
                                ('scribe_867', 'byzantine_holder', 'Basileios', 'male',
                                 'declared', NULL, 'orthodox', 'history', NULL, NULL, NULL,
                                 NULL, 'alive', 'valid', NULL)
                                """
                        )
                        for package_id, name, feature, path in (
                                ('dlc004_ep1', 'The Royal Court', 'royal_court',
                                 'dlc/dlc004_ep1/dlc004.dlc'),
                                ('dlc014_ep3', 'Roads to Power', 'roads_to_power',
                                 'dlc/dlc014_ep3/dlc014.dlc'),
                        ):
                                connection.execute(
                                        """
                                        INSERT INTO reference.dlc_packages
                                        VALUES ('scribe_build', ?, ?, NULL, NULL, NULL, ?, 'hash',
                                                        'https://example.test/wiki?oldid=1', '1', 'valid', NULL)
                                        """,
                                        [package_id, name, path],
                                )
                                connection.execute(
                                        """
                                        INSERT INTO reference.dlc_feature_mappings
                                        VALUES ('scribe_build', ?, ?, 'reviewed', 'test evidence')
                                        """,
                                        [feature, package_id],
                                )
                finally:
                        connection.close()

                arguments = dict(
                        game_root=self.game_root,
                        reference_snapshot_id="scribe_build",
                        baseline_id="scribe_867",
                        database_path=self.database_path,
                )
                load_title_history_candidate(**arguments)
                load_title_history_candidate(**arguments)
                connection = connect(self.database_path)
                try:
                        state_faiths = connection.execute(
                                """
                                SELECT title_id, faith_id, effective_date, source_group,
                                             source_declaration_order
                                FROM reference.title_baseline_state_faiths
                                ORDER BY title_id
                                """
                        ).fetchall()
                        events = connection.execute(
                                """
                                SELECT event_type, text_value, validation_note
                                FROM reference.title_history_events
                                WHERE title_id = 'e_byzantium'
                                    AND event_type IN ('court_type_set', 'state_faith_set',
                                                                         'dlc_gated_conditional_noop')
                                ORDER BY event_sequence
                                """
                        ).fetchall()
                        declarations = connection.execute(
                                """
                                SELECT title_id, resolution_status
                                FROM source.title_history_declarations
                                WHERE operation_key = 'effect'
                                ORDER BY title_id
                                """
                        ).fetchall()
                        personal_faith = connection.execute(
                                """
                                SELECT faith_id, faith_source_key
                                FROM reference.character_baseline_states
                                WHERE baseline_id = 'scribe_867'
                                    AND character_id = 'byzantine_holder'
                                """
                        ).fetchone()
                finally:
                        connection.close()

                self.assertEqual(
                        [("e_byzantium", "orthodox", date(866, 1, 1), "title_history", 3)],
                        state_faiths,
                )
                self.assertEqual(
                        [
                                ("court_type_set", "court_intrigue",
                                 "holder=byzantine_holder; installed royal_court"),
                                ("state_faith_set", "orthodox",
                                 "holder=byzantine_holder; government=administrative_government"),
                                ("dlc_gated_conditional_noop", "roads_to_power",
                                 "installed dlc014_ep3 makes government fallback condition false"),
                        ],
                        events,
                )
                self.assertEqual(
                        [("e_byzantium", "normalized"), ("k_islands", "preserved")],
                        declarations,
                )
                self.assertEqual(("orthodox", "history"), personal_faith)

                history.write_text(
                        f"""
e_byzantium = {{
    800.1.1 = {{ holder = byzantine_holder }}
    866.1.1 = {{ government = feudal_government {exact_effect} }}
}}
""",
                        encoding="utf-8",
                )
                load_title_history_candidate(**arguments)
                connection = connect(self.database_path)
                try:
                        self.assertEqual(
                                (0,),
                                connection.execute(
                                        "SELECT count(*) FROM reference.title_baseline_state_faiths"
                                ).fetchone(),
                        )
                        self.assertEqual(
                                ("warning",),
                                connection.execute(
                                        """
                                        SELECT validation_status FROM reference.title_baseline_states
                                        WHERE baseline_id = 'scribe_867' AND title_id = 'e_byzantium'
                                        """
                                ).fetchone(),
                        )
                finally:
                        connection.close()

    def test_succession_laws_replace_and_clear_with_installed_definitions(self) -> None:
        history = self.game_root / "history" / "titles"
        (history / "law_history.txt").write_text(
            """
d_ruucuu = {
  700.1.1 = { succession_laws = { feudal_elective_succession_law male_only_law } }
  800.1.1 = { succession_laws = { male_only_law } }
}
k_islands = {
  700.1.1 = { succession_laws = { feudal_elective_succession_law } }
  800.1.1 = { succession_laws = { } }
}
""",
            encoding="utf-8",
        )
        laws = self.game_root / "common" / "laws"
        laws.mkdir(parents=True)
        (laws / "00_succession_laws.txt").write_text(
            """
succession_order_laws = {
  feudal_elective_succession_law = { succession = { order_of_succession = election } }
}
succession_gender_laws = {
  male_only_law = { succession = { gender_law = male_only } }
}
""",
            encoding="utf-8",
        )
        (laws / "_laws.info").write_text(
            "law_group_name = { law_name = { succession = { order_of_succession = inheritance } } }\n",
            encoding="utf-8",
        )

        load_title_history_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            database_path=self.database_path,
        )
        connection = connect(self.database_path)
        try:
            definitions = connection.execute(
                """
                SELECT law_id, law_group_id, source_path
                FROM reference.law_definitions
                WHERE reference_snapshot_id = 'scribe_build'
                ORDER BY law_id
                """
            ).fetchall()
            active_laws = connection.execute(
                """
                SELECT title_id, law_order, law_id, effective_date,
                       source_declaration_order, validation_status
                FROM reference.title_baseline_laws
                WHERE baseline_id = 'scribe_867'
                ORDER BY title_id, law_order
                """
            ).fetchall()
            declarations = connection.execute(
                """
                SELECT title_id, effective_date, resolution_status
                FROM source.title_history_declarations
                WHERE operation_key = 'succession_laws'
                ORDER BY title_id, effective_date
                """
            ).fetchall()
            events = connection.execute(
                """
                SELECT title_id, effective_date, text_value
                FROM reference.title_history_events
                WHERE event_type = 'succession_laws_replaced'
                ORDER BY title_id, effective_date
                """
            ).fetchall()
        finally:
            connection.close()

        self.assertEqual(
            [
                ("feudal_elective_succession_law", "succession_order_laws", "common/laws/00_succession_laws.txt"),
                ("male_only_law", "succession_gender_laws", "common/laws/00_succession_laws.txt"),
            ],
            definitions,
        )
        self.assertEqual(
            [("d_ruucuu", 1, "male_only_law", date(800, 1, 1), 2, "valid")],
            active_laws,
        )
        self.assertEqual(
            [
                ("d_ruucuu", "0700-01-01", "normalized"),
                ("d_ruucuu", "0800-01-01", "normalized"),
                ("k_islands", "0700-01-01", "normalized"),
                ("k_islands", "0800-01-01", "normalized"),
            ],
            declarations,
        )
        self.assertEqual(
            [
                ("d_ruucuu", "0700-01-01", "feudal_elective_succession_law,male_only_law"),
                ("d_ruucuu", "0800-01-01", "male_only_law"),
                ("k_islands", "0700-01-01", "feudal_elective_succession_law"),
                ("k_islands", "0800-01-01", ""),
            ],
            events,
        )
        inspection = get_title_inspection(
            "scribe_867", "d_ruucuu", self.database_path
        )
        self.assertIsNotNone(inspection)
        self.assertEqual(
            [
                {
                    "law_order": 1,
                    "law_id": "male_only_law",
                    "law_group_id": "succession_gender_laws",
                    "effective_date": date(800, 1, 1),
                    "source_declaration_order": 2,
                    "source_path": "common/laws/00_succession_laws.txt",
                    "source_line_start": 6,
                    "source_line_end": 6,
                    "validation_status": "valid",
                    "validation_note": None,
                }
            ],
            inspection["laws"],
        )

    def test_de_jure_liege_replaces_and_clears_without_changing_hierarchy(self) -> None:
        history = self.game_root / "history" / "titles" / "titles.txt"
        history.write_text(
            """
c_ucinaa = {
  700.1.1 = { de_jure_liege = d_ruucuu }
  800.1.1 = { de_jure_liege = e_world }
}
d_ruucuu = {
  700.1.1 = { de_jure_liege = k_islands }
  800.1.1 = { de_jure_liege = 0 }
}
""",
            encoding="utf-8",
        )

        load_title_history_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            database_path=self.database_path,
        )
        connection = connect(self.database_path)
        try:
            states = connection.execute(
                """
                SELECT title_id, de_jure_liege_title_id, de_jure_liege_status,
                       effective_date, source_declaration_order
                FROM reference.title_baseline_de_jure_lieges
                WHERE baseline_id = 'scribe_867'
                ORDER BY title_id
                """
            ).fetchall()
            events = connection.execute(
                """
                SELECT title_id, effective_date, text_value, validation_status
                FROM reference.title_history_events
                WHERE event_type = 'de_jure_liege_replaced'
                ORDER BY title_id, effective_date
                """
            ).fetchall()
            declarations = connection.execute(
                """
                SELECT scalar_value, raw_script, resolution_status
                FROM source.title_history_declarations
                WHERE operation_key = 'de_jure_liege'
                ORDER BY declaration_order
                """
            ).fetchall()
            static_parent = connection.execute(
                """
                SELECT parent_title_id FROM reference.titles
                WHERE baseline_id = 'scribe_867' AND title_id = 'c_ucinaa'
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(
            [
                ("c_ucinaa", "e_world", "declared", date(800, 1, 1), 2),
                ("d_ruucuu", None, "explicit_clear", date(800, 1, 1), 4),
            ],
            states,
        )
        self.assertEqual(
            [
                ("c_ucinaa", "0700-01-01", "d_ruucuu", "valid"),
                ("c_ucinaa", "0800-01-01", "e_world", "valid"),
                ("d_ruucuu", "0700-01-01", "k_islands", "valid"),
                ("d_ruucuu", "0800-01-01", None, "valid"),
            ],
            events,
        )
        self.assertEqual(
            [
                ("d_ruucuu", "d_ruucuu", "normalized"),
                ("e_world", "e_world", "normalized"),
                ("k_islands", "k_islands", "normalized"),
                ("0", "0", "normalized"),
            ],
            declarations,
        )
        self.assertEqual(("d_ruucuu",), static_parent)
        inspection = get_title_inspection(
            "scribe_867", "c_ucinaa", self.database_path
        )
        self.assertIsNotNone(inspection)
        self.assertEqual("d_ruucuu", inspection["parent_title_id"])
        self.assertEqual("e_world", inspection["de_jure_liege_title_id"])
        self.assertEqual("declared", inspection["de_jure_liege_status"])
        self.assertEqual(date(800, 1, 1), inspection["de_jure_effective_date"])
        self.assertEqual(2, inspection["de_jure_source_declaration_order"])

    def test_exact_de_jure_liege_effect_replays_but_mixed_body_remains_opaque(self) -> None:
        history = self.game_root / "history" / "titles" / "titles.txt"
        history.write_text(
            """
k_islands = {
  800.1.1 = {
    effect = { set_de_jure_liege_title = title:e_world }
  }
}
d_ruucuu = {
  800.1.1 = {
    effect = {
      set_de_jure_liege_title = title:e_world
      set_variable = altered
    }
  }
}
c_ucinaa = {
    800.1.1 = {
        effect = { set_de_jure_liege_title = e_world }
    }
}
b_other = {
    800.1.1 = {
        effect = { set_de_jure_liege_title = title:e_missing }
    }
}
""",
            encoding="utf-8",
        )

        load_title_history_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            database_path=self.database_path,
        )
        connection = connect(self.database_path)
        try:
            de_jure = connection.execute(
                """
                SELECT title_id, de_jure_liege_title_id, de_jure_liege_status,
                       effective_date, source_declaration_order
                FROM reference.title_baseline_de_jure_lieges
                WHERE baseline_id = 'scribe_867'
                ORDER BY title_id
                """
            ).fetchall()
            states = connection.execute(
                """
                SELECT title_id, validation_status, validation_note
                FROM reference.title_baseline_states
                WHERE baseline_id = 'scribe_867'
                                    AND title_id IN ('k_islands', 'd_ruucuu', 'c_ucinaa', 'b_other')
                ORDER BY title_id
                """
            ).fetchall()
            declarations = connection.execute(
                """
                SELECT title_id, resolution_status, raw_script
                FROM source.title_history_declarations
                WHERE operation_key = 'effect'
                ORDER BY declaration_order
                """
            ).fetchall()
            event = connection.execute(
                """
                SELECT title_id, event_type, text_value, validation_note
                FROM reference.title_history_events
                WHERE event_type = 'de_jure_liege_replaced'
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(
            [("k_islands", "e_world", "declared", date(800, 1, 1), 1)],
            de_jure,
        )
        self.assertEqual(
            [
                ("b_other", "warning", "not evaluated: effect"),
                ("c_ucinaa", "warning", "not evaluated: effect"),
                ("d_ruucuu", "warning", "not evaluated: effect"),
                ("k_islands", "valid", None),
            ],
            states,
        )
        self.assertEqual("normalized", declarations[0][1])
        self.assertIn("set_de_jure_liege_title", declarations[0][2])
        self.assertEqual("preserved", declarations[1][1])
        self.assertEqual("preserved", declarations[2][1])
        self.assertEqual("preserved", declarations[3][1])
        self.assertEqual(
            (
                "k_islands",
                "de_jure_liege_replaced",
                "e_world",
                "effect-form title-scope de-jure replacement",
            ),
            event,
        )

    def test_dynasty_prestige_helper_materializes_a_floor_not_an_exact_level(self) -> None:
        history = self.game_root / "history" / "titles" / "titles.txt"
        history.write_text(
            """
c_ucinaa = {
  700.1.1 = { holder = first_holder }
  800.1.1 = {
    effect = { tgp_set_minamoto_taira_dynasty_prestige_effect = yes }
  }
}
d_ruucuu = {
  800.1.1 = {
    effect = { tgp_set_minamoto_taira_dynasty_prestige_effect = yes }
  }
}
k_islands = {
  700.1.1 = { holder = first_holder }
  800.1.1 = {
    effect = {
      tgp_set_minamoto_taira_dynasty_prestige_effect = yes
      set_variable = altered
    }
  }
}
""",
            encoding="utf-8",
        )
        effects = self.game_root / "common" / "scripted_effects"
        effects.mkdir(parents=True)
        helper = effects / "10_dlc_tgp_japan_scripted_effects.txt"
        helper.write_text(
            """
tgp_set_minamoto_taira_dynasty_prestige_effect = {
  holder.dynasty ?= {
    while = {
      limit = { dynasty_prestige_level < 5 }
      add_dynasty_prestige_level = 1
    }
  }
}
""",
            encoding="utf-8",
        )
        connection = connect(self.database_path)
        try:
            connection.execute(
                """
                INSERT INTO reference.dynasties VALUES
                ('scribe_build', 'test_dynasty', 'common/dynasties/test.txt',
                 1, 1, 1, '{}', '1.0.0', 'dynasty', 'valid', NULL)
                """
            )
            connection.execute(
                """
                INSERT INTO reference.character_baseline_states VALUES
                ('scribe_867', 'first_holder', 'First Holder', 'male', 'default',
                 NULL, NULL, NULL, 'test_dynasty', NULL, NULL, NULL, 'alive',
                 'valid', NULL)
                """
            )
        finally:
            connection.close()

        load_title_history_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            database_path=self.database_path,
        )
        connection = connect(self.database_path)
        try:
            constraints = connection.execute(
                """
                SELECT dynasty_id, minimum_prestige_level, value_status,
                       effective_date, source_title_id, source_holder_character_id,
                       source_declaration_order, helper_source_path,
                       validation_status
                FROM reference.dynasty_baseline_prestige_constraints
                WHERE baseline_id = 'scribe_867'
                """
            ).fetchall()
            declarations = connection.execute(
                """
                SELECT title_id, resolution_status
                FROM source.title_history_declarations
                WHERE operation_key = 'effect'
                ORDER BY declaration_order
                """
            ).fetchall()
            states = connection.execute(
                """
                SELECT title_id, validation_status, validation_note
                FROM reference.title_baseline_states
                WHERE baseline_id = 'scribe_867'
                  AND title_id IN ('c_ucinaa', 'd_ruucuu', 'k_islands')
                ORDER BY title_id
                """
            ).fetchall()
            event = connection.execute(
                """
                SELECT title_id, event_type, text_value, integer_value,
                       validation_note
                FROM reference.title_history_events
                WHERE event_type = 'dynasty_prestige_minimum_established'
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(
            [
                (
                    "test_dynasty", 5, "lower_bound_only", date(800, 1, 1),
                    "c_ucinaa", "first_holder", 2,
                    "common/scripted_effects/10_dlc_tgp_japan_scripted_effects.txt",
                    "valid",
                )
            ],
            constraints,
        )
        self.assertEqual(
            [
                ("c_ucinaa", "normalized"),
                ("d_ruucuu", "preserved"),
                ("k_islands", "preserved"),
            ],
            declarations,
        )
        self.assertEqual(
            [
                ("c_ucinaa", "valid", None),
                ("d_ruucuu", "warning", "not evaluated: effect"),
                ("k_islands", "warning", "not evaluated: effect"),
            ],
            states,
        )
        self.assertEqual(
            (
                "c_ucinaa", "dynasty_prestige_minimum_established",
                "test_dynasty", 5,
                "holder=first_holder; lower_bound_only",
            ),
            event,
        )
        inspection = get_title_inspection(
            "scribe_867", "c_ucinaa", self.database_path
        )
        self.assertEqual(
            "test_dynasty",
            inspection["dynasty_prestige_constraints"][0]["dynasty_id"],
        )
        self.assertEqual(
            5,
            inspection["dynasty_prestige_constraints"][0]["minimum_prestige_level"],
        )
        helper.write_text(
            """
tgp_set_minamoto_taira_dynasty_prestige_effect = {
  holder.dynasty ?= { add_dynasty_prestige_level = 5 }
}
""",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            ValueError, "dynasty-prestige helper does not match reviewed semantics"
        ):
            load_title_history_candidate(
                game_root=self.game_root,
                reference_snapshot_id="scribe_build",
                baseline_id="scribe_867",
                database_path=self.database_path,
            )
        connection = connect(self.database_path)
        try:
            retained_count = connection.execute(
                """
                SELECT count(*)
                FROM reference.dynasty_baseline_prestige_constraints
                WHERE baseline_id = 'scribe_867'
                """
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual((1,), retained_count)

    def test_direct_dynasty_prestige_floor_uses_unambiguous_dynasty_field(self) -> None:
        history = self.game_root / "history" / "titles" / "titles.txt"
        history.write_text(
            """
c_ucinaa = {
  700.1.1 = {
    holder = warning_holder
    effect = {
      holder.dynasty ?= {
        while = {
          limit = { dynasty_prestige_level < 9 }
          add_dynasty_prestige_level = 1
        }
      }
    }
  }
}
d_ruucuu = {
  700.1.1 = {
    holder = warning_holder
    effect = {
      holder.dynasty ?= {
        while = {
          limit = { dynasty_prestige_level < 9 }
          add_dynasty_prestige_level = 1
        }
      }
      set_variable = altered
    }
  }
}
""",
            encoding="utf-8",
        )
        connection = connect(self.database_path)
        try:
            connection.execute(
                """
                INSERT INTO reference.dynasties VALUES
                ('scribe_build', 'warning_dynasty', 'common/dynasties/test.txt',
                 1, 1, 1, '{}', '1.0.0', 'dynasty', 'valid', NULL)
                """
            )
            connection.execute(
                """
                INSERT INTO reference.character_baseline_states VALUES
                ('scribe_867', 'warning_holder', 'Warning Holder', 'male',
                 'default', NULL, NULL, NULL, 'warning_dynasty', NULL, NULL,
                 NULL, 'alive', 'warning', 'not evaluated: unrelated effect')
                """
            )
        finally:
            connection.close()

        load_title_history_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            database_path=self.database_path,
        )
        connection = connect(self.database_path)
        try:
            constraints = connection.execute(
                """
                SELECT dynasty_id, minimum_prestige_level, value_status,
                       source_title_id, source_holder_character_id,
                       source_declaration_order, helper_source_path,
                       helper_raw_sha256
                FROM reference.dynasty_baseline_prestige_constraints
                WHERE baseline_id = 'scribe_867'
                """
            ).fetchall()
            declarations = connection.execute(
                """
                SELECT title_id, resolution_status
                FROM source.title_history_declarations
                WHERE operation_key = 'effect'
                ORDER BY declaration_order
                """
            ).fetchall()
            event = connection.execute(
                """
                SELECT integer_value
                FROM reference.title_history_events
                WHERE title_id = 'c_ucinaa'
                  AND event_type = 'dynasty_prestige_minimum_established'
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(
            [
                (
                    "warning_dynasty", 9, "lower_bound_only", "c_ucinaa",
                    "warning_holder", 2, "history/titles/titles.txt", None,
                )
            ],
            constraints,
        )
        self.assertEqual(
            [("c_ucinaa", "normalized"), ("d_ruucuu", "preserved")],
            declarations,
        )
        self.assertEqual((9,), event)

    def test_tributary_relationship_replaces_without_changing_liege_or_de_jure(self) -> None:
        history = self.game_root / "history" / "titles" / "titles.txt"
        history.write_text(
            """
c_ucinaa = {
  700.1.1 = {
    tributary_of = { suzerain = d_ruucuu contract_group = tributary_mandala }
  }
  800.1.1 = {
    tributary_of = { suzerain = k_islands contract_group = tributary_mandala }
  }
}
c_future = {
    700.1.1 = {
        tributary_of = { suzerain = d_missing contract_group = tributary_mandala }
    }
}
""",
            encoding="utf-8",
        )
        groups = self.game_root / "common" / "subject_contracts" / "groups"
        groups.mkdir(parents=True)
        (groups / "subject_contract_groups.txt").write_text(
            "tributary_mandala = { is_tributary = yes }\n",
            encoding="utf-8",
        )

        load_title_history_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            database_path=self.database_path,
        )
        connection = connect(self.database_path)
        try:
            state = connection.execute(
                """
                SELECT suzerain_title_id, contract_group_id, effective_date,
                       source_declaration_order, validation_status
                FROM reference.title_baseline_tributaries
                WHERE baseline_id = 'scribe_867' AND title_id = 'c_ucinaa'
                """
            ).fetchone()
            events = connection.execute(
                """
                SELECT effective_date, text_value, validation_note
                FROM reference.title_history_events
                WHERE title_id = 'c_ucinaa'
                  AND event_type = 'tributary_relationship_replaced'
                ORDER BY effective_date
                """
            ).fetchall()
            declarations = connection.execute(
                """
                SELECT raw_script, resolution_status
                FROM source.title_history_declarations
                WHERE title_id = 'c_ucinaa' AND operation_key = 'tributary_of'
                ORDER BY declaration_order
                """
            ).fetchall()
            title_state = connection.execute(
                """
                SELECT liege_title_id FROM reference.title_baseline_states
                WHERE baseline_id = 'scribe_867' AND title_id = 'c_ucinaa'
                """
            ).fetchone()
            unresolved = connection.execute(
                """
                SELECT validation_note FROM reference.title_baseline_states
                WHERE baseline_id = 'scribe_867' AND title_id = 'c_future'
                """
            ).fetchone()
            unresolved_relationship = connection.execute(
                """
                SELECT count(*) FROM reference.title_baseline_tributaries
                WHERE baseline_id = 'scribe_867' AND title_id = 'c_future'
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(
            ("k_islands", "tributary_mandala", date(800, 1, 1), 2, "valid"),
            state,
        )
        self.assertEqual(
            [
                ("0700-01-01", "d_ruucuu", "contract_group=tributary_mandala"),
                ("0800-01-01", "k_islands", "contract_group=tributary_mandala"),
            ],
            events,
        )
        self.assertEqual(["normalized", "normalized"], [row[1] for row in declarations])
        self.assertIn("suzerain = d_ruucuu", declarations[0][0])
        self.assertEqual((None,), title_state)
        self.assertIn("tributary_of", unresolved[0])
        self.assertEqual((0,), unresolved_relationship)
        inspection = get_title_inspection(
            "scribe_867", "c_ucinaa", self.database_path
        )
        self.assertEqual("k_islands", inspection["suzerain_title_id"])
        self.assertEqual("tributary_mandala", inspection["tributary_contract_group_id"])
        self.assertEqual("d_ruucuu", inspection["parent_title_id"])


if __name__ == "__main__":
    unittest.main()