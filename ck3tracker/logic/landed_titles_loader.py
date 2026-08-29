"""Parse installed CK3 landed titles into a versioned DuckDB candidate snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import re
from uuid import uuid4

from logic.root_database import connect


PARSER_NAME = "installed_landed_titles"
PARSER_VERSION = "1.0.0"
TITLE_PATTERN = re.compile(r"^([ekdcb]_[A-Za-z0-9_-]+)\s*=\s*\{")
CAPITAL_PATTERN = re.compile(r"^capital\s*=\s*([ekdcb]_[A-Za-z0-9_-]+)")
RANK_BY_PREFIX = {
    "e": "empire",
    "k": "kingdom",
    "d": "duchy",
    "c": "county",
    "b": "barony",
}
EXPECTED_CHAIN = {
    "e": "e",
    "k": "ke",
    "d": "dke",
    "c": "cdke",
    "b": "bcdke",
}


@dataclass(frozen=True)
class ParsedTitle:
    title_id: str
    title_rank: str
    parent_title_id: str | None
    capital_title_id: str | None
    source_path: str
    source_line: int
    source_order: int


@dataclass(frozen=True)
class LandedTitlesLoadResult:
    reference_snapshot_id: str
    baseline_id: str
    title_count: int
    selectable_count: int
    warning_count: int
    parser_run_id: str


def parse_landed_title_files(game_root: str | Path) -> tuple[list[ParsedTitle], list[str]]:
    """Parse all installed landed-title text files and report duplicate keys."""
    root = Path(game_root)
    source_root = root / "common" / "landed_titles"
    if not source_root.is_dir():
        raise FileNotFoundError(f"Landed-title source folder does not exist: {source_root}")

    declarations: list[ParsedTitle] = []
    duplicate_notes: list[str] = []
    first_declaration: dict[str, ParsedTitle] = {}
    declaration_indexes: dict[str, int] = {}
    source_order = 0

    for path in sorted(source_root.rglob("*.txt")):
        relative_path = path.relative_to(root).as_posix()
        stack: list[tuple[int, str]] = []
        active_title: ParsedTitle | None = None
        for line_number, raw_line in enumerate(
            path.read_text(encoding="utf-8-sig").splitlines(),
            1,
        ):
            line = raw_line.split("#", 1)[0].rstrip()
            if not line.strip():
                continue
            indentation = len(line) - len(line.lstrip(" \t"))
            content = line.strip()
            title_match = TITLE_PATTERN.match(content)
            if title_match:
                while stack and indentation <= stack[-1][0]:
                    stack.pop()
                title_id = title_match.group(1)
                source_order += 1
                record = ParsedTitle(
                    title_id=title_id,
                    title_rank=RANK_BY_PREFIX[title_id[0]],
                    parent_title_id=stack[-1][1] if stack else None,
                    capital_title_id=None,
                    source_path=relative_path,
                    source_line=line_number,
                    source_order=source_order,
                )
                existing = first_declaration.get(title_id)
                if existing is None:
                    first_declaration[title_id] = record
                    declaration_indexes[title_id] = len(declarations)
                    declarations.append(record)
                else:
                    duplicate_notes.append(
                        f"{title_id}: {existing.source_path}:{existing.source_line}; "
                        f"{relative_path}:{line_number}"
                    )
                stack.append((indentation, title_id))
                active_title = record
                continue

            capital_match = CAPITAL_PATTERN.match(content)
            if capital_match and stack:
                title_id = stack[-1][1]
                existing = first_declaration.get(title_id)
                if existing is not None and existing == active_title:
                    replacement = ParsedTitle(
                        title_id=existing.title_id,
                        title_rank=existing.title_rank,
                        parent_title_id=existing.parent_title_id,
                        capital_title_id=capital_match.group(1),
                        source_path=existing.source_path,
                        source_line=existing.source_line,
                        source_order=existing.source_order,
                    )
                    first_declaration[title_id] = replacement
                    declarations[declaration_indexes[title_id]] = replacement
                    active_title = replacement

    return declarations, duplicate_notes


def validate_title_chains(
    titles: list[ParsedTitle],
    duplicate_notes: list[str],
) -> dict[str, tuple[bool, str | None]]:
    """Mark titles selectable only when their parent ranks form a canonical chain."""
    by_id = {title.title_id: title for title in titles}
    duplicate_ids = {note.split(":", 1)[0] for note in duplicate_notes}
    validation: dict[str, tuple[bool, str | None]] = {}

    for title in titles:
        if title.title_id in duplicate_ids:
            validation[title.title_id] = (False, "duplicate title declarations")
            continue
        chain = [title.title_id[0]]
        visited = {title.title_id}
        parent_id = title.parent_title_id
        invalid_note: str | None = None
        while parent_id is not None:
            if parent_id in visited:
                invalid_note = "cyclic parent hierarchy"
                break
            visited.add(parent_id)
            parent = by_id.get(parent_id)
            if parent is None:
                invalid_note = f"missing parent title: {parent_id}"
                break
            chain.append(parent.title_id[0])
            parent_id = parent.parent_title_id
        actual_chain = "".join(chain)
        if invalid_note is None and actual_chain != EXPECTED_CHAIN[title.title_id[0]]:
            invalid_note = f"non-canonical rank chain: {actual_chain}"
        validation[title.title_id] = (invalid_note is None, invalid_note)

    return validation


def load_landed_titles_candidate(
    *,
    game_root: str | Path,
    reference_snapshot_id: str,
    baseline_id: str,
    game_version: str,
    steam_build_id: str,
    baseline_date: str = "0867-01-01",
    database_path: str | Path | None = None,
) -> LandedTitlesLoadResult:
    """Replace one unpromoted candidate title slice transactionally."""
    root = Path(game_root).resolve()
    started_at = datetime.now(timezone.utc)
    parser_run_id = f"{reference_snapshot_id}:{PARSER_NAME}:{uuid4()}"
    titles, duplicate_notes = parse_landed_title_files(root)
    validation = validate_title_chains(titles, duplicate_notes)
    static_capitals = _resolve_static_capitals(titles)
    source_paths = sorted({title.source_path for title in titles})
    manifests = [_source_manifest(root, relative_path) for relative_path in source_paths]
    warning_count = len(duplicate_notes) + sum(
        1 for selectable, _ in validation.values() if not selectable
    )

    connection = connect(database_path)
    try:
        existing = connection.execute(
            """
            SELECT game_version, steam_build_id, review_status
            FROM source.reference_snapshots
            WHERE reference_snapshot_id = ?
            """,
            [reference_snapshot_id],
        ).fetchone()
        if existing is not None and existing[2] == "promoted":
            raise ValueError("A promoted reference snapshot cannot be replaced")
        if existing is not None and existing[:2] != (game_version, steam_build_id):
            raise ValueError("Snapshot ID already belongs to a different installed build")

        connection.execute("BEGIN TRANSACTION")
        connection.execute(
            "DELETE FROM reference.titles WHERE baseline_id = ?",
            [baseline_id],
        )
        connection.execute(
            "DELETE FROM reference.baselines WHERE baseline_id = ?",
            [baseline_id],
        )
        connection.execute(
            "DELETE FROM source.source_files WHERE reference_snapshot_id = ? AND source_group = ?",
            [reference_snapshot_id, PARSER_NAME],
        )
        connection.execute(
            """
            INSERT INTO source.reference_snapshots
            (reference_snapshot_id, game_version, steam_build_id, map_profile, review_status)
            VALUES (?, ?, ?, 'ck3', 'candidate')
            ON CONFLICT (reference_snapshot_id) DO NOTHING
            """,
            [reference_snapshot_id, game_version, steam_build_id],
        )
        connection.execute(
            """
            INSERT INTO reference.baselines
            (baseline_id, reference_snapshot_id, bookmark_id, baseline_date,
             label, support_status, historical_state_complete)
            VALUES (?, ?, 'bm_867', ?, '867', 'candidate', false)
            """,
            [baseline_id, reference_snapshot_id, baseline_date],
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
        connection.executemany(
            """
            INSERT INTO reference.titles
            (baseline_id, title_id, title_rank, parent_title_id, de_jure_liege_id,
             localization_key, display_name, selectable, source_path, source_line,
             parser_version, validation_status, validation_note, source_order,
             declared_capital_title_id, static_capital_title_id,
             static_capital_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    baseline_id,
                    title.title_id,
                    title.title_rank,
                    title.parent_title_id,
                    title.parent_title_id,
                    title.title_id,
                    _fallback_display_name(title.title_id),
                    validation[title.title_id][0],
                    title.source_path,
                    title.source_line,
                    PARSER_VERSION,
                    "valid" if validation[title.title_id][0] else "warning",
                    validation[title.title_id][1],
                    title.source_order,
                    title.capital_title_id,
                    static_capitals[title.title_id][0],
                    static_capitals[title.title_id][1],
                )
                for title in titles
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
                len(titles),
                warning_count,
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

    return LandedTitlesLoadResult(
        reference_snapshot_id=reference_snapshot_id,
        baseline_id=baseline_id,
        title_count=len(titles),
        selectable_count=sum(1 for selectable, _ in validation.values() if selectable),
        warning_count=warning_count,
        parser_run_id=parser_run_id,
    )


