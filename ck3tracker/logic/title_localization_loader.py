"""Load installed English CK3 localization into a candidate reference snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import re
from typing import Iterable
from uuid import uuid4

import duckdb

from logic.root_database import connect


PARSER_NAME = "installed_localization_english"
PARSER_VERSION = "1.0.0"
LANGUAGE = "english"
DECLARATION_PATTERN = re.compile(
    r'^\s*([^\s:#]+):(\d*)\s+"(.*)"\s*(?:#.*)?$'
)


@dataclass(frozen=True)
class LocalizationDeclaration:
    localization_key: str
    value_version: int | None
    display_value: str
    relative_path: str
    source_line: int
    declaration_order: int


@dataclass(frozen=True)
class ResolvedLocalization:
    declaration: LocalizationDeclaration
    resolution_status: str


@dataclass(frozen=True)
class TitleLocalizationLoadResult:
    reference_snapshot_id: str
    declaration_count: int
    localization_count: int
    localized_title_count: int
    missing_title_count: int
    conflict_count: int
    parser_run_id: str


def parse_english_localization(
    game_root: str | Path,
) -> tuple[list[LocalizationDeclaration], list[str]]:
    """Parse installed English localization files in deterministic path order."""
    root = Path(game_root).resolve()
    source_root = root / "localization" / "english"
    if not source_root.is_dir():
        raise FileNotFoundError(f"English localization folder does not exist: {source_root}")

    declarations: list[LocalizationDeclaration] = []
    warnings: list[str] = []
    declaration_order = 0
    for path in sorted(source_root.rglob("*.yml")):
        relative_path = path.relative_to(root).as_posix()
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        header_found = False
        for source_line, raw_line in enumerate(lines, 1):
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if not header_found:
                if stripped != "l_english:":
                    raise ValueError(
                        f"Expected l_english header at {relative_path}:{source_line}"
                    )
                header_found = True
                continue
            match = DECLARATION_PATTERN.match(raw_line)
            if match is None:
                warnings.append(f"unparsed line: {relative_path}:{source_line}")
                continue
            declaration_order += 1
            declarations.append(
                LocalizationDeclaration(
                    localization_key=match.group(1),
                    value_version=int(match.group(2)) if match.group(2) else None,
                    display_value=_unescape_value(match.group(3)),
                    relative_path=relative_path,
                    source_line=source_line,
                    declaration_order=declaration_order,
                )
            )
        if not header_found:
            raise ValueError(f"Missing l_english header: {relative_path}")

    return declarations, warnings


def resolve_localizations(
    declarations: list[LocalizationDeclaration],
) -> tuple[dict[str, ResolvedLocalization], dict[int, str]]:
    """Resolve duplicate keys by deterministic source order while retaining conflicts."""
    by_key: dict[str, list[LocalizationDeclaration]] = {}
    for declaration in declarations:
        by_key.setdefault(declaration.localization_key, []).append(declaration)

    resolved: dict[str, ResolvedLocalization] = {}
    declaration_statuses: dict[int, str] = {}
    for localization_key, candidates in by_key.items():
        values = {candidate.display_value for candidate in candidates}
        if len(candidates) == 1:
            status = "valid"
        elif len(values) == 1:
            status = "identical_duplicate"
        else:
            status = "review_required"
        winner = candidates[-1]
        resolved[localization_key] = ResolvedLocalization(winner, status)
        for candidate in candidates:
            declaration_statuses[candidate.declaration_order] = status

    return resolved, declaration_statuses


def load_title_localizations_candidate(
    *,
    game_root: str | Path,
    reference_snapshot_id: str,
    database_path: str | Path | None = None,
) -> TitleLocalizationLoadResult:
    """Replace one candidate snapshot's English localization slice atomically."""
    root = Path(game_root).resolve()
    started_at = datetime.now(timezone.utc)
    parser_run_id = f"{reference_snapshot_id}:{PARSER_NAME}:{uuid4()}"
    declarations, parse_warnings = parse_english_localization(root)
    resolved, declaration_statuses = resolve_localizations(declarations)
    source_paths = [
        path.relative_to(root).as_posix()
        for path in sorted((root / "localization" / "english").rglob("*.yml"))
    ]
    manifests = [_source_manifest(root, relative_path) for relative_path in source_paths]
    conflict_count = sum(
        1 for item in resolved.values() if item.resolution_status == "review_required"
    )

    connection = connect(database_path)
    try:
        snapshot = connection.execute(
            """
            SELECT review_status
            FROM source.reference_snapshots
            WHERE reference_snapshot_id = ?
            """,
            [reference_snapshot_id],
        ).fetchone()
        if snapshot is None:
            raise ValueError("Reference snapshot must exist before localization is loaded")
        if snapshot[0] == "promoted":
            raise ValueError("A promoted reference snapshot cannot be replaced")

        title_ids = [
            row[0]
            for row in connection.execute(
                """
                SELECT t.title_id
                FROM reference.titles t
                JOIN reference.baselines b USING (baseline_id)
                WHERE b.reference_snapshot_id = ?
                """,
                [reference_snapshot_id],
            ).fetchall()
        ]
        title_updates = [
            (
                resolved[title_id].declaration.display_value
                if title_id in resolved
                else _fallback_display_name(title_id),
                title_id,
                reference_snapshot_id,
            )
            for title_id in title_ids
        ]
        localized_title_count = sum(title_id in resolved for title_id in title_ids)
        missing_title_count = len(title_ids) - localized_title_count

        connection.execute("BEGIN TRANSACTION")
        connection.execute(
            """
            DELETE FROM source.localization_declarations
            WHERE reference_snapshot_id = ? AND language = ?
            """,
            [reference_snapshot_id, LANGUAGE],
        )
        connection.execute(
            """
            DELETE FROM reference.localizations
            WHERE reference_snapshot_id = ? AND language = ?
            """,
            [reference_snapshot_id, LANGUAGE],
        )
        connection.execute(
            """
            DELETE FROM source.source_files
            WHERE reference_snapshot_id = ? AND source_group = ?
            """,
            [reference_snapshot_id, PARSER_NAME],
        )
        connection.executemany(
            """
            INSERT INTO source.source_files
            (reference_snapshot_id, relative_path, source_group, byte_size,
             modified_at_utc, sha256, parser_run_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (reference_snapshot_id, *manifest[:1], PARSER_NAME, *manifest[1:], parser_run_id)
                for manifest in manifests
            ],
        )
        _bulk_insert(
            connection,
            """
            INSERT INTO source.localization_declarations
            (reference_snapshot_id, language, localization_key, value_version,
             display_value, relative_path, source_line, declaration_order,
             is_winner, resolution_status)
            SELECT unnest[1]::VARCHAR, unnest[2]::VARCHAR, unnest[3]::VARCHAR,
                   unnest[4]::INTEGER, unnest[5]::VARCHAR, unnest[6]::VARCHAR,
                   unnest[7]::INTEGER, unnest[8]::BIGINT, unnest[9]::BOOLEAN,
                   unnest[10]::VARCHAR
            FROM unnest(?)
            """,
            (
                (
                    reference_snapshot_id,
                    LANGUAGE,
                    declaration.localization_key,
                    declaration.value_version,
                    declaration.display_value,
                    declaration.relative_path,
                    declaration.source_line,
                    declaration.declaration_order,
                    resolved[declaration.localization_key].declaration.declaration_order
                    == declaration.declaration_order,
                    declaration_statuses[declaration.declaration_order],
                )
                for declaration in declarations
            ),
        )
        _bulk_insert(
            connection,
            """
            INSERT INTO reference.localizations
            (reference_snapshot_id, language, localization_key, value_version,
             display_value, source_path, source_line, parser_version,
             resolution_status)
            SELECT unnest[1]::VARCHAR, unnest[2]::VARCHAR, unnest[3]::VARCHAR,
                   unnest[4]::INTEGER, unnest[5]::VARCHAR, unnest[6]::VARCHAR,
                   unnest[7]::INTEGER, unnest[8]::VARCHAR, unnest[9]::VARCHAR
            FROM unnest(?)
            """,
            (
                (
                    reference_snapshot_id,
                    LANGUAGE,
                    localization_key,
                    item.declaration.value_version,
                    item.declaration.display_value,
                    item.declaration.relative_path,
                    item.declaration.source_line,
                    PARSER_VERSION,
                    item.resolution_status,
                )
                for localization_key, item in resolved.items()
            ),
        )
        connection.executemany(
            """
            UPDATE reference.titles AS t
            SET localization_key = ?, display_name = ?
            FROM reference.baselines AS b
            WHERE t.baseline_id = b.baseline_id
              AND t.title_id = ?
              AND b.reference_snapshot_id = ?
            """,
            [
                (title_id, display_name, title_id, snapshot_id)
                for display_name, title_id, snapshot_id in title_updates
            ],
        )
        connection.execute(
            """
            INSERT INTO source.parser_runs
            (parser_run_id, reference_snapshot_id, parser_name, parser_version,
             status, started_at_utc, completed_at_utc, row_count, warning_count)
            VALUES (?, ?, ?, ?, 'completed', ?, ?, ?, ?)
            """,
            [
                parser_run_id,
                reference_snapshot_id,
                PARSER_NAME,
                PARSER_VERSION,
                started_at,
                datetime.now(timezone.utc),
                len(declarations),
                len(parse_warnings) + missing_title_count + conflict_count,
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

    return TitleLocalizationLoadResult(
        reference_snapshot_id=reference_snapshot_id,
        declaration_count=len(declarations),
        localization_count=len(resolved),
        localized_title_count=localized_title_count,
        missing_title_count=missing_title_count,
        conflict_count=conflict_count,
        parser_run_id=parser_run_id,
    )


def _source_manifest(root: Path, relative_path: str) -> tuple[str, int, datetime, str]:
    path = root / Path(relative_path)
    statistics = path.stat()
    return (
        relative_path,
        statistics.st_size,
        datetime.fromtimestamp(statistics.st_mtime, timezone.utc),
        sha256(path.read_bytes()).hexdigest(),
    )


def _bulk_insert(
    connection: duckdb.DuckDBPyConnection,
    sql: str,
    rows: Iterable[tuple[object, ...]],
    chunk_size: int = 10_000,
) -> None:
    chunk: list[tuple[object, ...]] = []
    for row in rows:
        chunk.append(row)
        if len(chunk) == chunk_size:
            connection.execute(sql, [chunk])
            chunk.clear()
    if chunk:
        connection.execute(sql, [chunk])


def _unescape_value(value: str) -> str:
    return value.replace(r"\"", '"').replace(r"\\", "\\")


def _fallback_display_name(title_id: str) -> str:
    return title_id[2:].replace("_", " ").title()