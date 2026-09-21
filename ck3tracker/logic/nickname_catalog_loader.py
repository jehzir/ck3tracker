"""Load installed CK3 nickname definitions with resolved labels and provenance."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from logic.root_database import connect
from logic.title_history_loader import _assignments, _scalar_value, _strip_comments


PARSER_NAME = "installed_nicknames"
PARSER_VERSION = "1.0.0"
REVIEWED_ORPHAN_ID = "nick_the_bastard_rumoured"
REVIEWED_ORPHAN_PATH = "common/nicknames/00_nicknames.txt"
REVIEWED_ORPHAN_RAW = "{ is_bad = yes }"
REVIEWED_GAME_VERSION = "1.19.0.6"
REVIEWED_STEAM_BUILD_ID = "23530548"
TEXT_SUFFIXES = {".asset", ".gui", ".info", ".txt", ".yml"}


@dataclass(frozen=True)
class NicknameCatalogLoadResult:
    reference_snapshot_id: str
    nickname_count: int
    localized_count: int
    reviewed_orphan_count: int
    parser_run_id: str


@dataclass(frozen=True)
class _ParsedNickname:
    nickname_id: str
    is_bad: bool
    is_prefix: bool
    source_path: str
    source_line_start: int
    source_line_end: int
    source_order: int
    raw_script: str


def load_nickname_catalog_candidate(
    *,
    game_root: str | Path,
    reference_snapshot_id: str,
    database_path: str | Path | None = None,
) -> NicknameCatalogLoadResult:
    """Replace one candidate snapshot's installed nickname catalog."""
    root = Path(game_root).resolve()
    source_root = root / "common" / "nicknames"
    if not source_root.is_dir():
        raise FileNotFoundError(f"Nickname source folder does not exist: {source_root}")

    parsed, manifests = _parse_installed_definitions(root, source_root)
    parser_run_id = f"{reference_snapshot_id}:{PARSER_NAME}:{uuid4()}"
    started_at = datetime.now(timezone.utc)
    connection = connect(database_path)
    try:
        snapshot = connection.execute(
            """
            SELECT game_version, steam_build_id, review_status
            FROM source.reference_snapshots
            WHERE reference_snapshot_id = ?
            """,
            [reference_snapshot_id],
        ).fetchone()
        if snapshot is None:
            raise ValueError("Existing reference snapshot is required")
        if snapshot[2] == "promoted":
            raise ValueError("A promoted nickname catalog cannot be replaced")

        orphan = next(
            (item for item in parsed if item.nickname_id == REVIEWED_ORPHAN_ID),
            None,
        )
        _validate_reviewed_orphan(root, connection, reference_snapshot_id, snapshot, orphan)
        rows = _resolve_catalog_rows(connection, reference_snapshot_id, parsed)

        connection.execute("BEGIN TRANSACTION")
        connection.execute(
            "DELETE FROM reference.nicknames WHERE reference_snapshot_id = ?",
            [reference_snapshot_id],
        )
        connection.execute(
            """
            DELETE FROM source.source_files
            WHERE reference_snapshot_id = ? AND source_group = ?
            """,
            [reference_snapshot_id, PARSER_NAME],
        )
        connection.executemany(
            "INSERT INTO source.source_files VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (reference_snapshot_id, *manifest, parser_run_id)
                for manifest in manifests
            ],
        )
        connection.executemany(
            "INSERT INTO reference.nicknames VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        connection.execute(
            """
            INSERT INTO source.parser_runs VALUES
            (?, ?, ?, ?, 'completed', ?, ?, ?, 0, NULL)
            """,
            [
                parser_run_id,
                reference_snapshot_id,
                PARSER_NAME,
                PARSER_VERSION,
                started_at,
                datetime.now(timezone.utc),
                len(rows),
            ],
        )
        connection.execute("COMMIT")
    except Exception:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        connection.close()

    return NicknameCatalogLoadResult(
        reference_snapshot_id,
        len(rows),
        sum(row[15] == "valid" for row in rows),
        sum(row[15] == "reviewed_orphan" for row in rows),
        parser_run_id,
    )


