# Trial-backed Holdings proof view
import dash
import pandas as pd
from dash import Input, Output, State, callback, dcc, html

from logic.acquisition_service import record_county_acquisition
from logic.trial_service import get_active_trial_counties, load_trial_tables

dash.register_page(__name__, path="/holdings", name="Holdings")

PAGE_STYLE = {"padding": "1.25rem 1.5rem", "backgroundColor": "#1e1e1e", "color": "#e0e0e0", "minHeight": "100vh"}
HEADER_STYLE = {"textAlign": "left", "padding": "0.75rem", "borderBottom": "2px solid #78b7b0", "fontWeight": "700", "color": "#e0e0e0"}
CELL_STYLE = {"textAlign": "left", "padding": "0.55rem 0.65rem", "borderBottom": "1px solid #4a4a4a", "color": "#e0e0e0"}


def _active_counties(tables):
    return get_active_trial_counties(tables)


def _table(headers, rows):
    return html.Table(
        [html.Thead(html.Tr([html.Th(header, style=HEADER_STYLE) for header in headers])), html.Tbody(rows)],
        className="dhs-table",
        style={"width": "100%", "borderCollapse": "collapse", "tableLayout": "fixed", "marginTop": "0.75rem"},
    )


def _holdings_summary():
    tables = load_trial_tables()
    counties = _active_counties(tables)
    base_baronies = tables["base_baronies"]
    holdings = tables["holding_observations"]
    rows = []
    for county in counties.to_dict("records"):
        slots = base_baronies[base_baronies["county_id"] == county["county_id"]]
        observed = holdings[holdings["county_id"] == county["county_id"]]
        occupied = int((observed["holding_type"] != "empty").sum())
        attention = "Control watch" if county["control"] < 50 else "Stable"
        rows.append(html.Tr([
            html.Td(county["county_name"], style=CELL_STYLE),
            html.Td(county["ownership_scope"], style=CELL_STYLE),
            html.Td(county["duchy_id"], style=CELL_STYLE),
            html.Td(county["county_holder_name"], style=CELL_STYLE),
            html.Td(county["control"], style=CELL_STYLE),
            html.Td(county["development"], style=CELL_STYLE),
            html.Td(f"{occupied}/{len(slots)}", style=CELL_STYLE),
            html.Td(attention, style=CELL_STYLE),
        ]))
    return html.Div([
        html.H3("Holdings summary", className="dhs-section-heading"),
        html.P("Current realm snapshot. Open a scope tab to record a major update."),
        _table(["County", "Scope", "Duchy", "Holder", "Control", "Dev", "Occupied / Slots", "Status"], rows),
    ])


def _county_scope_summary():
    tables = load_trial_tables()
    counties = tables["county_observations"]
    lifecycle = tables.get("county_lifecycle", pd.DataFrame())
    lifecycle_by_county = lifecycle.set_index("county_id").to_dict("index") if not lifecycle.empty else {}
    identity_rows = [html.Tr([
        html.Td(county["county_name"], style=CELL_STYLE),
        html.Td(county["ownership_scope"], style=CELL_STYLE),
        html.Td(county["county_holder_name"], style=CELL_STYLE),
        html.Td(lifecycle_by_county.get(county["county_id"], {}).get("lifecycle_state", "active"), style=CELL_STYLE),
    ]) for county in counties.to_dict("records")]
    state_rows = [html.Tr([
        html.Td(county["county_name"], style=CELL_STYLE),
        html.Td(county["control"], style=CELL_STYLE),
        html.Td(county["development"], style=CELL_STYLE),
        html.Td(county["popular_opinion"], style=CELL_STYLE),
        html.Td(f'{county["culture"]} / {county["faith"]}', style=CELL_STYLE),
    ]) for county in counties.to_dict("records")]
    return html.Div([
        html.H3("County state", className="dhs-section-heading"),
        html.P("County-wide values are updated at major run events, not every game-day tick."),
        html.Div([
            html.Div([
                html.H4("Counties", className="dhs-subheading"),
                _table(["County", "Scope", "Holder", "Lifecycle"], identity_rows),
            ], className="dhs-scope-column"),
            html.Div([
                html.H4("Update points", className="dhs-subheading"),
                _table(["County", "Control", "Development", "Popular Opinion", "Culture / Faith"], state_rows),
            ], className="dhs-scope-column"),
        ], className="dhs-county-layout"),
        html.H4("County history and recovery", className="dhs-subheading"),
        _county_history_workspace(),
    ])


