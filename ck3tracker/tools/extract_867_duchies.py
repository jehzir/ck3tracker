"""Extract canonical 867 duchy metadata from a saved CK3 Wiki HTML page."""

from __future__ import annotations

import csv
from html.parser import HTMLParser
from pathlib import Path


SOURCE = Path(__file__).parents[1] / "raw" / "duchies_source.html"
OUTPUT = Path(__file__).parents[1] / "data" / "reference" / "ck3_867_duchies.csv"


class DuchyTableParser(HTMLParser):
    """Read only the de jure duchy table from the saved wiki HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.in_de_jure_section = False
        self.in_target_table = False
        self.in_row = False
        self.in_cell = False
        self.section_heading: str | None = None
        self.cell_text: list[str] = []
        self.row: list[str] = []
        self.rows: list[list[str]] = []
        self.cell_tag = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "h2":
            self.section_heading = None
        elif tag == "span" and attributes.get("class") == "mw-headline":
            self.section_heading = ""
        elif tag == "table" and self.in_de_jure_section and not self.in_target_table:
            self.in_target_table = True
        elif tag == "tr" and self.in_target_table:
            self.in_row = True
            self.row = []
        elif tag in {"th", "td"} and self.in_row:
            self.in_cell = True
            self.cell_tag = tag
            self.cell_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "span" and self.section_heading:
            if self.section_heading == "De jure duchies":
                self.in_de_jure_section = True
            elif self.section_heading == "Uncreatable duchies":
                self.in_de_jure_section = False
                self.in_target_table = False
            self.section_heading = None
        elif tag in {"th", "td"} and self.in_cell:
            value = " ".join("".join(self.cell_text).split())
            self.row.append(value)
            self.in_cell = False
            self.cell_tag = ""
        elif tag == "tr" and self.in_row:
            if self.row:
                self.rows.append(self.row)
            self.in_row = False
        elif tag == "table" and self.in_target_table:
            self.in_target_table = False

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.cell_text.append(data)
        elif self.section_heading is not None:
            self.section_heading += data


def extract() -> list[dict[str, str]]:
    parser = DuchyTableParser()
    parser.feed(SOURCE.read_text(encoding="utf-8"))

    records: list[dict[str, str]] = []
    for row in parser.rows:
        if len(row) < 17 or row[0] == "Duchy":
            continue

        # The first cell is the wiki's color marker, not data.
        values = row[1:]
        record = {
            "duchy_name": values[0],
            "kingdom_name_867": values[1],
            "empire_name_867": values[4],
            "county_count_867": values[7],
            "barony_count_867": values[8],
            "average_development_867": values[9],
            "special_buildings": values[12],
            "alternative_names": values[13],
            "capital_county_name": values[14],
            "duchy_id": values[15],
            "start_date": "867",
            "source": "CK3 Wiki List of duchies",
        }
        if record["duchy_id"].startswith("d_"):
            records.append(record)

    return records


def main() -> None:
    records = extract()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(records[0]) if records else []
    with OUTPUT.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    print(f"extracted={len(records)}")
    print(f"output={OUTPUT}")


if __name__ == "__main__":
    main()
