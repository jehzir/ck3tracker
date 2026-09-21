"""Freeze installed-tree and residual-warning evidence for one readiness report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from uuid import uuid4

from logic.game_tree_scanner import (
    PATH_NORMALIZATION_VERSION,
    SCANNER_NAME,
    SCANNER_VERSION,
    scan_game_tree,
)
from logic.root_database import connect
from logic.title_history_loader import _assignments


LEDGER_VERSION = "1.0.0"
SHAPE_ALGORITHM_VERSION = "ordered-assignment-keys-v1"


@dataclass(frozen=True)
class PrereleaseEvidenceFreezeResult:
    report_id: str
    scan_id: str
    file_count: int
    directory_count: int
    manifest_sha256: str
    warning_subject_count: int
    warning_declaration_count: int
    warning_ledger_sha256: str


def freeze_prerelease_evidence(
    *,
    report_id: str,
    game_root: str | Path,
    steam_manifest_path: str | Path,
    launcher_settings_path: str | Path,
    branch_evidence_path: str | Path,
    expected_file_count: int,
    expected_directory_count: int,
    expected_warning_subject_count: int,
    expected_warning_declaration_count: int,
    database_path: str | Path | None = None,
) -> PrereleaseEvidenceFreezeResult:
    """Append one all-or-nothing prerelease comparison freeze."""
    manifest = scan_game_tree(game_root)
    if (manifest.file_count, manifest.directory_count) != (
        expected_file_count,
        expected_directory_count,
    ):
        raise ValueError("Installed game-tree counts changed before freeze")
    build_evidence = _read_build_evidence(
        steam_manifest_path, launcher_settings_path, branch_evidence_path
    )
    scan_id = f"game-tree:{uuid4()}"
    frozen_at = datetime.now(timezone.utc)
    connection = connect(database_path)
    try:
        report = connection.execute(
            """
            SELECT report.baseline_id, report.reference_snapshot_id,
                   report.overall_status, snapshot.game_version,
                   snapshot.steam_build_id
            FROM reference.promotion_readiness_reports report
            JOIN source.reference_snapshots snapshot
              ON snapshot.reference_snapshot_id = report.reference_snapshot_id
            WHERE report.report_id = ?
            """,
            [report_id],
        ).fetchone()
        if report is None:
            raise ValueError(f"Unknown readiness report: {report_id}")
        baseline_id, snapshot_id, report_status, game_version, steam_build_id = map(
            str, report
        )
        if report_status != "blocked":
            raise ValueError("Prerelease freeze requires the reviewed blocked report")
        if steam_build_id != build_evidence["steam_build_id"]:
            raise ValueError("Steam build evidence does not match the snapshot")
        if game_version != build_evidence["game_version"]:
            raise ValueError("Launcher game version does not match the snapshot")
        if connection.execute(
            "SELECT count(*) FROM reference.promotion_readiness_freezes WHERE report_id = ?",
            [report_id],
        ).fetchone()[0]:
            raise ValueError("Readiness report is already frozen")

        warnings, declarations = _warning_ledger(
            connection, report_id, baseline_id, snapshot_id, manifest
        )
        if (len(warnings), len(declarations)) != (
            expected_warning_subject_count,
            expected_warning_declaration_count,
        ):
            raise ValueError("Residual character warning ledger changed before freeze")
        ledger_payload = {
            "ledger_version": LEDGER_VERSION,
            "shape_algorithm_version": SHAPE_ALGORITHM_VERSION,
            "warnings": warnings,
            "declarations": declarations,
        }
        ledger_digest = _json_sha256(ledger_payload)

        connection.execute("BEGIN TRANSACTION")
        connection.execute(
            """
            INSERT INTO source.game_tree_scans
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                scan_id, snapshot_id, frozen_at, SCANNER_NAME, SCANNER_VERSION,
                PATH_NORMALIZATION_VERSION, build_evidence["steam_app_id"],
                build_evidence["steam_build_id"], build_evidence["steam_branch"],
                build_evidence["clausewitz_revision"],
                build_evidence["locator"], build_evidence["digest"],
                manifest.file_count, manifest.directory_count,
                manifest.manifest_sha256,
            ],
        )
        connection.executemany(
            "INSERT INTO source.game_tree_entries VALUES (?, ?, ?, ?, ?, ?)",
            [
                (scan_id, entry.relative_path, entry.entry_kind, entry.byte_size,
                 entry.mtime_unix_ns, entry.sha256)
                for entry in manifest.entries
            ],
        )
        connection.execute(
            "INSERT INTO reference.promotion_readiness_freezes VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [report_id, scan_id, frozen_at, LEDGER_VERSION,
             SHAPE_ALGORITHM_VERSION, len(warnings), len(declarations), ledger_digest],
        )
        connection.executemany(
            "INSERT INTO reference.promotion_readiness_character_warnings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(report_id, baseline_id, snapshot_id, *warning) for warning in warnings],
        )
        connection.executemany(
            "INSERT INTO reference.promotion_readiness_character_warning_declarations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(report_id, *declaration) for declaration in declarations],
        )
        connection.execute("COMMIT")
        return PrereleaseEvidenceFreezeResult(
            report_id, scan_id, manifest.file_count, manifest.directory_count,
            manifest.manifest_sha256, len(warnings), len(declarations), ledger_digest,
        )
    except Exception:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        connection.close()


