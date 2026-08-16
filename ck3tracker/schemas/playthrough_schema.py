# Playthrough Schema
from dataclasses import dataclass


@dataclass
class Playthrough:
    """Represents a single CK3 playthrough session."""
    playthrough_id: str
    ruler_name: str
    start_year: int
    starting_domain_capital: str
    status: str = "active"

    def __repr__(self):
        return f"{self.ruler_name} [{self.status}] ({self.start_year}) - {self.starting_domain_capital}"
