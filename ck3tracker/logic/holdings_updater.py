# Holdings Updater Logic - Handle NEW and OWNED holding updates

def get_holding_by_index(holdings_list, index):
    """Get a single holding by its index in the list."""
    if index < 0 or index >= len(holdings_list):
        return None
    return holdings_list[index]


def create_new_holding(barony_name, county_name, holding_type, duchy_name, terrain, 
                       status, control, dev, tax, levies, buildings_count, open_slots, special=False):
    """Create a new holding with all required fields."""
    return {
        "Barony_Name": barony_name,
        "County_Name": county_name,
        "Holding_Type": holding_type,
        "Duchy_Name": duchy_name,
        "Terrain_Type": terrain,
        "Status": status,
        "Control": control,
        "Development": dev,
        "Tax": tax,
        "Levies": levies,
        "Buildings_Count": buildings_count,
        "Open_Building_Slots": open_slots,
        "Special": special,
    }


def update_owned_holding(holding, status=None, control=None, dev=None, tax=None, 
                         levies=None, buildings_count=None, open_slots=None):
    """Update an existing holding with event-driven changes. Special remains immutable."""
    updated = holding.copy()
    
    if status is not None:
        updated["Status"] = status
    if control is not None:
        updated["Control"] = control
    if dev is not None:
        updated["Development"] = dev
    if tax is not None:
        updated["Tax"] = tax
    if levies is not None:
        updated["Levies"] = levies
    if buildings_count is not None:
        updated["Buildings_Count"] = buildings_count
    if open_slots is not None:
        updated["Open_Building_Slots"] = open_slots
    
    return updated