def _county_history_workspace(county_id="c_annaba"):
    tables = load_trial_tables()
    counties = tables["county_observations"]
    options = [
        {"label": row["county_name"], "value": row["county_id"]}
        for row in counties.to_dict("records")
    ]
    return html.Div([
        dcc.Dropdown(
            options=options, value=county_id, clearable=False,
            id="county-history-selector", className="updater-status-dropdown",
            placeholder="Select county history",
        ),
        html.Div(
            id="county-history-detail",
            children=_county_history_detail(county_id),
            className="dhs-history-detail",
        ),
    ], className="dhs-history-workspace")


def _county_history_detail(county_id):
    tables = load_trial_tables()
    counties = tables["county_observations"]
    base_baronies = tables["base_baronies"]
    lifecycle = tables.get("county_lifecycle", pd.DataFrame())
    county_rows = counties[counties["county_id"] == county_id]
    if county_rows.empty:
        return html.P("No county history exists for this target.")
    county = county_rows.iloc[0].to_dict()
    lifecycle_rows = lifecycle[lifecycle["county_id"] == county_id]
    state = lifecycle_rows.iloc[0].to_dict() if not lifecycle_rows.empty else {
        "lifecycle_state": "active",
        "reason": "Current active county snapshot.",
    }
    baronies = base_baronies[base_baronies["county_id"] == county_id].sort_values("slot_number")
    barony_text = ", ".join(row["barony_id"] for row in baronies.to_dict("records"))
    archived = state.get("lifecycle_state") == "archived"
    action = html.Button(
        "Restore / Reclaim County",
        id="county-reclaim-action",
        className="dhs-action-button",
        style={"marginTop": "0.75rem"},
    ) if archived else html.P("County is currently active; record changes through Editor.")
    return html.Div([
        html.Div([
            html.Strong(f'{county["county_name"]} | {county["duchy_id"]}'),
            html.Span(f'Lifecycle: {state.get("lifecycle_state", "active")}', className="dhs-status-text"),
        ], className="dhs-history-heading"),
        html.Div(f'Historical holder snapshot: {county.get("county_holder_name", "unrecorded")}'),
        html.Div(f'Historical control / development: {county["control"]} / {county["development"]}'),
        html.Div(f"Attached baronies: {barony_text}"),
        html.Div(f'Recovery note: {state.get("reason", "Historical observation retained.")}'),
        action,
    ], className="dhs-history-record")


def _duchy_scope_summary():
    tables = load_trial_tables()
    counties = _active_counties(tables)
    base_baronies = tables["base_baronies"]
    rows = []
    for duchy_id, duchy_counties in counties.groupby("duchy_id"):
        base_count = len(base_baronies[base_baronies["duchy_id"] == duchy_id])
        rows.append(html.Tr([
            html.Td(duchy_id, style=CELL_STYLE),
            html.Td(len(duchy_counties), style=CELL_STYLE),
            html.Td(base_count, style=CELL_STYLE),
            html.Td("In progress", style=CELL_STYLE),
        ]))
    return html.Div([
        html.H3("Duchy state", className="dhs-section-heading"),
        html.P("Duchy scope summarizes title progress and its underlying county structure."),
        _table(["Duchy", "Observed Counties", "Base Baronies", "Status"], rows),
    ])


