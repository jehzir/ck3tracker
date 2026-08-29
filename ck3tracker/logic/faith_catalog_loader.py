"""Load installed CK3 faith IDs with parent religions and linked wiki provenance."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from logic.root_database import connect
from logic.title_history_loader import _assignments, _strip_comments


PARSER_NAME = "installed_faiths"
PARSER_VERSION = "1.0.0"


@dataclass(frozen=True)
class WikiPageEvidence:
    page_key: str
    canonical_url: str
    permanent_url: str
    revision_id: str
    retrieved_at_utc: datetime
    stated_game_version: str | None
    review_status: str


@dataclass(frozen=True)
class FaithCatalogLoadResult:
    reference_snapshot_id: str
    faith_count: int
    parser_run_id: str


def load_faith_catalog_candidate(
    *,
    game_root: str | Path,
    reference_snapshot_id: str,
    wiki_root: WikiPageEvidence,
    wiki_faith: WikiPageEvidence,
    database_path: str | Path | None = None,
) -> FaithCatalogLoadResult:
    """Replace one candidate snapshot's installed faith catalog and wiki evidence."""
    if wiki_root.page_key != "wiki_root" or wiki_faith.page_key != "faith":
        raise ValueError("Expected wiki_root and faith page evidence")
    if wiki_faith.review_status != "reviewed":
        raise ValueError("Faith wiki evidence must be reviewed")

    root = Path(game_root).resolve()
    source_root = root / "common" / "religion" / "religion_types"
    if not source_root.is_dir():
        raise FileNotFoundError(f"Faith source folder does not exist: {source_root}")

    rows: list[tuple[object, ...]] = []
    manifests: list[tuple[object, ...]] = []
    seen: set[str] = set()
    source_order = 0
    for path in sorted(source_root.glob("*.txt")):
        raw_bytes = path.read_bytes()
        relative_path = path.relative_to(root).as_posix()
        manifests.append((
            reference_snapshot_id,
            relative_path,
            PARSER_NAME,
            len(raw_bytes),
            datetime.fromtimestamp(path.stat().st_mtime, timezone.utc),
            sha256(raw_bytes).hexdigest(),
        ))
        text = _strip_comments(raw_bytes.decode("utf-8-sig"))
        for religion in _assignments(text):
            if religion.value_kind != "block":
                continue
            religion_body = religion.raw_value[1:-1]
            for field in _assignments(religion_body, religion.line_start):
                if field.key != "faiths" or field.value_kind != "block":
                    continue
                for faith in _assignments(field.raw_value[1:-1], field.line_start):
                    if faith.value_kind != "block":
                        continue
                    source_order += 1
                    if faith.key in seen:
                        raise ValueError(f"Duplicate faith ID: {faith.key}")
                    seen.add(faith.key)
                    rows.append((
                        reference_snapshot_id,
                        faith.key,
                        religion.key,
                        relative_path,
                        faith.line_start,
                        faith.line_end,
                        source_order,
                        faith.raw_value,
                        PARSER_VERSION,
                        wiki_faith.page_key,
                        "valid",
                        None,
                    ))

    parser_run_id = f"{reference_snapshot_id}:{PARSER_NAME}:{uuid4()}"
    started_at = datetime.now(timezone.utc)
    connection = connect(database_path)
    try:
        snapshot = connection.execute(
            "SELECT review_status FROM source.reference_snapshots WHERE reference_snapshot_id = ?",
            [reference_snapshot_id],
        ).fetchone()
        if snapshot is None:
            raise ValueError("Existing reference snapshot is required")
        if snapshot[0] == "promoted":
            raise ValueError("A promoted faith catalog cannot be replaced")

        connection.execute("BEGIN TRANSACTION")
        connection.execute(
            "DELETE FROM reference.faiths WHERE reference_snapshot_id = ?",
            [reference_snapshot_id],
        )
        connection.execute(
            "DELETE FROM source.source_files WHERE reference_snapshot_id = ? AND source_group = ?",
            [reference_snapshot_id, PARSER_NAME],
        )
        connection.executemany(
            "INSERT INTO source.source_files VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(*manifest, parser_run_id) for manifest in manifests],
        )
        for page in (wiki_root, wiki_faith):
            connection.execute(
                "DELETE FROM source.wiki_pages WHERE reference_snapshot_id = ? AND page_key = ?",
                [reference_snapshot_id, page.page_key],
            )
            connection.execute(
                "INSERT INTO source.wiki_pages VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [reference_snapshot_id, page.page_key, page.canonical_url,
                 page.permanent_url, page.revision_id, page.retrieved_at_utc,
                 page.stated_game_version, page.review_status],
            )
        connection.execute(
            "DELETE FROM source.wiki_page_links WHERE reference_snapshot_id = ? AND from_page_key = 'wiki_root' AND to_page_key = 'faith'",
            [reference_snapshot_id],
        )
        connection.execute(
            "INSERT INTO source.wiki_page_links VALUES (?, 'wiki_root', 'faith', 'Faith', ?)",
            [reference_snapshot_id, wiki_faith.canonical_url],
        )
        connection.executemany(
            "INSERT INTO reference.faiths VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        connection.execute(
            """
            INSERT INTO source.parser_runs VALUES
            (?, ?, ?, ?, 'completed', ?, ?, ?, 0, NULL)
            """,
            [parser_run_id, reference_snapshot_id, PARSER_NAME, PARSER_VERSION,
             started_at, datetime.now(timezone.utc), len(rows)],
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

    return FaithCatalogLoadResult(reference_snapshot_id, len(rows), parser_run_id)