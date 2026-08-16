# Holdings Updater UI Component

import dash
from dash import html, dcc, Input, Output, State

def create_updater_panel(selected_row=None, selected_holding=None):
    """
    Create the holdings updater panel below the table.
    Shows NEW mode (empty form) or OWNED mode (selected row data).
    """
    
    if selected_row is not None and selected_holding is not None:
        # OWNED MODE: Update existing holding
        return html.Div(
            [
                html.H4("Update Holding", style={"marginTop": "2rem", "marginBottom": "1rem", "color": "#e0e0e0"}),
                
                # Header: Barony | County | Special
                html.Div(
                    [
                        html.Span(selected_holding.get("Barony_Name", ""), style={"fontWeight": "bold", "fontSize": "1.2em", "color": "#a8d5ff"}),
                        html.Span(" | ", style={"color": "#777", "margin": "0 0.5rem"}),
                        html.Span(selected_holding.get("County_Name", ""), style={"color": "#b8b8b8"}),
                        html.Span(" | ", style={"color": "#777", "margin": "0 0.5rem"}),
                        html.Span(
                            "✓ Special" if selected_holding.get("Special") else "—",
                            style={"color": "#ffaa33" if selected_holding.get("Special") else "#555"}
                        ),
                    ],
                    style={"marginBottom": "1.5rem", "padding": "0.75rem", "backgroundColor": "#1a1a1a", "borderRadius": "4px"}
                ),
                
                # Editable Fields Grid
                html.Div(
                    [
                        # Status
                        html.Div(
                            [
                                html.Label("Status", style={"fontWeight": "bold", "color": "#e0e0e0", "display": "block", "marginBottom": "0.5rem"}),
                                dcc.Dropdown(
                                    id="updater-status",
                                    options=[
                                        {"label": "Domain", "value": "domain"},
                                        {"label": "Leased", "value": "leased"},
                                        {"label": "Vassal", "value": "vassal"},
                                        {"label": "Gifted", "value": "gifted"},
                                    ],
                                    value=selected_holding.get("Status", "domain"),
                                    className="updater-status-dropdown",
                                    style={"width": "100%"},
                                )
                            ],
                            style={"flex": "1", "marginRight": "1rem", "minWidth": "120px"}
                        ),
                        
                        # Control (%)
                        html.Div(
                            [
                                html.Label("Control %", style={"fontWeight": "bold", "color": "#e0e0e0", "display": "block", "marginBottom": "0.5rem"}),
                                dcc.Input(
                                    id="updater-control",
                                    type="number",
                                    value=selected_holding.get("Control", 0),
                                    min=0,
                                    max=100,
                                    style={"width": "100%", "padding": "0.5rem", "backgroundColor": "#2b2b2b", "color": "#e0e0e0", "border": "1px solid #3a3a3a"}
                                )
                            ],
                            style={"flex": "1", "marginRight": "1rem", "minWidth": "100px"}
                        ),
                        
                        # Dev
                        html.Div(
                            [
                                html.Label("Dev", style={"fontWeight": "bold", "color": "#e0e0e0", "display": "block", "marginBottom": "0.5rem"}),
                                dcc.Input(
                                    id="updater-dev",
                                    type="number",
                                    value=selected_holding.get("Development", 0),
                                    min=0,
                                    style={"width": "100%", "padding": "0.5rem", "backgroundColor": "#2b2b2b", "color": "#e0e0e0", "border": "1px solid #3a3a3a"}
                                )
                            ],
                            style={"flex": "1", "marginRight": "1rem", "minWidth": "80px"}
                        ),
                        
                        # Tax
                        html.Div(
                            [
                                html.Label("Tax", style={"fontWeight": "bold", "color": "#e0e0e0", "display": "block", "marginBottom": "0.5rem"}),
                                dcc.Input(
                                    id="updater-tax",
                                    type="number",
                                    value=selected_holding.get("Tax", 0),
                                    step=0.01,
                                    style={"width": "100%", "padding": "0.5rem", "backgroundColor": "#2b2b2b", "color": "#e0e0e0", "border": "1px solid #3a3a3a"}
                                )
                            ],
                            style={"flex": "1", "marginRight": "1rem", "minWidth": "80px"}
                        ),
                    ],
                    style={"display": "flex", "marginBottom": "1.5rem", "flexWrap": "wrap", "gap": "1rem"}
                ),
                
                # Second Row: Levies, Buildings, Open Slots
                html.Div(
                    [
                        # Levies
                        html.Div(
                            [
                                html.Label("Levies", style={"fontWeight": "bold", "color": "#e0e0e0", "display": "block", "marginBottom": "0.5rem"}),
                                dcc.Input(
                                    id="updater-levies",
                                    type="number",
                                    value=selected_holding.get("Levies", 0),
                                    min=0,
                                    style={"width": "100%", "padding": "0.5rem", "backgroundColor": "#2b2b2b", "color": "#e0e0e0", "border": "1px solid #3a3a3a"}
                                )
                            ],
                            style={"flex": "1", "marginRight": "1rem", "minWidth": "100px"}
                        ),
                        
                        # Buildings Count
                        html.Div(
                            [
                                html.Label("Buildings", style={"fontWeight": "bold", "color": "#e0e0e0", "display": "block", "marginBottom": "0.5rem"}),
                                dcc.Input(
                                    id="updater-buildings",
                                    type="number",
                                    value=selected_holding.get("Buildings_Count", 0),
                                    min=0,
                                    style={"width": "100%", "padding": "0.5rem", "backgroundColor": "#2b2b2b", "color": "#e0e0e0", "border": "1px solid #3a3a3a"}
                                )
                            ],
                            style={"flex": "1", "marginRight": "1rem", "minWidth": "100px"}
                        ),
                        
                        # Open Bld Slots
                        html.Div(
                            [
                                html.Label("Open Bld Slots", style={"fontWeight": "bold", "color": "#e0e0e0", "display": "block", "marginBottom": "0.5rem"}),
                                dcc.Input(
                                    id="updater-open-slots",
                                    type="number",
                                    value=selected_holding.get("Open_Building_Slots", 0),
                                    min=0,
                                    style={"width": "100%", "padding": "0.5rem", "backgroundColor": "#2b2b2b", "color": "#e0e0e0", "border": "1px solid #3a3a3a"}
                                )
                            ],
                            style={"flex": "1", "minWidth": "100px"}
                        ),
                    ],
                    style={"display": "flex", "marginBottom": "1.5rem", "flexWrap": "wrap", "gap": "1rem"}
                ),
                
                # Action Buttons
                html.Div(
                    [
                        html.Button(
                            "Update",
                            id="updater-btn-update",
                            n_clicks=0,
                            style={
                                "padding": "0.75rem 1.5rem",
                                "backgroundColor": "#4a7c7e",
                                "color": "#fff",
                                "border": "none",
                                "borderRadius": "4px",
                                "cursor": "pointer",
                                "marginRight": "0.5rem",
                                "fontWeight": "bold"
                            }
                        ),
                        html.Button(
                            "Cancel",
                            id="updater-btn-cancel",
                            n_clicks=0,
                            style={
                                "padding": "0.75rem 1.5rem",
                                "backgroundColor": "#555",
                                "color": "#fff",
                                "border": "none",
                                "borderRadius": "4px",
                                "cursor": "pointer",
                                "fontWeight": "bold"
                            }
                        ),
                    ],
                    style={"display": "flex"}
                ),
                
                # Hidden store for current row index
                dcc.Store(id="updater-row-index", data=selected_row),
            ],
            style={
                "padding": "1.5rem",
                "backgroundColor": "#2b2b2b",
                "borderRadius": "8px",
                "borderLeft": "4px solid #4a7c7e",
            }
        )
    
    else:
        # EMPTY STATE: No row selected
        return html.Div(
            [
                html.P(
                    "Select a holding row to update its metrics",
                    style={
                        "color": "#999",
                        "fontStyle": "italic",
                        "marginTop": "2rem",
                        "textAlign": "center",
                        "padding": "2rem"
                    }
                )
            ],
            style={"backgroundColor": "#2b2b2b", "borderRadius": "8px", "borderLeft": "4px solid #555"}
        )
