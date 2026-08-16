# Playthroughs Provider - Load and manage playthrough sessions
from schemas.playthrough_schema import Playthrough


# Seed data - placeholder dead runs
SEED_PLAYTHROUGHS = [
    Playthrough(
        playthrough_id="dummy_dead_mallorca_867",
        ruler_name="Dead Run Placeholder",
        start_year=867,
        starting_domain_capital="Mallorca",
        status="dead"
    ),
    Playthrough(
        playthrough_id="dummy_dead_byzant_867",
        ruler_name="Dead Run Placeholder",
        start_year=867,
        starting_domain_capital="Constantinople",
        status="dead"
    ),
]

# In-memory store (will be replaced with database later)
_playthroughs = {p.playthrough_id: p for p in SEED_PLAYTHROUGHS}


def get_all_playthroughs():
    """Return all available playthroughs."""
    return list(_playthroughs.values())


def get_playthrough(playthrough_id):
    """Get a specific playthrough by ID."""
    return _playthroughs.get(playthrough_id)


def create_playthrough(playthrough_id, ruler_name, start_year, starting_domain_capital, status="active"):
    """Create a new playthrough."""
    playthrough = Playthrough(
        playthrough_id=playthrough_id,
        ruler_name=ruler_name,
        start_year=start_year,
        starting_domain_capital=starting_domain_capital,
        status=status,
    )
    _playthroughs[playthrough_id] = playthrough
    return playthrough


def create_default_playthrough():
    """Create a new clean playthrough and make it active."""
    index = len(_playthroughs) + 1
    playthrough_id = f"clean_run_{index}_{__import__('time').time_ns()}"
    return create_playthrough(
        playthrough_id=playthrough_id,
        ruler_name=f"Fresh Campaign {index}",
        start_year=867,
        starting_domain_capital="New Realm",
        status="active",
    )