def _barony_scope_workspace():
    tables = load_trial_tables()
    county_options = _active_counties(tables)[["county_id", "county_name", "duchy_id"]].drop_duplicates()
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
        html.Div(id="trial-action-message", style={"marginTop": "1rem", "color": "#9be28f"}),
        html.Div(id="trial-county-detail", children=_county_detail("c_constantine", include_selector=False, include_county_state=False, include_context_heading=False), style={"marginTop": "1rem"}),
        html.Div(id="trial-barony-editor", children=_barony_editor("c_constantine", "b_constantine", "update")),
    ])


def _barony_target_card(county_id, mode):
    tables = load_trial_tables()
    slots = tables["base_baronies"]
    holdings = tables["holding_observations"]
    slots = slots[slots["county_id"] == county_id].sort_values("slot_number")
    options = []
    for slot in slots.to_dict("records"):
        observed = holdings[holdings["barony_id"] == slot["barony_id"]]
        live = observed.iloc[0].to_dict() if not observed.empty else {}
        status = live.get("holder_type", "open") if mode == "update" else slot["slot_status"]
        options.append({"label": f'{slot["slot_number"]}. {slot["barony_id"]} | {status}', "value": slot["barony_id"]})
    return html.Div([
        html.Label("Barony to edit", className="dhs-field-label"),
        dcc.RadioItems(
            options=options, value=options[0]["value"] if options else None,
            id="trial-barony-selector", inline=False,
            labelStyle={"display": "flex", "alignItems": "center", "gap": "0.45rem", "marginBottom": "0.35rem"},
            inputStyle={"margin": 0},
        ),
    ])


def _selected_barony_context(county_id, barony_id):
    tables = load_trial_tables()
    counties = _active_counties(tables)
    county_rows = counties[counties["county_id"] == county_id]
    county_name = county_rows.iloc[0]["county_name"] if not county_rows.empty else county_id
    return html.Div([
        html.Span("Selected barony", className="dhs-context-label"),
        html.Strong(f"{barony_id or 'None'} | {county_name}"),
    ], className="dhs-selected-context")


def _barony_scope_summary():
    tables = load_trial_tables()
    base_baronies = tables["base_baronies"]
    holdings = tables["holding_observations"]
    rows = []
    for slot in base_baronies.to_dict("records"):
        observed = holdings[holdings["barony_id"] == slot["barony_id"]]
        live = observed.iloc[0].to_dict() if not observed.empty else {}
        rows.append(html.Tr([
            html.Td(slot["barony_id"], style=CELL_STYLE),
            html.Td(slot["county_id"], style=CELL_STYLE),
            html.Td(slot["holding_type"], style=CELL_STYLE),
            html.Td(live.get("holder_type", "unobserved"), style=CELL_STYLE),
            html.Td(live.get("tax", "-"), style=CELL_STYLE),
            html.Td(live.get("levies", "-"), style=CELL_STYLE),
        ]))
    return html.Div([
        html.H3("Barony state", className="dhs-section-heading"),
        html.P("Read-only holding summary. Use Editor to record a major update."),
        _table(["Barony", "County", "Type", "Holder", "Tax", "Levies"], rows),
    ])


def _county_editor_workspace():
    tables = load_trial_tables()
    options = [
        {"label": row["county_name"], "value": row["county_id"]}
        for row in _active_counties(tables).to_dict("records")
    ]
    return html.Div([
        html.H4("County update", className="dhs-subheading"),
        dcc.Dropdown(options=options, value="c_constantine", clearable=False, className="updater-status-dropdown"),
        html.Div([
            html.Div([html.Label("Control"), dcc.Input(type="number", value=100, min=0, max=100)], className="dhs-editor-field"),
            html.Div([html.Label("Development"), dcc.Input(type="number", value=10, min=0)], className="dhs-editor-field"),
            html.Div([html.Label("Popular opinion"), dcc.Input(type="number", value=20)], className="dhs-editor-field"),
            html.Div([html.Label("Event note"), dcc.Input(type="text", placeholder="Major run event")], className="dhs-editor-field"),
        ], className="trial-editor-grid", style={"marginTop": "1rem"}),
        html.Button("Save County Update", className="dhs-action-button", style={"marginTop": "1rem"}),
    ], className="dhs-editor-surface")


