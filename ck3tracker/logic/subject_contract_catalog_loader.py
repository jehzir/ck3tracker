"""Load installed CK3 subject-contract types and obligation levels."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import re
from uuid import uuid4

from logic.root_database import connect
from logic.title_history_loader import _assignments, _scalar_value, _strip_comments


PARSER_NAME = "installed_subject_contracts"
PARSER_VERSION = "1.0.0"
REVIEWED_GAME_VERSION = "1.19.0.6"
REVIEWED_STEAM_BUILD_ID = "23530548"
EXPECTED_FILE_COUNT = 15
EXPECTED_TYPE_COUNT = 64
EXPECTED_OBLIGATION_COUNT = 194
TOP_LEVEL_SCALARS = {
    "ai_standard_liege_desire",
    "ai_standard_vassal_desire",
}
TEXT_SUFFIXES = {".asset", ".gui", ".info", ".txt", ".yml"}
REVIEWED_NONLOCALIZED_TYPES = {
    "herder_government_obligations": "reviewed_fixed_engine_structural",
    "japan_administrative_salary": "reviewed_inactive_remnant",
    "meritocratic_tribute_gold": "reviewed_inactive_remnant",
    "meritocratic_tribute_prestige": "reviewed_inactive_remnant",
    "iqta_special_rights": "reviewed_inactive_remnant",
    "ghazi_special_rights": "reviewed_inactive_remnant",
}
REVIEWED_NONLOCALIZED_OBLIGATIONS = {
    "meritocratic_tributary_tax_none",
    "meritocratic_tributary_tax_low",
    "meritocratic_tributary_tax_normal",
    "meritocratic_tributary_tax_high",
    "meritocratic_prestige_transfer_none",
    "meritocratic_prestige_transfer_low",
    "meritocratic_prestige_transfer_normal",
    "meritocratic_prestige_transfer_high",
    "iqta_special_rights_default",
    "iqta_special_rights_granted",
    "ghazi_special_rights_default",
    "ghazi_special_rights_granted",
}
EXPECTED_EXCEPTION_PATHS = {
    "herder_government_obligations": "common/subject_contracts/contracts/herder.txt",
    "japan_administrative_salary": "common/subject_contracts/contracts/japan_administrative.txt",
    "meritocratic_tribute_gold": "common/subject_contracts/contracts/meritocratic.txt",
    "meritocratic_tribute_prestige": "common/subject_contracts/contracts/meritocratic.txt",
    "iqta_special_rights": "common/subject_contracts/contracts/special_contracts.txt",
    "ghazi_special_rights": "common/subject_contracts/contracts/special_contracts.txt",
}
EXPECTED_EXCEPTION_SHA256 = {
    "herder_government_obligations": "6c86798f19fd2bc8ac197fc2efc3ed91f21a49c2ac190dbee117a43f058f441a",
    "japan_administrative_salary": "253ad5d2a3e2c1005fc01283b0f71f9c53f263cb39b4e67d7e7878a3202c89b4",
    "meritocratic_tribute_gold": "14116db9c47c776163fd006495b301e0f3d0e4759d7be52053e650a7da820923",
    "meritocratic_tribute_prestige": "a481887877fda0d82f493b957f7a2b9984676a8cf7f3fad1596c714e9dd67e5a",
    "iqta_special_rights": "389249dfb49e3f7eaeb359597dda58722d44c9ae264b998d82c6e18e78297a85",
    "ghazi_special_rights": "5cc405e8f19d1c886b8f26642caad9a9f8e2549ec770b65dddfa0844a1c3470a",
}
EXPECTED_EXCEPTION_LEVELS = {
    "herder_government_obligations": ("default",),
    "japan_administrative_salary": (
        "salary_very_low",
        "salary_low",
        "salary_medium",
        "salary_high",
        "salary_very_high",
    ),
    "meritocratic_tribute_gold": (
        "meritocratic_tributary_tax_none",
        "meritocratic_tributary_tax_low",
        "meritocratic_tributary_tax_normal",
        "meritocratic_tributary_tax_high",
    ),
    "meritocratic_tribute_prestige": (
        "meritocratic_prestige_transfer_none",
        "meritocratic_prestige_transfer_low",
        "meritocratic_prestige_transfer_normal",
        "meritocratic_prestige_transfer_high",
    ),
    "iqta_special_rights": (
        "iqta_special_rights_default",
        "iqta_special_rights_granted",
    ),
    "ghazi_special_rights": (
        "ghazi_special_rights_default",
        "ghazi_special_rights_granted",
    ),
}


@dataclass(frozen=True)
class SubjectContractCatalogLoadResult:
    reference_snapshot_id: str
    type_count: int
    obligation_count: int
    localized_obligation_count: int
    reviewed_nonlocalized_count: int
    parser_run_id: str


@dataclass(frozen=True)
class _ParsedObligation:
    contract_type_id: str
    obligation_id: str
    level_index: int
    is_default: bool
    source_path: str
    source_line_start: int
    source_line_end: int
    source_order: int
    raw_script: str


@dataclass(frozen=True)
class _ParsedContractType:
    contract_type_id: str
    source_path: str
    raw_script: str
    obligations: tuple[_ParsedObligation, ...]


def load_subject_contract_catalog_candidate(
    *,
    game_root: str | Path,
    reference_snapshot_id: str,
    database_path: str | Path | None = None,
) -> SubjectContractCatalogLoadResult:
    """Replace one candidate snapshot's installed subject-contract catalog."""
    root = Path(game_root).resolve()
    source_root = root / "common" / "subject_contracts" / "contracts"
    if not source_root.is_dir():
        raise FileNotFoundError(f"Subject-contract source folder does not exist: {source_root}")

    contract_types, manifests = _parse_installed_definitions(root, source_root)
    _validate_corpus_shape(contract_types, manifests)
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
            raise ValueError("A promoted subject-contract catalog cannot be replaced")
        if (
            str(snapshot[0]) != REVIEWED_GAME_VERSION
            or str(snapshot[1]) != REVIEWED_STEAM_BUILD_ID
        ):
            raise ValueError("Reviewed subject-contract exceptions are build-bound")

        _validate_reviewed_exceptions(root, contract_types)
        rows = _resolve_catalog_rows(connection, reference_snapshot_id, contract_types)

        connection.execute("BEGIN TRANSACTION")
        connection.execute(
            "DELETE FROM reference.subject_contract_obligations WHERE reference_snapshot_id = ?",
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
            """
            INSERT INTO source.source_files
            (reference_snapshot_id, relative_path, source_group, byte_size,
             modified_at_utc, sha256, parser_run_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (reference_snapshot_id, *manifest, parser_run_id)
                for manifest in manifests
            ],
        )
        connection.executemany(
            """
            INSERT INTO reference.subject_contract_obligations
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
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

    return SubjectContractCatalogLoadResult(
        reference_snapshot_id,
        len(contract_types),
        len(rows),
        sum(row[9] is not None for row in rows),
        sum(row[19] != "valid" for row in rows),
        parser_run_id,
    )


def _parse_installed_definitions(
    root: Path,
    source_root: Path,
) -> tuple[list[_ParsedContractType], list[tuple[object, ...]]]:
    contract_types: list[_ParsedContractType] = []
    manifests: list[tuple[object, ...]] = []
    seen_types: set[str] = set()
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
            if assignment.value_kind == "scalar":
                if (
                    relative_path != "common/subject_contracts/contracts/special_contracts.txt"
                    or assignment.key not in TOP_LEVEL_SCALARS
                ):
                    raise ValueError(f"Unexpected top-level scalar: {assignment.key}")
                _scalar_value(assignment.raw_value)
                continue
            if assignment.key in seen_types:
                raise ValueError(f"Duplicate subject-contract type ID: {assignment.key}")
            seen_types.add(assignment.key)
            obligation_blocks = [
                field
                for field in _assignments(
                    assignment.raw_value[1:-1], assignment.line_start
                )
                if field.key == "obligation_levels"
            ]
            if len(obligation_blocks) != 1 or obligation_blocks[0].value_kind != "block":
                raise ValueError(
                    f"Subject-contract type must have one obligation_levels block: {assignment.key}"
                )
            obligations: list[_ParsedObligation] = []
            seen_obligations: set[str] = set()
            for level_index, level in enumerate(
                _assignments(
                    obligation_blocks[0].raw_value[1:-1],
                    obligation_blocks[0].line_start,
                )
            ):
                if level.value_kind != "block":
                    raise ValueError(
                        f"Subject-contract obligation must be a block: {assignment.key}.{level.key}"
                    )
                if level.key in seen_obligations:
                    raise ValueError(
                        f"Duplicate obligation ID in {assignment.key}: {level.key}"
                    )
                seen_obligations.add(level.key)
                defaults = [
                    field
                    for field in _assignments(level.raw_value[1:-1], level.line_start)
                    if field.key == "default"
                ]
                if len(defaults) > 1 or any(field.value_kind != "scalar" for field in defaults):
                    raise ValueError(f"Malformed default marker: {assignment.key}.{level.key}")
                default_value = (
                    _scalar_value(defaults[0].raw_value) if defaults else "no"
                )
                if default_value not in {"yes", "no"}:
                    raise ValueError(
                        f"Invalid default marker {default_value}: {assignment.key}.{level.key}"
                    )
                source_order += 1
                obligations.append(
                    _ParsedObligation(
                        assignment.key,
                        level.key,
                        level_index,
                        default_value == "yes",
                        relative_path,
                        level.line_start,
                        level.line_end,
                        source_order,
                        level.raw_value,
                    )
                )
            contract_types.append(
                _ParsedContractType(
                    assignment.key,
                    relative_path,
                    assignment.raw_value,
                    tuple(obligations),
                )
            )
    return contract_types, manifests


def _validate_corpus_shape(
    contract_types: list[_ParsedContractType],
    manifests: list[tuple[object, ...]],
) -> None:
    obligation_count = sum(len(item.obligations) for item in contract_types)
    if (
        len(manifests) != EXPECTED_FILE_COUNT
        or len(contract_types) != EXPECTED_TYPE_COUNT
        or obligation_count != EXPECTED_OBLIGATION_COUNT
    ):
        raise ValueError(
            "Subject-contract corpus shape changed: "
            f"files={len(manifests)}, types={len(contract_types)}, "
            f"obligations={obligation_count}"
        )


def _validate_reviewed_exceptions(
    root: Path,
    contract_types: list[_ParsedContractType],
) -> None:
    by_id = {item.contract_type_id: item for item in contract_types}
    if (
        set(EXPECTED_EXCEPTION_PATHS) != set(REVIEWED_NONLOCALIZED_TYPES)
        or set(EXPECTED_EXCEPTION_SHA256) != set(REVIEWED_NONLOCALIZED_TYPES)
    ):
        raise AssertionError("Reviewed subject-contract exception configuration is inconsistent")
    for contract_type_id, expected_path in EXPECTED_EXCEPTION_PATHS.items():
        item = by_id.get(contract_type_id)
        if item is None or item.source_path != expected_path:
            raise ValueError(f"Reviewed subject-contract definition changed: {contract_type_id}")
        if sha256(item.raw_script.encode()).hexdigest() != EXPECTED_EXCEPTION_SHA256[contract_type_id]:
            raise ValueError(f"Reviewed subject-contract definition changed: {contract_type_id}")
        if tuple(level.obligation_id for level in item.obligations) != EXPECTED_EXCEPTION_LEVELS[contract_type_id]:
            raise ValueError(f"Reviewed subject-contract levels changed: {contract_type_id}")

    expected_missing_obligations = {
        level
        for type_id in REVIEWED_NONLOCALIZED_TYPES
        for level in EXPECTED_EXCEPTION_LEVELS[type_id]
        if level in REVIEWED_NONLOCALIZED_OBLIGATIONS
    }
    if expected_missing_obligations != REVIEWED_NONLOCALIZED_OBLIGATIONS:
        raise AssertionError("Reviewed obligation exception configuration is inconsistent")

    usage_paths = _installed_usage_paths(
        root,
        set(REVIEWED_NONLOCALIZED_TYPES) | REVIEWED_NONLOCALIZED_OBLIGATIONS,
    )
    allowed = {
        "herder_government_obligations": {
            "common/subject_contracts/groups/subject_contract_groups.txt",
        },
    }
    for stable_id, paths in usage_paths.items():
        if paths != allowed.get(stable_id, set()):
            raise ValueError(f"Reviewed subject-contract consumers changed: {stable_id}")

    group_path = root / "common" / "subject_contracts" / "groups" / "subject_contract_groups.txt"
    government_path = root / "common" / "governments" / "00_government_types.txt"
    interaction_path = root / "common" / "character_interactions" / "00_modifiy_vassal_contract.txt"
    localization_path = root / "localization" / "english" / "government_l_english.yml"
    required_evidence = {
        group_path: (b"herder_vassal", b"herder_government_obligations"),
        government_path: (b"vassal_contract_group = herder_vassal",),
        interaction_path: (b"vassal_contract_has_modifiable_obligations = yes",),
        localization_path: (b"herder_government_vassals_label", b"Herder [obligations|E] cannot be adjusted"),
    }
    for path, needles in required_evidence.items():
        if not path.is_file() or any(needle not in path.read_bytes() for needle in needles):
            raise ValueError(f"Reviewed subject-contract reachability evidence changed: {path}")


def _installed_usage_paths(root: Path, stable_ids: set[str]) -> dict[str, set[str]]:
    definitions_root = "common/subject_contracts/contracts/"
    usages = {stable_id: set() for stable_id in stable_ids}
    patterns = {
        stable_id: re.compile(
            rb"(?<![A-Za-z0-9_])"
            + re.escape(stable_id.encode("utf-8"))
            + rb"(?![A-Za-z0-9_])"
        )
        for stable_id in stable_ids
    }
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative_path = path.relative_to(root).as_posix()
        if relative_path.startswith(definitions_root):
            continue
        raw_bytes = path.read_bytes()
        for stable_id, pattern in patterns.items():
            if pattern.search(raw_bytes):
                usages[stable_id].add(relative_path)
    return usages


def _resolve_catalog_rows(
    connection,
    reference_snapshot_id: str,
    contract_types: list[_ParsedContractType],
) -> list[tuple[object, ...]]:
    keys = list(REVIEWED_NONLOCALIZED_TYPES)
    keys.extend(
        item.contract_type_id
        for item in contract_types
        if item.contract_type_id not in REVIEWED_NONLOCALIZED_TYPES
    )
    keys.extend(
        level.obligation_id
        for item in contract_types
        for level in item.obligations
    )
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
    reviewed_ids = set(REVIEWED_NONLOCALIZED_TYPES) | REVIEWED_NONLOCALIZED_OBLIGATIONS
    if any(stable_id in localizations for stable_id in reviewed_ids):
        raise ValueError("Reviewed subject-contract exception now has localization")

    expected_localized = set(keys) - reviewed_ids
    unresolved = sorted(
        stable_id
        for stable_id in expected_localized
        if stable_id not in localizations or localizations[stable_id][4] != "valid"
    )
    if unresolved:
        raise ValueError("Unresolved subject-contract localization: " + ", ".join(unresolved))

    rows: list[tuple[object, ...]] = []
    for contract_type in contract_types:
        type_localization = localizations.get(contract_type.contract_type_id)
        type_status = REVIEWED_NONLOCALIZED_TYPES.get(contract_type.contract_type_id)
        for level in contract_type.obligations:
            obligation_localization = localizations.get(level.obligation_id)
            obligation_reviewed = level.obligation_id in REVIEWED_NONLOCALIZED_OBLIGATIONS
            validation_status = type_status or (
                "reviewed_inactive_remnant" if obligation_reviewed else "valid"
            )
            rows.append(
                (
                    reference_snapshot_id,
                    contract_type.contract_type_id,
                    level.obligation_id,
                    level.level_index,
                    level.is_default,
                    None if type_status else contract_type.contract_type_id,
                    None if type_status else str(type_localization[1]),
                    None if type_status else str(type_localization[2]),
                    None if type_status else int(type_localization[3]),
                    None if obligation_reviewed else level.obligation_id,
                    None if obligation_reviewed else str(obligation_localization[1]),
                    None if obligation_reviewed else str(obligation_localization[2]),
                    None if obligation_reviewed else int(obligation_localization[3]),
                    level.source_path,
                    level.source_line_start,
                    level.source_line_end,
                    level.source_order,
                    level.raw_script,
                    PARSER_VERSION,
                    validation_status,
                    (
                        "Reviewed Scribe non-localized subject-contract definition"
                        if validation_status != "valid"
                        else None
                    ),
                )
            )
    return rows
