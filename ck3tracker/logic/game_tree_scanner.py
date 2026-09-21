"""Create deterministic content manifests for a complete installed CK3 game tree."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import unicodedata


SCANNER_NAME = "installed_game_tree"
SCANNER_VERSION = "1.0.0"
PATH_NORMALIZATION_VERSION = "nfc-posix-utf8-v1"
_REPARSE_POINT = 0x400


@dataclass(frozen=True)
class GameTreeEntry:
    relative_path: str
    entry_kind: str
    byte_size: int | None
    mtime_unix_ns: int | None
    sha256: str | None


@dataclass(frozen=True)
class GameTreeManifest:
    entries: tuple[GameTreeEntry, ...]
    file_count: int
    directory_count: int
    manifest_sha256: str


def scan_game_tree(game_root: str | Path) -> GameTreeManifest:
    """Hash every regular file and directory below one resolved game root."""
    root = Path(game_root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"Game root is not a directory: {root}")
    entries: list[GameTreeEntry] = []
    normalized_paths: dict[str, str] = {}
    casefold_paths: dict[str, str] = {}

    for current_root, directory_names, file_names in os.walk(root, followlinks=False):
        directory_names.sort(key=lambda value: value.encode("utf-8"))
        file_names.sort(key=lambda value: value.encode("utf-8"))
        current = Path(current_root)
        children = [
            (item, "directory") for item in directory_names
        ] + [
            (item, "file") for item in file_names
        ]
        for name, kind in children:
            path = current / name
            stat = path.stat(follow_symlinks=False)
            if path.is_symlink() or getattr(stat, "st_file_attributes", 0) & _REPARSE_POINT:
                raise ValueError(f"Game tree contains a link or reparse point: {path}")
            relative_path = _normalize_relative_path(root, path)
            prior = normalized_paths.setdefault(relative_path, str(path))
            if prior != str(path):
                raise ValueError(f"Duplicate normalized path: {relative_path}")
            folded = relative_path.casefold()
            prior_folded = casefold_paths.setdefault(folded, relative_path)
            if prior_folded != relative_path:
                raise ValueError(
                    f"Case-fold path collision: {prior_folded}, {relative_path}"
                )
            if kind == "directory":
                entries.append(GameTreeEntry(relative_path, kind, None, None, None))
            elif path.is_file():
                digest, byte_size = _hash_file(path)
                if byte_size != stat.st_size:
                    raise ValueError(f"File changed while scanning: {relative_path}")
                entries.append(
                    GameTreeEntry(
                        relative_path, kind, byte_size, stat.st_mtime_ns, digest
                    )
                )
            else:
                raise ValueError(f"Unsupported game-tree entry: {path}")

    entries.sort(key=lambda entry: entry.relative_path.encode("utf-8"))
    file_count = sum(entry.entry_kind == "file" for entry in entries)
    directory_count = len(entries) - file_count
    payload = {
        "path_normalization_version": PATH_NORMALIZATION_VERSION,
        "file_count": file_count,
        "directory_count": directory_count,
        "entries": [
            [
                entry.entry_kind,
                entry.relative_path,
                entry.byte_size,
                entry.mtime_unix_ns,
                entry.sha256,
            ]
            for entry in entries
        ],
    }
    digest = sha256(
        json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return GameTreeManifest(tuple(entries), file_count, directory_count, digest)


def _normalize_relative_path(root: Path, path: Path) -> str:
    relative = path.relative_to(root)
    parts = tuple(unicodedata.normalize("NFC", part) for part in relative.parts)
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"Invalid relative game-tree path: {relative}")
    normalized = "/".join(parts)
    if normalized.startswith("/") or ":" in parts[0]:
        raise ValueError(f"Absolute game-tree path: {normalized}")
    return normalized


def _hash_file(path: Path) -> tuple[str, int]:
    digest = sha256()
    byte_size = 0
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
            byte_size += len(chunk)
    return digest.hexdigest(), byte_size