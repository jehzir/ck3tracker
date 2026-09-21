"""Tests for deterministic complete game-tree manifests."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from logic.game_tree_scanner import scan_game_tree


class GameTreeScannerTests(unittest.TestCase):
    def test_scans_files_directories_and_detects_content_or_metadata_drift(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            folder = root / "Folder"
            folder.mkdir()
            source = folder / "source.txt"
            source.write_bytes(b"alpha")
            first = scan_game_tree(root)
            second = scan_game_tree(root)
            self.assertEqual((1, 1), (first.file_count, first.directory_count))
            self.assertEqual(first.manifest_sha256, second.manifest_sha256)
            self.assertEqual(
                ["Folder", "Folder/source.txt"],
                [entry.relative_path for entry in first.entries],
            )
            source.write_bytes(b"bravo")
            changed = scan_game_tree(root)
            self.assertNotEqual(first.manifest_sha256, changed.manifest_sha256)


if __name__ == "__main__":
    unittest.main()