def _source_manifest(root: Path, relative_path: str) -> tuple[str, int, datetime, str]:
    path = root / Path(relative_path)
    statistics = path.stat()
    digest = sha256(path.read_bytes()).hexdigest()
    modified_at = datetime.fromtimestamp(statistics.st_mtime, timezone.utc)
    return relative_path, statistics.st_size, modified_at, digest


def _resolve_static_capitals(
    titles: list[ParsedTitle],
) -> dict[str, tuple[str | None, str]]:
    first_baronies: dict[str, ParsedTitle] = {}
    for title in titles:
        if title.title_rank != "barony" or title.parent_title_id is None:
            continue
        current = first_baronies.get(title.parent_title_id)
        if current is None or title.source_order < current.source_order:
            first_baronies[title.parent_title_id] = title

    capitals: dict[str, tuple[str | None, str]] = {}
    for title in titles:
        if title.capital_title_id is not None:
            capitals[title.title_id] = (title.capital_title_id, "declared_static")
        elif title.title_rank == "county" and title.title_id in first_baronies:
            capitals[title.title_id] = (
                first_baronies[title.title_id].title_id,
                "derived_first_barony",
            )
        elif title.title_rank == "barony":
            capitals[title.title_id] = (None, "not_applicable")
        else:
            capitals[title.title_id] = (None, "no_declaration")
    return capitals


def _fallback_display_name(title_id: str) -> str:
    return title_id[2:].replace("_", " ").title()