def _duchy_editor_workspace():
    tables = load_trial_tables()
    options = [
        {"label": row["title_name"], "value": row["title_id"]}
        for row in tables["title_progress"].to_dict("records")
    ]
    return html.Div([
        html.H4("Duchy update", className="dhs-subheading"),
        dcc.Dropdown(options=options, value=options[0]["value"], clearable=False, className="updater-status-dropdown"),
        html.Div([
            html.Div([html.Label("Title status"), dcc.Input(type="text", value="in progress")], className="dhs-editor-field"),
            html.Div([html.Label("Event note"), dcc.Input(type="text", placeholder="Major run event")], className="dhs-editor-field"),
        ], className="trial-editor-grid", style={"marginTop": "1rem"}),
        html.Button("Save Duchy Update", className="dhs-action-button", style={"marginTop": "1rem"}),
    ], className="dhs-editor-surface")


def _editor_scope_workspace():
    tables = load_trial_tables()
    county_options = _active_counties(tables)[["county_id", "county_name", "duchy_id"]].drop_duplicates()
    options = []
    for county in county_options.to_dict("records"):
        baronies = tables["base_baronies"][tables["base_baronies"]["county_id"] == county["county_id"]]
        barony_ids = [row["barony_id"] for row in baronies.to_dict("records")]
        options.append({
            "label": f'{county["county_name"]} | {county["duchy_id"]} | {len(barony_ids)} baronies',
            "value": county["county_id"],
            "search": " ".join([county["county_name"], county["county_id"], county["duchy_id"], *barony_ids]),
        })
    return html.Div([
        html.Div([
            html.H3("Record a major update", className="dhs-section-heading"),
            html.Div(id="selected-barony-context", children=_selected_barony_context("c_constantine", "b_constantine")),
        ], className="dhs-editor-heading-row"),
        html.Label("County filter", className="dhs-field-label"),
        dcc.Dropdown(
            options=options, id="trial-county-selector", value="c_constantine", clearable=False,
            searchable=True, placeholder="Search county, duchy, or barony",
            className="updater-status-dropdown", style={"marginBottom": "1rem", "color": "#e0e0e0"},
        ),
        html.Div([
            html.Div([
            html.Label("What are you editing?", className="dhs-field-label"),
            dcc.RadioItems(
                options=[
                    {"label": "Barony", "value": "barony"},
                    {"label": "County", "value": "county"},
                    {"label": "Duchy", "value": "duchy"},
                ],
                value="barony", id="trial-editor-scope", inline=True,
                labelStyle={"display": "inline-flex", "alignItems": "center", "gap": "0.55rem", "marginRight": "1.5rem"},
                inputStyle={"margin": 0},
            ),
            ], className="dhs-radio-card"),
            html.Div([
            html.Label("Update style", className="dhs-field-label"),
            dcc.RadioItems(
                options=[{"label": "New / Conquered", "value": "new"}, {"label": "Update / Realm", "value": "update"}],
                value="update", id="trial-holding-mode", inline=True,
                labelStyle={"display": "inline-flex", "alignItems": "center", "gap": "0.55rem", "marginRight": "1.5rem"},
                inputStyle={"margin": 0},
            ),
            ], className="dhs-radio-card"),
            html.Div(id="trial-barony-target-card", children=_barony_target_card("c_constantine", "update"), className="dhs-radio-card dhs-barony-target-card"),
        ], className="dhs-editor-choice-grid"),
        html.Div([
            html.Div(id="editor-scope-content", children=_barony_scope_workspace(), style={"marginTop": "1.5rem"}),
        ], className="dhs-editor-detail"),
    ])


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


