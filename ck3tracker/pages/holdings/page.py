# Trial-backed Holdings proof view
import dash
from dash import Input, Output, State, callback, dcc, html

from logic.acquisition_service import record_county_acquisition
from logic.trial_service import load_trial_tables

dash.register_page(__name__, path="/holdings", name="Holdings")

PAGE_STYLE = {"padding": "2rem", "backgroundColor": "#1e1e1e", "color": "#e0e0e0", "minHeight": "100vh"}
HEADER_STYLE = {"textAlign": "left", "padding": "0.65rem", "borderBottom": "1px solid #555", "fontWeight": "bold"}
CELL_STYLE = {"textAlign": "left", "padding": "0.65rem", "borderBottom": "1px solid #3a3a3a"}


def _table(headers, rows):
    return html.Table(
        [html.Thead(html.Tr([html.Th(header, style=HEADER_STYLE) for header in headers])), html.Tbody(rows)],
        style={"width": "100%", "borderCollapse": "collapse", "tableLayout": "fixed", "color": "#e0e0e0", "marginTop": "0.75rem"},
    )


def _county_detail(county_id):
    tables = load_trial_tables()
    counties = tables["county_observations"]
    base_baronies = tables["base_baronies"]
    holdings = tables["holding_observations"]
    county_rows = counties[counties["county_id"] == county_id]
    if county_rows.empty:
        return html.P("No trial observation exists for this county.")
    county = county_rows.iloc[0].to_dict()
    slots = base_baronies[base_baronies["county_id"] == county_id].sort_values("slot_number")
    observed = holdings[holdings["county_id"] == county_id].set_index("barony_id")
    summary = html.Div(
        [
            html.Div(f"Holder: {county['county_holder_name']} ({county['county_holder_role']})"),
            html.Div(f"Scope: {county['ownership_scope']} | Holder type: {county['county_holder_type']}"),
            html.Div(f"Control: {county['control']} | Dev: {county['development']} | Popular Opinion: {county['popular_opinion']}"),
            html.Div(f"Culture: {county['culture']} | Faith: {county['faith']}"),
        ],
        style={"padding": "1rem", "backgroundColor": "#2b2b2b", "borderLeft": "4px solid #4a7c7e", "lineHeight": "1.8"},
    )
    rows = []
    for slot in slots.to_dict("records"):
        live = observed.loc[slot["barony_id"]].to_dict() if slot["barony_id"] in observed.index else {}
        rows.append(html.Tr([
            html.Td(slot["slot_number"], style=CELL_STYLE),
            html.Td(slot["barony_id"], style=CELL_STYLE),
            html.Td(slot["holding_type"], style=CELL_STYLE),
            html.Td("Capital" if slot["is_county_capital"] else "", style=CELL_STYLE),
            html.Td(slot["slot_status"], style=CELL_STYLE),
            html.Td(live.get("holder_type", "unobserved"), style=CELL_STYLE),
            html.Td(live.get("tax", "-"), style=CELL_STYLE),
            html.Td(live.get("levies", "-"), style=CELL_STYLE),
            html.Td(live.get("plague_resistance", "-"), style=CELL_STYLE),
        ]))
    return html.Div([
        html.H3(f"{county['county_name']} | {county['duchy_id']}", style={"color": "#e0e0e0"}),
        html.H4("County-wide daily state", style={"color": "#e0e0e0"}),
        summary,
        html.H4("Barony slots and observed holdings", style={"color": "#e0e0e0", "marginTop": "1.5rem"}),
        _table(["Slot", "Barony ID", "Base Type", "Capital", "Slot State", "Observed Holder", "Tax", "Levies", "Plague Res."], rows),
    ])


def _new_county_detail(county_id):
    tables = load_trial_tables()
    base_baronies = tables["base_baronies"]
    slots = base_baronies[base_baronies["county_id"] == county_id].sort_values("slot_number")
    if slots.empty:
        return html.P("No canonical barony structure exists for this county.")

    rows = [
        html.Tr([
            html.Td(slot["slot_number"], style=CELL_STYLE),
            html.Td(slot["barony_id"], style=CELL_STYLE),
            html.Td(slot["holding_type"], style=CELL_STYLE),
            html.Td("Capital" if slot["is_county_capital"] else "", style=CELL_STYLE),
            html.Td(slot["slot_status"], style=CELL_STYLE),
        ])
        for slot in slots.to_dict("records")
    ]
    return html.Div([
        html.H3("New / Conquered County", style={"color": "#e0e0e0"}),
        html.P("This creates the full base slot structure before daily values are entered."),
        _table(["Slot", "Barony ID", "Base Type", "Capital", "Slot State"], rows),
        html.Button(
            "Record County Acquisition",
            id="trial-record-acquisition",
            n_clicks=0,
            style={"marginTop": "1rem", "padding": "0.75rem 1rem", "backgroundColor": "#4a7c7e", "color": "#fff", "border": "none"},
        ),
    ])


def layout():
    tables = load_trial_tables()
    options = tables["county_observations"][["county_id", "county_name"]].drop_duplicates().to_dict("records")
    return html.Div([
        html.H1("Holdings", style={"color": "#e0e0e0"}),
        html.P("Trial proof view | Scribe 1.19.0.6 | [VALIDATED]", style={"color": "#9be28f"}),
        dcc.RadioItems(
            options=[
                {"label": "New / Conquered", "value": "new"},
                {"label": "Update / Realm", "value": "update"},
            ],
            value="update",
            id="trial-holding-mode",
            inline=True,
            labelStyle={"marginRight": "1.5rem"},
            style={"marginBottom": "1rem"},
        ),
        html.Label("County", style={"fontWeight": "bold"}),
        dcc.Dropdown(
            options=[{"label": option["county_name"], "value": option["county_id"]} for option in options],
            id="trial-county-selector",
            value="c_constantine",
            clearable=False,
            className="updater-status-dropdown",
            style={"marginTop": "0.5rem", "color": "#e0e0e0"},
        ),
        html.Div(id="trial-action-message", style={"marginTop": "1rem", "color": "#9be28f"}),
        html.Div(id="trial-county-detail", children=_county_detail("c_constantine"), style={"marginTop": "1.5rem"}),
    ], style=PAGE_STYLE)


@callback(
    Output("trial-county-detail", "children"),
    Input("trial-county-selector", "value"),
    Input("trial-holding-mode", "value"),
)
def update_trial_county_detail(county_id, mode):
    return _new_county_detail(county_id) if mode == "new" else _county_detail(county_id)


@callback(
    Output("trial-action-message", "children"),
    Input("trial-record-acquisition", "n_clicks"),
    State("trial-county-selector", "value"),
    State("trial-holding-mode", "value"),
    prevent_initial_call=True,
)
def record_trial_acquisition(n_clicks, county_id, mode):
    if not n_clicks or mode != "new":
        return ""
    record_county_acquisition(county_id, "trial_dead_run", "realm", "vassal", "manual_trial_update")
    return f"Recorded acquisition for {county_id}: base barony state persisted."
