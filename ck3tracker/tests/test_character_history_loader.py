"""Tests for candidate character history and holder lifecycle validation."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from logic.character_history_loader import load_character_history_candidate
from logic.landed_titles_loader import load_landed_titles_candidate
from logic.reference_inspector_provider import get_title_inspection
from logic.root_database import connect
from logic.title_history_loader import load_title_history_candidate


class CharacterHistoryLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.game_root = root / "game"
        self.database_path = root / "tracker.duckdb"
        titles = self.game_root / "common" / "landed_titles"
        titles.mkdir(parents=True)
        (titles / "titles.txt").write_text(
            """
e_world = {
  k_test = {
    d_test = {
      c_alive = { b_alive = { } }
      c_dead = { b_dead = { } }
            c_loropeni = { b_loropeni = { } }
            c_nyene = { b_nyene = { } }
    }
  }
}
""",
            encoding="utf-8",
        )
        title_history = self.game_root / "history" / "titles"
        title_history.mkdir(parents=True)
        (title_history / "titles.txt").write_text(
            """
c_alive = { 867.1.1 = { holder = alive_person } }
c_dead = { 800.1.1 = { holder = dead_person } }
""",
            encoding="utf-8-sig",
        )
        characters = self.game_root / "history" / "characters"
        characters.mkdir(parents=True)
        (characters / "a_people.txt").write_text(
            """