def _warning_ledger(connection, report_id, baseline_id, snapshot_id, manifest):
    finding = connection.execute(
        """
        SELECT subject_count FROM reference.promotion_readiness_findings
        WHERE report_id = ? AND finding_code = 'character_history_review'
          AND classification = 'blocking'
        """,
        [report_id],
    ).fetchone()
    state_rows = connection.execute(
        """
        SELECT * FROM reference.character_baseline_states
        WHERE baseline_id = ? AND validation_status = 'warning'
        ORDER BY character_id
        """,
        [baseline_id],
    ).fetchall()
    if finding is None or int(finding[0]) != len(state_rows):
        raise ValueError("Readiness finding does not match live character warnings")
    baseline_date = str(connection.execute(
        "SELECT baseline_date FROM reference.baselines WHERE baseline_id = ?",
        [baseline_id],
    ).fetchone()[0])
    character_ids = [str(row[1]) for row in state_rows]
    declaration_rows = connection.execute(
        """
        SELECT declaration.character_id, declaration.reference_snapshot_id,
               declaration.declaration_order, declaration.source_block_order,
               declaration.operation_order, declaration.effective_date,
               declaration.operation_key, declaration.resolution_status,
               declaration.source_path, source_file.sha256,
               source_file.parser_run_id, declaration.parser_version,
               declaration.raw_script
        FROM source.character_history_declarations declaration
        JOIN source.source_files source_file
          ON source_file.reference_snapshot_id = declaration.reference_snapshot_id
         AND source_file.relative_path = declaration.source_path
         AND source_file.source_group = 'installed_character_history'
        JOIN reference.promotion_readiness_evidence evidence
          ON evidence.report_id = ?
         AND evidence.parser_name = 'installed_character_history'
         AND evidence.parser_run_id = source_file.parser_run_id
         AND evidence.parser_version = declaration.parser_version
        WHERE declaration.reference_snapshot_id = ?
          AND declaration.character_id IN (SELECT unnest(?))
          AND declaration.operation_key = 'effect'
          AND declaration.resolution_status = 'preserved'
          AND declaration.effective_date <= ?
        ORDER BY declaration.character_id, declaration.declaration_order
        """,
        [report_id, snapshot_id, character_ids, baseline_date],
    ).fetchall()
    full_tree_hashes = {
        entry.relative_path: entry.sha256
        for entry in manifest.entries
        if entry.entry_kind == "file"
    }
    declarations = []
    by_character: dict[str, list[list[object]]] = {}
    for row in declaration_rows:
        source_path = str(row[8])
        source_hash = str(row[9])
        if full_tree_hashes.get(source_path) != source_hash:
            raise ValueError(f"Parser and full-tree hashes differ: {source_path}")
        raw_script = str(row[12])
        shape = _structural_shape(raw_script)
        declaration = [
            str(row[0]), str(row[1]), int(row[2]),
            int(row[3]) if row[3] is not None else None, int(row[4]), str(row[5]),
            str(row[6]), str(row[7]), source_path, source_hash, str(row[10]),
            str(row[11]), sha256(raw_script.encode("utf-8")).hexdigest(), shape,
            sha256(shape.encode("utf-8")).hexdigest(), None,
        ]
        declarations.append(declaration)
        by_character.setdefault(str(row[0]), []).append(declaration)
    if set(by_character) != set(character_ids):
        raise ValueError("Warning subjects and preserved declarations do not reconcile")

    warnings = []
    for state in state_rows:
        character_id = str(state[1])
        linked = by_character[character_id]
        warnings.append([
            character_id, str(state[13]), str(state[14]),
            _json_sha256([str(value) if value is not None else None for value in state]),
            len(linked), _json_sha256(linked),
        ])
    return warnings, declarations


def _structural_shape(raw_script: str) -> str:
    def shape_fields(text: str, start_line: int) -> str:
        parts = []
        for field in _assignments(text, start_line):
            if field.value_kind == "block":
                parts.append(f"{field.key}{{{shape_fields(field.raw_value[1:-1], field.line_start)}}}")
            else:
                parts.append(f"{field.key}=<{field.value_kind}>")
        return "+".join(parts)

    return shape_fields(raw_script[1:-1], 1)


def _read_build_evidence(steam_manifest_path, launcher_settings_path, branch_evidence_path):
    paths = [Path(steam_manifest_path), Path(launcher_settings_path), Path(branch_evidence_path)]
    contents = [path.read_bytes() for path in paths]
    steam_text = contents[0].decode("utf-8-sig")
    launcher = json.loads(contents[1].decode("utf-8-sig"))
    branch = contents[2].decode("utf-8-sig").strip()
    app_id = _acf_value(steam_text, "appid")
    build_id = _acf_value(steam_text, "buildid")
    game_version = str(launcher["rawVersion"])
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/release/[0-9.]+", branch):
        raise ValueError("Invalid Clausewitz branch evidence")
    evidence_rows = [
        [str(path.resolve()), sha256(content).hexdigest()]
        for path, content in zip(paths, contents, strict=True)
    ]
    return {
        "steam_app_id": app_id,
        "steam_build_id": build_id,
        "steam_branch": branch,
        "clausewitz_revision": None,
        "game_version": game_version,
        "locator": json.dumps(evidence_rows, ensure_ascii=True, separators=(",", ":")),
        "digest": _json_sha256(evidence_rows),
    }


def _acf_value(text: str, key: str) -> str:
    match = re.search(rf'^\s*"{re.escape(key)}"\s+"([^"]+)"\s*$', text, re.MULTILINE)
    if match is None:
        raise ValueError(f"Steam manifest lacks {key}")
    return match.group(1)


def _json_sha256(value) -> str:
    return sha256(
        json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()