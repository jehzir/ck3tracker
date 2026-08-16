# Dashboard Summary Computation

from data.holdings_provider import get_holdings

def compute_dashboard_summary():
    holdings = get_holdings()

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
    counties = {h["County_Name"] for h in holdings}
    duchies = {h["Duchy_Name"] for h in holdings}

    total_tax = sum(h["Tax"] for h in holdings)
    total_levies = sum(h["Levies"] for h in holdings)

    control_low = sum(1 for h in holdings if h["Control"] <= 25)
    dev_avg = sum(h["Development"] for h in holdings) / len(holdings)

    terrain_dist = {}
    for h in holdings:
        t = h["Terrain_Type"]
        terrain_dist[t] = terrain_dist.get(t, 0) + 1

    return {
        "counties_total": len(counties),
        "counties_goal": None,  # You will wire this later
        "duchies_held": len(duchies),
        "domain_size": len(holdings),
        "total_tax": round(total_tax, 2),
        "total_levies": total_levies,
        "control_low_count": control_low,
        "development_avg": round(dev_avg, 2),
        "terrain_distribution": terrain_dist
    }
