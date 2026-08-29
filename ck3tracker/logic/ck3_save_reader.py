"""Read bounded metadata from a CK3 save without extracting or modifying it."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from zipfile import BadZipFile, ZipFile


GAMESTATE_MEMBER = "gamestate"
MAX_METADATA_BYTES = 1_048_576


class CK3SaveError(ValueError):
    """Raised when a file is not a readable CK3 save container."""


@dataclass(frozen=True)
class CK3SaveMetadata:
    """Player-facing metadata retained at the start of a CK3 gamestate."""

    source_path: Path
    save_game_version: int
    game_version: str
    game_date: str
    player_name: str
    title_name: str
    player_tier: int
    player_character_id: int
    house_name: str | None
    government_id: str | None
    dlcs: tuple[str, ...]
    can_get_achievements: bool
    ironman: bool


@dataclass(frozen=True)
class CK3SaveCandidate:
    """Filesystem metadata used to choose a save before parsing it."""

    source_path: Path
    file_name: str
    size_bytes: int
    modified_at_ns: int


@dataclass(frozen=True)
class CK3SaveBaselineIdentity:
    """Stable save identifiers needed to propose a playthrough baseline."""

    source_path: Path
    player_character_id: int
    primary_title_id: str
    realm_capital_title_id: str
    domain_title_ids: tuple[str, ...]
    culture_numeric_id: int
    faith_numeric_id: int
    house_numeric_id: int


@dataclass(frozen=True)
class _SaveTitle:
    numeric_id: int
    title_id: str
    title_rank: str
    holder_character_id: int | None
    de_jure_liege_numeric_id: int | None


TITLE_RANK_BY_PREFIX = {
    "b": "barony",
    "c": "county",
    "d": "duchy",
    "k": "kingdom",
    "e": "empire",
}
TITLE_RANK_BY_TIER = {
    1: "barony",
    2: "county",
    3: "duchy",
    4: "kingdom",
    5: "empire",
}


def list_save_candidates(
    save_directory: str | Path,
    limit: int = 50,
) -> tuple[CK3SaveCandidate, ...]:
    """List newest CK3 saves without opening or decompressing their contents."""
    directory = Path(save_directory)
    if not directory.is_dir():
        raise CK3SaveError(f"Save directory does not exist: {directory}")
    if limit < 1:
        raise ValueError("limit must be at least 1")

    candidates: list[CK3SaveCandidate] = []
    for path in directory.glob("*.ck3"):
        if not path.is_file():
            continue
        statistics = path.stat()
        candidates.append(
            CK3SaveCandidate(
                source_path=path.resolve(),
                file_name=path.name,
                size_bytes=statistics.st_size,
                modified_at_ns=statistics.st_mtime_ns,
            )
        )
    candidates.sort(key=lambda candidate: (-candidate.modified_at_ns, candidate.file_name.casefold()))
    return tuple(candidates[:limit])


def read_save_metadata(save_path: str | Path) -> CK3SaveMetadata:
    """Read only the bounded metadata prefix of one compressed CK3 save."""
    path = Path(save_path)
    if not path.is_file():
        raise CK3SaveError(f"Save file does not exist: {path}")

    try:
        with ZipFile(path) as archive:
            if GAMESTATE_MEMBER not in archive.namelist():
                raise CK3SaveError("CK3 save does not contain a gamestate member")
            with archive.open(GAMESTATE_MEMBER) as stream:
                prefix = stream.read(MAX_METADATA_BYTES + 1)
    except BadZipFile as error:
        raise CK3SaveError("File is not a readable compressed CK3 save") from error

    block = _extract_metadata_block(prefix)
    values = _parse_top_level_assignments(block)
    portrait_values = _parse_top_level_assignments(
        _required_block(values, "meta_main_portrait")
    )

    return CK3SaveMetadata(
        source_path=path.resolve(),
        save_game_version=_required_int(values, "save_game_version"),
        game_version=_required_text(values, "version"),
        game_date=_required_text(values, "meta_date"),
        player_name=_required_text(values, "meta_player_name"),
        title_name=_required_text(values, "meta_title_name"),
        player_tier=_required_int(values, "meta_player_tier"),
        player_character_id=_required_int(portrait_values, "id"),
        house_name=_optional_text(values, "meta_house_name"),
        government_id=_optional_text(values, "meta_government"),
        dlcs=tuple(_quoted_values(values.get("dlcs", "{}"))),
        can_get_achievements=_required_bool(values, "can_get_achievements"),
        ironman=_required_bool(values, "ironman"),
    )


def read_save_baseline_identity(save_path: str | Path) -> CK3SaveBaselineIdentity:
    """Resolve stable player and title IDs from a selected CK3 save."""
    metadata = read_save_metadata(save_path)
    character_values, played_character_id = _read_player_records(
        metadata.source_path,
        metadata.player_character_id,
    )
    if played_character_id != metadata.player_character_id:
        raise CK3SaveError("Metadata portrait does not match the played character")

    landed_values = _parse_top_level_assignments(
        _required_block(character_values, "landed_data")
    )
    domain_numeric_ids = _integer_values(_required_text(landed_values, "domain"))
    if not domain_numeric_ids:
        raise CK3SaveError("Played character has no landed domain titles")
    realm_capital_numeric_id = _required_int(landed_values, "realm_capital")

    titles = _read_title_records(metadata.source_path, set(domain_numeric_ids))
    missing_ids = set(domain_numeric_ids) - titles.keys()
    if missing_ids:
        missing = ", ".join(str(value) for value in sorted(missing_ids))
        raise CK3SaveError(f"Domain title records are missing: {missing}")
    if realm_capital_numeric_id not in titles:
        raise CK3SaveError("Realm capital is not present in the played character domain")

    expected_rank = TITLE_RANK_BY_TIER.get(metadata.player_tier)
    if expected_rank is None:
        raise CK3SaveError(f"Unsupported player title tier: {metadata.player_tier}")
    primary_candidates = [
        titles[numeric_id]
        for numeric_id in domain_numeric_ids
        if titles[numeric_id].title_rank == expected_rank
        and titles[numeric_id].holder_character_id == metadata.player_character_id
    ]
    if not primary_candidates:
        raise CK3SaveError(
            "Played character primary title cannot be resolved from the ordered domain"
        )

    realm_capital = titles[realm_capital_numeric_id]
    if realm_capital.title_rank != "barony":
        raise CK3SaveError("Played character realm capital is not a barony title")

    return CK3SaveBaselineIdentity(
        source_path=metadata.source_path,
        player_character_id=metadata.player_character_id,
        primary_title_id=primary_candidates[0].title_id,
        realm_capital_title_id=realm_capital.title_id,
        domain_title_ids=tuple(titles[value].title_id for value in domain_numeric_ids),
        culture_numeric_id=_required_int(character_values, "culture"),
        faith_numeric_id=_required_int(character_values, "faith"),
        house_numeric_id=_required_int(character_values, "dynasty_house"),
    )


def _read_player_records(
    save_path: Path,
    player_character_id: int,
) -> tuple[dict[str, str], int]:
    character_values: dict[str, str] | None = None
    played_character_id: int | None = None
    character_opener = f"{player_character_id}={{"

    with ZipFile(save_path) as archive, archive.open(GAMESTATE_MEMBER) as stream:
        lines = iter(stream)
        for raw_line in lines:
            stripped = raw_line.decode("utf-8", errors="replace").strip()
            if character_values is None and stripped == character_opener:
                candidate = _parse_top_level_assignments(
                    _capture_block(stripped, lines)
                )
                if "first_name" in candidate and "landed_data" in candidate:
                    character_values = candidate
            elif played_character_id is None and stripped == "played_character={":
                played_values = _parse_top_level_assignments(
                    _capture_block(stripped, lines)
                )
                played_character_id = _required_int(played_values, "character")
            if character_values is not None and played_character_id is not None:
                return character_values, played_character_id

    raise CK3SaveError("Played character records could not be resolved")


def _read_title_records(
    save_path: Path,
    numeric_ids: set[int],
) -> dict[int, _SaveTitle]:
    records: dict[int, _SaveTitle] = {}
    openers = {f"{numeric_id}={{": numeric_id for numeric_id in numeric_ids}

    with ZipFile(save_path) as archive, archive.open(GAMESTATE_MEMBER) as stream:
        lines = iter(stream)
        for raw_line in lines:
            stripped = raw_line.decode("utf-8", errors="replace").strip()
            numeric_id = openers.get(stripped)
            if numeric_id is None:
                continue
            values = _parse_top_level_assignments(_capture_block(stripped, lines))
            title_id = _optional_text(values, "key")
            if title_id is None:
                continue
            title_rank = TITLE_RANK_BY_PREFIX.get(title_id[:1])
            if title_rank is None or not title_id.startswith(f"{title_id[:1]}_"):
                raise CK3SaveError(f"Unsupported CK3 title key: {title_id}")
            records[numeric_id] = _SaveTitle(
                numeric_id=numeric_id,
                title_id=title_id,
                title_rank=title_rank,
                holder_character_id=_optional_int(values, "holder"),
                de_jure_liege_numeric_id=_optional_int(values, "de_jure_liege"),
            )
            if records.keys() == numeric_ids:
                return records

    return records


def _capture_block(opening_line: str, lines) -> str:
    opening_index = opening_line.find("{")
    parts = [opening_line[opening_index:] + "\n"]
    depth = _brace_delta(parts[0])
    for raw_line in lines:
        line = raw_line.decode("utf-8", errors="replace")
        parts.append(line)
        depth += _brace_delta(line)
        if depth == 0:
            return "".join(parts)
    raise CK3SaveError("Gamestate record has an unclosed block")


def _brace_delta(text: str) -> int:
    depth = 0
    quoted = False
    escaped = False
    for character in text:
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
    return depth


def _extract_metadata_block(prefix: bytes) -> str:
    if len(prefix) > MAX_METADATA_BYTES:
        prefix = prefix[:MAX_METADATA_BYTES]
    text = prefix.decode("utf-8", errors="replace")
    marker = "meta_data="
    marker_index = text.find(marker)
    if marker_index < 0:
        raise CK3SaveError("Gamestate metadata marker was not found")

    opening_index = marker_index + len(marker)
    while opening_index < len(text) and text[opening_index].isspace():
        opening_index += 1
    if opening_index >= len(text) or text[opening_index] != "{":
        raise CK3SaveError("Gamestate metadata block is malformed")

    closing_index = _find_balanced_end(text, opening_index)
    if closing_index is None:
        raise CK3SaveError(
            f"Gamestate metadata exceeds the {MAX_METADATA_BYTES}-byte safety limit"
        )
    return text[opening_index : closing_index + 1]


def _parse_top_level_assignments(block: str) -> dict[str, str]:
    values: dict[str, str] = {}
    position = 1
    content_end = len(block) - 1

    while position < content_end:
        while position < content_end and block[position].isspace():
            position += 1
        key_start = position
        while position < content_end and (
            block[position].isalnum() or block[position] in "_.-"
        ):
            position += 1
        key = block[key_start:position]
        while position < content_end and block[position].isspace():
            position += 1
        if not key or position >= content_end or block[position] != "=":
            position += 1
            continue

        position += 1
        while position < content_end and block[position].isspace():
            position += 1
        value_start = position
        if position < content_end and block[position] == "{":
            value_end = _find_balanced_end(block, position)
            if value_end is None:
                raise CK3SaveError(f"Unclosed metadata value: {key}")
            position = value_end + 1
        elif position < content_end and block[position] == '"':
            position = _find_quoted_end(block, position) + 1
        else:
            while position < content_end and not block[position].isspace():
                position += 1
        values[key] = block[value_start:position]

    return values


def _find_balanced_end(text: str, opening_index: int) -> int | None:
    depth = 0
    quoted = False
    escaped = False
    for index in range(opening_index, len(text)):
        character = text[index]
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
            continue
        if character == '"':
            quoted = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return index
    return None


def _find_quoted_end(text: str, opening_index: int) -> int:
    escaped = False
    for index in range(opening_index + 1, len(text)):
        character = text[index]
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == '"':
            return index
    raise CK3SaveError("Unclosed quoted metadata value")


def _required_text(values: dict[str, str], key: str) -> str:
    value = _optional_text(values, key)
    if value is None:
        raise CK3SaveError(f"Required metadata field is missing: {key}")
    return value


def _required_block(values: dict[str, str], key: str) -> str:
    value = values.get(key)
    if value is None or not value.startswith("{") or not value.endswith("}"):
        raise CK3SaveError(f"Required metadata block is missing: {key}")
    return value


def _optional_text(values: dict[str, str], key: str) -> str | None:
    raw_value = values.get(key)
    if raw_value is None:
        return None
    if raw_value.startswith('"') and raw_value.endswith('"'):
        return raw_value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return raw_value


def _required_int(values: dict[str, str], key: str) -> int:
    try:
        return int(_required_text(values, key))
    except ValueError as error:
        raise CK3SaveError(f"Metadata field is not an integer: {key}") from error


def _optional_int(values: dict[str, str], key: str) -> int | None:
    value = _optional_text(values, key)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError as error:
        raise CK3SaveError(f"Metadata field is not an integer: {key}") from error


def _required_bool(values: dict[str, str], key: str) -> bool:
    value = _required_text(values, key)
    if value not in {"yes", "no"}:
        raise CK3SaveError(f"Metadata field is not yes/no: {key}")
    return value == "yes"


def _quoted_values(raw_value: str) -> list[str]:
    return [
        value.replace('\\"', '"').replace("\\\\", "\\")
        for value in re.findall(r'"((?:\\.|[^"\\])*)"', raw_value)
    ]


def _integer_values(raw_value: str) -> tuple[int, ...]:
    return tuple(int(value) for value in re.findall(r"\d+", raw_value))