"""Tests for bounded, read-only CK3 save metadata extraction."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZIP_DEFLATED, ZipFile

from logic.ck3_save_reader import (
    CK3SaveError,
    list_save_candidates,
    read_save_baseline_identity,
    read_save_metadata,
)


GAMESTATE = b'''meta_data={
    save_game_version=15
    version="1.19.0.6"
    meta_date=867.1.18
    meta_player_name="Chieftain Yi Zi'"
    meta_title_name="Chiefdom of Ucinaa"
    meta_coat_of_arms={ pattern="pattern_solid.dds" }
    meta_player_tier=2
    meta_main_portrait={ type=boy id=37862 random_seed=37862 }
    meta_house_name="Yi"
    meta_government=tribal_government
    dlcs={ "All Under Heaven" "The Northern Lords" }
    can_get_achievements=yes
    ironman=no
}
living_character={}
'''

IDENTITY_GAMESTATE = GAMESTATE + b'''landed_titles={
    landed_titles={
        17453={
            key=c_ucinaa
            de_jure_liege=17452
            holder=37862
            capital=17453
        }
        17454={
            key=b_simajiri
            de_jure_liege=17453
            holder=37862
            capital_barony=yes
        }
    }
}
living={
    37862={
        first_name="Zi'"
        culture=47
        faith=120
        dynasty_house=11833
        landed_data={
            domain={ 17453 17454 }
            realm_capital=17454
            government=tribal_government
        }
    }
}
played_character={
    name="Jehzir"
    character=37862
    player=1
}
currently_played_characters={ 37862 }
'''

MULTI_DUCHY_GAMESTATE = (
    IDENTITY_GAMESTATE
    .replace(b'meta_player_tier=2', b'meta_player_tier=3', 1)
    .replace(
        b'        17453={',
        b'''        17452={
            key=d_ruucuu
            holder=37862
        }
        17212={
            key=d_liuqiu
            holder=37862
        }
        17453={''',
        1,
    )
    .replace(
        b'domain={ 17453 17454 }',
        b'domain={ 17452 17212 17453 17454 }',
        1,
    )
)


class CK3SaveReaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.save_path = Path(self.temporary_directory.name) / "example.ck3"

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _write_save(self, gamestate: bytes = GAMESTATE) -> None:
        with ZipFile(self.save_path, "w", ZIP_DEFLATED) as archive:
            archive.writestr("gamestate", gamestate)

    def test_reads_expected_metadata_without_extracting_files(self) -> None:
        self._write_save()

        metadata = read_save_metadata(self.save_path)

        self.assertEqual("1.19.0.6", metadata.game_version)
        self.assertEqual("867.1.18", metadata.game_date)
        self.assertEqual("Chieftain Yi Zi'", metadata.player_name)
        self.assertEqual("Chiefdom of Ucinaa", metadata.title_name)
        self.assertEqual(2, metadata.player_tier)
        self.assertEqual(37862, metadata.player_character_id)
        self.assertEqual("Yi", metadata.house_name)
        self.assertEqual("tribal_government", metadata.government_id)
        self.assertEqual(("All Under Heaven", "The Northern Lords"), metadata.dlcs)
        self.assertTrue(metadata.can_get_achievements)
        self.assertFalse(metadata.ironman)
        self.assertEqual(["example.ck3"], [path.name for path in self.save_path.parent.iterdir()])

    def test_rejects_non_archive_file(self) -> None:
        self.save_path.write_text("not a CK3 save", encoding="utf-8")

        with self.assertRaisesRegex(CK3SaveError, "not a readable compressed CK3 save"):
            read_save_metadata(self.save_path)

    def test_rejects_archive_without_gamestate(self) -> None:
        with ZipFile(self.save_path, "w", ZIP_DEFLATED) as archive:
            archive.writestr("other", "content")

        with self.assertRaisesRegex(CK3SaveError, "does not contain a gamestate"):
            read_save_metadata(self.save_path)

    def test_rejects_metadata_over_safety_limit(self) -> None:
        self._write_save(b"meta_data={\n" + b"x" * 1_048_576)

        with self.assertRaisesRegex(CK3SaveError, "safety limit"):
            read_save_metadata(self.save_path)

    def test_lists_newest_candidates_without_parsing_them(self) -> None:
        older_path = Path(self.temporary_directory.name) / "older.ck3"
        older_path.write_text("not parsed", encoding="utf-8")
        self.save_path.write_text("also not parsed", encoding="utf-8")
        older_path.touch()
        self.save_path.touch()
        older_path_stat = older_path.stat()
        older_path.touch()
        self.save_path.touch()
        older_time = older_path_stat.st_mtime_ns - 1_000_000_000
        os.utime(older_path, ns=(older_time, older_time))

        candidates = list_save_candidates(self.save_path.parent, limit=1)

        self.assertEqual(("example.ck3",), tuple(item.file_name for item in candidates))
        self.assertEqual(len("also not parsed"), candidates[0].size_bytes)

    def test_resolves_stable_player_primary_title_and_realm_capital_ids(self) -> None:
        self._write_save(IDENTITY_GAMESTATE)

        identity = read_save_baseline_identity(self.save_path)

        self.assertEqual(37862, identity.player_character_id)
        self.assertEqual("c_ucinaa", identity.primary_title_id)
        self.assertEqual("b_simajiri", identity.realm_capital_title_id)
        self.assertEqual(("c_ucinaa", "b_simajiri"), identity.domain_title_ids)
        self.assertEqual(47, identity.culture_numeric_id)
        self.assertEqual(120, identity.faith_numeric_id)
        self.assertEqual(11833, identity.house_numeric_id)

    def test_uses_ordered_domain_for_multiple_titles_at_player_tier(self) -> None:
        self._write_save(MULTI_DUCHY_GAMESTATE)

        identity = read_save_baseline_identity(self.save_path)

        self.assertEqual("d_ruucuu", identity.primary_title_id)
        self.assertEqual(
            ("d_ruucuu", "d_liuqiu", "c_ucinaa", "b_simajiri"),
            identity.domain_title_ids,
        )


if __name__ == "__main__":
    unittest.main()