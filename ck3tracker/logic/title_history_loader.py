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
PARSER_VERSION = "1.18.0"
DATE_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
TITLE_PATTERN = re.compile(r"^[ekdcb]_[A-Za-z0-9_-]+$")
NORMALIZED_OPERATIONS = {
    "holder",
    "holder_ignore_head_of_faith_requirement",
    "liege",
    "government",
    "change_development_level",
}
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
TGP_DYNASTY_PRESTIGE_EFFECT_PATH = (
    "common/scripted_effects/10_dlc_tgp_japan_scripted_effects.txt"
)
TGP_DYNASTY_PRESTIGE_EFFECT_DEFINITION = (
    "{ holder.dynasty ?= { while = { limit = { dynasty_prestige_level < 5 } "
    "add_dynasty_prestige_level = 1 } } }"
)
DIRECT_DYNASTY_PRESTIGE_LEVEL_9_EFFECT_DEFINITION = (
    "{ holder.dynasty ?= { while = { limit = { dynasty_prestige_level < 9 } "
    "add_dynasty_prestige_level = 1 } } }"
)
EP3_FEATURE_FLAG = "roads_to_power"
EP3_EFFECT_PATH = "common/scripted_effects/07_dlc_ep3_scripted_effects.txt"
EP3_EFFECT_DEFINITION = (
    "{ if = { limit = { NOT = { has_dlc_feature = roads_to_power } "
    "game_start_date = $DATE$ } holder ?= { "
    "empty_treasury_when_abandoning_landed_life_effect = yes "
    "destroy_title = prev } } }"
)
EP3_HISTORY_EFFECT_DEFINITION = (
    "{ holder ?= { if = { limit = { NOT = { has_realm_law = "
    "landless_adventurer_succession_law } } add_realm_law = "
    "landless_adventurer_succession_law } } }"
)
ROYAL_COURT_FEATURE_FLAG = "royal_court"
COURT_STATE_REPLAY_EXCLUDED_TITLE_IDS = {"k_balhae"}
COURT_LANGUAGE_PATTERN = re.compile(r"^language_[A-Za-z0-9_-]+$")
COURT_TYPE_PATTERN = re.compile(r"^court_[A-Za-z0-9_-]+$")
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
class SubjectContractGroupDefinition:
    contract_group_id: str
    source_path: str
    source_line_start: int
    source_line_end: int
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


