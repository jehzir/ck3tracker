"""Extract the canonical 867 barony hierarchy from CK3 landed titles."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path


SOURCE = Path(__file__).parents[1] / "raw" / "ck3_867_00_landed_titles.txt"
OUTPUT = Path(__file__).parents[1] / "data" / "reference" / "ck3_867_baronies.csv"
TITLE_PATTERN = re.compile(r"^[ekdbc]_[A-Za-z0-9_-]+$")
TITLE_LINE_PATTERN = re.compile(r"^([ekdbc]_[A-Za-z0-9_-]+)\s*=\s*\{")
CAPITAL_LINE_PATTERN = re.compile(r"^capital\s*=\s*([ekdbc]_[A-Za-z0-9_-]+)")


@dataclass
class TitleRecord:
    title_id: str
    title_level: str
    parent_id: str | None
    capital_id: str | None = None


def title_level(title_id: str) -> str:
    return title_id[0]


def parse_title_blocks(source: str) -> dict[str, TitleRecord]:
    records: dict[str, TitleRecord] = {}
    title_stack: list[tuple[int, str]] = []

    for raw_line in source.splitlines():
        line_without_comment = raw_line.split("#", 1)[0].rstrip()
        if not line_without_comment.strip():
            continue
        indentation = len(line_without_comment) - len(line_without_comment.lstrip(" \t"))
        content = line_without_comment.strip()

        title_match = TITLE_LINE_PATTERN.match(content)
        if title_match:
            while title_stack and indentation <= title_stack[-1][0]:
                title_stack.pop()
            title_id = title_match.group(1)
            parent_id = title_stack[-1][1] if title_stack else None
            records[title_id] = TitleRecord(
                title_id=title_id,
                title_level=title_level(title_id),
                parent_id=parent_id,
            )
            title_stack.append((indentation, title_id))
            continue

        capital_match = CAPITAL_LINE_PATTERN.match(content)
        if capital_match and title_stack:
            records[title_stack[-1][1]].capital_id = capital_match.group(1)
    return records


def extract() -> list[dict[str, str]]:
    records = parse_title_blocks(SOURCE.read_text(encoding="utf-8"))
    first_barony_by_county: dict[str, str] = {}
    for record in records.values():
        if record.title_level != "b" or record.parent_id is None:
            continue
        first_barony_by_county.setdefault(record.parent_id, record.title_id)

    baronies = []
    for record in records.values():
        if record.title_level != "b" or record.parent_id is None:
            continue
        county = records.get(record.parent_id)
        duchy = records.get(county.parent_id) if county and county.parent_id else None
        kingdom = records.get(duchy.parent_id) if duchy and duchy.parent_id else None
        empire = records.get(kingdom.parent_id) if kingdom and kingdom.parent_id else None
        if not county or not duchy:
            continue
        is_county_capital = first_barony_by_county.get(county.title_id) == record.title_id
        baronies.append(
            {
                "barony_id": record.title_id,
                "county_id": county.title_id,
                "duchy_id": duchy.title_id,
                "kingdom_id": kingdom.title_id if kingdom else "",
                "empire_id": empire.title_id if empire else "",
                "is_county_capital": "true" if is_county_capital else "false",
                "capital_derivation": "first_barony_in_county_block" if is_county_capital else "",
                "start_date": "867",
                "source": "CK3 00_landed_titles.txt",
            }
        )
    return sorted(baronies, key=lambda row: row["barony_id"])


def main() -> None:
    rows = extract()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"extracted={len(rows)}")
    print(f"output={OUTPUT}")


if __name__ == "__main__":
    main()