alive_person = {
  name = "Alive"
  culture = old_culture
  religion = test_faith
  dynasty = test_dynasty
    800.1.1 = { birth = 799.1.1 }
  850.1.1 = { culture = new_culture effect = { test = yes } }
  900.1.1 = { death = yes }
}
dead_person = {
  name = "Dead"
  female = yes
  culture = test_culture
  faith = test_faith
  700.1.1 = { birth = yes }
  850.1.1 = { death = { death_reason = test } }
}
duplicate_person = { name = "First" 800.1.1 = { birth = yes } }
culture_effect_person = {
    name = "Culture Effect"
    culture = mon
    800.1.1 = { birth = yes }
    850.1.1 = {
        effect = {
            set_culture = culture:burmese
            add_character_flag = do_not_generate_starting_family
        }
    }
    900.1.1 = { effect = { set_culture = culture:future_culture } }
}
nested_effect_person = {
    name = "Nested Effect"
    culture = mon
    800.1.1 = { birth = yes }
    850.1.1 = { effect = { if = { set_culture = culture:burmese } } }
}
appearance_flag_person = {
    850.1.1 = { effect = { add_character_flag = has_scripted_appearance } }
}
family_flag_person = {
    850.1.1 = { effect = { add_character_flag = do_not_generate_starting_family } }
}
unsafe_flag_person = {
    850.1.1 = { effect = { add_character_flag = should_become_independent } }
}
mixed_effect_person = {
    850.1.1 = {
        effect = {
            add_character_flag = has_scripted_appearance
            set_realm_capital = title:c_test
        }
    }
}
relationship_person = {
    850.1.1 = {
        effect = {
            set_relation_friend = { target = character:alive_person reason = friend_generic_history }
            add_opinion = { target = character:alive_person opinion = 20 }
        }
    }
}
mixed_relationship_person = {
    850.1.1 = {
        effect = {
            set_relation_rival = character:alive_person
            add_gold = 100
        }
    }
}
""",
            encoding="utf-8-sig",
        )
        (characters / "z_people.txt").write_text(
            'duplicate_person = { name = "Second" 800.1.1 = { birth = yes } }',
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
        load_title_history_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            database_path=self.database_path,
        )
        connection = connect(self.database_path)
        try:
            for order, (culture_id, language_id) in enumerate(
                (
                    ("new_culture", "language_new"),
                    ("test_culture", "language_test"),
                    ("burmese", "language_burmese"),
                    ("mon", "language_mon"),
                    ("bobo", "language_bobo"),
                    ("future_culture", "language_future"),
                ),
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
                    INSERT INTO reference.culture_native_languages
                    VALUES ('scribe_build', ?, ?,
                            'common/culture/cultures/test.txt', 1, 1, ?,
                            '1.1.0', 'valid', NULL)
                    """,
                    [culture_id, language_id, order],
                )
        finally:
            connection.close()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_materializes_identity_and_validates_holder_lifecycle(self) -> None:
        result = load_character_history_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            database_path=self.database_path,
        )
        connection = connect(self.database_path)
        try:
            people = connection.execute(
                """
                SELECT character_id, display_name, sex, sex_status, culture_id,
                       faith_id, faith_source_key, lifecycle_status,
                       validation_status, validation_note
                FROM reference.character_baseline_states
                WHERE character_id IN ('alive_person', 'dead_person', 'duplicate_person')
                ORDER BY character_id
                """
            ).fetchall()
            holders = connection.execute(
                """
                SELECT title_id, holder_character_id, lifecycle_status, validation_status
                FROM reference.title_holder_validations ORDER BY title_id
                """
            ).fetchall()
            native_languages = connection.execute(
                """
                SELECT character_id, language_id, knowledge_kind, source_group,
                       source_declaration_order
                FROM reference.character_baseline_languages
                ORDER BY character_id
                """
            ).fetchall()
            duplicate_statuses = connection.execute(
                """
                SELECT DISTINCT resolution_status
                FROM source.character_history_declarations
                WHERE character_id = 'duplicate_person'
                """
            ).fetchall()
            duplicate_blocks = connection.execute(
                """
                SELECT duplicate_classification, baseline_conflict_fields, count(*)
                FROM source.character_history_blocks
                WHERE character_id = 'duplicate_person'
                GROUP BY ALL
                """
            ).fetchone()
            birth_event = connection.execute(
                """
                SELECT effective_date, validation_status, validation_note
                FROM reference.character_history_events
                WHERE character_id = 'alive_person' AND event_type = 'birth'
                """
            ).fetchone()
            effect_states = connection.execute(
                """
                SELECT character_id, culture_id, validation_status, validation_note
                FROM reference.character_baseline_states
                WHERE character_id IN ('culture_effect_person', 'nested_effect_person')
                ORDER BY character_id
                """
            ).fetchall()
            culture_events = connection.execute(
                """
                SELECT character_id, effective_date, event_type, text_value,
                       source_declaration_order, validation_status
                FROM reference.character_history_events
                WHERE event_type = 'set_culture'
                ORDER BY effective_date
                """
            ).fetchall()
            effect_resolutions = connection.execute(
                """
                SELECT character_id, effective_date, resolution_status
                FROM source.character_history_declarations
                WHERE operation_key = 'effect'
                  AND character_id IN ('culture_effect_person', 'nested_effect_person')
                ORDER BY character_id, effective_date
                """
            ).fetchall()
            flag_states = connection.execute(
                """
                SELECT character_id, validation_status, validation_note
                FROM reference.character_baseline_states
                WHERE character_id IN (
                    'appearance_flag_person', 'family_flag_person',
                    'unsafe_flag_person', 'mixed_effect_person',
                    'relationship_person', 'mixed_relationship_person'
                )
                ORDER BY character_id
                """
            ).fetchall()
            flag_resolutions = connection.execute(
                """
                SELECT character_id, resolution_status
                FROM source.character_history_declarations
                WHERE operation_key = 'effect'
                  AND character_id IN (
                    'appearance_flag_person', 'family_flag_person',
                                        'unsafe_flag_person', 'mixed_effect_person',
                                        'relationship_person', 'mixed_relationship_person'
                  )
                ORDER BY character_id
                """
            ).fetchall()
            state = connection.execute(
                """
                SELECT s.review_status, b.support_status, b.historical_state_complete
                FROM source.reference_snapshots s JOIN reference.baselines b USING (reference_snapshot_id)
                """
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual("new_culture", people[0][4])
        self.assertEqual("alive_at_baseline", people[0][7])
        self.assertEqual("warning", people[0][8])
        self.assertIn("effect", people[0][9])
        self.assertEqual(("dead_person", "Dead", "female", "declared"), people[1][:4])
        self.assertEqual("dead_at_baseline", people[1][7])
        self.assertEqual("warning", people[2][8])
        self.assertIsNone(people[2][1])
        self.assertEqual(
            [
                ("c_alive", "alive_person", "alive_at_baseline", "valid"),
                ("c_dead", "dead_person", "dead_at_baseline", "warning"),
            ],
            holders,
        )
        self.assertEqual(
            [
                ("alive_person", "language_new", "native", "culture", 1),
                ("culture_effect_person", "language_burmese", "native", "culture", 3),
                ("dead_person", "language_test", "native", "culture", 2),
                ("nested_effect_person", "language_mon", "native", "culture", 4),
            ],
            native_languages,
        )
        self.assertEqual([("review_required",)], duplicate_statuses)
        self.assertEqual(("conflicting_at_baseline", "display_name", 2), duplicate_blocks)
        self.assertEqual(
            (
                "0800-01-01",
                "warning",
                "embedded lifecycle date differs from enclosing date",
            ),
            birth_event,
        )
        self.assertEqual(
            [
                ("culture_effect_person", "burmese", "valid", None),
                ("nested_effect_person", "mon", "warning", "not evaluated: effect"),
            ],
            effect_states,
        )
        self.assertEqual(
            [
                ("culture_effect_person", "0850-01-01", "set_culture", "burmese", 20, "valid"),
                ("culture_effect_person", "0900-01-01", "set_culture", "future_culture", 21, "valid"),
            ],
            culture_events,
        )
        self.assertEqual(
            [
                ("culture_effect_person", "0850-01-01", "normalized"),
                ("culture_effect_person", "0900-01-01", "normalized"),
                ("nested_effect_person", "0850-01-01", "preserved"),
            ],
            effect_resolutions,
        )
        self.assertEqual(
            [
                ("appearance_flag_person", "valid", None),
                ("family_flag_person", "valid", None),
                ("mixed_effect_person", "warning", "not evaluated: effect"),
                ("mixed_relationship_person", "warning", "not evaluated: effect"),
                ("relationship_person", "valid", None),
                ("unsafe_flag_person", "warning", "not evaluated: effect"),
            ],
            flag_states,
        )
        self.assertEqual(
            [
                ("appearance_flag_person", "normalized"),
                ("family_flag_person", "normalized"),
                ("mixed_effect_person", "preserved"),
                ("mixed_relationship_person", "preserved"),
                ("relationship_person", "normalized"),
                ("unsafe_flag_person", "preserved"),
            ],
            flag_resolutions,
        )
        self.assertEqual(("candidate", "candidate", False), state)
        self.assertEqual(11, result.character_count)
        self.assertEqual(2, result.holder_validation_count)
        self.assertEqual(1, result.holder_warning_count)

    def test_exact_lope_duplicate_adjudication_selects_castilian(self) -> None:
        characters = self.game_root / "history" / "characters"
        basque = characters / "basque.txt"
        castilian = characters / "castilian.txt"
        shared = """
  name = "Lope"
  dynasty = 681
  religion = catholic
  culture = {culture}
  father = 71410
  mother = 71411
  1208.1.1 = {{ birth = "1208.1.1" }}
  1235.1.1 = {{ death = "1235.1.1" }}
"""
        basque.write_text(
            "71419 = {" + shared.format(culture="basque") + "}\n",
            encoding="utf-8-sig",
        )
        castilian.write_text(
            "71419 = {" + shared.format(culture="castilian") + "}\n",
            encoding="utf-8-sig",
        )
        connection = connect(self.database_path)
        try:
            connection.execute(
                """
                INSERT INTO reference.languages
                VALUES ('scribe_build', 'language_castilian',
                        'common/culture/pillars/test.txt', 1, 1, 5, '{}',
                        '1.1.0', 'valid', NULL)
                """
            )
            connection.execute(
                """
                INSERT INTO reference.culture_native_languages
                VALUES ('scribe_build', 'castilian', 'language_castilian',
                        'common/culture/cultures/test.txt', 1, 1, 5,
                        '1.1.0', 'valid', NULL)
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
        load_character_history_candidate(**arguments)
        load_character_history_candidate(**arguments)
        connection = connect(self.database_path)
        try:
            lope = connection.execute(
                """
                SELECT display_name, culture_id, faith_id, dynasty_id,
                       birth_date, death_date, lifecycle_status,
                       validation_status, validation_note
                FROM reference.character_baseline_states
                WHERE character_id = '71419'
                """
            ).fetchone()
            blocks = connection.execute(
                """
                SELECT source_path, duplicate_classification,
                       baseline_conflict_fields
                FROM source.character_history_blocks
                WHERE character_id = '71419'
                ORDER BY source_path
                """
            ).fetchall()
            declarations = connection.execute(
                """
                SELECT source_path, resolution_status, count(*)
                FROM source.character_history_declarations
                WHERE character_id = '71419'
                GROUP BY ALL ORDER BY source_path
                """
            ).fetchall()
            unrelated = connection.execute(
                """
                SELECT culture_id, validation_status, validation_note
                FROM reference.character_baseline_states
                WHERE character_id = 'duplicate_person'
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(
            (
                "Lope", "castilian", "catholic", "681", "1208-01-01",
                "1235-01-01", "not_born_at_baseline", "valid", None,
            ),
            lope,
        )
        self.assertEqual(
            [
                ("history/characters/basque.txt", "reviewed_superseded", None),
                ("history/characters/castilian.txt", "reviewed_winner", None),
            ],
            blocks,
        )
        self.assertEqual(
            [
                ("history/characters/basque.txt", "reviewed_superseded", 8),
                ("history/characters/castilian.txt", "reviewed_winner", 8),
            ],
            declarations,
        )
        self.assertEqual(
            (None, "warning",
             "baseline-conflicting duplicate character declarations: display_name"),
            unrelated,
        )

        castilian.write_text(
            "71419 = {" + shared.format(culture="leonese") + "}\n",
            encoding="utf-8-sig",
        )
        load_character_history_candidate(**arguments)
        connection = connect(self.database_path)
        try:
            self.assertEqual(
                (
                    None,
                    "warning",
                    "baseline-conflicting duplicate character declarations: culture_id",
                ),
                connection.execute(
                    """
                    SELECT culture_id, validation_status, validation_note
                    FROM reference.character_baseline_states
                    WHERE character_id = '71419'
                    """
                ).fetchone(),
            )
            self.assertEqual(
                [("conflicting_at_baseline", "culture_id", 2)],
                connection.execute(
                    """
                    SELECT duplicate_classification, baseline_conflict_fields,
                           count(*)
                    FROM source.character_history_blocks
                    WHERE character_id = '71419'
                    GROUP BY ALL
                    """
                ).fetchall(),
            )
        finally:
            connection.close()

    def test_exact_bobo_duplicate_adjudication_restores_bobo0060(self) -> None:
        bobo = self.game_root / "history" / "characters" / "bobo.txt"
        yama = """bobo0050 = {
  name = "Yama"
  dynasty = bobodyn005
  religion = west_african_pagan
  culture = bobo
  father = bobo0049
  1186.1.1 = { birth = yes }
  1244.1.1 = { death = yes }
}
"""
        labidiedo = """bobo0050 = {
  name = "Labidiedo"
  dynasty = bobodyn006
  religion = ashari
  culture = bobo
  father = bobo0059
  1193.1.1 = { birth = yes }
  1254.1.1 = { death = yes }
}
"""
        bobo.write_text(yama + labidiedo, encoding="utf-8-sig")
        connection = connect(self.database_path)
        try:
            connection.execute(
                """
                UPDATE reference.baselines
                SET baseline_date = DATE '1220-01-01'
                WHERE baseline_id = 'scribe_867'
                """
            )
            connection.execute(
                """
                UPDATE reference.title_baseline_states
                SET holder_character_id = CASE title_id
                    WHEN 'c_loropeni' THEN 'bobo0050'
                    WHEN 'c_nyene' THEN 'bobo0060'
                END
                WHERE baseline_id = 'scribe_867'
                  AND title_id IN ('c_loropeni', 'c_nyene')
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

        load_character_history_candidate(**arguments)
        load_character_history_candidate(**arguments)
        connection = connect(self.database_path)
        try:
            states = connection.execute(
                """
                SELECT character_id, display_name, dynasty_id, faith_id,
                       culture_id, birth_date, death_date, validation_status
                FROM reference.character_baseline_states
                WHERE character_id IN ('bobo0050', 'bobo0060')
                ORDER BY character_id
                """
            ).fetchall()
            blocks = connection.execute(
                """
                SELECT character_id, duplicate_classification, count(*)
                FROM source.character_history_blocks
                WHERE character_id = 'bobo0050'
                GROUP BY ALL ORDER BY duplicate_classification
                """
            ).fetchall()
            declarations = connection.execute(
                """
                SELECT character_id, resolution_status, count(*)
                FROM source.character_history_declarations
                WHERE character_id = 'bobo0050'
                GROUP BY ALL ORDER BY resolution_status
                """
            ).fetchall()
            holders = connection.execute(
                """
                SELECT title_id, holder_character_id, validation_status
                FROM reference.title_holder_validations
                WHERE title_id IN ('c_loropeni', 'c_nyene')
                ORDER BY title_id
                """
            ).fetchall()
            unrelated = connection.execute(
                """
                SELECT validation_status, validation_note
                FROM reference.character_baseline_states
                WHERE character_id = 'duplicate_person'
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(
            [
                ("bobo0050", "Yama", "bobodyn005", "west_african_pagan",
                 "bobo", "1186-01-01", "1244-01-01", "valid"),
                ("bobo0060", "Labidiedo", "bobodyn006", "ashari",
                 "bobo", "1193-01-01", "1254-01-01", "valid"),
            ],
            states,
        )
        self.assertEqual(
            [
                ("bobo0050", "reviewed_corrected", 1),
                ("bobo0050", "reviewed_winner", 1),
            ],
            blocks,
        )
        self.assertEqual(
            [
                ("bobo0050", "reviewed_corrected", 7),
                ("bobo0050", "reviewed_winner", 7),
            ],
            declarations,
        )
        self.assertEqual(
            [
                ("c_loropeni", "bobo0050", "valid"),
                ("c_nyene", "bobo0060", "valid"),
            ],
            holders,
        )
        self.assertEqual(
            ("warning",
             "baseline-conflicting duplicate character declarations: display_name"),
            unrelated,
        )

        bobo.write_text(
            yama + labidiedo.replace('name = "Labidiedo"', 'name = "Changed"'),
            encoding="utf-8-sig",
        )
        load_character_history_candidate(**arguments)
        connection = connect(self.database_path)
        try:
            self.assertEqual(
                [
                    (
                        "bobo0050",
                        "warning",
                        "baseline-conflicting duplicate character declarations: "
                        "birth_date, death_date, display_name, dynasty_id, faith_id",
                    ),
                ],
                connection.execute(
                    """
                    SELECT character_id, validation_status, validation_note
                    FROM reference.character_baseline_states
                    WHERE character_id IN ('bobo0050', 'bobo0060')
                    ORDER BY character_id
                    """
                ).fetchall(),
            )
            self.assertEqual(
                [("conflicting_at_baseline", 2)],
                connection.execute(
                    """
                    SELECT duplicate_classification, count(*)
                    FROM source.character_history_blocks
                    WHERE character_id = 'bobo0050'
                    GROUP BY ALL
                    """
                ).fetchall(),
            )
        finally:
            connection.close()

        bobo.write_text(
            yama + labidiedo + """bobo0060 = {
  name = "Independent"
  culture = bobo
  800.1.1 = { birth = yes }
}
""",
            encoding="utf-8-sig",
        )
        load_character_history_candidate(**arguments)
        connection = connect(self.database_path)
        try:
            self.assertEqual(
                [
                    ("bobo0050", None, "warning"),
                    ("bobo0060", "Independent", "valid"),
                ],
                connection.execute(
                    """
                    SELECT character_id, display_name, validation_status
                    FROM reference.character_baseline_states
                    WHERE character_id IN ('bobo0050', 'bobo0060')
                    ORDER BY character_id
                    """
                ).fetchall(),
            )
            self.assertEqual(
                [("conflicting_at_baseline", 2)],
                connection.execute(
                    """
                    SELECT duplicate_classification, count(*)
                    FROM source.character_history_blocks
                    WHERE character_id = 'bobo0050'
                    GROUP BY ALL
                    """
                ).fetchall(),
            )
        finally:
            connection.close()

    def test_reviewed_runtime_holder_adjudication_preserves_declared_holder(self) -> None:
        connection = connect(self.database_path)
        try:
            connection.execute(
                """
                INSERT INTO reference.title_holder_adjudications
                (baseline_id, title_id, declared_holder_character_id,
                 adjudicated_holder_character_id, evidence_kind, evidence_path,
                 evidence_sha256, evidence_game_version, evidence_date,
                 save_player_character_id, review_status, review_note)
                VALUES ('scribe_867', 'c_dead', 'dead_person', 'alive_person',
                        'immediate_save', 'test.ck3', 'abc123', '1.19.0.6',
                        DATE '0867-01-01', 42, 'reviewed', 'runtime holder observed')
                """
            )
        finally:
            connection.close()

        load_character_history_candidate(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            database_path=self.database_path,
        )
        connection = connect(self.database_path)
        try:
            declared = connection.execute(
                """
                SELECT holder_character_id
                FROM reference.title_baseline_states
                WHERE baseline_id = 'scribe_867' AND title_id = 'c_dead'
                """
            ).fetchone()
            validation = connection.execute(
                """
                SELECT holder_character_id, declaration_status, lifecycle_status,
                       validation_status, validation_note
                FROM reference.title_holder_validations
                WHERE baseline_id = 'scribe_867' AND title_id = 'c_dead'
                """
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(("dead_person",), declared)
        self.assertEqual(
            (
                "alive_person",
                "runtime_adjudicated",
                "alive_at_baseline",
                "valid",
                "runtime holder observed; installed declaration retained as dead_person",
            ),
            validation,
        )
        inspection = get_title_inspection("scribe_867", "c_dead", self.database_path)
        self.assertIsNotNone(inspection)
        self.assertEqual("alive_person", inspection["holder_character_id"])
        self.assertEqual("dead_person", inspection["declared_holder_character_id"])
        self.assertEqual("immediate_save", inspection["holder_evidence_kind"])
        self.assertEqual("abc123", inspection["holder_evidence_sha256"])

    def test_candidate_reload_is_idempotent(self) -> None:
        arguments = {
            "game_root": self.game_root,
            "reference_snapshot_id": "scribe_build",
            "baseline_id": "scribe_867",
            "database_path": self.database_path,
        }
        connection = connect(self.database_path)
        try:
            connection.execute(
                """
                INSERT INTO reference.character_baseline_languages
                VALUES ('scribe_867', 'alive_person', 'language_learned',
                        'history_granted', '0850-01-01', 'title_history', 99,
                        'valid', NULL)
                """
            )
        finally:
            connection.close()
        load_character_history_candidate(**arguments)
        load_character_history_candidate(**arguments)
        connection = connect(self.database_path)
        try:
            counts = connection.execute(
                """
                SELECT
                  (SELECT count(*) FROM reference.character_baseline_states),
                  (SELECT count(*) FROM reference.character_baseline_languages),
                  (SELECT count(*) FROM reference.title_holder_validations),
                  (SELECT count(*) FROM source.source_files),
                  (SELECT count(*) FROM source.parser_runs)
                """
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual((11, 5, 2, 4, 4), counts)

    def test_complete_language_effects_materialize_history_granted_rows(self) -> None:
        characters = self.game_root / "history" / "characters" / "languages.txt"
        characters.write_text(
            """
language_one = {
  culture = test_culture
  850.1.1 = { effect = { learn_language_of_culture = culture:mon } }
}
language_two = {
  culture = test_culture
  851.1.1 = {
    effect = {
      learn_language_of_culture = culture:mon
      learn_language_of_culture = culture:burmese
    }
  }
}
language_native = {
  culture = mon
  852.1.1 = { effect = { learn_language_of_culture = culture:mon } }
}
language_existing = {
  culture = test_culture
  853.1.1 = { effect = { learn_language_of_culture = culture:mon } }
}
language_mixed = {
  culture = test_culture
  854.1.1 = {
    effect = {
      learn_language_of_culture = culture:mon
      add_gold = 10
    }
  }
}
language_future = {
    culture = test_culture
    900.1.1 = { effect = { learn_language_of_culture = culture:mon } }
}
""",
            encoding="utf-8-sig",
        )
        connection = connect(self.database_path)
        try:
            connection.execute(
                """
                INSERT INTO reference.character_baseline_languages
                VALUES ('scribe_867', 'language_existing', 'language_mon',
                        'history_granted', '0840-01-01', 'title_history', 99,
                        'valid', NULL)
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

        load_character_history_candidate(**arguments)
        load_character_history_candidate(**arguments)
        connection = connect(self.database_path)
        try:
            languages = connection.execute(
                """
                SELECT character_id, language_id, knowledge_kind,
                      effective_date::VARCHAR, source_group,
                      source_declaration_order
                FROM reference.character_baseline_languages
                WHERE character_id LIKE 'language_%'
                ORDER BY character_id, language_id
                """
            ).fetchall()
            states = connection.execute(
                """
                SELECT character_id, validation_status, validation_note
                FROM reference.character_baseline_states
                WHERE character_id LIKE 'language_%'
                ORDER BY character_id
                """
            ).fetchall()
            declarations = connection.execute(
                """
                SELECT character_id, resolution_status
                FROM source.character_history_declarations
                WHERE source_path = 'history/characters/languages.txt'
                  AND operation_key = 'effect'
                ORDER BY character_id
                """
            ).fetchall()
        finally:
            connection.close()

        self.assertEqual(
            [
                ("language_existing", "language_mon", "history_granted",
                 "0840-01-01", "title_history", 99),
                ("language_existing", "language_test", "native", None, "culture", 2),
                ("language_future", "language_test", "native", None, "culture", 2),
                ("language_mixed", "language_test", "native", None, "culture", 2),
                ("language_native", "language_mon", "native", None, "culture", 4),
                ("language_one", "language_mon", "history_granted",
                 "0850-01-01", "character_history", 33),
                ("language_one", "language_test", "native", None, "culture", 2),
                ("language_two", "language_burmese", "history_granted",
                 "0851-01-01", "character_history", 35),
                ("language_two", "language_mon", "history_granted",
                 "0851-01-01", "character_history", 35),
                ("language_two", "language_test", "native", None, "culture", 2),
            ],
            languages,
        )
        self.assertEqual(
            [
                ("language_existing", "valid", None),
                ("language_future", "valid", None),
                ("language_mixed", "warning", "not evaluated: effect"),
                ("language_native", "valid", None),
                ("language_one", "valid", None),
                ("language_two", "valid", None),
            ],
            states,
        )
        self.assertEqual(
            [
                ("language_existing", "normalized"),
                ("language_future", "normalized"),
                ("language_mixed", "preserved"),
                ("language_native", "normalized"),
                ("language_one", "normalized"),
                ("language_two", "normalized"),
            ],
            declarations,
        )

    def test_unresolved_language_effect_preserves_existing_state(self) -> None:
        arguments = dict(
            game_root=self.game_root,
            reference_snapshot_id="scribe_build",
            baseline_id="scribe_867",
            database_path=self.database_path,
        )
        load_character_history_candidate(**arguments)
        connection = connect(self.database_path)
        try:
            before = connection.execute(
                "SELECT count(*) FROM reference.character_baseline_states"
            ).fetchone()
        finally:
            connection.close()
        (self.game_root / "history" / "characters" / "language_bad.txt").write_text(
            """
language_bad = {
  culture = test_culture
  850.1.1 = {
    effect = { learn_language_of_culture = culture:missing_culture }
  }
}
""",
            encoding="utf-8-sig",
        )

        with self.assertRaisesRegex(
            ValueError, "Language effects reference unresolved cultures"
        ):
            load_character_history_candidate(**arguments)

        connection = connect(self.database_path)
        try:
            after = connection.execute(
                "SELECT count(*) FROM reference.character_baseline_states"
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual(before, after)

    def test_unresolved_native_language_mapping_preserves_existing_state(self) -> None:
        arguments = {
            "game_root": self.game_root,
            "reference_snapshot_id": "scribe_build",
            "baseline_id": "scribe_867",
            "database_path": self.database_path,
        }
        load_character_history_candidate(**arguments)
        connection = connect(self.database_path)
        try:
            connection.execute(
                """
                DELETE FROM reference.culture_native_languages
                WHERE reference_snapshot_id = 'scribe_build'
                  AND culture_id = 'new_culture'
                """
            )
        finally:
            connection.close()

        with self.assertRaisesRegex(
            ValueError, "Baseline cultures lack valid native-language mappings"
        ):
            load_character_history_candidate(**arguments)

        connection = connect(self.database_path)
        try:
            counts = connection.execute(
                """
                SELECT (SELECT count(*) FROM reference.character_baseline_states),
                       (SELECT count(*) FROM reference.character_baseline_languages)
                """
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual((11, 4), counts)


if __name__ == "__main__":
    unittest.main()