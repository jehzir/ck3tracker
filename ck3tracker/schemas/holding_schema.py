# Holding schema - represents a single holding in the realm
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Holding:
    """Represents a single holding (barony) in the CK3 realm."""
    
    # Structural fields
    holding_id: str
    barony_name: str
    holding_type: str  # e.g., "Castle", "City", "Temple"
    county_id: str
    duchy_id: str
    terrain: str  # e.g., "Plains", "Mountain", "Forest"
    
    # Numeric fields
    levies: int = 0
    taxes: float = 0.0
    development: float = 0.0
    control: int = 0  # 0-100
    
    # Ownership fields
    owned_by_character_id: Optional[str] = None
    owned_by_realm_id: Optional[str] = None
    
    # Acquisition fields
    acquired_at: Optional[int] = None  # Year acquired
    acquisition_method: Optional[str] = None  # e.g., "conquest", "inheritance", "fabricate"
    
    # Lists
    buildings: List[str] = field(default_factory=list)
    modifiers: List[str] = field(default_factory=list)
    
    def __repr__(self):
        return f"Holding({self.barony_name} - {self.holding_type} in {self.county_id})"
