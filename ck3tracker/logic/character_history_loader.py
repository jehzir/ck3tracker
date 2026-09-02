"""Load installed CK3 character history and validate candidate title holders."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from hashlib import sha256
from pathlib import Path
import re
from typing import Iterable
from uuid import uuid4

import duckdb

from logic.root_database import connect
from logic.title_history_loader import (
    CK3Date,
    _assignments,
    _parse_date,
    _scalar_value,
    _strip_comments,
)


PARSER_NAME = "installed_character_history"
PARSER_VERSION = "1.8.0"
CHARACTER_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
IDENTITY_OPERATIONS = {
    "name",
    "female",
    "culture",
    "religion",
    "faith",
    "dynasty",
    "dynasty_house",
}
LIFECYCLE_OPERATIONS = {"birth", "death"}
NON_PROJECTING_CHARACTER_FLAGS = {
    "do_not_generate_starting_family",
    "has_scripted_appearance",
}
NON_PROJECTING_RELATIONSHIP_EFFECTS = {
    "add_opinion",
    "break_alliance",
    "create_betrothal",
    "make_concubine",
    "reverse_add_opinion",
    "set_father",
    "set_primary_spouse",
    "set_relation_best_friend",
    "set_relation_friend",
    "set_relation_lover",
    "set_relation_nemesis",
    "set_relation_potential_friend",
    "set_relation_potential_rival",
    "set_relation_rival",
    "set_relation_soulmate",
}


@dataclass(frozen=True)
class CharacterOperation:
    declaration_order: int
    character_id: str
    character_declaration_order: int
    effective_date: CK3Date | None
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
class CharacterHistoryBlock:
    source_block_order: int
    character_id: str
    source_path: str
    source_line_start: int
    source_line_end: int
    raw_script: str
    raw_sha256: str
    semantic_sha256: str
    duplicate_classification: str = "unique"
    baseline_conflict_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class CharacterHistoryParseResult:
    operations: tuple[CharacterOperation, ...]
    blocks: tuple[CharacterHistoryBlock, ...]
    duplicate_character_ids: frozenset[str]
    manifests: tuple[tuple[str, int, datetime, str], ...]
    character_count: int


@dataclass(frozen=True)
class CharacterHistoryLoadResult:
    reference_snapshot_id: str
    baseline_id: str
    character_count: int
    declaration_count: int
    event_count: int
    state_count: int
    holder_validation_count: int
    holder_warning_count: int
    parser_run_id: str


def parse_character_history(game_root: str | Path) -> CharacterHistoryParseResult:
    """Parse all static and dated installed character-history operations."""
    root = Path(game_root).resolve()
    source_root = root / "history" / "characters"
    if not source_root.is_dir():
        raise FileNotFoundError(f"Character-history folder does not exist: {source_root}")

    operations: list[CharacterOperation] = []
    blocks: list[CharacterHistoryBlock] = []
    manifests: list[tuple[str, int, datetime, str]] = []
    character_occurrences: dict[str, int] = {}
    global_order = 0
    character_declaration_order = 0
    for path in sorted(source_root.rglob("*.txt")):
        relative_path = path.relative_to(root).as_posix()
        raw_bytes = path.read_bytes()
        text = raw_bytes.decode("utf-8-sig")
        manifests.append(
            (
                relative_path,
                len(raw_bytes),
                datetime.fromtimestamp(path.stat().st_mtime, timezone.utc),
                sha256(raw_bytes).hexdigest(),
            )
        )
        clean_text = _strip_comments(text)
        for character in _assignments(clean_text):
            if not CHARACTER_PATTERN.match(character.key) or character.value_kind != "block":
                continue
            character_declaration_order += 1
            character_occurrences[character.key] = character_occurrences.get(character.key, 0) + 1
            static_order = 0
            block_operations: list[CharacterOperation] = []
            for assignment in _assignments(character.raw_value[1:-1], character.line_start):
                effective_date = _parse_date(assignment.key)
                if effective_date is not None and assignment.value_kind == "block":
                    dated_order = 0
                    for dated_assignment in _assignments(
                        assignment.raw_value[1:-1], assignment.line_start
                    ):
                        dated_order += 1
                        global_order += 1
                        operations.append(
                            _operation(
                                global_order,
                                character.key,
                                character_declaration_order,
                                effective_date,
                                dated_order,
                                dated_assignment,
                                relative_path,
                            )
                        )
                        block_operations.append(operations[-1])
                    continue
                static_order += 1
                global_order += 1
                operations.append(
                    _operation(
                        global_order,
                        character.key,
                        character_declaration_order,
                        None,
                        static_order,
                        assignment,
                        relative_path,
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
                CharacterHistoryBlock(
                    character_declaration_order,
                    character.key,
                    relative_path,
                    character.line_start,
                    character.line_end,
                    character.raw_value,
                    sha256(character.raw_value.encode("utf-8")).hexdigest(),
                    sha256(semantic_text.encode("utf-8")).hexdigest(),
                )
            )

    duplicates = frozenset(
        character_id
        for character_id, count in character_occurrences.items()
        if count > 1
    )
    return CharacterHistoryParseResult(
        tuple(operations), tuple(blocks), duplicates, tuple(manifests), len(character_occurrences)
    )


def load_character_history_candidate(
    *,
    game_root: str | Path,
    reference_snapshot_id: str,
    baseline_id: str,
    database_path: str | Path | None = None,
) -> CharacterHistoryLoadResult:
    """Replace character evidence and holder validation for one candidate baseline."""
    started_at = datetime.now(timezone.utc)
    parser_run_id = f"{reference_snapshot_id}:{PARSER_NAME}:{uuid4()}"
    parsed = parse_character_history(game_root)
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
            raise ValueError("Promoted character history cannot be replaced")

        (
            classified_blocks,
            duplicate_classifications,
            conflict_fields,
            reviewed_winner_blocks,
            reviewed_character_ids,
        ) = (
            _classify_character_blocks(parsed.blocks, parsed.operations, baseline[0])
        )
        baseline_conflicting_ids = frozenset(
            character_id
            for character_id, classification in duplicate_classifications.items()
            if classification == "conflicting_at_baseline"
        )
        states, events = _materialize_character_states(
            parsed.operations,
            duplicate_classifications,
            conflict_fields,
            baseline[0],
            reviewed_winner_blocks,
            reviewed_character_ids,
        )
        block_classifications = {
            block.source_block_order: block.duplicate_classification
            for block in classified_blocks
        }
        native_languages = _materialize_native_languages(
            connection, reference_snapshot_id, states
        )
        history_languages = _materialize_history_languages(
            connection,
            reference_snapshot_id,
            baseline_id,
            events,
            native_languages,
            baseline[0],
        )
        state_by_id = {state[0]: state for state in states}
        holders = connection.execute(
            """
            SELECT title_id, holder_character_id
            FROM reference.title_baseline_states
            WHERE baseline_id = ? AND holder_character_id IS NOT NULL
            ORDER BY title_id
            """,
            [baseline_id],
        ).fetchall()
        adjudications = {
            str(row[0]): (str(row[1]), str(row[2]), str(row[3]))
            for row in connection.execute(
                """
                SELECT title_id, declared_holder_character_id,
                       adjudicated_holder_character_id, review_note
                FROM reference.title_holder_adjudications
                WHERE baseline_id = ? AND review_status = 'reviewed'
                """,
                [baseline_id],
            ).fetchall()
        }
        validations = _holder_validations(
            holders, state_by_id, baseline_conflicting_ids, adjudications
        )
        holder_warning_count = sum(row[-2] == "warning" for row in validations)
        warning_count = len(baseline_conflicting_ids) + sum(
            row[-2] == "warning" for row in states
        ) + sum(row[-2] == "warning" for row in events) + holder_warning_count

        connection.execute("BEGIN TRANSACTION")
        connection.execute(
            """
            DELETE FROM reference.character_baseline_languages
                        WHERE baseline_id = ?
                            AND (
                                knowledge_kind = 'native'
                                OR source_group = 'character_history'
                            )
            """,
            [baseline_id],
        )
        for table, column in (
            ("source.character_history_declarations", "reference_snapshot_id"),
            ("source.character_history_blocks", "reference_snapshot_id"),
            ("reference.character_history_events", "reference_snapshot_id"),
            ("reference.character_baseline_states", "baseline_id"),
            ("reference.title_holder_validations", "baseline_id"),
        ):
            value = reference_snapshot_id if column == "reference_snapshot_id" else baseline_id
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
        _bulk_insert(
            connection,
            """
            INSERT INTO source.character_history_blocks
            SELECT unnest[1]::VARCHAR, unnest[2]::BIGINT, unnest[3]::VARCHAR,
                   unnest[4]::VARCHAR, unnest[5]::INTEGER, unnest[6]::INTEGER,
                   unnest[7]::VARCHAR, unnest[8]::VARCHAR, unnest[9]::VARCHAR,
                   unnest[10]::VARCHAR, unnest[11]::VARCHAR
            FROM unnest(?)
            """,
            (
                (
                    reference_snapshot_id,
                    item.source_block_order,
                    item.character_id,
                    item.source_path,
                    item.source_line_start,
                    item.source_line_end,
                    item.raw_script,
                    item.raw_sha256,
                    item.semantic_sha256,
                    item.duplicate_classification,
                    ",".join(item.baseline_conflict_fields) or None,
                )
                for item in classified_blocks
            ),
        )
        _bulk_insert(
            connection,
            """
            INSERT INTO source.character_history_declarations
            SELECT unnest[1]::VARCHAR, unnest[2]::BIGINT, unnest[3]::VARCHAR,
                   unnest[4]::VARCHAR, unnest[5]::INTEGER, unnest[6]::VARCHAR,
                   unnest[7]::VARCHAR, unnest[8]::VARCHAR, unnest[9]::VARCHAR,
                   unnest[10]::VARCHAR, unnest[11]::INTEGER, unnest[12]::INTEGER,
                   unnest[13]::VARCHAR, unnest[14]::VARCHAR, unnest[15]::VARCHAR,
                   unnest[16]::BIGINT
            FROM unnest(?)
            """,
            (
                (
                    reference_snapshot_id,
                    item.declaration_order,
                    item.character_id,
                    str(item.effective_date) if item.effective_date else None,
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
                    "reviewed_winner"
                    if block_classifications.get(item.character_declaration_order)
                    == "reviewed_winner"
                    else "reviewed_corrected"
                    if block_classifications.get(item.character_declaration_order)
                    == "reviewed_corrected"
                    else "reviewed_superseded"
                    if block_classifications.get(item.character_declaration_order)
                    == "reviewed_superseded"
                    else "review_required"
                    if duplicate_classifications.get(item.character_id)
                    == "conflicting_at_baseline"
                    else "normalized"
                    if item.operation_key in IDENTITY_OPERATIONS | LIFECYCLE_OPERATIONS
                    or _extract_character_effects(item)[1]
                    else "preserved",
                    item.character_declaration_order,
                )
                for item in parsed.operations
            ),
        )
        _bulk_insert(
            connection,
            """
            INSERT INTO reference.character_history_events
            SELECT unnest[1]::VARCHAR, unnest[2]::VARCHAR, unnest[3]::VARCHAR,
                   unnest[4]::BIGINT, unnest[5]::VARCHAR, unnest[6]::VARCHAR,
                   unnest[7]::BIGINT, unnest[8]::VARCHAR, unnest[9]::VARCHAR
            FROM unnest(?)
            """,
            ((reference_snapshot_id, *event) for event in events),
        )
        _bulk_insert(
            connection,
            """
            INSERT INTO reference.character_baseline_states
            SELECT unnest[1]::VARCHAR, unnest[2]::VARCHAR, unnest[3]::VARCHAR,
                   unnest[4]::VARCHAR, unnest[5]::VARCHAR, unnest[6]::VARCHAR,
                   unnest[7]::VARCHAR, unnest[8]::VARCHAR, unnest[9]::VARCHAR,
                   unnest[10]::VARCHAR, unnest[11]::VARCHAR, unnest[12]::VARCHAR,
                   unnest[13]::VARCHAR, unnest[14]::VARCHAR, unnest[15]::VARCHAR
            FROM unnest(?)
            """,
            ((baseline_id, *state) for state in states),
        )
        connection.executemany(
            """
            INSERT INTO reference.character_baseline_languages
            (baseline_id, character_id, language_id, knowledge_kind,
             effective_date, source_group, source_declaration_order,
             validation_status, validation_note)
            VALUES (?, ?, ?, 'native', NULL, 'culture', ?, 'valid', NULL)
            """,
            [(baseline_id, *row) for row in native_languages],
        )
        if history_languages:
            connection.executemany(
                """
                INSERT INTO reference.character_baseline_languages
                (baseline_id, character_id, language_id, knowledge_kind,
                 effective_date, source_group, source_declaration_order,
                 validation_status, validation_note)
                VALUES (?, ?, ?, 'history_granted', ?, 'character_history', ?,
                        'valid', NULL)
                """,
                [(baseline_id, *row) for row in history_languages],
            )
        connection.executemany(
            """
            INSERT INTO reference.title_holder_validations
            (baseline_id, title_id, holder_character_id, declaration_status,
             uniqueness_status, lifecycle_status, validation_status, validation_note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [(baseline_id, *validation) for validation in validations],
        )
        connection.execute(
            """
            INSERT INTO source.parser_runs
            (parser_run_id, reference_snapshot_id, parser_name, parser_version,
             status, started_at_utc, completed_at_utc, row_count, warning_count)
            VALUES (?, ?, ?, ?, 'completed', ?, ?, ?, ?)
            """,
            [parser_run_id, reference_snapshot_id, PARSER_NAME, PARSER_VERSION,
             started_at, datetime.now(timezone.utc), len(parsed.operations), warning_count],
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

    return CharacterHistoryLoadResult(
        reference_snapshot_id,
        baseline_id,
        parsed.character_count,
        len(parsed.operations),
        len(events),
        len(states),
        len(validations),
        holder_warning_count,
        parser_run_id,
    )


def _operation(
    declaration_order: int,
    character_id: str,
    character_declaration_order: int,
    effective_date: CK3Date | None,
    operation_order: int,
    assignment,
    source_path: str,
) -> CharacterOperation:
    return CharacterOperation(
        declaration_order,
        character_id,
        character_declaration_order,
        effective_date,
        operation_order,
        assignment.key,
        assignment.value_kind,
        _scalar_value(assignment.raw_value) if assignment.value_kind == "scalar" else None,
        assignment.raw_value,
        source_path,
        assignment.line_start,
        assignment.line_end,
        "utf-8-sig",
    )


def _materialize_character_states(
    operations: tuple[CharacterOperation, ...],
    duplicate_classifications: dict[str, str],
    conflict_fields: dict[str, set[str]],
    baseline_date: date,
    reviewed_winner_blocks: dict[str, int] | None = None,
    reviewed_character_ids: dict[int, str] | None = None,
) -> tuple[list[tuple[object, ...]], list[tuple[object, ...]]]:
    cutoff = CK3Date(baseline_date.year, baseline_date.month, baseline_date.day)
    reviewed_winner_blocks = reviewed_winner_blocks or {}
    reviewed_character_ids = reviewed_character_ids or {}
    by_character: dict[str, list[CharacterOperation]] = {}
    for operation in operations:
        winner_block = reviewed_winner_blocks.get(operation.character_id)
        if (
            winner_block is not None
            and operation.character_declaration_order != winner_block
            and operation.character_declaration_order not in reviewed_character_ids
        ):
            continue
        character_id = reviewed_character_ids.get(
            operation.character_declaration_order, operation.character_id
        )
        by_character.setdefault(character_id, []).append(operation)

    states: list[tuple[object, ...]] = []
    events: list[tuple[object, ...]] = []
    event_sequence = 0
    for character_id in sorted(by_character):
        name = culture = faith = faith_source = dynasty = house = None
        sex = "male"
        sex_status = "inferred_default"
        birth_date = death_date = None
        unresolved: set[str] = set()
        ordered = sorted(
            by_character[character_id],
            key=lambda item: (
                item.effective_date is not None,
                item.effective_date or CK3Date(0, 1, 1),
                item.declaration_order,
            ),
        )
        for operation in ordered:
            if operation.effective_date is not None and operation.operation_key in LIFECYCLE_OPERATIONS:
                event_sequence += 1
                embedded = operation.scalar_value
                event_status = "valid"
                event_note = None
                if embedded not in {None, "yes"}:
                    embedded_date = _parse_date(embedded)
                    if embedded_date is not None and embedded_date != operation.effective_date:
                        event_status = "warning"
                        event_note = "embedded lifecycle date differs from enclosing date"
                events.append((
                    character_id,
                    str(operation.effective_date),
                    event_sequence,
                    operation.operation_key,
                    embedded,
                    operation.declaration_order,
                    event_status,
                    event_note,
                ))
                if operation.operation_key == "birth":
                    birth_date = operation.effective_date
                else:
                    death_date = operation.effective_date
                continue
            if operation.effective_date is not None and operation.operation_key == "effect":
                effect_events, fully_normalized = _extract_character_effects(operation)
                for event_type, text_value, event_status, event_note in effect_events:
                    event_sequence += 1
                    events.append((
                        character_id,
                        str(operation.effective_date),
                        event_sequence,
                        event_type,
                        text_value,
                        operation.declaration_order,
                        event_status,
                        event_note,
                    ))
                    if (
                        operation.effective_date <= cutoff
                        and event_type == "set_culture"
                        and event_status == "valid"
                    ):
                        culture = text_value
                if operation.effective_date <= cutoff and not fully_normalized:
                    unresolved.add("effect")
                continue
            if operation.effective_date is not None and operation.effective_date > cutoff:
                continue
            value = operation.scalar_value
            if operation.operation_key == "name" and value is not None:
                name = value
            elif operation.operation_key == "female" and value is not None:
                sex = "female" if value == "yes" else "male"
                sex_status = "declared"
            elif operation.operation_key == "culture" and value is not None:
                culture = value
            elif operation.operation_key in {"religion", "faith"} and value is not None:
                faith = value
                faith_source = operation.operation_key
            elif operation.operation_key == "dynasty" and value is not None:
                dynasty = value
            elif operation.operation_key == "dynasty_house" and value is not None:
                house = value

        if birth_date is None:
            lifecycle = "unknown_birth"
        elif birth_date > cutoff:
            lifecycle = "not_born_at_baseline"
        elif death_date is not None and death_date <= cutoff:
            lifecycle = "dead_at_baseline"
        else:
            lifecycle = "alive_at_baseline"
        validation_status = "valid"
        notes: list[str] = []
        ambiguous = conflict_fields.get(character_id, set())
        if "display_name" in ambiguous:
            name = None
        if "sex" in ambiguous:
            sex = "unknown"
            sex_status = "ambiguous_duplicate"
        if "culture_id" in ambiguous:
            culture = None
        if "faith_id" in ambiguous:
            faith = None
            faith_source = None
        if "dynasty_id" in ambiguous:
            dynasty = None
        if "dynasty_house_id" in ambiguous:
            house = None
        if "birth_date" in ambiguous:
            birth_date = None
        if "death_date" in ambiguous:
            death_date = None
        if duplicate_classifications.get(character_id) == "conflicting_at_baseline":
            validation_status = "warning"
            notes.append(
                "baseline-conflicting duplicate character declarations: "
                + ", ".join(sorted(ambiguous))
            )
        if unresolved:
            validation_status = "warning"
            notes.append("not evaluated: " + ", ".join(sorted(unresolved)))
        states.append((
            character_id,
            name,
            sex,
            sex_status,
            culture,
            faith,
            faith_source,
            dynasty,
            house,
            str(birth_date) if birth_date else None,
            str(death_date) if death_date else None,
            lifecycle,
            validation_status,
            "; ".join(notes) if notes else None,
        ))
    return states, events


def _materialize_native_languages(
    connection: duckdb.DuckDBPyConnection,
    reference_snapshot_id: str,
    states: list[tuple[object, ...]],
) -> list[tuple[str, str, int]]:
    mappings = {
        str(row[0]): (str(row[1]), int(row[2]))
        for row in connection.execute(
            """
            SELECT native.culture_id, native.language_id,
                   native.source_declaration_order
            FROM reference.culture_native_languages native
            JOIN reference.languages language
              USING (reference_snapshot_id, language_id)
            WHERE native.reference_snapshot_id = ?
              AND native.validation_status = 'valid'
              AND language.validation_status = 'valid'
            """,
            [reference_snapshot_id],
        ).fetchall()
    }
    unresolved_cultures = sorted({
        str(state[4])
        for state in states
        if state[4] is not None and str(state[4]) not in mappings
    })
    if unresolved_cultures:
        raise ValueError(
            "Baseline cultures lack valid native-language mappings: "
            + ", ".join(unresolved_cultures)
        )
    return [
        (str(state[0]), mappings[str(state[4])][0], mappings[str(state[4])][1])
        for state in states
        if state[4] is not None
    ]


def _materialize_history_languages(
    connection: duckdb.DuckDBPyConnection,
    reference_snapshot_id: str,
    baseline_id: str,
    events: list[tuple[object, ...]],
    native_languages: list[tuple[str, str, int]],
    baseline_date: date,
) -> list[tuple[str, str, str, int]]:
    mappings = {
        str(row[0]): str(row[1])
        for row in connection.execute(
            """
            SELECT native.culture_id, native.language_id
            FROM reference.culture_native_languages native
            JOIN reference.languages language
              USING (reference_snapshot_id, language_id)
            WHERE native.reference_snapshot_id = ?
              AND native.validation_status = 'valid'
              AND language.validation_status = 'valid'
            """,
            [reference_snapshot_id],
        ).fetchall()
    }
    cutoff = CK3Date(baseline_date.year, baseline_date.month, baseline_date.day)
    language_events = [
        event
        for event in events
        if event[3] == "learn_language_of_culture"
        and CK3Date(*map(int, str(event[1]).split("-"))) <= cutoff
    ]
    unresolved = sorted({str(event[4]) for event in language_events if str(event[4]) not in mappings})
    if unresolved:
        raise ValueError(
            "Language effects reference unresolved cultures: " + ", ".join(unresolved)
        )
    known_pairs = {
        (str(row[0]), str(row[1]))
        for row in connection.execute(
            """
            SELECT character_id, language_id
            FROM reference.character_baseline_languages
            WHERE baseline_id = ? AND source_group = 'title_history'
            """,
            [baseline_id],
        ).fetchall()
    }
    known_pairs.update((character_id, language_id) for character_id, language_id, _ in native_languages)
    learned: list[tuple[str, str, str, int]] = []
    for event in language_events:
        character_id = str(event[0])
        language_id = mappings[str(event[4])]
        pair = (character_id, language_id)
        if pair in known_pairs:
            continue
        known_pairs.add(pair)
        learned.append((character_id, language_id, str(event[1]), int(event[5])))
    return learned


def _extract_character_effects(
    operation: CharacterOperation,
) -> tuple[list[tuple[str, str | None, str, str | None]], bool]:
    if operation.operation_key != "effect" or operation.value_kind != "block":
        return [], False

    fields = list(_assignments(operation.raw_script[1:-1], operation.source_line_start))
    if fields and all(
        field.key == "learn_language_of_culture"
        and field.value_kind == "scalar"
        for field in fields
    ):
        effects: list[tuple[str, str | None, str, str | None]] = []
        for field in fields:
            target = _scalar_value(field.raw_value)
            if not target.startswith("culture:"):
                return [], False
            culture_id = target[8:]
            if not CHARACTER_PATTERN.fullmatch(culture_id):
                return [], False
            effects.append(
                ("learn_language_of_culture", culture_id, "valid", None)
            )
        return effects, True

    effects: list[tuple[str, str | None, str, str | None]] = []
    handled = 0
    for field in fields:
        if field.key == "set_culture" and field.value_kind == "scalar":
            target = _scalar_value(field.raw_value)
            if target.startswith("culture:"):
                target = target[8:]
            status = "valid" if CHARACTER_PATTERN.fullmatch(target) else "warning"
            note = None if status == "valid" else "culture effect target is not a stable culture ID"
            effects.append((field.key, target or None, status, note))
            handled += 1
        elif field.key == "add_character_flag" and field.value_kind == "scalar":
            if _scalar_value(field.raw_value) in NON_PROJECTING_CHARACTER_FLAGS:
                handled += 1
        elif field.key in NON_PROJECTING_RELATIONSHIP_EFFECTS:
            handled += 1
    return effects, handled > 0 and handled == len(fields)


def _classify_character_blocks(
    blocks: tuple[CharacterHistoryBlock, ...],
    operations: tuple[CharacterOperation, ...],
    baseline_date: date,
) -> tuple[
    list[CharacterHistoryBlock],
    dict[str, str],
    dict[str, set[str]],
    dict[str, int],
    dict[int, str],
]:
    cutoff = CK3Date(baseline_date.year, baseline_date.month, baseline_date.day)
    blocks_by_character: dict[str, list[CharacterHistoryBlock]] = {}
    operations_by_block: dict[int, list[CharacterOperation]] = {}
    for block in blocks:
        blocks_by_character.setdefault(block.character_id, []).append(block)
    for operation in operations:
        operations_by_block.setdefault(operation.character_declaration_order, []).append(operation)

    classifications: dict[str, str] = {}
    conflicts_by_character: dict[str, set[str]] = {}
    reviewed_winner_blocks: dict[str, int] = {}
    reviewed_character_ids: dict[int, str] = {}
    classified: list[CharacterHistoryBlock] = []
    for character_id, character_blocks in blocks_by_character.items():
        if len(character_blocks) == 1:
            classified.extend(character_blocks)
            continue
        if len({block.semantic_sha256 for block in character_blocks}) == 1:
            classification = "semantic_identical"
            conflicts: set[str] = set()
        else:
            states = [
                _character_block_state(
                    operations_by_block.get(block.source_block_order, []), cutoff
                )
                for block in character_blocks
            ]
            conflicts = {
                field
                for field in states[0]
                if len({state[field] for state in states if state[field] is not None}) > 1
            }
            if conflicts:
                classification = "conflicting_at_baseline"
            else:
                classification = "additive_nonconflicting"
        reviewed_winner = _reviewed_lope_winner(
            character_id, character_blocks, operations_by_block
        )
        if reviewed_winner is not None:
            classification = "reviewed"
            conflicts = set()
            reviewed_winner_blocks[character_id] = reviewed_winner
        reviewed_bobo = _reviewed_bobo_correction(
            character_id,
            character_blocks,
            operations_by_block,
            set(blocks_by_character),
        )
        reviewed_corrected = None
        if reviewed_bobo is not None:
            reviewed_winner, reviewed_corrected = reviewed_bobo
            classification = "reviewed"
            conflicts = set()
            reviewed_winner_blocks[character_id] = reviewed_winner
            reviewed_character_ids[reviewed_corrected] = "bobo0060"
        classifications[character_id] = classification
        conflicts_by_character[character_id] = conflicts
        classified.extend(
            CharacterHistoryBlock(
                block.source_block_order,
                block.character_id,
                block.source_path,
                block.source_line_start,
                block.source_line_end,
                block.raw_script,
                block.raw_sha256,
                block.semantic_sha256,
                "reviewed_winner"
                if block.source_block_order == reviewed_winner
                else "reviewed_corrected"
                if block.source_block_order == reviewed_corrected
                else "reviewed_superseded"
                if reviewed_winner is not None
                else classification,
                tuple(sorted(conflicts)),
            )
            for block in character_blocks
        )
    return (
        sorted(classified, key=lambda item: item.source_block_order),
        classifications,
        conflicts_by_character,
        reviewed_winner_blocks,
        reviewed_character_ids,
    )


def _reviewed_lope_winner(
    character_id: str,
    blocks: list[CharacterHistoryBlock],
    operations_by_block: dict[int, list[CharacterOperation]],
) -> int | None:
    if character_id != "71419" or len(blocks) != 2:
        return None
    expected = {
        "history/characters/basque.txt": "basque",
        "history/characters/castilian.txt": "castilian",
    }
    block_by_path = {block.source_path: block for block in blocks}
    if set(block_by_path) != set(expected):
        return None
    for source_path, culture_id in expected.items():
        operations = operations_by_block.get(
            block_by_path[source_path].source_block_order, []
        )
        signature = [
            (
                operation.operation_key,
                str(operation.effective_date) if operation.effective_date else None,
                operation.scalar_value,
            )
            for operation in operations
        ]
        if signature != [
            ("name", None, "Lope"),
            ("dynasty", None, "681"),
            ("religion", None, "catholic"),
            ("culture", None, culture_id),
            ("father", None, "71410"),
            ("mother", None, "71411"),
            ("birth", "1208-01-01", "1208.1.1"),
            ("death", "1235-01-01", "1235.1.1"),
        ]:
            return None
    return block_by_path["history/characters/castilian.txt"].source_block_order


def _reviewed_bobo_correction(
    character_id: str,
    blocks: list[CharacterHistoryBlock],
    operations_by_block: dict[int, list[CharacterOperation]],
    all_character_ids: set[str],
) -> tuple[int, int] | None:
    if (
        character_id != "bobo0050"
        or len(blocks) != 2
        or "bobo0060" in all_character_ids
    ):
        return None
    ordered_blocks = sorted(blocks, key=lambda item: item.source_block_order)
    if any(
        block.source_path != "history/characters/bobo.txt"
        for block in ordered_blocks
    ):
        return None
    expected_signatures = [
        [
            ("name", None, "Yama"),
            ("dynasty", None, "bobodyn005"),
            ("religion", None, "west_african_pagan"),
            ("culture", None, "bobo"),
            ("father", None, "bobo0049"),
            ("birth", "1186-01-01", "yes"),
            ("death", "1244-01-01", "yes"),
        ],
        [
            ("name", None, "Labidiedo"),
            ("dynasty", None, "bobodyn006"),
            ("religion", None, "ashari"),
            ("culture", None, "bobo"),
            ("father", None, "bobo0059"),
            ("birth", "1193-01-01", "yes"),
            ("death", "1254-01-01", "yes"),
        ],
    ]
    for block, expected_signature in zip(ordered_blocks, expected_signatures):
        signature = [
            (
                operation.operation_key,
                str(operation.effective_date) if operation.effective_date else None,
                operation.scalar_value,
            )
            for operation in operations_by_block.get(block.source_block_order, [])
        ]
        if signature != expected_signature:
            return None
    return (
        ordered_blocks[0].source_block_order,
        ordered_blocks[1].source_block_order,
    )


def _character_block_state(
    operations: list[CharacterOperation],
    cutoff: CK3Date,
) -> dict[str, str | None]:
    state = {
        "display_name": None,
        "sex": "male",
        "culture_id": None,
        "faith_id": None,
        "dynasty_id": None,
        "dynasty_house_id": None,
        "birth_date": None,
        "death_date": None,
    }
    ordered = sorted(
        operations,
        key=lambda item: (
            item.effective_date is not None,
            item.effective_date or CK3Date(0, 1, 1),
            item.declaration_order,
        ),
    )
    for operation in ordered:
        if operation.operation_key in LIFECYCLE_OPERATIONS and operation.effective_date:
            state[f"{operation.operation_key}_date"] = str(operation.effective_date)
            continue
        if operation.effective_date is not None and operation.effective_date > cutoff:
            continue
        value = operation.scalar_value
        field = {
            "name": "display_name",
            "female": "sex",
            "culture": "culture_id",
            "religion": "faith_id",
            "faith": "faith_id",
            "dynasty": "dynasty_id",
            "dynasty_house": "dynasty_house_id",
        }.get(operation.operation_key)
        if field and value is not None:
            state[field] = "female" if field == "sex" and value == "yes" else "male" if field == "sex" else value
    return state


def _holder_validations(
    holders: list[tuple[str, str]],
    states: dict[str, tuple[object, ...]],
    duplicate_character_ids: frozenset[str],
    adjudications: dict[str, tuple[str, str, str]] | None = None,
) -> list[tuple[object, ...]]:
    adjudications = adjudications or {}
    rows: list[tuple[object, ...]] = []
    for title_id, declared_character_id in holders:
        adjudication = adjudications.get(title_id)
        is_current_adjudication = (
            adjudication is not None and adjudication[0] == declared_character_id
        )
        character_id = adjudication[1] if is_current_adjudication else declared_character_id
        state = states.get(character_id)
        declaration_status = (
            "runtime_adjudicated"
            if is_current_adjudication
            else "found"
            if state
            else "missing"
        )
        uniqueness = "duplicate" if character_id in duplicate_character_ids else "unique"
        lifecycle = str(state[11]) if state else "unknown"
        valid = declaration_status == "found" and uniqueness == "unique" and lifecycle == "alive_at_baseline"
        if is_current_adjudication:
            valid = uniqueness == "unique" and lifecycle == "alive_at_baseline"
        notes: list[str] = []
        if is_current_adjudication:
            notes.append(
                f"{adjudication[2]}; installed declaration retained as {declared_character_id}"
            )
        elif adjudication is not None:
            notes.append("runtime adjudication does not match the current installed declaration")
        if declaration_status == "missing":
            notes.append("holder has no character declaration")
        if uniqueness == "duplicate":
            notes.append("holder character has duplicate declarations")
        if lifecycle != "alive_at_baseline":
            notes.append(f"holder lifecycle is {lifecycle}")
        rows.append((
            title_id,
            character_id,
            declaration_status,
            uniqueness,
            lifecycle,
            "valid" if valid else "warning",
            "; ".join(notes) if notes else None,
        ))
    return rows


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