def _parse_installed_definitions(
    root: Path,
    source_root: Path,
) -> tuple[list[_ParsedNickname], list[tuple[object, ...]]]:
    parsed: list[_ParsedNickname] = []
    manifests: list[tuple[object, ...]] = []
    seen: set[str] = set()
    source_order = 0
    for path in sorted(source_root.glob("*.txt")):
        raw_bytes = path.read_bytes()
        relative_path = path.relative_to(root).as_posix()
        manifests.append(
            (
                relative_path,
                PARSER_NAME,
                len(raw_bytes),
                datetime.fromtimestamp(path.stat().st_mtime, timezone.utc),
                sha256(raw_bytes).hexdigest(),
            )
        )
        text = _strip_comments(raw_bytes.decode("utf-8-sig"))
        for assignment in _assignments(text):
            if assignment.value_kind != "block":
                raise ValueError(
                    f"Nickname definition must be a block: {assignment.key}"
                )
            if assignment.key in seen:
                raise ValueError(f"Duplicate nickname ID: {assignment.key}")
            seen.add(assignment.key)
            source_order += 1
            fields: dict[str, str] = {}
            for field in _assignments(
                assignment.raw_value[1:-1], assignment.line_start
            ):
                if field.key not in {"is_bad", "is_prefix"}:
                    raise ValueError(
                        f"Unknown nickname field {field.key}: {assignment.key}"
                    )
                if field.key in fields or field.value_kind != "scalar":
                    raise ValueError(
                        f"Malformed nickname field {field.key}: {assignment.key}"
                    )
                value = _scalar_value(field.raw_value)
                if value not in {"yes", "no"}:
                    raise ValueError(
                        f"Invalid nickname boolean {field.key}={value}: {assignment.key}"
                    )
                fields[field.key] = value
            parsed.append(
                _ParsedNickname(
                    assignment.key,
                    fields.get("is_bad", "no") == "yes",
                    fields.get("is_prefix", "no") == "yes",
                    relative_path,
                    assignment.line_start,
                    assignment.line_end,
                    source_order,
                    assignment.raw_value,
                )
            )
    return parsed, manifests


def _validate_reviewed_orphan(
    root: Path,
    connection,
    reference_snapshot_id: str,
    snapshot,
    orphan: _ParsedNickname | None,
) -> None:
    if orphan is None:
        raise ValueError(f"Reviewed nickname orphan is missing: {REVIEWED_ORPHAN_ID}")
    exact_definition = (
        orphan.source_path == REVIEWED_ORPHAN_PATH
        and orphan.raw_script == REVIEWED_ORPHAN_RAW
        and orphan.is_bad
        and not orphan.is_prefix
        and str(snapshot[0]) == REVIEWED_GAME_VERSION
        and str(snapshot[1]) == REVIEWED_STEAM_BUILD_ID
    )
    if not exact_definition:
        raise ValueError("Reviewed nickname orphan definition changed")
    if _installed_usage_paths(root, REVIEWED_ORPHAN_ID):
        raise ValueError("Reviewed nickname orphan has installed consumers")
    history_usage = connection.execute(
        """
        SELECT count(*)
        FROM source.character_history_declarations
        WHERE reference_snapshot_id = ?
          AND (scalar_value = ? OR raw_script LIKE ?)
        """,
        [reference_snapshot_id, REVIEWED_ORPHAN_ID, f"%{REVIEWED_ORPHAN_ID}%"],
    ).fetchone()[0]
    if history_usage:
        raise ValueError("Reviewed nickname orphan is used by character history")


def _installed_usage_paths(root: Path, nickname_id: str) -> list[str]:
    needle = nickname_id.encode("utf-8")
    usages: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative_path = path.relative_to(root).as_posix()
        if relative_path.startswith("common/nicknames/"):
            continue
        if needle in path.read_bytes():
            usages.append(relative_path)
    return usages


def _resolve_catalog_rows(
    connection,
    reference_snapshot_id: str,
    parsed: list[_ParsedNickname],
) -> list[tuple[object, ...]]:
    keys = [item.nickname_id for item in parsed]
    localization_rows = connection.execute(
        """
        SELECT localization_key, display_value, source_path, source_line,
               resolution_status
        FROM reference.localizations
        WHERE reference_snapshot_id = ? AND language = 'english'
          AND localization_key IN (SELECT unnest(?))
        """,
        [reference_snapshot_id, keys],
    ).fetchall()
    localizations = {str(row[0]): row for row in localization_rows}
    unresolved = sorted(
        item.nickname_id
        for item in parsed
        if item.nickname_id != REVIEWED_ORPHAN_ID
        and (
            item.nickname_id not in localizations
            or localizations[item.nickname_id][4] != "valid"
        )
    )
    if unresolved:
        raise ValueError("Unresolved nickname localization: " + ", ".join(unresolved))
    if REVIEWED_ORPHAN_ID in localizations:
        raise ValueError("Reviewed nickname orphan now has localization")

    rows: list[tuple[object, ...]] = []
    for item in parsed:
        localization = localizations.get(item.nickname_id)
        is_orphan = item.nickname_id == REVIEWED_ORPHAN_ID
        rows.append(
            (
                reference_snapshot_id,
                item.nickname_id,
                item.is_bad,
                item.is_prefix,
                None if is_orphan else "english",
                None if is_orphan else item.nickname_id,
                None if is_orphan else str(localization[1]),
                item.source_path,
                item.source_line_start,
                item.source_line_end,
                item.source_order,
                item.raw_script,
                None if is_orphan else str(localization[2]),
                None if is_orphan else int(localization[3]),
                PARSER_VERSION,
                "reviewed_orphan" if is_orphan else "valid",
                (
                    "Installed Scribe definition has no localization or consumer"
                    if is_orphan
                    else None
                ),
            )
        )
    return rows