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


if __name__ == "__main__":
    unittest.main()