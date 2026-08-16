# Playthroughs Provider - Load and manage playthrough sessions
from schemas.playthrough_schema import Playthrough


# Seed data - initial playthroughs
SEED_PLAYTHROUGHS = [
    Playthrough(
        playthrough_id="crt_mallorca_867",
        ruler_name="CarthageRunMallorca",
        start_year=867,
        starting_domain_capital="Mallorca"
    ),
    Playthrough(
        playthrough_id="byzant_867",
        ruler_name="Byzantine Emperor",
        start_year=867,
        starting_domain_capital="Constantinople"
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


def create_playthrough(playthrough_id, ruler_name, start_year, starting_domain_capital):
    """Create a new playthrough."""
    playthrough = Playthrough(
        playthrough_id=playthrough_id,
        ruler_name=ruler_name,
        start_year=start_year,
        starting_domain_capital=starting_domain_capital
    )
    _playthroughs[playthrough_id] = playthrough
    return playthrough