def _reviewed_package_id(connection, reference_snapshot_id: str, feature_flag: str) -> str | None:
        row = connection.execute(
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
                [reference_snapshot_id, feature_flag],
        ).fetchone()
        return str(row[0]) if row else None


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
    dynasty_prestige_helper_manifest = None
    if any(_is_tgp_dynasty_prestige_invocation(operation) for operation in operations):
        dynasty_prestige_helper_manifest = _verify_tgp_dynasty_prestige_evidence(
            Path(game_root).resolve()
        )
        manifests.append(dynasty_prestige_helper_manifest)
    has_historical_adventurer_effects = any(
        _historical_adventurer_fields(operation) is not None for operation in operations
    )
    if (
        any(_ep3_no_dlc_invocation_date(operation) for operation in operations)
        or has_historical_adventurer_effects
    ):
        manifests.extend(_verify_ep3_no_dlc_evidence(
            Path(game_root).resolve(),
            require_history_helper=has_historical_adventurer_effects,
        ))
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
    tributary_fields = [
        fields for operation in operations
        if (fields := _tributary_fields(operation)) is not None
    ]
    required_contract_group_ids = {fields[1] for fields in tributary_fields}
    contract_group_definitions: list[SubjectContractGroupDefinition] = []
    if required_contract_group_ids:
        contract_group_definitions, contract_manifests = (
            _load_required_tributary_contract_groups(
                Path(game_root).resolve(), required_contract_group_ids
            )
        )
        manifests.extend(contract_manifests)
    installed_tributary_contract_group_ids = {
        definition.contract_group_id for definition in contract_group_definitions
    }

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
        tgp_package_id = _reviewed_package_id(
            connection, reference_snapshot_id, TGP_FEATURE_FLAG
        )
        ep3_package_id = _reviewed_package_id(
            connection, reference_snapshot_id, EP3_FEATURE_FLAG
        )
        royal_court_package_id = _reviewed_package_id(
            connection, reference_snapshot_id, ROYAL_COURT_FEATURE_FLAG
        )
        name_localizations = _resolved_name_localizations(
            connection, reference_snapshot_id, operations
        )
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
        holder_dynasties = {
            str(row[0]): str(row[1])
            for row in connection.execute(
                """
                SELECT character.character_id, character.dynasty_id
                FROM reference.character_baseline_states character
                JOIN reference.baselines baseline USING (baseline_id)
                JOIN reference.dynasties dynasty
                  ON dynasty.reference_snapshot_id = baseline.reference_snapshot_id
                 AND dynasty.dynasty_id = character.dynasty_id
                WHERE character.baseline_id = ?
                                    AND character.dynasty_id IS NOT NULL
                  AND dynasty.validation_status = 'valid'
                """,
                [baseline_id],
            ).fetchall()
        }
        effective_operations = [
            operation
            for operation in operations
            if operation.title_id not in winning_blocks
            or operation.source_block_order == winning_blocks[operation.title_id]
        ]
        historical_adventurer_orders = _validated_historical_adventurer_orders(
            effective_operations, ep3_package_id
        )
        dynasty_prestige_constraints = _materialize_dynasty_prestige_constraints(
            effective_operations,
            baseline_date,
            holder_dynasties,
            dynasty_prestige_helper_manifest,
        )
        dynasty_prestige_by_order = {
            int(row[6]): (str(row[0]), str(row[5]), int(row[1]))
            for row in dynasty_prestige_constraints
        }
        installed_language_ids = {
            str(row[0])
            for row in connection.execute(
                """
                SELECT language_id FROM reference.languages
                WHERE reference_snapshot_id = ? AND validation_status = 'valid'
                """,
                [reference_snapshot_id],
            ).fetchall()
        }
        known_language_pairs = {
            (str(row[0]), str(row[1]))
            for row in connection.execute(
                """
                SELECT character_id, language_id
                FROM reference.character_baseline_languages
                WHERE baseline_id = ?
                  AND NOT (
                    knowledge_kind = 'history_granted'
                    AND source_group = 'title_history'
                  )
                """,
                [baseline_id],
            ).fetchall()
        }
        (
            baseline_court_states,
            court_assignments_by_order,
            learned_languages,
            court_language_learning_by_order,
        ) = _materialize_court_states(
            effective_operations,
            baseline_date,
            royal_court_package_id,
            installed_language_ids,
            known_language_pairs,
        )
        events = _normalized_events(
            effective_operations,
            title_rows,
            tgp_package_id=tgp_package_id,
            installed_law_ids=installed_law_ids,
            installed_title_ids=installed_title_ids,
            installed_tributary_contract_group_ids=installed_tributary_contract_group_ids,
            ep3_package_id=ep3_package_id,
            historical_adventurer_orders=historical_adventurer_orders,
            dynasty_prestige_by_order=dynasty_prestige_by_order,
            name_localizations=name_localizations,
            court_assignments_by_order=court_assignments_by_order,
            court_language_learning_by_order=court_language_learning_by_order,
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
            installed_tributary_contract_group_ids=installed_tributary_contract_group_ids,
            ep3_package_id=ep3_package_id,
            historical_adventurer_orders=historical_adventurer_orders,
            dynasty_prestige_orders=set(dynasty_prestige_by_order),
            name_localizations=name_localizations,
            normalized_court_orders={
                order
                for order, assignment in court_assignments_by_order.items()
                if assignment[3]
            },
        )
        baseline_laws = _materialize_title_laws(
            effective_operations, baseline_date, installed_law_ids
        )
        baseline_de_jure_lieges = _materialize_de_jure_lieges(
            effective_operations, baseline_date, installed_title_ids
        )
        baseline_tributaries = _materialize_tributaries(
            effective_operations,
            baseline_date,
            installed_title_ids,
            installed_tributary_contract_group_ids,
        )
        baseline_variables = _materialize_title_variables(
            effective_operations,
            baseline_date,
            historical_adventurer_orders,
            installed_title_ids,
        )
        baseline_name_overrides = _materialize_title_name_overrides(
            effective_operations, baseline_date, name_localizations
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
            "DELETE FROM reference.subject_contract_group_definitions WHERE reference_snapshot_id = ?",
            [reference_snapshot_id],
        )
        connection.execute(
            "DELETE FROM reference.title_baseline_tributaries WHERE baseline_id = ?",
            [baseline_id],
        )
        connection.execute(
            "DELETE FROM reference.title_baseline_variables WHERE baseline_id = ?",
            [baseline_id],
        )
        connection.execute(
            "DELETE FROM reference.dynasty_baseline_prestige_constraints WHERE baseline_id = ?",
            [baseline_id],
        )
        connection.execute(
            "DELETE FROM reference.title_baseline_name_overrides WHERE baseline_id = ?",
            [baseline_id],
        )
        connection.execute(
            "DELETE FROM reference.character_baseline_court_states WHERE baseline_id = ?",
            [baseline_id],
        )
        connection.execute(
            """
            DELETE FROM reference.character_baseline_languages
            WHERE baseline_id = ? AND knowledge_kind = 'history_granted'
              AND source_group = 'title_history'
            """,
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
                    or (
                        ep3_package_id is not None
                        and _ep3_no_dlc_invocation_date(item) is not None
                    )
                    or (
                        ep3_package_id is not None
                        and _is_roads_to_power_government_fallback(item)
                    )
                    or item.declaration_order in historical_adventurer_orders
                    or item.declaration_order in dynasty_prestige_by_order
                    or _ceremonial_title_variable(item, installed_title_ids) is not None
                    or _has_valid_succession_laws(item, installed_law_ids)
                    or _has_valid_de_jure_liege(item, installed_title_ids)
                    or _has_valid_tributary(
                        item,
                        installed_title_ids,
                        installed_tributary_contract_group_ids,
                    )
                    or _title_name_change(item, name_localizations) is not None
                    or (
                        item.declaration_order in court_assignments_by_order
                        and court_assignments_by_order[item.declaration_order][3]
                    )
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
        if contract_group_definitions:
            connection.executemany(
                """
                INSERT INTO reference.subject_contract_group_definitions
                VALUES (?, ?, TRUE, ?, ?, ?, ?, ?, ?, 'valid', NULL)
                """,
                [
                    (
                        reference_snapshot_id,
                        item.contract_group_id,
                        item.source_path,
                        item.source_line_start,
                        item.source_line_end,
                        item.raw_script,
                        item.raw_sha256,
                        PARSER_VERSION,
                    )
                    for item in contract_group_definitions
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
        if baseline_tributaries:
            connection.executemany(
                """
                INSERT INTO reference.title_baseline_tributaries
                (baseline_id, title_id, suzerain_title_id, contract_group_id,
                 effective_date, source_declaration_order, validation_status,
                 validation_note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [(baseline_id, *state) for state in baseline_tributaries],
            )
        if baseline_variables:
            connection.executemany(
                """
                INSERT INTO reference.title_baseline_variables
                (baseline_id, title_id, variable_name, value_kind, text_value,
                 effective_date, source_declaration_order, validation_status,
                 validation_note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [(baseline_id, *state) for state in baseline_variables],
            )
        if dynasty_prestige_constraints:
            connection.executemany(
                """
                INSERT INTO reference.dynasty_baseline_prestige_constraints
                (baseline_id, dynasty_id, minimum_prestige_level, value_status,
                 effective_date, source_title_id, source_holder_character_id,
                 source_declaration_order, helper_source_path, helper_raw_sha256,
                 validation_status, validation_note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [(baseline_id, *state) for state in dynasty_prestige_constraints],
            )
        if baseline_name_overrides:
            connection.executemany(
                """
                INSERT INTO reference.title_baseline_name_overrides
                (baseline_id, title_id, localization_key, display_name,
                 name_status, effective_date, source_declaration_order,
                 validation_status, validation_note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [(baseline_id, *state) for state in baseline_name_overrides],
            )
        if baseline_court_states:
            connection.executemany(
                """
                INSERT INTO reference.character_baseline_court_states
                (baseline_id, character_id, court_language_id,
                 court_language_effective_date,
                 court_language_source_declaration_order, court_type_id,
                 court_type_effective_date, court_type_source_declaration_order,
                 validation_status, validation_note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [(baseline_id, *state) for state in baseline_court_states],
            )
        if learned_languages:
            connection.executemany(
                """
                INSERT INTO reference.character_baseline_languages
                (baseline_id, character_id, language_id, knowledge_kind,
                 effective_date, source_group, source_declaration_order,
                 validation_status, validation_note)
                VALUES (?, ?, ?, 'history_granted', ?, 'title_history', ?,
                        'valid', NULL)
                """,
                [(baseline_id, *row) for row in learned_languages],
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
    installed_tributary_contract_group_ids: set[str] | None = None,
    ep3_package_id: str | None = None,
    historical_adventurer_orders: set[int] | None = None,
    dynasty_prestige_by_order: dict[int, tuple[str, str, int]] | None = None,
    name_localizations: dict[str, str] | None = None,
    court_assignments_by_order: dict[int, tuple[str, str, str, bool]] | None = None,
    court_language_learning_by_order: dict[int, tuple[str, str, bool]] | None = None,
) -> list[tuple[object, ...]]:
    installed_law_ids = installed_law_ids or set()
    installed_title_ids = installed_title_ids or set()
    installed_tributary_contract_group_ids = installed_tributary_contract_group_ids or set()
    historical_adventurer_orders = historical_adventurer_orders or set()
    dynasty_prestige_by_order = dynasty_prestige_by_order or {}
    name_localizations = name_localizations or {}
    court_assignments_by_order = court_assignments_by_order or {}
    court_language_learning_by_order = court_language_learning_by_order or {}
    events: list[tuple[object, ...]] = []
    parents = {str(row[0]): row[2] for row in title_rows}
    ranks = {str(row[0]): str(row[1]) for row in title_rows}
    ordered = sorted(operations, key=lambda item: (item.effective_date, item.declaration_order))
    sequence = 0
    for operation in ordered:
        court_assignment = court_assignments_by_order.get(operation.declaration_order)
        if court_assignment is not None:
            character_id, field_name, value_id, fully_normalized = court_assignment
            sequence += 1
            events.append((
                operation.title_id, operation.effective_date, sequence,
                f"{field_name}_set", value_id, None,
                operation.declaration_order, "valid",
                f"holder={character_id}; installed {ROYAL_COURT_FEATURE_FLAG}", None,
            ))
            learning = court_language_learning_by_order.get(operation.declaration_order)
            if learning is not None:
                learning_character_id, language_id, learned = learning
                sequence += 1
                events.append((
                    operation.title_id, operation.effective_date, sequence,
                    (
                        "court_language_learned"
                        if learned
                        else "court_language_learning_noop"
                    ),
                    language_id, None, operation.declaration_order, "valid",
                    (
                        f"holder={learning_character_id}; history_granted"
                        if learned
                        else f"holder={learning_character_id}; already_known"
                    ),
                    None,
                ))
            if fully_normalized:
                continue
        dynasty_prestige = dynasty_prestige_by_order.get(operation.declaration_order)
        if dynasty_prestige is not None:
            sequence += 1
            events.append((
                operation.title_id, operation.effective_date, sequence,
                "dynasty_prestige_minimum_established", dynasty_prestige[0],
                dynasty_prestige[2],
                operation.declaration_order, "valid",
                f"holder={dynasty_prestige[1]}; lower_bound_only", None,
            ))
            continue
        ceremonial_title_id = _ceremonial_title_variable(
            operation, installed_title_ids
        )
        if ceremonial_title_id is not None:
            sequence += 1
            events.append((
                operation.title_id, operation.effective_date, sequence,
                "title_variable_set",
                f"ceremonial_title={ceremonial_title_id}", None,
                operation.declaration_order, "valid", "value_kind=title", None,
            ))
            continue
        if operation.declaration_order in historical_adventurer_orders:
            historical_fields = _historical_adventurer_fields(operation)
            sequence += 1
            events.append((
                operation.title_id, operation.effective_date, sequence,
                "landless_adventurer_history_initialized",
                "landless_adventurer_succession_law", None,
                operation.declaration_order, "valid",
                "explicit title law makes helper idempotent", None,
            ))
            sequence += 1
            events.append((
                operation.title_id, operation.effective_date, sequence,
                "title_variable_set", "adventurer_creation_reason=historical", None,
                operation.declaration_order, "valid", "value_kind=flag", None,
            ))
            if historical_fields is not None and historical_fields[2] is not None:
                sequence += 1
                events.append((
                    operation.title_id, operation.effective_date, sequence,
                    "dlc_gated_noop", EP3_FEATURE_FLAG, None,
                    operation.declaration_order, "valid",
                    f"installed {ep3_package_id} makes destruction condition false",
                    str(operation.effective_date),
                ))
            continue
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
        ep3_date = _ep3_no_dlc_invocation_date(operation)
        if ep3_package_id is not None and ep3_date is not None:
            sequence += 1
            events.append((
                operation.title_id,
                operation.effective_date,
                sequence,
                "dlc_gated_noop",
                EP3_FEATURE_FLAG,
                None,
                operation.declaration_order,
                "valid",
                f"installed {ep3_package_id} makes destruction condition false",
                str(ep3_date),
            ))
            continue
        if (
            ep3_package_id is not None
            and _is_roads_to_power_government_fallback(operation)
        ):
            sequence += 1
            events.append((
                operation.title_id,
                operation.effective_date,
                sequence,
                "dlc_gated_conditional_noop",
                EP3_FEATURE_FLAG,
                None,
                operation.declaration_order,
                "valid",
                f"installed {ep3_package_id} makes government fallback condition false",
                None,
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
                (
                    "effect-form title-scope de-jure replacement"
                    if operation.operation_key == "effect"
                    else "dated title-history declaration replaces dynamic de-jure parentage"
                ),
                None,
            ))
            continue
        tributary = _tributary_relationship(
            operation, installed_title_ids, installed_tributary_contract_group_ids
        )
        if tributary is not None:
            sequence += 1
            events.append((
                operation.title_id,
                operation.effective_date,
                sequence,
                "tributary_relationship_replaced",
                tributary[0],
                None,
                operation.declaration_order,
                "valid",
                f"contract_group={tributary[1]}",
                None,
            ))
            continue
        if operation.operation_key not in NORMALIZED_OPERATIONS:
            name_change = _title_name_change(operation, name_localizations)
            if name_change is None:
                continue
            sequence += 1
            status, localization_key, display_name = name_change
            events.append((
                operation.title_id,
                operation.effective_date,
                sequence,
                (
                    "title_name_override_reset"
                    if status == "explicit_default"
                    else "title_name_override_set"
                ),
                localization_key,
                None,
                operation.declaration_order,
                "valid",
                (
                    "default title localization restored"
                    if status == "explicit_default"
                    else f"display_name={display_name}"
                ),
                None,
            ))
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
        elif operation.operation_key == "holder_ignore_head_of_faith_requirement":
            note = (
                "explicit title clear with head-of-faith eligibility bypass"
                if text_value == "0"
                else "holder assigned with head-of-faith eligibility bypass"
            )
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
    installed_tributary_contract_group_ids: set[str] | None = None,
    ep3_package_id: str | None = None,
    historical_adventurer_orders: set[int] | None = None,
    dynasty_prestige_orders: set[int] | None = None,
    name_localizations: dict[str, str] | None = None,
    normalized_court_orders: set[int] | None = None,
) -> list[tuple[object, ...]]:
    duplicate_classifications = duplicate_classifications or {}
    conflict_fields = conflict_fields or {}
    installed_law_ids = installed_law_ids or set()
    installed_title_ids = installed_title_ids or set()
    installed_tributary_contract_group_ids = installed_tributary_contract_group_ids or set()
    historical_adventurer_orders = historical_adventurer_orders or set()
    dynasty_prestige_orders = dynasty_prestige_orders or set()
    name_localizations = name_localizations or {}
    normalized_court_orders = normalized_court_orders or set()
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
            elif (
                operation.operation_key == "holder_ignore_head_of_faith_requirement"
                and value is not None
            ):
                holder = None if value == "0" else value
                holder_status = (
                    "explicit_unheld"
                    if value == "0"
                    else "declared_ignore_head_of_faith_requirement"
                )
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
                if operation.declaration_order in normalized_court_orders:
                    continue
                if operation.declaration_order in historical_adventurer_orders:
                    continue
                if operation.declaration_order in dynasty_prestige_orders:
                    continue
                if _ceremonial_title_variable(operation, installed_title_ids) is not None:
                    continue
                if _has_valid_de_jure_liege(operation, installed_title_ids):
                    continue
                if _title_name_change(operation, name_localizations) is not None:
                    continue
                recognized, fully_normalized = _extract_capital_effects(operation, {})
                is_tgp_noop = (
                    tgp_package_id is not None
                    and _tgp_no_dlc_invocation_date(operation) is not None
                )
                is_ep3_noop = (
                    ep3_package_id is not None
                    and _ep3_no_dlc_invocation_date(operation) is not None
                )
                is_ep3_government_fallback_noop = (
                    ep3_package_id is not None
                    and _is_roads_to_power_government_fallback(operation)
                )
                if (
                    (not recognized or not fully_normalized)
                    and not is_tgp_noop
                    and not is_ep3_noop
                    and not is_ep3_government_fallback_noop
                ):
                    unknown_operations.append(operation.operation_key)
            elif _has_valid_succession_laws(operation, installed_law_ids):
                continue
            elif _has_valid_de_jure_liege(operation, installed_title_ids):
                continue
            elif _has_valid_tributary(
                operation,
                installed_title_ids,
                installed_tributary_contract_group_ids,
            ):
                continue
            elif _title_name_change(operation, name_localizations) is not None:
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
    if operation.operation_key == "effect" and operation.value_kind == "block":
        fields = list(
            _assignments(operation.raw_script[1:-1], operation.source_line_start)
        )
        if (
            len(fields) != 1
            or fields[0].key != "set_de_jure_liege_title"
            or fields[0].value_kind != "scalar"
        ):
            return _INVALID_DE_JURE_TARGET
        scoped_target = _scalar_value(fields[0].raw_value)
        if not scoped_target.startswith("title:"):
            return _INVALID_DE_JURE_TARGET
        target = scoped_target[6:]
        if target not in installed_title_ids or target == operation.title_id:
            return _INVALID_DE_JURE_TARGET
        return target
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


def _tributary_fields(operation: HistoryOperation) -> tuple[str, str] | None:
    if operation.operation_key != "tributary_of" or operation.value_kind != "block":
        return None
    fields = list(_assignments(operation.raw_script[1:-1], operation.source_line_start))
    if len(fields) != 2 or {field.key for field in fields} != {"suzerain", "contract_group"}:
        return None
    values = {field.key: _scalar_value(field.raw_value) for field in fields}
    if not TITLE_PATTERN.fullmatch(values["suzerain"]):
        return None
    if not LAW_ID_PATTERN.fullmatch(values["contract_group"]):
        return None
    return values["suzerain"], values["contract_group"]


def _tributary_relationship(
    operation: HistoryOperation,
    installed_title_ids: set[str],
    installed_contract_group_ids: set[str],
) -> tuple[str, str] | None:
    fields = _tributary_fields(operation)
    if fields is None:
        return None
    suzerain, contract_group = fields
    if (
        suzerain == operation.title_id
        or suzerain not in installed_title_ids
        or contract_group not in installed_contract_group_ids
    ):
        return None
    return fields


def _has_valid_tributary(
    operation: HistoryOperation,
    installed_title_ids: set[str],
    installed_contract_group_ids: set[str],
) -> bool:
    return _tributary_relationship(
        operation, installed_title_ids, installed_contract_group_ids
    ) is not None


def _materialize_tributaries(
    operations: list[HistoryOperation],
    baseline_date: date,
    installed_title_ids: set[str],
    installed_contract_group_ids: set[str],
) -> list[tuple[object, ...]]:
    cutoff = CK3Date(baseline_date.year, baseline_date.month, baseline_date.day)
    latest: dict[str, tuple[HistoryOperation, tuple[str, str]]] = {}
    for operation in sorted(
        operations, key=lambda item: (item.effective_date, item.declaration_order)
    ):
        if operation.effective_date > cutoff:
            continue
        relationship = _tributary_relationship(
            operation, installed_title_ids, installed_contract_group_ids
        )
        if relationship is not None:
            latest[operation.title_id] = (operation, relationship)
    return [
        (
            title_id,
            relationship[0],
            relationship[1],
            str(operation.effective_date),
            operation.declaration_order,
            "valid",
            None,
        )
        for title_id, (operation, relationship) in sorted(latest.items())
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


def _ep3_no_dlc_invocation_date(operation: HistoryOperation) -> CK3Date | None:
    if operation.operation_key != "effect" or operation.value_kind != "block":
        return None
    fields = list(_assignments(operation.raw_script[1:-1], operation.source_line_start))
    if (
        len(fields) != 1
        or fields[0].key != "destroy_landless_title_no_dlc_effect"
        or fields[0].value_kind != "block"
    ):
        return None
    arguments = list(_assignments(fields[0].raw_value[1:-1], fields[0].line_start))
    if len(arguments) != 1 or arguments[0].key != "DATE":
        return None
    required_date = _parse_date(_scalar_value(arguments[0].raw_value))
    return required_date if required_date == operation.effective_date else None


def _is_roads_to_power_government_fallback(operation: HistoryOperation) -> bool:
    if operation.operation_key != "effect" or operation.value_kind != "block":
        return False
    fields = list(_assignments(operation.raw_script[1:-1], operation.source_line_start))
    if len(fields) != 1 or fields[0].key != "if" or fields[0].value_kind != "block":
        return False
    conditional = list(_assignments(fields[0].raw_value[1:-1], fields[0].line_start))
    if [field.key for field in conditional] != ["limit", "holder"]:
        return False
    if any(field.value_kind != "block" for field in conditional):
        return False
    limits = list(_assignments(conditional[0].raw_value[1:-1], conditional[0].line_start))
    if [field.key for field in limits] != ["exists", "NOT"]:
        return False
    if (
        limits[0].value_kind != "scalar"
        or _scalar_value(limits[0].raw_value) != "holder"
        or limits[1].value_kind != "block"
    ):
        return False
    negative = list(_assignments(limits[1].raw_value[1:-1], limits[1].line_start))
    if len(negative) != 1 or negative[0].key != "has_dlc_feature":
        return False
    if negative[0].value_kind != "scalar":
        return False
    if _scalar_value(negative[0].raw_value) != EP3_FEATURE_FLAG:
        return False
    consequences = list(
        _assignments(conditional[1].raw_value[1:-1], conditional[1].line_start)
    )
    return (
        [field.key for field in consequences]
        == ["empty_treasury_when_abandoning_landed_life_effect", "change_government"]
        and all(field.value_kind == "scalar" for field in consequences)
        and _scalar_value(consequences[0].raw_value) == "yes"
        and _scalar_value(consequences[1].raw_value) == "feudal_government"
    )


def _royal_court_assignment(
    operation: HistoryOperation,
) -> tuple[str, str, bool, bool] | None:
    if (
        operation.operation_key != "effect"
        or operation.value_kind != "block"
        or operation.title_id in COURT_STATE_REPLAY_EXCLUDED_TITLE_IDS
    ):
        return None
    fields = list(_assignments(operation.raw_script[1:-1], operation.source_line_start))
    matches: list[tuple[str, str, bool, bool]] = []
    for field in fields:
        if field.key != "if" or field.value_kind != "block":
            continue
        conditional = list(_assignments(field.raw_value[1:-1], field.line_start))
        if [item.key for item in conditional] != ["limit", "holder"]:
            continue
        if any(item.value_kind != "block" for item in conditional):
            continue
        limits = list(
            _assignments(conditional[0].raw_value[1:-1], conditional[0].line_start)
        )
        if [item.key for item in limits] != ["exists", "has_dlc_feature"]:
            continue
        if any(item.value_kind != "scalar" for item in limits):
            continue
        if (
            _scalar_value(limits[0].raw_value) != "holder"
            or _scalar_value(limits[1].raw_value) != ROYAL_COURT_FEATURE_FLAG
        ):
            continue
        consequences = list(
            _assignments(conditional[1].raw_value[1:-1], conditional[1].line_start)
        )
        if not consequences or consequences[0].value_kind != "scalar":
            continue
        field_name = consequences[0].key
        value_id = _scalar_value(consequences[0].raw_value)
        if field_name == "set_court_language":
            if not COURT_LANGUAGE_PATTERN.fullmatch(value_id):
                continue
        elif field_name == "set_court_type":
            if not COURT_TYPE_PATTERN.fullmatch(value_id):
                continue
        else:
            continue
        if len(consequences) == 1:
            matches.append((
                field_name.removeprefix("set_"), value_id, len(fields) == 1, False,
            ))
        elif (
            len(consequences) == 2
            and field_name == "set_court_language"
            and _is_exact_court_language_learning(consequences[1])
        ):
            matches.append((
                field_name.removeprefix("set_"), value_id, len(fields) == 1, True,
            ))
    return matches[0] if len(matches) == 1 else None


def _is_exact_court_language_learning(field: Assignment) -> bool:
    if field.key != "if" or field.value_kind != "block":
        return False
    conditional = list(_assignments(field.raw_value[1:-1], field.line_start))
    if [item.key for item in conditional] != ["limit", "learn_court_language_of"]:
        return False
    if conditional[0].value_kind != "block" or conditional[1].value_kind != "scalar":
        return False
    limits = list(
        _assignments(conditional[0].raw_value[1:-1], conditional[0].line_start)
    )
    if len(limits) != 1 or limits[0].key != "NOT" or limits[0].value_kind != "block":
        return False
    negative = list(_assignments(limits[0].raw_value[1:-1], limits[0].line_start))
    return (
        len(negative) == 1
        and negative[0].key == "knows_court_language_of"
        and negative[0].value_kind == "scalar"
        and _scalar_value(negative[0].raw_value) == "this"
        and _scalar_value(conditional[1].raw_value) == "this"
    )


def _materialize_court_states(
    operations: list[HistoryOperation],
    baseline_date: date,
    royal_court_package_id: str | None,
    installed_language_ids: set[str],
    known_language_pairs: set[tuple[str, str]],
) -> tuple[
    list[tuple[object, ...]],
    dict[int, tuple[str, str, str, bool]],
    list[tuple[object, ...]],
    dict[int, tuple[str, str, bool]],
]:
    if royal_court_package_id is None:
        return [], {}, [], {}
    cutoff = CK3Date(baseline_date.year, baseline_date.month, baseline_date.day)
    holders: dict[str, str | None] = {}
    states: dict[str, dict[str, tuple[str, HistoryOperation]]] = {}
    assignments_by_order: dict[int, tuple[str, str, str, bool]] = {}
    learned_languages: list[tuple[object, ...]] = []
    learning_by_order: dict[int, tuple[str, str, bool]] = {}
    known_languages = set(known_language_pairs)
    for operation in sorted(
        operations, key=lambda item: (item.effective_date, item.declaration_order)
    ):
        if operation.effective_date > cutoff:
            continue
        if operation.operation_key in {
            "holder",
            "holder_ignore_head_of_faith_requirement",
        } and operation.scalar_value is not None:
            holders[operation.title_id] = (
                None if operation.scalar_value == "0" else operation.scalar_value
            )
            continue
        assignment = _royal_court_assignment(operation)
        character_id = holders.get(operation.title_id)
        if assignment is None or character_id is None:
            continue
        field_name, value_id, outer_body_exact, has_learning = assignment
        if field_name == "court_language" and value_id not in installed_language_ids:
            continue
        fully_normalized = outer_body_exact and not has_learning
        if has_learning and outer_body_exact:
            learned = (character_id, value_id) not in known_languages
            if learned:
                known_languages.add((character_id, value_id))
                learned_languages.append((
                    character_id,
                    value_id,
                    str(operation.effective_date),
                    operation.declaration_order,
                ))
            learning_by_order[operation.declaration_order] = (
                character_id, value_id, learned,
            )
            fully_normalized = True
        states.setdefault(character_id, {})[field_name] = (value_id, operation)
        assignments_by_order[operation.declaration_order] = (
            character_id, field_name, value_id, fully_normalized,
        )
    rows: list[tuple[object, ...]] = []
    for character_id, fields in sorted(states.items()):
        language = fields.get("court_language")
        court_type = fields.get("court_type")
        rows.append((
            character_id,
            language[0] if language else None,
            str(language[1].effective_date) if language else None,
            language[1].declaration_order if language else None,
            court_type[0] if court_type else None,
            str(court_type[1].effective_date) if court_type else None,
            court_type[1].declaration_order if court_type else None,
            "valid",
            None,
        ))
    return rows, assignments_by_order, learned_languages, learning_by_order


def _historical_adventurer_fields(
    operation: HistoryOperation,
) -> tuple[str, str, CK3Date | None] | None:
    if operation.operation_key != "effect" or operation.value_kind != "block":
        return None
    fields = list(_assignments(operation.raw_script[1:-1], operation.source_line_start))
    field_keys = [field.key for field in fields]
    if field_keys not in ([
        "create_landless_adventurer_title_history_effect",
        "set_variable",
    ], [
        "create_landless_adventurer_title_history_effect",
        "set_variable",
        "destroy_landless_title_no_dlc_effect",
    ]):
        return None
    if fields[0].value_kind != "scalar" or _scalar_value(fields[0].raw_value) != "yes":
        return None
    variable_fields = list(_assignments(fields[1].raw_value[1:-1], fields[1].line_start))
    if [field.key for field in variable_fields] != ["name", "value"]:
        return None
    if (
        _scalar_value(variable_fields[0].raw_value) != "adventurer_creation_reason"
        or _scalar_value(variable_fields[1].raw_value) != "flag:historical"
    ):
        return None
    if len(fields) == 2:
        return "flag", "historical", None
    date_fields = list(_assignments(fields[2].raw_value[1:-1], fields[2].line_start))
    if len(date_fields) != 1 or date_fields[0].key != "DATE":
        return None
    required_date = _parse_date(_scalar_value(date_fields[0].raw_value))
    if required_date != operation.effective_date:
        return None
    return "flag", "historical", required_date


def _ceremonial_title_variable(
    operation: HistoryOperation,
    installed_title_ids: set[str],
) -> str | None:
    if operation.operation_key != "effect" or operation.value_kind != "block":
        return None
    fields = list(_assignments(operation.raw_script[1:-1], operation.source_line_start))
    if len(fields) != 1 or fields[0].key != "set_variable":
        return None
    if fields[0].value_kind != "block":
        return None
    variable_fields = list(
        _assignments(fields[0].raw_value[1:-1], fields[0].line_start)
    )
    if [field.key for field in variable_fields] != ["name", "value"]:
        return None
    if any(field.value_kind != "scalar" for field in variable_fields):
        return None
    if _scalar_value(variable_fields[0].raw_value) != "ceremonial_title":
        return None
    raw_value = _scalar_value(variable_fields[1].raw_value)
    if not raw_value.startswith("title:"):
        return None
    target_title_id = raw_value.removeprefix("title:")
    return target_title_id if target_title_id in installed_title_ids else None


def _is_tgp_dynasty_prestige_invocation(operation: HistoryOperation) -> bool:
    if operation.operation_key != "effect" or operation.value_kind != "block":
        return False
    fields = list(_assignments(operation.raw_script[1:-1], operation.source_line_start))
    return (
        len(fields) == 1
        and fields[0].key == "tgp_set_minamoto_taira_dynasty_prestige_effect"
        and fields[0].value_kind == "scalar"
        and _scalar_value(fields[0].raw_value) == "yes"
    )


def _is_direct_dynasty_prestige_level_9_effect(
    operation: HistoryOperation,
) -> bool:
    return (
        operation.operation_key == "effect"
        and operation.value_kind == "block"
        and " ".join(operation.raw_script.split())
        == DIRECT_DYNASTY_PRESTIGE_LEVEL_9_EFFECT_DEFINITION
    )


def _materialize_dynasty_prestige_constraints(
    operations: list[HistoryOperation],
    baseline_date: date,
    holder_dynasties: dict[str, str],
    helper_manifest: tuple[str, int, datetime, str] | None,
) -> list[tuple[object, ...]]:
    cutoff = CK3Date(baseline_date.year, baseline_date.month, baseline_date.day)
    holders: dict[str, str | None] = {}
    rows: list[tuple[object, ...]] = []
    for operation in sorted(
        operations, key=lambda item: (item.effective_date, item.declaration_order)
    ):
        if operation.effective_date > cutoff:
            continue
        if operation.operation_key in {
            "holder", "holder_ignore_head_of_faith_requirement"
        } and operation.scalar_value is not None:
            holders[operation.title_id] = (
                None if operation.scalar_value == "0" else operation.scalar_value
            )
            continue
        is_helper_invocation = _is_tgp_dynasty_prestige_invocation(operation)
        is_direct_level_9 = _is_direct_dynasty_prestige_level_9_effect(operation)
        if not is_helper_invocation and not is_direct_level_9:
            continue
        if is_helper_invocation and helper_manifest is None:
            continue
        holder_id = holders.get(operation.title_id)
        dynasty_id = holder_dynasties.get(holder_id or "")
        if holder_id is None or dynasty_id is None:
            continue
        minimum_level = 5 if is_helper_invocation else 9
        evidence_path = helper_manifest[0] if is_helper_invocation else operation.source_path
        evidence_hash = helper_manifest[3] if is_helper_invocation else None
        rows.append((
            dynasty_id, minimum_level, "lower_bound_only", str(operation.effective_date),
            operation.title_id, holder_id, operation.declaration_order,
            evidence_path, evidence_hash, "valid",
            f"exact effect establishes dynasty_prestige_level >= {minimum_level}",
        ))
    return rows


def _validated_historical_adventurer_orders(
    operations: list[HistoryOperation], ep3_package_id: str | None
) -> set[int]:
    if ep3_package_id is None:
        return set()
    valid: set[int] = set()
    by_title: dict[str, list[HistoryOperation]] = {}
    for operation in operations:
        by_title.setdefault(operation.title_id, []).append(operation)
    for operation in operations:
        if _historical_adventurer_fields(operation) is None:
            continue
        prior = sorted(
            (
                item for item in by_title[operation.title_id]
                if (item.effective_date, item.declaration_order)
                <= (operation.effective_date, operation.declaration_order)
            ),
            key=lambda item: (item.effective_date, item.declaration_order),
        )
        holder = None
        laws: tuple[str, ...] = ()
        for item in prior:
            if item.operation_key == "holder" and item.scalar_value is not None:
                holder = None if item.scalar_value == "0" else item.scalar_value
            law_ids = _succession_law_ids(item)
            if law_ids is not None:
                laws = law_ids
        if holder is not None and "landless_adventurer_succession_law" in laws:
            valid.add(operation.declaration_order)
    return valid


def _materialize_title_variables(
    operations: list[HistoryOperation],
    baseline_date: date,
    historical_adventurer_orders: set[int],
    installed_title_ids: set[str],
) -> list[tuple[object, ...]]:
    cutoff = CK3Date(baseline_date.year, baseline_date.month, baseline_date.day)
    latest: dict[tuple[str, str], tuple[HistoryOperation, str, str]] = {}
    for operation in sorted(
        operations, key=lambda item: (item.effective_date, item.declaration_order)
    ):
        if operation.effective_date > cutoff:
            continue
        if operation.declaration_order in historical_adventurer_orders:
            fields = _historical_adventurer_fields(operation)
        else:
            fields = None
        if fields is not None:
            latest[(operation.title_id, "adventurer_creation_reason")] = (
                operation, fields[0], fields[1]
            )
        ceremonial_title_id = _ceremonial_title_variable(
            operation, installed_title_ids
        )
        if ceremonial_title_id is not None:
            latest[(operation.title_id, "ceremonial_title")] = (
                operation, "title", ceremonial_title_id
            )
    return [
        (
            title_id, variable_name, value_kind, text_value,
            str(operation.effective_date), operation.declaration_order,
            "valid", None,
        )
        for (title_id, variable_name), (operation, value_kind, text_value)
        in sorted(latest.items())
    ]


def _materialize_title_name_overrides(
    operations: list[HistoryOperation],
    baseline_date: date,
    name_localizations: dict[str, str],
) -> list[tuple[object, ...]]:
    cutoff = CK3Date(baseline_date.year, baseline_date.month, baseline_date.day)
    latest: dict[str, tuple[HistoryOperation, tuple[str, str | None, str | None]]] = {}
    for operation in sorted(
        operations, key=lambda item: (item.effective_date, item.declaration_order)
    ):
        if operation.effective_date > cutoff:
            continue
        change = _title_name_change(operation, name_localizations)
        if change is not None:
            latest[operation.title_id] = (operation, change)
    return [
        (
            title_id, change[1], change[2], change[0],
            str(operation.effective_date), operation.declaration_order,
            "valid", None,
        )
        for title_id, (operation, change) in sorted(latest.items())
    ]


def _title_name_change(
    operation: HistoryOperation, name_localizations: dict[str, str]
) -> tuple[str, str | None, str | None] | None:
    localization_key = None
    if (
        operation.operation_key == "name"
        and operation.value_kind == "scalar"
        and operation.scalar_value is not None
    ):
        localization_key = operation.scalar_value
    elif operation.operation_key == "effect":
        localization_key = _set_title_name_effect_key(operation)
    if localization_key is not None:
        display_name = name_localizations.get(localization_key)
        if display_name is None:
            return None
        return "declared", localization_key, display_name
    if (
        operation.operation_key == "reset_name"
        and operation.value_kind == "scalar"
        and operation.scalar_value == "yes"
    ):
        return "explicit_default", None, None
    return None


def _set_title_name_effect_key(operation: HistoryOperation) -> str | None:
    if operation.operation_key != "effect" or operation.value_kind != "block":
        return None
    fields = list(_assignments(operation.raw_script[1:-1], operation.source_line_start))
    if (
        len(fields) != 1
        or fields[0].key != "set_title_name"
        or fields[0].value_kind != "scalar"
    ):
        return None
    return _scalar_value(fields[0].raw_value)


def _resolved_name_localizations(
    connection, reference_snapshot_id: str, operations: list[HistoryOperation]
) -> dict[str, str]:
    required_keys = {
        localization_key
        for operation in operations
        if (
            localization_key := (
                operation.scalar_value
                if operation.operation_key == "name"
                and operation.value_kind == "scalar"
                else _set_title_name_effect_key(operation)
            )
        ) is not None
    }
    resolved: dict[str, str] = {}
    for localization_key in sorted(required_keys):
        current_key = localization_key
        visited: set[str] = set()
        while current_key not in visited:
            visited.add(current_key)
            row = connection.execute(
                """
                SELECT display_value
                FROM reference.localizations
                WHERE reference_snapshot_id = ?
                  AND language = 'english'
                  AND localization_key = ?
                  AND resolution_status IN ('valid', 'identical_duplicate')
                """,
                [reference_snapshot_id, current_key],
            ).fetchone()
            if row is None:
                break
            display_name = str(row[0])
            alias = re.fullmatch(r"\$([^$]+)\$", display_name)
            if alias is None:
                resolved[localization_key] = display_name
                break
            current_key = alias.group(1)
    return resolved


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


def _load_required_tributary_contract_groups(
    game_root: Path,
    required_group_ids: set[str],
) -> tuple[list[SubjectContractGroupDefinition], list[tuple[str, int, datetime, str]]]:
    source_root = game_root / "common" / "subject_contracts" / "groups"
    if not source_root.is_dir():
        raise FileNotFoundError(f"Subject contract group folder does not exist: {source_root}")
    definitions: list[SubjectContractGroupDefinition] = []
    manifests: list[tuple[str, int, datetime, str]] = []
    seen: set[str] = set()
    for path in sorted(source_root.rglob("*.txt")):
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
            if group.key not in required_group_ids:
                continue
            if group.value_kind != "block" or group.key in seen:
                raise ValueError(f"Invalid tributary contract group: {group.key}")
            fields = list(_assignments(group.raw_value[1:-1], group.line_start))
            if not any(
                field.key == "is_tributary"
                and field.value_kind == "scalar"
                and _scalar_value(field.raw_value) == "yes"
                for field in fields
            ):
                raise ValueError(f"Contract group is not tributary: {group.key}")
            seen.add(group.key)
            definitions.append(SubjectContractGroupDefinition(
                group.key,
                relative_path,
                group.line_start,
                group.line_end,
                group.raw_value,
                sha256(group.raw_value.encode("utf-8")).hexdigest(),
            ))
    missing = sorted(required_group_ids - seen)
    if missing:
        raise ValueError(f"Unresolved tributary contract groups: {', '.join(missing)}")
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


def _verify_tgp_dynasty_prestige_evidence(
    game_root: Path,
) -> tuple[str, int, datetime, str]:
    path = game_root / TGP_DYNASTY_PRESTIGE_EFFECT_PATH
    raw_bytes = path.read_bytes()
    text, _ = _decode_history(raw_bytes)
    definitions = [
        assignment
        for assignment in _assignments(_strip_comments(text))
        if assignment.key == "tgp_set_minamoto_taira_dynasty_prestige_effect"
        and assignment.value_kind == "block"
    ]
    if (
        len(definitions) != 1
        or " ".join(definitions[0].raw_value.split())
        != TGP_DYNASTY_PRESTIGE_EFFECT_DEFINITION
    ):
        raise ValueError(
            "Installed TGP dynasty-prestige helper does not match reviewed semantics: "
            f"{TGP_DYNASTY_PRESTIGE_EFFECT_PATH}"
        )
    return (
        TGP_DYNASTY_PRESTIGE_EFFECT_PATH,
        len(raw_bytes),
        datetime.fromtimestamp(path.stat().st_mtime, timezone.utc),
        sha256(raw_bytes).hexdigest(),
    )


def _verify_ep3_no_dlc_evidence(
    game_root: Path,
    *,
    require_history_helper: bool = False,
) -> list[tuple[str, int, datetime, str]]:
    path = game_root / EP3_EFFECT_PATH
    raw_bytes = path.read_bytes()
    text, _ = _decode_history(raw_bytes)
    definitions = [
        assignment
        for assignment in _assignments(_strip_comments(text))
        if assignment.key == "destroy_landless_title_no_dlc_effect"
        and assignment.value_kind == "block"
    ]
    if (
        len(definitions) != 1
        or " ".join(definitions[0].raw_value.split()) != EP3_EFFECT_DEFINITION
    ):
        raise ValueError(
            f"Installed EP3 evidence does not match reviewed semantics: {EP3_EFFECT_PATH}"
        )
    if require_history_helper:
        history_definitions = [
            assignment
            for assignment in _assignments(_strip_comments(text))
            if assignment.key == "create_landless_adventurer_title_history_effect"
            and assignment.value_kind == "block"
        ]
        if (
            len(history_definitions) != 1
            or " ".join(history_definitions[0].raw_value.split())
            != EP3_HISTORY_EFFECT_DEFINITION
        ):
            raise ValueError(
                f"Installed EP3 history helper does not match reviewed semantics: {EP3_EFFECT_PATH}"
            )
    return [(
        EP3_EFFECT_PATH,
        len(raw_bytes),
        datetime.fromtimestamp(path.stat().st_mtime, timezone.utc),
        sha256(raw_bytes).hexdigest(),
    )]


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