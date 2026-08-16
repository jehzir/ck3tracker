# Dashboard Service - Aggregate provider data into dashboard metrics

from logic.holdings_provider import get_holdings
from logic.counties_provider import get_counties
from logic.duchies_provider import get_duchies
from logic.character_provider import get_character

def get_dashboard_metrics(playthrough_id=None):
    """
    Aggregates data from all providers and returns dashboard metrics.
    """
    holdings = get_holdings(playthrough_id)
    
    # If no holdings exist, return None placeholders
    if not holdings:
        return {
            "counties_total": None,
            "counties_goal": None,
            "duchies_held": None,
            "domain_size": None,
            "total_tax": None,
            "total_levies": None,
            "control_low_count": None,
            "development_avg": None,
            "terrain_distribution": None
        }
    
    # Otherwise compute real values
    counties = {h.get("County_Name") for h in holdings if h.get("County_Name")}
    duchies = {h.get("Duchy_Name") for h in holdings if h.get("Duchy_Name")}
    
    total_tax = sum(h.get("Tax", 0) for h in holdings)
    total_levies = sum(h.get("Levies", 0) for h in holdings)
    
    control_low = sum(1 for h in holdings if h.get("Control", 100) <= 25)
    dev_avg = sum(h.get("Development", 0) for h in holdings) / len(holdings) if holdings else 0
    
    terrain_dist = {}
    for h in holdings:
        t = h.get("Terrain_Type", "Unknown")
        terrain_dist[t] = terrain_dist.get(t, 0) + 1
    
    return {
        "counties_total": len(counties),
        "counties_goal": None,
        "duchies_held": len(duchies),
        "domain_size": len(holdings),
        "total_tax": round(total_tax, 2),
        "total_levies": total_levies,
        "control_low_count": control_low,
        "development_avg": round(dev_avg, 2),
        "terrain_distribution": terrain_dist
    }
