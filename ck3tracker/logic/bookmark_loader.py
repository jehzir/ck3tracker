"""Load installed CK3 bookmark collections into a candidate date profile."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from logic.root_database import connect
from logic.title_history_loader import _assignments, _parse_date, _scalar_value, _strip_comments


PARSER_NAME = "installed_bookmarks"
PARSER_VERSION = "1.1.0"

DLC_FEATURE_MAPPINGS = {
    "all_under_heaven": (
        "dlc022_ep4",
        "https://ck3.paradoxwikis.com/index.php?title=All_Under_Heaven&oldid=35744",
        "35744",
        "All Under Heaven page identifies new historical bookmarks as expansion features.",
    ),
    "khans_of_the_steppe": (
        "dlc020_ce2",
        "https://ck3.paradoxwikis.com/index.php?title=Khans_of_the_Steppe&oldid=33551",
        "33551",
        "Khans of the Steppe page identifies the Temujin bookmark as expansion content.",
    ),
    "landless_adventurer": (
        "dlc014_ep3",
        "https://ck3.paradoxwikis.com/index.php?title=Roads_to_Power&oldid=33550",
        "33550",
        "Roads to Power page identifies landless Adventurers as expansion features.",
    ),
}


@dataclass(frozen=True)
class BookmarkDeclaration:
    declaration_order: int
    entity_kind: str
    entity_id: str
    raw_script: str
    source_path: str
    source_line_start: int
    source_line_end: int


@dataclass(frozen=True)
class ParsedBookmark:
    bookmark_id: str
    group_id: str
    explicit_start_date: str | None
    is_playable: bool
    is_recommended: bool
    weight_script: str | None
    dlc_flag: str | None
    characters: tuple[tuple[object, ...], ...]


@dataclass(frozen=True)
class BookmarkParseResult:
    declarations: tuple[BookmarkDeclaration, ...]
    groups: tuple[tuple[str, str], ...]
    bookmarks: tuple[ParsedBookmark, ...]
    dlc_packages: tuple[DlcPackageEvidence, ...]
    manifests: tuple[tuple[str, int, datetime, str], ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class DlcPackageEvidence:
    package_id: str
    display_name: str
    steam_id: str | None
    pops_id: str | None
    msgr_id: str | None
    source_path: str
    source_sha256: str
    wiki_permanent_url: str
    wiki_revision_id: str
    evidence_note: str


@dataclass(frozen=True)
class BookmarkLoadResult:
    reference_snapshot_id: str
    baseline_id: str
    group_count: int
    bookmark_count: int
    direct_character_count: int
    related_character_count: int
    baseline_bookmark_count: int
    warning_count: int
    parser_run_id: str


def parse_bookmarks(game_root: str | Path) -> BookmarkParseResult:
    """Parse installed groups, bookmarks, challenges, and all source manifests."""
    root = Path(game_root).resolve()
    source_root = root / "common" / "bookmarks"
    if not source_root.is_dir():
        raise FileNotFoundError(f"Bookmark folder does not exist: {source_root}")

    manifests = [_manifest(root, path) for path in sorted(source_root.rglob("*")) if path.is_file()]
    declarations: list[BookmarkDeclaration] = []
    groups: list[tuple[str, str]] = []
    bookmarks: list[ParsedBookmark] = []
    warnings: list[str] = []
    seen: dict[tuple[str, str], int] = {}
    declaration_order = 0

    definition_files = (
        (source_root / "groups" / "00_bookmark_groups.txt", "group"),
        (source_root / "bookmarks" / "00_bookmarks.txt", "bookmark"),
        (source_root / "challenge_characters" / "00_challenge_characters.txt", "challenge"),
    )
    for path, entity_kind in definition_files:
        if not path.is_file():
            raise FileNotFoundError(f"Bookmark definition file does not exist: {path}")
        relative_path = path.relative_to(root).as_posix()
        text = _strip_comments(path.read_text(encoding="utf-8-sig"))
        for entity in _assignments(text):
            if entity.value_kind != "block":
                continue
            declaration_order += 1
            key = (entity_kind, entity.key)
            seen[key] = seen.get(key, 0) + 1
            declarations.append(
                BookmarkDeclaration(
                    declaration_order,
                    entity_kind,
                    entity.key,
                    entity.raw_value,
                    relative_path,
                    entity.line_start,
                    entity.line_end,
                )
            )
            fields = list(_assignments(entity.raw_value[1:-1], entity.line_start))
            if entity_kind == "group":
                start_date = _last_scalar(fields, "default_start_date")
                if start_date is None or _parse_date(start_date) is None:
                    warnings.append(f"{entity.key}: missing or invalid default_start_date")
                else:
                    groups.append((entity.key, _canonical_date(start_date)))
            elif entity_kind == "bookmark":
                bookmarks.append(_parse_bookmark(entity.key, fields))

    warnings.extend(
        f"duplicate {kind} declaration: {entity_id} ({count})"
        for (kind, entity_id), count in seen.items()
        if count > 1
    )
    dlc_packages = _load_dlc_package_evidence(
        root,
        {bookmark.dlc_flag for bookmark in bookmarks if bookmark.dlc_flag},
    )
    manifests.extend(
        _manifest(root, root / package.source_path) for package in dlc_packages
    )
    return BookmarkParseResult(
        tuple(declarations),
        tuple(groups),
        tuple(bookmarks),
        dlc_packages,
        tuple(manifests),
        tuple(warnings),
    )


def load_bookmarks_candidate(
    *,
    game_root: str | Path,
    reference_snapshot_id: str,
    baseline_id: str,
    database_path: str | Path | None = None,
) -> BookmarkLoadResult:
    """Replace installed bookmark evidence and link matching themes to a candidate baseline."""
    started_at = datetime.now(timezone.utc)
    parser_run_id = f"{reference_snapshot_id}:{PARSER_NAME}:{uuid4()}"
    parsed = parse_bookmarks(game_root)
    duplicate_ids = {
        warning.split(": ", 1)[1].rsplit(" (", 1)[0]
        for warning in parsed.warnings
        if warning.startswith("duplicate ")
    }
    groups_by_id = dict(parsed.groups)

    connection = connect(database_path)
    try:
        snapshot = connection.execute(
            "SELECT review_status FROM source.reference_snapshots WHERE reference_snapshot_id = ?",
            [reference_snapshot_id],
        ).fetchone()
        baseline = connection.execute(
            """
            SELECT baseline_date, support_status
            FROM reference.baselines
            WHERE baseline_id = ? AND reference_snapshot_id = ?
            """,
            [baseline_id, reference_snapshot_id],
        ).fetchone()
        if snapshot is None or baseline is None:
            raise ValueError("Existing snapshot and baseline are required")
        if snapshot[0] == "promoted" or baseline[1] == "promoted":
            raise ValueError("Promoted bookmark data cannot be replaced")

        baseline_date = baseline[0].isoformat()
        normalized_bookmarks: list[tuple[object, ...]] = []
        featured_rows: list[tuple[object, ...]] = []
        dlc_rows: list[tuple[object, ...]] = []
        bookmark_warnings: list[str] = []
        for bookmark in parsed.bookmarks:
            inherited_date = groups_by_id.get(bookmark.group_id)
            effective_date = bookmark.explicit_start_date or inherited_date
            notes: list[str] = []
            if inherited_date is None:
                notes.append("bookmark group is missing")
            if effective_date is None:
                notes.append("effective start date is missing")
            if bookmark.explicit_start_date and inherited_date and bookmark.explicit_start_date != inherited_date:
                notes.append("bookmark date disagrees with group date")
            if bookmark.bookmark_id in duplicate_ids:
                notes.append("duplicate bookmark declaration requires review")
            status = "warning" if notes else "valid"
            bookmark_warnings.extend(f"{bookmark.bookmark_id}: {note}" for note in notes)
            normalized_bookmarks.append(
                (
                    reference_snapshot_id,
                    bookmark.bookmark_id,
                    bookmark.group_id,
                    bookmark.explicit_start_date,
                    effective_date or "0000-00-00",
                    bookmark.is_playable,
                    bookmark.is_recommended,
                    bookmark.weight_script,
                    bookmark.bookmark_id,
                    f"{bookmark.bookmark_id}_desc",
                    status,
                    "; ".join(notes) if notes else None,
                )
            )
            featured_rows.extend(
                _validated_characters(connection, reference_snapshot_id, baseline_id, bookmark)
            )
            if bookmark.dlc_flag:
                mapping = DLC_FEATURE_MAPPINGS.get(bookmark.dlc_flag)
                resolved_package_id = mapping[0] if mapping else None
                dlc_rows.append(
                    (
                        reference_snapshot_id,
                        bookmark.bookmark_id,
                        "requires_dlc_flag",
                        bookmark.dlc_flag,
                        "resolved" if mapping else "raw_flag",
                        (
                            f"Reviewed feature mapping to {resolved_package_id}"
                            if mapping
                            else "No reviewed flag-to-package mapping exists"
                        ),
                        resolved_package_id,
                    )
                )

        baseline_bookmarks = [
            (baseline_id, bookmark.bookmark_id, bookmark.validation_status, bookmark.validation_note)
            for bookmark in _bookmark_rows(normalized_bookmarks)
            if bookmark.effective_start_date == baseline_date
        ]
        warning_count = (
            len(parsed.warnings)
            + len(bookmark_warnings)
            + sum(row[-2] == "warning" for row in featured_rows)
            + sum(row[4] != "resolved" for row in dlc_rows)
        )

        connection.execute("BEGIN TRANSACTION")
        for table, column, value in (
            ("source.bookmark_declarations", "reference_snapshot_id", reference_snapshot_id),
            ("reference.bookmark_groups", "reference_snapshot_id", reference_snapshot_id),
            ("reference.bookmarks", "reference_snapshot_id", reference_snapshot_id),
            ("reference.bookmark_featured_characters", "reference_snapshot_id", reference_snapshot_id),
            ("reference.bookmark_dlc_requirements", "reference_snapshot_id", reference_snapshot_id),
            ("reference.dlc_feature_mappings", "reference_snapshot_id", reference_snapshot_id),
            ("reference.dlc_packages", "reference_snapshot_id", reference_snapshot_id),
            ("reference.baseline_bookmarks", "baseline_id", baseline_id),
        ):
            connection.execute(f"DELETE FROM {table} WHERE {column} = ?", [value])
        connection.execute(
            "DELETE FROM source.source_files WHERE reference_snapshot_id = ? AND source_group = ?",
            [reference_snapshot_id, PARSER_NAME],
        )
        connection.executemany(
            """
            INSERT INTO source.source_files
            (reference_snapshot_id, relative_path, source_group, byte_size,
             modified_at_utc, sha256, parser_run_id) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (reference_snapshot_id, item[0], PARSER_NAME, *item[1:], parser_run_id)
                for item in parsed.manifests
            ],
        )
        connection.executemany(
            """
            INSERT INTO source.bookmark_declarations
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    reference_snapshot_id,
                    item.declaration_order,
                    item.entity_kind,
                    item.entity_id,
                    item.raw_script,
                    item.source_path,
                    item.source_line_start,
                    item.source_line_end,
                    "utf-8-sig",
                    PARSER_VERSION,
                    "review_required" if item.entity_id in duplicate_ids else "preserved",
                )
                for item in parsed.declarations
            ],
        )
        connection.executemany(
            """
            INSERT INTO reference.bookmark_groups
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (reference_snapshot_id, group_id, start_date, group_id, "valid", None)
                for group_id, start_date in parsed.groups
            ],
        )
        connection.executemany(
            "INSERT INTO reference.bookmarks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            normalized_bookmarks,
        )
        connection.executemany(
            "INSERT INTO reference.bookmark_featured_characters VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            featured_rows,
        )
        if parsed.dlc_packages:
            connection.executemany(
                """
                INSERT INTO reference.dlc_packages
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'valid', NULL)
                """,
                [
                    (
                        reference_snapshot_id,
                        package.package_id,
                        package.display_name,
                        package.steam_id,
                        package.pops_id,
                        package.msgr_id,
                        package.source_path,
                        package.source_sha256,
                        package.wiki_permanent_url,
                        package.wiki_revision_id,
                    )
                    for package in parsed.dlc_packages
                ],
            )
            connection.executemany(
                """
                INSERT INTO reference.dlc_feature_mappings
                VALUES (?, ?, ?, 'reviewed', ?)
                """,
                [
                    (
                        reference_snapshot_id,
                        feature_flag,
                        mapping[0],
                        mapping[3],
                    )
                    for feature_flag, mapping in DLC_FEATURE_MAPPINGS.items()
                    if any(package.package_id == mapping[0] for package in parsed.dlc_packages)
                ],
            )
        if dlc_rows:
            connection.executemany(
                """
                INSERT INTO reference.bookmark_dlc_requirements
                (reference_snapshot_id, bookmark_id, requirement_kind,
                 requirement_value, resolution_status, validation_note,
                 resolved_package_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                dlc_rows,
            )
        connection.executemany(
            "INSERT INTO reference.baseline_bookmarks VALUES (?, ?, ?, ?)",
            baseline_bookmarks,
        )
        connection.execute(
            "UPDATE reference.baselines SET bookmark_id = NULL WHERE baseline_id = ?",
            [baseline_id],
        )
        connection.execute(
            """
            INSERT INTO source.parser_runs
            (parser_run_id, reference_snapshot_id, parser_name, parser_version,
             status, started_at_utc, completed_at_utc, row_count, warning_count)
            VALUES (?, ?, ?, ?, 'completed', ?, ?, ?, ?)
            """,
            [parser_run_id, reference_snapshot_id, PARSER_NAME, PARSER_VERSION,
             started_at, datetime.now(timezone.utc), len(parsed.declarations), warning_count],
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

    direct_count = sum(row[4] == "featured" for row in featured_rows)
    return BookmarkLoadResult(
        reference_snapshot_id,
        baseline_id,
        len(parsed.groups),
        len(parsed.bookmarks),
        direct_count,
        len(featured_rows) - direct_count,
        len(baseline_bookmarks),
        warning_count,
        parser_run_id,
    )


@dataclass(frozen=True)
class _BookmarkRow:
    bookmark_id: str
    effective_start_date: str
    validation_status: str
    validation_note: str | None


def _bookmark_rows(rows: list[tuple[object, ...]]) -> list[_BookmarkRow]:
    return [_BookmarkRow(str(row[1]), str(row[4]), str(row[10]), row[11]) for row in rows]


def _load_dlc_package_evidence(
    game_root: Path,
    feature_flags: set[str],
) -> tuple[DlcPackageEvidence, ...]:
    packages: list[DlcPackageEvidence] = []
    for feature_flag in sorted(feature_flags):
        mapping = DLC_FEATURE_MAPPINGS.get(feature_flag)
        if mapping is None:
            continue
        package_id, wiki_url, wiki_revision_id, evidence_note = mapping
        descriptor_folder = game_root / "dlc" / package_id
        descriptors = sorted(descriptor_folder.glob("*.dlc"))
        if len(descriptors) != 1:
            raise ValueError(
                f"Expected one installed descriptor for {package_id}, found {len(descriptors)}"
            )
        descriptor = descriptors[0]
        fields = list(_assignments(_strip_comments(descriptor.read_text(encoding="utf-8-sig"))))
        descriptor_path = _last_scalar(fields, "path")
        pops_id = _last_scalar(fields, "pops_id")
        if descriptor_path != f"dlc/{package_id}" or pops_id != f"ck3_{package_id}":
            raise ValueError(f"Installed descriptor identity mismatch for {package_id}")
        relative_path, _, _, descriptor_sha256 = _manifest(game_root, descriptor)
        packages.append(
            DlcPackageEvidence(
                package_id,
                _last_scalar(fields, "name") or package_id,
                _last_scalar(fields, "steam_id"),
                pops_id,
                _last_scalar(fields, "msgr_id"),
                relative_path,
                descriptor_sha256,
                wiki_url,
                wiki_revision_id,
                evidence_note,
            )
        )
    return tuple(packages)


def _parse_bookmark(bookmark_id: str, fields) -> ParsedBookmark:
    group_id = _last_scalar(fields, "group") or ""
    raw_date = _last_scalar(fields, "start_date")
    explicit_date = _canonical_date(raw_date) if raw_date else None
    direct = [field for field in fields if field.key == "character" and field.value_kind == "block"]
    characters: list[tuple[object, ...]] = []
    ordinal = 0
    for featured_index, character in enumerate(direct, 1):
        ordinal += 1
        parent_ordinal = ordinal
        characters.append(_character_row(character, ordinal, None, "featured"))
        related = [
            field for field in _assignments(character.raw_value[1:-1], character.line_start)
            if field.key == "character" and field.value_kind == "block"
        ]
        for relation in related:
            ordinal += 1
            characters.append(_character_row(relation, ordinal, parent_ordinal, "related"))
    return ParsedBookmark(
        bookmark_id,
        group_id,
        explicit_date,
        _last_scalar(fields, "is_playable") == "yes",
        _last_scalar(fields, "recommended") == "yes",
        next((field.raw_value for field in fields if field.key == "weight"), None),
        _last_scalar(fields, "requires_dlc_flag"),
        tuple(characters),
    )


def _character_row(character, ordinal: int, parent: int | None, kind: str) -> tuple[object, ...]:
    fields = list(_assignments(character.raw_value[1:-1], character.line_start))
    return (
        ordinal,
        parent,
        kind,
        _last_scalar(fields, "history_id"),
        _last_scalar(fields, "title"),
        _last_scalar(fields, "name"),
        _last_scalar(fields, "relation"),
        _last_scalar(fields, "type"),
        _last_scalar(fields, "difficulty"),
        next((field.raw_value for field in fields if field.key == "position"), None),
    )


def _validated_characters(connection, snapshot_id: str, baseline_id: str, bookmark: ParsedBookmark) -> list[tuple[object, ...]]:
    rows: list[tuple[object, ...]] = []
    for character in bookmark.characters:
        ordinal, parent, kind, history_id, title_id, name_key, relation_key, character_type, difficulty, position = character
        notes: list[str] = []
        if kind == "featured":
            if not history_id or not connection.execute(
                "SELECT 1 FROM reference.character_baseline_states WHERE baseline_id = ? AND character_id = ?",
                [baseline_id, history_id],
            ).fetchone():
                notes.append("history character is missing")
            if not title_id or not connection.execute(
                "SELECT 1 FROM reference.titles WHERE baseline_id = ? AND title_id = ?",
                [baseline_id, title_id],
            ).fetchone():
                notes.append("featured title is missing")
            if not name_key or not connection.execute(
                """
                SELECT 1 FROM reference.localizations
                WHERE reference_snapshot_id = ? AND language = 'english' AND localization_key = ?
                """,
                [snapshot_id, name_key],
            ).fetchone():
                notes.append("name localization is missing")
        rows.append((
            snapshot_id,
            bookmark.bookmark_id,
            ordinal,
            parent,
            kind,
            history_id,
            title_id,
            name_key,
            relation_key,
            character_type,
            difficulty,
            position,
            "warning" if notes else "valid",
            "; ".join(notes) if notes else None,
        ))
    return rows


def _last_scalar(fields, key: str) -> str | None:
    matches = [field for field in fields if field.key == key and field.value_kind == "scalar"]
    return _scalar_value(matches[-1].raw_value) if matches else None


def _canonical_date(value: str) -> str:
    parsed = _parse_date(value)
    if parsed is None:
        raise ValueError(f"Invalid CK3 bookmark date: {value}")
    return str(parsed)


def _manifest(root: Path, path: Path) -> tuple[str, int, datetime, str]:
    raw_bytes = path.read_bytes()
    return (
        path.relative_to(root).as_posix(),
        len(raw_bytes),
        datetime.fromtimestamp(path.stat().st_mtime, timezone.utc),
        sha256(raw_bytes).hexdigest(),
    )