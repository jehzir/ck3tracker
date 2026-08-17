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


def _barony_editor(county_id, barony_id, mode):
    tables = load_trial_tables()
    base_baronies = tables["base_baronies"]
    holdings = tables["holding_observations"]
    base_rows = base_baronies[(base_baronies["county_id"] == county_id) & (base_baronies["barony_id"] == barony_id)]
    if base_rows.empty:
        return html.P("Select a barony to edit.")
    base = base_rows.iloc[0].to_dict()
    observed_rows = holdings[holdings["barony_id"] == barony_id]
    observed = observed_rows.iloc[0].to_dict() if not observed_rows.empty else {}
    preset = observed if mode == "update" else base
    input_style = {
        "width": "100%",
        "boxSizing": "border-box",
        "padding": "0.55rem 0.65rem",
        "backgroundColor": "#2b2b2b",
        "color": "#e0e0e0",
        "border": "1px solid #4a4a4a",
        "borderRadius": "4px",
    }
    field_style = {"minWidth": 0, "display": "flex", "flexDirection": "column", "gap": "0.4rem"}
    return html.Div([
        html.H4(f"{barony_id} editor", style={"color": "#e0e0e0", "marginTop": "1.5rem"}),
        html.Div([
            html.Div(f"Preset: {preset.get('holding_type', base['holding_type'])} | {'County capital' if base['is_county_capital'] else 'Regular slot'}"),
            html.Div(f"Slot state: {base['slot_status']} | Mode: {'observed realm state' if mode == 'update' else 'new acquisition preset'}"),
        ], style={"padding": "0.85rem", "backgroundColor": "#2b2b2b", "borderLeft": "4px solid #4a7c7e", "lineHeight": "1.8"}),
        html.Div([
            html.Div([html.Label("Holder type"), dcc.Dropdown(
                id="trial-barony-holder-type",
                options=[{"label": "Ruler", "value": "ruler"}, {"label": "Vassal", "value": "vassal"}],
                value=observed.get("holder_type", "vassal"), clearable=False,
                className="updater-status-dropdown",
            )], style=field_style),
            html.Div([html.Label("Tax"), dcc.Input(id="trial-barony-tax", type="number", value=observed.get("tax", None), step=0.01, style=input_style)], style=field_style),
            html.Div([html.Label("Levies"), dcc.Input(id="trial-barony-levies", type="number", value=observed.get("levies", None), step=1, style=input_style)], style=field_style),
            html.Div([html.Label("Plague resistance"), dcc.Input(id="trial-barony-plague", type="number", value=observed.get("plague_resistance", None), step=1, style=input_style)], style=field_style),
        ], className="trial-editor-grid", style={"marginTop": "1rem"}),
        html.Div([
            html.Label("Buildings / notes"),
            dcc.Input(id="trial-barony-notes", type="text", value="", placeholder="Optional observation note", style=input_style),
        ], style={"marginTop": "1rem", **field_style}),
        html.Button("Save Trial Observation", id="trial-save-barony", n_clicks=0, style={"marginTop": "1rem", "padding": "0.65rem 1rem", "backgroundColor": "#4a7c7e", "color": "#fff", "border": "none"}),
    ], style={"padding": "1rem", "backgroundColor": "#242424", "border": "1px solid #3a3a3a", "marginTop": "0.75rem"})


def _barony_selector(county_id, mode):
    tables = load_trial_tables()
    slots = tables["base_baronies"]
    holdings = tables["holding_observations"]
    slots = slots[slots["county_id"] == county_id].sort_values("slot_number")
    if slots.empty:
        return html.P("No baronies are available for this county.")
    options = []
    for slot in slots.to_dict("records"):
        observed = holdings[holdings["barony_id"] == slot["barony_id"]]
        live = observed.iloc[0].to_dict() if not observed.empty else {}
        status = live.get("holder_type", "open") if mode == "update" else slot["slot_status"]
        options.append({"label": f'{slot["slot_number"]}. {slot["barony_id"]} | {slot["holding_type"]} | {status}', "value": slot["barony_id"]})
    selected = options[0]["value"]
    return html.Div([
        html.H4("Select barony to edit", style={"color": "#e0e0e0", "marginTop": "1.5rem"}),
        dcc.RadioItems(
            options=options,
            value=selected,
            id="trial-barony-selector",
            className="trial-barony-radio-list",
            labelStyle={"display": "flex", "alignItems": "center", "gap": "0.6rem", "padding": "0.55rem 0.7rem"},
            inputStyle={"margin": 0},
        ),
        html.Div(id="trial-barony-editor", children=_barony_editor(county_id, selected, mode)),
    ], className="trial-barony-section")


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
        _barony_selector(county_id, "update"),
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
        _barony_selector(county_id, "new"),
        html.Button(
            "Record County Acquisition",
            id="trial-record-acquisition",
            n_clicks=0,
            style={"marginTop": "1rem", "padding": "0.75rem 1rem", "backgroundColor": "#4a7c7e", "color": "#fff", "border": "none"},
        ),
    ])


def layout():
    tables = load_trial_tables()
    county_options = tables["county_observations"][["county_id", "county_name", "duchy_id"]].drop_duplicates()
    base_baronies = tables["base_baronies"]
    options = []
    for county in county_options.to_dict("records"):
        baronies = base_baronies[base_baronies["county_id"] == county["county_id"]].sort_values("slot_number")
        barony_ids = [row["barony_id"] for row in baronies.to_dict("records")]
        options.append({
            "label": f'{county["county_name"]} | {county["duchy_id"]} | {len(barony_ids)} baronies',
            "value": county["county_id"],
            "search": " ".join([county["county_name"], county["county_id"], county["duchy_id"], *barony_ids]),
        })
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
            labelStyle={"display": "inline-flex", "alignItems": "center", "gap": "0.55rem", "marginRight": "1.5rem"},
            inputStyle={"margin": 0},
            style={"marginBottom": "1rem"},
        ),
        html.Label("County", style={"fontWeight": "bold"}),
        dcc.Dropdown(
            options=options,
            id="trial-county-selector",
            value="c_constantine",
            clearable=False,
            searchable=True,
            placeholder="Search county, duchy, or barony",
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


@callback(
    Output("trial-barony-editor", "children"),
    Input("trial-barony-selector", "value"),
    State("trial-county-selector", "value"),
    State("trial-holding-mode", "value"),
)
def update_trial_barony_editor(barony_id, county_id, mode):
    return _barony_editor(county_id, barony_id, mode)