def _county_detail(county_id, include_selector=True, include_county_state=True, include_context_heading=True):
    tables = load_trial_tables()
    counties = _active_counties(tables)
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
    county_state = [
        html.H4("County-wide daily state", style={"color": "#e0e0e0"}),
        summary,
    ] if include_county_state else []
    context_heading = [
        html.H3(f"{county['county_name']} | {county['duchy_id']}", style={"color": "#e0e0e0"}),
    ] if include_context_heading else []
    table_heading = [
        html.H4("Barony slots and observed holdings", style={"color": "#e0e0e0", "marginTop": "1.5rem"}),
    ] if include_context_heading else []
    return html.Div([
        *context_heading,
        *county_state,
        *table_heading,
        _table(["Slot", "Barony ID", "Base Type", "Capital", "Slot State", "Observed Holder", "Tax", "Levies", "Plague Res."], rows),
        _barony_selector(county_id, "update") if include_selector else html.Div(),
    ])


def _new_county_detail(county_id, include_selector=True):
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
        _barony_selector(county_id, "new") if include_selector else html.Div(),
        html.Button(
            "Record County Acquisition",
            id="trial-record-acquisition",
            n_clicks=0,
            style={"marginTop": "1rem", "padding": "0.75rem 1rem", "backgroundColor": "#4a7c7e", "color": "#fff", "border": "none"},
        ),
    ])


def layout():
    return html.Div([
        html.H1("Holdings", className="dhs-page-heading"),
            html.P("Trial proof view | Scribe 1.19.0.6 | [VALIDATED]", className="dhs-validation-badge"),
        dcc.Tabs(
            id="holdings-scope-tabs",
            value="summary",
            children=[
                dcc.Tab(label="Holdings summary", value="summary"),
                dcc.Tab(label="Barony", value="barony"),
                dcc.Tab(label="County", value="county"),
                dcc.Tab(label="Duchy", value="duchy"),
                dcc.Tab(label="Editor", value="editor"),
            ],
                className="dhs-tabs",
                style={"marginBottom": "1.5rem"},
        ),
        html.Div(id="holdings-scope-content", children=_holdings_summary()),
    ], className="dhs-holdings-page", style=PAGE_STYLE)


@callback(Output("holdings-scope-content", "children"), Input("holdings-scope-tabs", "value"))
def update_holdings_scope(scope):
    if scope == "editor":
        return _editor_scope_workspace()
    if scope == "barony":
        return _barony_scope_summary()
    if scope == "county":
        return _county_scope_summary()
    if scope == "duchy":
        return _duchy_scope_summary()
    return _holdings_summary()


@callback(
    Output("county-history-detail", "children"),
    Input("county-history-selector", "value"),
)
def update_county_history(county_id):
    return _county_history_detail(county_id)


@callback(
    Output("trial-county-detail", "children"),
    Input("trial-county-selector", "value"),
    Input("trial-holding-mode", "value"),
)
def update_trial_county_detail(county_id, mode):
    return _new_county_detail(county_id, include_selector=False) if mode == "new" else _county_detail(county_id, include_selector=False, include_county_state=False, include_context_heading=False)


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


@callback(
    Output("trial-barony-target-card", "children"),
    Input("trial-county-selector", "value"),
    Input("trial-holding-mode", "value"),
)
def update_trial_barony_target(county_id, mode):
    return _barony_target_card(county_id, mode)


@callback(
    Output("selected-barony-context", "children"),
    Input("trial-barony-selector", "value"),
    Input("trial-county-selector", "value"),
)
def update_selected_barony_context(barony_id, county_id):
    return _selected_barony_context(county_id, barony_id)


@callback(
    Output("editor-scope-content", "children"),
    Input("trial-editor-scope", "value"),
)
def update_editor_scope(scope):
    if scope == "county":
        return _county_editor_workspace()
    if scope == "duchy":
        return _duchy_editor_workspace()
    return _barony_scope_workspace()
