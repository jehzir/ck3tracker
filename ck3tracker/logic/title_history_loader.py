"""Load installed CK3 title history and materialize a candidate baseline date."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from hashlib import sha256
from pathlib import Path
import re
from typing import Iterator
from uuid import uuid4

from logic.root_database import connect


PARSER_NAME = "installed_title_history"
PARSER_VERSION = "1.4.0"
DATE_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
TITLE_PATTERN = re.compile(r"^[ekdcb]_[A-Za-z0-9_-]+$")
NORMALIZED_OPERATIONS = {"holder", "liege", "government", "change_development_level"}
CAPITAL_OPERATIONS = {"set_capital_county", "set_capital_barony"}
LOAD_ORDER_PAGE_KEY = "title_history_load_order"
LOAD_ORDER_CANONICAL_URL = "https://ck3.paradoxwikis.com/Modding#Single_object_override"
LOAD_ORDER_PERMANENT_URL = "https://ck3.paradoxwikis.com/index.php?title=Modding&oldid=35725#Single_object_override"
LOAD_ORDER_REVISION_ID = "35725"
TGP_FEATURE_FLAG = "all_under_heaven"
TGP_EFFECT_PATH = "common/scripted_effects/10_dlc_tgp_scripted_effects.txt"
TGP_TRIGGER_PATH = "common/scripted_triggers/00_has_dlc_scripted_triggers.txt"
TGP_EFFECT_DEFINITION = (
    "{ if = { limit = { NOT = { has_dlc_feature = all_under_heaven } "
    "game_start_date = $DATE$ } holder ?= { "
    "empty_treasury_when_abandoning_landed_life_effect = yes "
    "destroy_title = prev } } }"
)
TGP_TRIGGER_DEFINITION = "{ has_dlc_feature = all_under_heaven }"
LAW_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


@dataclass(frozen=True, order=True)
class CK3Date:
    year: int
    month: int
    day: int

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"


@dataclass(frozen=True)
class Assignment:
    key: str
    raw_value: str
    value_kind: str
    line_start: int
    line_end: int


@dataclass(frozen=True)
class HistoryOperation:
    declaration_order: int
    source_block_order: int
    title_id: str
    effective_date: CK3Date
    operation_order: int
    operation_key: str
    value_kind: str
    scalar_value: str | None
    raw_script: str
    source_path: str
    source_line_start: int
    source_line_end: int
    encoding_name: str


@dataclass(frozen=True)
class TitleHistoryBlock:
    source_block_order: int
    title_id: str
    source_path: str
    source_line_start: int
    source_line_end: int
    raw_script: str
    raw_sha256: str
    semantic_sha256: str
    duplicate_classification: str = "unique"
    baseline_conflict_fields: tuple[str, ...] = ()
    resolution_status: str = "sole_declaration"
    is_winner: bool = True


@dataclass(frozen=True)
class LawDefinition:
    law_id: str
    law_group_id: str
    source_path: str
    source_line_start: int
    source_line_end: int
    source_order: int
    raw_script: str
    raw_sha256: str


@dataclass(frozen=True)
class TitleHistoryLoadResult:
    reference_snapshot_id: str
    baseline_id: str
    declaration_count: int
    event_count: int
    state_count: int
    warning_count: int
    parser_run_id: str


def parse_title_history(
    game_root: str | Path,
) -> tuple[
    list[HistoryOperation],
    list[TitleHistoryBlock],
    list[str],
    list[tuple[str, int, datetime, str]],
]:
    """Parse all dated title-history operations with source provenance."""
    root = Path(game_root).resolve()
    source_root = root / "history" / "titles"
    if not source_root.is_dir():
        raise FileNotFoundError(f"Title-history folder does not exist: {source_root}")

    operations: list[HistoryOperation] = []
    blocks: list[TitleHistoryBlock] = []
    warnings: list[str] = []
    manifests: list[tuple[str, int, datetime, str]] = []
    declaration_order = 0
    source_block_order = 0
    title_occurrences: dict[str, int] = {}
    for path in sorted(source_root.rglob("*.txt")):
        relative_path = path.relative_to(root).as_posix()
        raw_bytes = path.read_bytes()
        text, encoding_name = _decode_history(raw_bytes)
        manifests.append(
            (
                relative_path,
                len(raw_bytes),
                datetime.fromtimestamp(path.stat().st_mtime, timezone.utc),
                sha256(raw_bytes).hexdigest(),
            )
        )
        clean_text = _strip_comments(text)
        for title in _assignments(clean_text):
            if not TITLE_PATTERN.match(title.key) or title.value_kind != "block":
                continue
            source_block_order += 1
            title_occurrences[title.key] = title_occurrences.get(title.key, 0) + 1
            block_operations: list[HistoryOperation] = []
            for dated_block in _assignments(title.raw_value[1:-1], title.line_start):
                effective_date = _parse_date(dated_block.key)
                if effective_date is None or dated_block.value_kind != "block":
                    continue
                operation_order = 0
                for operation in _assignments(
                    dated_block.raw_value[1:-1], dated_block.line_start
                ):
                    operation_order += 1
                    declaration_order += 1
                    scalar_value = (
                        _scalar_value(operation.raw_value)
                        if operation.value_kind == "scalar"
                        else None
                    )
                    operations.append(
                        HistoryOperation(
                            declaration_order=declaration_order,
                            source_block_order=source_block_order,
                            title_id=title.key,
                            effective_date=effective_date,
                            operation_order=operation_order,
                            operation_key=operation.key,
                            value_kind=operation.value_kind,
                            scalar_value=scalar_value,
                            raw_script=operation.raw_value,
                            source_path=relative_path,
                            source_line_start=operation.line_start,
                            source_line_end=operation.line_end,
                            encoding_name=encoding_name,
                        )
                    )
                    block_operations.append(operations[-1])
            semantic_text = "\n".join(
                sorted(
                    f"{item.effective_date}|{item.operation_key}|{item.value_kind}|"
                    f"{item.scalar_value if item.scalar_value is not None else ' '.join(item.raw_script.split())}"
                    for item in block_operations
                )
            )
            blocks.append(
                TitleHistoryBlock(
                    source_block_order,
                    title.key,
                    relative_path,
                    title.line_start,
                    title.line_end,
                    title.raw_value,
                    sha256(title.raw_value.encode("utf-8")).hexdigest(),
                    sha256(semantic_text.encode("utf-8")).hexdigest(),
                )
            )

    warnings.extend(
        f"duplicate title declaration: {title_id} ({count})"
        for title_id, count in title_occurrences.items()
        if count > 1
    )
    return operations, blocks, warnings, manifests


def load_title_history_candidate(
    *,
    game_root: str | Path,
    reference_snapshot_id: str,
    baseline_id: str,
    database_path: str | Path | None = None,
) -> TitleHistoryLoadResult:
    """Replace title-history evidence and one candidate baseline state atomically."""
    started_at = datetime.now(timezone.utc)
    parser_run_id = f"{reference_snapshot_id}:{PARSER_NAME}:{uuid4()}"
    operations, blocks, parse_warnings, manifests = parse_title_history(game_root)
    if any(_tgp_no_dlc_invocation_date(operation) for operation in operations):
        manifests.extend(_verify_tgp_no_dlc_evidence(Path(game_root).resolve()))
    required_law_ids = {
        law_id
        for operation in operations
        for law_id in (_succession_law_ids(operation) or ())
    }
    law_definitions: list[LawDefinition] = []
    if any(operation.operation_key == "succession_laws" for operation in operations):
        law_definitions, law_manifests = _load_required_law_definitions(
            Path(game_root).resolve(), required_law_ids
        )
        manifests.extend(law_manifests)
    installed_law_ids = {definition.law_id for definition in law_definitions}

    connection = connect(database_path)
    try:
        snapshot = connection.execute(
            "SELECT review_status FROM source.reference_snapshots WHERE reference_snapshot_id = ?",
            [reference_snapshot_id],
        ).fetchone()
        baseline = connection.execute(
            """
            SELECT baseline_date, support_status, historical_state_complete
            FROM reference.baselines
            WHERE baseline_id = ? AND reference_snapshot_id = ?
            """,
            [baseline_id, reference_snapshot_id],
        ).fetchone()
        if snapshot is None or baseline is None:
            raise ValueError("Existing snapshot and baseline are required")
        if snapshot[0] == "promoted" or baseline[1] == "promoted":
            raise ValueError("Promoted reference history cannot be replaced")

        baseline_date = baseline[0]
        tgp_package = connection.execute(
            """
            SELECT package.package_id
            FROM reference.dlc_feature_mappings mapping
            JOIN reference.dlc_packages package
              ON package.reference_snapshot_id = mapping.reference_snapshot_id
             AND package.package_id = mapping.package_id
            WHERE mapping.reference_snapshot_id = ?
              AND mapping.feature_flag = ?
              AND mapping.review_status = 'reviewed'
              AND package.validation_status = 'valid'
            """,
            [reference_snapshot_id, TGP_FEATURE_FLAG],
        ).fetchone()
        tgp_package_id = str(tgp_package[0]) if tgp_package else None
        classified_blocks, duplicate_classifications, conflict_fields, winning_blocks = (
            _classify_duplicate_blocks(blocks, operations, baseline_date)
        )
        title_rows = connection.execute(
                """
                SELECT title_id, title_rank, parent_title_id,
                       static_capital_title_id, static_capital_status
                FROM reference.titles
                WHERE baseline_id = ?
                ORDER BY title_id
                """,
                [baseline_id],
            ).fetchall()
        installed_title_ids = {str(row[0]) for row in title_rows}
        effective_operations = [
            operation
            for operation in operations
            if operation.title_id not in winning_blocks
            or operation.source_block_order == winning_blocks[operation.title_id]
        ]
        events = _normalized_events(
            effective_operations,
            title_rows,
            tgp_package_id=tgp_package_id,
            installed_law_ids=installed_law_ids,
            installed_title_ids=installed_title_ids,
        )
        states = _materialize_states(
            title_rows,
            effective_operations,
            events,
            baseline_date,
            duplicate_classifications,
            conflict_fields,
            tgp_package_id=tgp_package_id,
            installed_law_ids=installed_law_ids,
            installed_title_ids=installed_title_ids,
        )
        baseline_laws = _materialize_title_laws(
            effective_operations, baseline_date, installed_law_ids
        )
        baseline_de_jure_lieges = _materialize_de_jure_lieges(
            effective_operations, baseline_date, installed_title_ids
        )
        warning_count = len(parse_warnings) + sum(
            state[-3] == "warning" for state in states
        )

        connection.execute("BEGIN TRANSACTION")
        connection.execute(
            "DELETE FROM source.wiki_pages WHERE reference_snapshot_id = ? AND page_key = ?",
            [reference_snapshot_id, LOAD_ORDER_PAGE_KEY],
        )
        connection.execute(
            """
            INSERT INTO source.wiki_pages
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                reference_snapshot_id,
                LOAD_ORDER_PAGE_KEY,
                LOAD_ORDER_CANONICAL_URL,
                LOAD_ORDER_PERMANENT_URL,
                LOAD_ORDER_REVISION_ID,
                started_at,
                None,
                "reviewed",
            ],
        )
        connection.execute(
            """
            INSERT OR REPLACE INTO source.wiki_page_links
            VALUES (?, 'wiki_root', ?, 'Modding', 'https://ck3.paradoxwikis.com/Modding')
            """,
            [reference_snapshot_id, LOAD_ORDER_PAGE_KEY],
        )
        connection.execute(
            "DELETE FROM source.title_history_declarations WHERE reference_snapshot_id = ?",
            [reference_snapshot_id],
        )
        connection.execute(
            "DELETE FROM source.title_history_blocks WHERE reference_snapshot_id = ?",
            [reference_snapshot_id],
        )
        connection.execute(
            "DELETE FROM reference.title_history_events WHERE reference_snapshot_id = ?",
            [reference_snapshot_id],
        )
        connection.execute(
            "DELETE FROM reference.law_definitions WHERE reference_snapshot_id = ?",
            [reference_snapshot_id],
        )
        connection.execute(
            "DELETE FROM reference.title_baseline_laws WHERE baseline_id = ?",
            [baseline_id],
        )
        connection.execute(
            "DELETE FROM reference.title_baseline_de_jure_lieges WHERE baseline_id = ?",
            [baseline_id],
        )
        connection.execute(
            "DELETE FROM reference.title_baseline_states WHERE baseline_id = ?",
            [baseline_id],
        )
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
                for item in manifests
            ],
        )
        connection.executemany(
            """
            INSERT INTO source.title_history_blocks
            (reference_snapshot_id, source_block_order, title_id, source_path,
             source_line_start, source_line_end, raw_script, raw_sha256,
             semantic_sha256, duplicate_classification,
             baseline_conflict_fields, resolution_status, is_winner)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    reference_snapshot_id,
                    item.source_block_order,
                    item.title_id,
                    item.source_path,
                    item.source_line_start,
                    item.source_line_end,
                    item.raw_script,
                    item.raw_sha256,
                    item.semantic_sha256,
                    item.duplicate_classification,
                    ",".join(item.baseline_conflict_fields) or None,
                    item.resolution_status,
                    item.is_winner,
                )
                for item in classified_blocks
            ],
        )
        connection.executemany(
            """
            INSERT INTO source.title_history_declarations
            (reference_snapshot_id, declaration_order, title_id, effective_date,
             operation_order, operation_key, value_kind, scalar_value, raw_script,
             source_path, source_line_start, source_line_end, encoding_name,
             parser_version, resolution_status, source_block_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    reference_snapshot_id,
                    item.declaration_order,
                    item.title_id,
                    str(item.effective_date),
                    item.operation_order,
                    item.operation_key,
                    item.value_kind,
                    item.scalar_value,
                    item.raw_script,
                    item.source_path,
                    item.source_line_start,
                    item.source_line_end,
                    item.encoding_name,
                    PARSER_VERSION,
                    "superseded"
                    if item.title_id in winning_blocks
                    and item.source_block_order != winning_blocks[item.title_id]
                    else "review_required"
                    if duplicate_classifications.get(item.title_id) == "conflicting_at_baseline"
                    else "normalized"
                    if item.operation_key in NORMALIZED_OPERATIONS
                    or _extract_capital_effects(item, {})[1]
                    or (
                        tgp_package_id is not None
                        and _tgp_no_dlc_invocation_date(item) is not None
                    )
                    or _has_valid_succession_laws(item, installed_law_ids)
                    or _has_valid_de_jure_liege(item, installed_title_ids)
                    else "preserved",
                    item.source_block_order,
                )
                for item in operations
            ],
        )
        if law_definitions:
            connection.executemany(
                """
                INSERT INTO reference.law_definitions
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'valid', NULL)
                """,
                [
                    (
                        reference_snapshot_id,
                        item.law_id,
                        item.law_group_id,
                        item.source_path,
                        item.source_line_start,
                        item.source_line_end,
                        item.source_order,
                        item.raw_script,
                        item.raw_sha256,
                        PARSER_VERSION,
                    )
                    for item in law_definitions
                ],
            )
        if events:
            connection.executemany(
                """
                INSERT INTO reference.title_history_events
                (reference_snapshot_id, title_id, effective_date, event_sequence,
                 event_type, text_value, integer_value, source_declaration_order,
                 validation_status, validation_note, required_game_start_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (reference_snapshot_id, event[0], str(event[1]), *event[2:])
                    for event in events
                ],
            )
        if baseline_laws:
            connection.executemany(
                """
                INSERT INTO reference.title_baseline_laws
                (baseline_id, title_id, law_order, law_id, effective_date,
                 source_declaration_order, validation_status, validation_note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [(baseline_id, *law) for law in baseline_laws],
            )
        if baseline_de_jure_lieges:
            connection.executemany(
                """
                INSERT INTO reference.title_baseline_de_jure_lieges
                (baseline_id, title_id, de_jure_liege_title_id,
                 de_jure_liege_status, effective_date, source_declaration_order,
                 validation_status, validation_note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [(baseline_id, *state) for state in baseline_de_jure_lieges],
            )
        connection.executemany(
            """
            INSERT INTO reference.title_baseline_states
            (baseline_id, title_id, holder_character_id, holder_status,
             liege_title_id, liege_status, government_id, government_status,
             development_level, development_status, capital_title_id,
             capital_status, validation_status, validation_note,
             capital_source_event_sequence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [(baseline_id, *state) for state in states],
        )
        connection.execute(
            """
            INSERT INTO source.parser_runs
            (parser_run_id, reference_snapshot_id, parser_name, parser_version,
             status, started_at_utc, completed_at_utc, row_count, warning_count)
            VALUES (?, ?, ?, ?, 'completed', ?, ?, ?, ?)
            """,
            [parser_run_id, reference_snapshot_id, PARSER_NAME, PARSER_VERSION,
             started_at, datetime.now(timezone.utc), len(operations), warning_count],
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

    return TitleHistoryLoadResult(
        reference_snapshot_id, baseline_id, len(operations), len(events),
        len(states), warning_count, parser_run_id
    )


def _normalized_events(
    operations: list[HistoryOperation],
    title_rows: list[tuple[object, ...]],
    *,
    tgp_package_id: str | None = None,
    installed_law_ids: set[str] | None = None,
    installed_title_ids: set[str] | None = None,
) -> list[tuple[object, ...]]:
    installed_law_ids = installed_law_ids or set()
    installed_title_ids = installed_title_ids or set()
    events: list[tuple[object, ...]] = []
    parents = {str(row[0]): row[2] for row in title_rows}
    ranks = {str(row[0]): str(row[1]) for row in title_rows}
    ordered = sorted(operations, key=lambda item: (item.effective_date, item.declaration_order))
    sequence = 0
    for operation in ordered:
        capital_effects, _ = _extract_capital_effects(operation, parents, ranks)
        if capital_effects:
            for owner_id, event_type, target_id, required_date, status, note in capital_effects:
                sequence += 1
                events.append((
                    owner_id, operation.effective_date, sequence, event_type,
                    target_id, None, operation.declaration_order, status, note,
                    required_date,
                ))
            continue
        tgp_date = _tgp_no_dlc_invocation_date(operation)
        if tgp_package_id is not None and tgp_date is not None:
            sequence += 1
            events.append((
                operation.title_id,
                operation.effective_date,
                sequence,
                "dlc_gated_noop",
                TGP_FEATURE_FLAG,
                None,
                operation.declaration_order,
                "valid",
                f"installed {tgp_package_id} makes destruction condition false",
                str(tgp_date),
            ))
            continue
        law_ids = _succession_law_ids(operation)
        if law_ids is not None and set(law_ids) <= installed_law_ids:
            sequence += 1
            events.append((
                operation.title_id,
                operation.effective_date,
                sequence,
                "succession_laws_replaced",
                ",".join(law_ids),
                None,
                operation.declaration_order,
                "valid",
                "installed law IDs replace the prior explicit title-law set",
                None,
            ))
            continue
        de_jure_target = _de_jure_liege_target(operation, installed_title_ids)
        if de_jure_target is not _INVALID_DE_JURE_TARGET:
            sequence += 1
            events.append((
                operation.title_id,
                operation.effective_date,
                sequence,
                "de_jure_liege_replaced",
                de_jure_target,
                None,
                operation.declaration_order,
                "valid",
                "dated title-history declaration replaces dynamic de-jure parentage",
                None,
            ))
            continue
        if operation.operation_key not in NORMALIZED_OPERATIONS:
            continue
        sequence += 1
        integer_value = None
        text_value = operation.scalar_value
        status = "valid"
        note = None
        if operation.operation_key == "change_development_level":
            try:
                integer_value = int(operation.scalar_value or "")
                text_value = None
            except ValueError:
                status = "warning"
                note = "development delta is not an integer"
        events.append((operation.title_id, operation.effective_date, sequence,
                       operation.operation_key, text_value, integer_value,
                       operation.declaration_order, status, note, None))
    return events


def _materialize_states(
    title_rows: list[tuple[object, ...]],
    operations: list[HistoryOperation],
    events: list[tuple[object, ...]],
    baseline_date: date,
    duplicate_classifications: dict[str, str] | None = None,
    conflict_fields: dict[str, set[str]] | None = None,
    *,
    tgp_package_id: str | None = None,
    installed_law_ids: set[str] | None = None,
    installed_title_ids: set[str] | None = None,
) -> list[tuple[object, ...]]:
    duplicate_classifications = duplicate_classifications or {}
    conflict_fields = conflict_fields or {}
    installed_law_ids = installed_law_ids or set()
    installed_title_ids = installed_title_ids or set()
    cutoff = CK3Date(baseline_date.year, baseline_date.month, baseline_date.day)
    by_title: dict[str, list[HistoryOperation]] = {}
    for operation in operations:
        if operation.effective_date <= cutoff:
            by_title.setdefault(operation.title_id, []).append(operation)

    capital_events: dict[str, list[tuple[object, ...]]] = {}
    for event in events:
        if event[3] in CAPITAL_OPERATIONS and event[1] <= cutoff:
            capital_events.setdefault(str(event[0]), []).append(event)

    states: list[tuple[object, ...]] = []
    for title_row in title_rows:
        title_id = str(title_row[0])
        capital = title_row[3]
        capital_status = str(title_row[4] or "no_declaration")
        capital_source_sequence = None
        holder = liege = government = None
        holder_status = liege_status = government_status = "no_declaration"
        development = 0
        development_status = "no_declaration"
        unknown_operations: list[str] = []
        ordered = sorted(
            by_title.get(title_id, []),
            key=lambda item: (item.effective_date, item.declaration_order),
        )
        for operation in ordered:
            value = operation.scalar_value
            if operation.operation_key == "holder" and value is not None:
                holder = None if value == "0" else value
                holder_status = "explicit_unheld" if value == "0" else "declared"
            elif operation.operation_key == "liege" and value is not None:
                liege = None if value == "0" else value
                liege_status = "explicit_independent" if value == "0" else "declared"
            elif operation.operation_key == "government" and value is not None:
                government = value
                government_status = "declared"
            elif operation.operation_key == "change_development_level":
                try:
                    development += int(value or "")
                    development_status = "derived"
                except ValueError:
                    unknown_operations.append(operation.operation_key)
            elif operation.operation_key == "effect":
                recognized, fully_normalized = _extract_capital_effects(operation, {})
                is_tgp_noop = (
                    tgp_package_id is not None
                    and _tgp_no_dlc_invocation_date(operation) is not None
                )
                if (not recognized or not fully_normalized) and not is_tgp_noop:
                    unknown_operations.append(operation.operation_key)
            elif _has_valid_succession_laws(operation, installed_law_ids):
                continue
            elif _has_valid_de_jure_liege(operation, installed_title_ids):
                continue
            else:
                unknown_operations.append(operation.operation_key)
        for event in capital_events.get(title_id, []):
            required_date = event[9]
            if event[7] != "valid" or (
                required_date is not None and required_date != str(cutoff)
            ):
                continue
            capital = event[4]
            capital_status = (
                "history_set_capital_county"
                if event[3] == "set_capital_county"
                else "history_set_capital_barony"
            )
            capital_source_sequence = event[2]
        ambiguous_fields = (
            conflict_fields.get(title_id, set())
            if duplicate_classifications.get(title_id) == "conflicting_at_baseline"
            else set()
        )
        if "holder" in ambiguous_fields:
            holder = None
            holder_status = "ambiguous_duplicate"
        if "liege" in ambiguous_fields:
            liege = None
            liege_status = "ambiguous_duplicate"
        if "government" in ambiguous_fields:
            government = None
            government_status = "ambiguous_duplicate"
        validation_note = None
        validation_status = "valid"
        if unknown_operations:
            validation_status = "warning"
            validation_note = "not evaluated: " + ", ".join(sorted(set(unknown_operations)))
        if duplicate_classifications.get(title_id) == "conflicting_at_baseline":
            validation_status = "warning"
            duplicate_note = "baseline-conflicting duplicate title declarations: " + ", ".join(
                sorted(ambiguous_fields)
            )
            validation_note = (
                f"{validation_note}; {duplicate_note}"
                if validation_note
                else duplicate_note
            )
        states.append((
            title_id, holder, holder_status, liege, liege_status, government,
            government_status, development if development_status == "derived" else None,
            development_status, capital, capital_status, validation_status,
            validation_note, capital_source_sequence,
        ))
    return states


def _materialize_title_laws(
    operations: list[HistoryOperation],
    baseline_date: date,
    installed_law_ids: set[str],
) -> list[tuple[object, ...]]:
    cutoff = CK3Date(baseline_date.year, baseline_date.month, baseline_date.day)
    latest: dict[str, tuple[HistoryOperation, tuple[str, ...]]] = {}
    ordered = sorted(operations, key=lambda item: (item.effective_date, item.declaration_order))
    for operation in ordered:
        if operation.effective_date > cutoff:
            continue
        law_ids = _succession_law_ids(operation)
        if law_ids is not None and set(law_ids) <= installed_law_ids:
            latest[operation.title_id] = (operation, law_ids)
    rows: list[tuple[object, ...]] = []
    for title_id, (operation, law_ids) in latest.items():
        rows.extend(
            (
                title_id,
                law_order,
                law_id,
                str(operation.effective_date),
                operation.declaration_order,
                "valid",
                None,
            )
            for law_order, law_id in enumerate(law_ids, start=1)
        )
    return rows


_INVALID_DE_JURE_TARGET = object()


def _de_jure_liege_target(
    operation: HistoryOperation, installed_title_ids: set[str]
) -> str | None | object:
    if operation.operation_key != "de_jure_liege" or operation.value_kind != "scalar":
        return _INVALID_DE_JURE_TARGET
    target = operation.scalar_value
    if target == "0":
        return None
    if target is None or target not in installed_title_ids or target == operation.title_id:
        return _INVALID_DE_JURE_TARGET
    return target


def _has_valid_de_jure_liege(
    operation: HistoryOperation, installed_title_ids: set[str]
) -> bool:
    return _de_jure_liege_target(operation, installed_title_ids) is not _INVALID_DE_JURE_TARGET


def _materialize_de_jure_lieges(
    operations: list[HistoryOperation],
    baseline_date: date,
    installed_title_ids: set[str],
) -> list[tuple[object, ...]]:
    cutoff = CK3Date(baseline_date.year, baseline_date.month, baseline_date.day)
    latest: dict[str, tuple[HistoryOperation, str | None]] = {}
    ordered = sorted(operations, key=lambda item: (item.effective_date, item.declaration_order))
    for operation in ordered:
        if operation.effective_date > cutoff:
            continue
        target = _de_jure_liege_target(operation, installed_title_ids)
        if target is not _INVALID_DE_JURE_TARGET:
            latest[operation.title_id] = (operation, target)
    return [
        (
            title_id,
            target,
            "explicit_clear" if target is None else "declared",
            str(operation.effective_date),
            operation.declaration_order,
            "valid",
            None,
        )
        for title_id, (operation, target) in sorted(latest.items())
    ]


def _classify_duplicate_blocks(
    blocks: list[TitleHistoryBlock],
    operations: list[HistoryOperation],
    baseline_date: date,
) -> tuple[
    list[TitleHistoryBlock],
    dict[str, str],
    dict[str, set[str]],
    dict[str, int],
]:
    cutoff = CK3Date(baseline_date.year, baseline_date.month, baseline_date.day)
    blocks_by_title: dict[str, list[TitleHistoryBlock]] = {}
    operations_by_block: dict[int, list[HistoryOperation]] = {}
    for block in blocks:
        blocks_by_title.setdefault(block.title_id, []).append(block)
    for operation in operations:
        operations_by_block.setdefault(operation.source_block_order, []).append(operation)

    classifications: dict[str, str] = {}
    conflicts_by_title: dict[str, set[str]] = {}
    winning_blocks: dict[str, int] = {}
    classified: list[TitleHistoryBlock] = []
    singleton_keys = {"holder", "liege", "government"}
    for title_id, title_blocks in blocks_by_title.items():
        if len(title_blocks) == 1:
            classified.extend(title_blocks)
            continue
        if len({block.semantic_sha256 for block in title_blocks}) == 1:
            classification = "semantic_identical"
            conflict_fields: set[str] = set()
        else:
            dated_values: dict[tuple[CK3Date, str], set[str]] = {}
            for block in title_blocks:
                for operation in operations_by_block.get(block.source_block_order, []):
                    if operation.operation_key in singleton_keys and operation.scalar_value is not None:
                        dated_values.setdefault(
                            (operation.effective_date, operation.operation_key), set()
                        ).add(operation.scalar_value)
            dated_conflicts = {
                (effective_date, key)
                for (effective_date, key), observed in dated_values.items()
                if len(observed) > 1
            }
            baseline_conflicts = {
                key for effective_date, key in dated_conflicts if effective_date <= cutoff
            }
            if baseline_conflicts:
                conflict_fields = baseline_conflicts
                source_paths = {block.source_path for block in title_blocks}
                winning_path = max(source_paths)
                candidates = [
                    block for block in title_blocks if block.source_path == winning_path
                ]
                if len(source_paths) > 1 and len(candidates) == 1:
                    classification = "resolved_by_source_order"
                    winning_blocks[title_id] = candidates[0].source_block_order
                else:
                    classification = "conflicting_at_baseline"
            elif any(effective_date > cutoff for effective_date, _ in dated_conflicts):
                classification = "conflicting_after_baseline"
                conflict_fields = set()
            else:
                classification = "additive_nonconflicting"
                conflict_fields = set()
        classifications[title_id] = classification
        conflicts_by_title[title_id] = conflict_fields
        classified.extend(
            TitleHistoryBlock(
                block.source_block_order,
                block.title_id,
                block.source_path,
                block.source_line_start,
                block.source_line_end,
                block.raw_script,
                block.raw_sha256,
                block.semantic_sha256,
                classification,
                tuple(sorted(conflict_fields)),
                "winner"
                if winning_blocks.get(title_id) == block.source_block_order
                else "superseded"
                if title_id in winning_blocks
                else "unresolved",
                winning_blocks.get(title_id) == block.source_block_order,
            )
            for block in title_blocks
        )
    return (
        sorted(classified, key=lambda item: item.source_block_order),
        classifications,
        conflicts_by_title,
        winning_blocks,
    )


def _extract_capital_effects(
    operation: HistoryOperation,
    parents: dict[str, object],
    ranks: dict[str, str] | None = None,
) -> tuple[list[tuple[object, ...]], bool]:
    if operation.operation_key != "effect" or operation.value_kind != "block":
        return [], False

    fields = list(_assignments(operation.raw_script[1:-1], operation.source_line_start))
    effects: list[tuple[object, ...]] = []
    handled = 0
    for field in fields:
        if field.key == "set_capital_county" and field.value_kind == "scalar":
            target = _scalar_value(field.raw_value)
            if target.startswith("title:"):
                target = target[6:]
            status = "valid" if (
                target.startswith("c_")
                and (ranks is None or ranks.get(target) == "county")
            ) else "warning"
            note = None if status == "valid" else "capital county target is not an installed county"
            effects.append((operation.title_id, field.key, target, None, status, note))
            handled += 1
        elif field.key == "set_capital_barony" and field.value_kind == "scalar":
            value = _scalar_value(field.raw_value)
            owner_id = parents.get(operation.title_id)
            status = "valid" if (
                value == "yes"
                and owner_id is not None
                and (ranks is None or ranks.get(operation.title_id) == "barony")
            ) else "warning"
            note = None if status == "valid" else "capital barony requires yes on a parented barony"
            effects.append((owner_id or operation.title_id, field.key, operation.title_id, None, status, note))
            handled += 1
        elif field.key == "if" and field.value_kind == "block":
            conditional = list(_assignments(field.raw_value[1:-1], field.line_start))
            limits = [item for item in conditional if item.key == "limit" and item.value_kind == "block"]
            setters = [item for item in conditional if item.key == "set_capital_barony" and item.value_kind == "scalar"]
            if len(limits) == 1 and len(setters) == 1 and len(conditional) == 2:
                conditions = list(_assignments(limits[0].raw_value[1:-1], limits[0].line_start))
                if len(conditions) == 1 and conditions[0].key == "game_start_date":
                    required = _parse_date(_scalar_value(conditions[0].raw_value))
                    value = _scalar_value(setters[0].raw_value)
                    owner_id = parents.get(operation.title_id)
                    status = "valid" if (
                        required
                        and value == "yes"
                        and owner_id is not None
                        and (ranks is None or ranks.get(operation.title_id) == "barony")
                    ) else "warning"
                    note = None if status == "valid" else "unsupported conditional capital barony effect"
                    effects.append((
                        owner_id or operation.title_id,
                        "set_capital_barony",
                        operation.title_id,
                        str(required) if required else None,
                        status,
                        note,
                    ))
                    handled += 1
    return effects, handled == len(fields)


def _tgp_no_dlc_invocation_date(operation: HistoryOperation) -> CK3Date | None:
    if operation.operation_key != "effect" or operation.value_kind != "block":
        return None
    fields = list(_assignments(operation.raw_script[1:-1], operation.source_line_start))
    if (
        len(fields) != 1
        or fields[0].key != "destroy_landless_title_no_tgp_dlc_effect"
        or fields[0].value_kind != "block"
    ):
        return None
    arguments = list(_assignments(fields[0].raw_value[1:-1], fields[0].line_start))
    if len(arguments) != 1 or arguments[0].key != "DATE":
        return None
    required_date = _parse_date(_scalar_value(arguments[0].raw_value))
    return required_date if required_date == operation.effective_date else None


def _succession_law_ids(operation: HistoryOperation) -> tuple[str, ...] | None:
    if operation.operation_key != "succession_laws" or operation.value_kind != "block":
        return None
    content = _strip_comments(operation.raw_script[1:-1]).strip()
    if not content:
        return ()
    law_ids = tuple(content.split())
    if len(set(law_ids)) != len(law_ids) or not all(
        LAW_ID_PATTERN.fullmatch(law_id) for law_id in law_ids
    ):
        return None
    return law_ids


def _has_valid_succession_laws(
    operation: HistoryOperation, installed_law_ids: set[str]
) -> bool:
    law_ids = _succession_law_ids(operation)
    return law_ids is not None and set(law_ids) <= installed_law_ids


def _load_required_law_definitions(
    game_root: Path,
    required_law_ids: set[str],
) -> tuple[list[LawDefinition], list[tuple[str, int, datetime, str]]]:
    source_root = game_root / "common" / "laws"
    if not source_root.is_dir():
        raise FileNotFoundError(f"Law definition folder does not exist: {source_root}")
    paths = sorted(source_root.glob("*.txt"))
    info_path = source_root / "_laws.info"
    if info_path.is_file():
        paths.append(info_path)
    definitions: list[LawDefinition] = []
    manifests: list[tuple[str, int, datetime, str]] = []
    seen: set[str] = set()
    source_order = 0
    for path in paths:
        raw_bytes = path.read_bytes()
        relative_path = path.relative_to(game_root).as_posix()
        manifests.append((
            relative_path,
            len(raw_bytes),
            datetime.fromtimestamp(path.stat().st_mtime, timezone.utc),
            sha256(raw_bytes).hexdigest(),
        ))
        text, _ = _decode_history(raw_bytes)
        for group in _assignments(_strip_comments(text)):
            if group.value_kind != "block":
                continue
            for law in _assignments(group.raw_value[1:-1], group.line_start):
                if law.key not in required_law_ids:
                    continue
                if law.value_kind != "block" or law.key in seen:
                    raise ValueError(f"Invalid or duplicate installed law ID: {law.key}")
                source_order += 1
                seen.add(law.key)
                definitions.append(LawDefinition(
                    law.key,
                    group.key,
                    relative_path,
                    law.line_start,
                    law.line_end,
                    source_order,
                    law.raw_value,
                    sha256(law.raw_value.encode("utf-8")).hexdigest(),
                ))
    missing = sorted(required_law_ids - seen)
    if missing:
        raise ValueError(f"Unresolved installed succession law IDs: {', '.join(missing)}")
    return definitions, manifests


def _verify_tgp_no_dlc_evidence(
    game_root: Path,
) -> list[tuple[str, int, datetime, str]]:
    expected = {
        TGP_EFFECT_PATH: (
            "destroy_landless_title_no_tgp_dlc_effect",
            TGP_EFFECT_DEFINITION,
        ),
        TGP_TRIGGER_PATH: ("has_tgp_dlc_trigger", TGP_TRIGGER_DEFINITION),
    }
    manifests: list[tuple[str, int, datetime, str]] = []
    for relative_path, (definition_key, expected_script) in expected.items():
        path = game_root / relative_path
        raw_bytes = path.read_bytes()
        text, _ = _decode_history(raw_bytes)
        definitions = [
            assignment
            for assignment in _assignments(_strip_comments(text))
            if assignment.key == definition_key and assignment.value_kind == "block"
        ]
        if len(definitions) != 1 or " ".join(definitions[0].raw_value.split()) != expected_script:
            raise ValueError(f"Installed TGP evidence does not match reviewed semantics: {relative_path}")
        manifests.append((
            relative_path,
            len(raw_bytes),
            datetime.fromtimestamp(path.stat().st_mtime, timezone.utc),
            sha256(raw_bytes).hexdigest(),
        ))
    return manifests


def _assignments(text: str, base_line: int = 1) -> Iterator[Assignment]:
    position = 0
    while position < len(text):
        while position < len(text) and text[position].isspace():
            position += 1
        key_start = position
        while position < len(text) and (text[position].isalnum() or text[position] in "_.-"):
            position += 1
        key = text[key_start:position]
        while position < len(text) and text[position].isspace():
            position += 1
        if not key or position >= len(text) or text[position] != "=":
            position += 1
            continue
        position += 1
        while position < len(text) and text[position].isspace():
            position += 1
        value_start = position
        if position < len(text) and text[position] == "{":
            position = _balanced_end(text, position) + 1
            value_kind = "block"
        elif position < len(text) and text[position] == '"':
            position = _quoted_end(text, position) + 1
            value_kind = "scalar"
        else:
            while position < len(text) and not text[position].isspace() and text[position] != "}":
                position += 1
            value_kind = "scalar"
        raw_value = text[value_start:position]
        line_start = base_line + text.count("\n", 0, key_start)
        line_end = base_line + text.count("\n", 0, max(value_start, position - 1))
        yield Assignment(key, raw_value, value_kind, line_start, line_end)


def _strip_comments(text: str) -> str:
    output: list[str] = []
    quoted = escaped = in_comment = False
    for character in text:
        if in_comment:
            if character == "\n":
                in_comment = False
                output.append(character)
            else:
                output.append(" ")
            continue
        if quoted:
            output.append(character)
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
        elif character == '"':
            quoted = True
            output.append(character)
        elif character == "#":
            in_comment = True
            output.append(" ")
        else:
            output.append(character)
    return "".join(output)


def _balanced_end(text: str, opening: int) -> int:
    depth = 0
    quoted = escaped = False
    for index in range(opening, len(text)):
        character = text[index]
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
        elif character == '"':
            quoted = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("Unclosed Clausewitz block")


def _quoted_end(text: str, opening: int) -> int:
    escaped = False
    for index in range(opening + 1, len(text)):
        if escaped:
            escaped = False
        elif text[index] == "\\":
            escaped = True
        elif text[index] == '"':
            return index
    raise ValueError("Unclosed quoted value")


def _parse_date(value: str) -> CK3Date | None:
    match = DATE_PATTERN.match(value)
    if match is None:
        return None
    year, month, day = (int(part) for part in match.groups())
    if month not in range(1, 13) or day not in range(1, 32):
        raise ValueError(f"Invalid CK3 date: {value}")
    return CK3Date(year, month, day)


def _scalar_value(raw_value: str) -> str:
    if raw_value.startswith('"') and raw_value.endswith('"'):
        return raw_value[1:-1].replace(r'\"', '"').replace(r"\\", "\\")
    return raw_value


def _decode_history(raw_bytes: bytes) -> tuple[str, str]:
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        return raw_bytes.decode("utf-8-sig"), "utf-8-sig"
    try:
        return raw_bytes.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return raw_bytes.decode("cp1252"), "cp1252"