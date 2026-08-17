import dash
from dash import html
from schemas.dashboard_schema import dashboard_summary_fields
from theme import DARK_PAGE_STYLE, DARK_CARD_STYLE, TEXT, ACCENT
from logic.dashboard_service import get_dashboard_metrics
from logic.trial_service import get_trial_summary, validate_trial_summary

dash.register_page(
    __name__,
    path="/",
    name="Dashboard",
    title="CK3 Tracker — Dashboard"
)

# Dark mode colors
BACKGROUND = "#1e1e1e"
CARD_BG = "#2b2b2b"
TEXT = "#e0e0e0"
ACCENT = "#3a3a3a"

def layout():
    summary = get_dashboard_metrics()
    trial = get_trial_summary()
    trial_validated = validate_trial_summary(trial)

    trial_headers = [
        "Title",
        "Status",
        "Domain Baronies",
        "Realm Baronies",
        "Base Baronies",
        "Domain Counties",
        "Realm Counties",
        "Creation Cost",
    ]
    table_header_style = {
        "textAlign": "left",
        "padding": "0.75rem",
        "borderBottom": "1px solid #555",
        "fontWeight": "bold",
    }
    table_cell_style = {
        "textAlign": "left",
        "padding": "0.75rem",
        "borderBottom": "1px solid #3a3a3a",
    }
    trial_rows = [
        html.Tr(
            [
                html.Td(title["title_name"], style=table_cell_style),
                html.Td(title["title_status"], style=table_cell_style),
                html.Td(title["domain_barony_count"], style=table_cell_style),
                html.Td(title["realm_barony_count"], style=table_cell_style),
                html.Td(title["base_barony_count"], style=table_cell_style),
                html.Td(title["domain_county_count"], style=table_cell_style),
                html.Td(title["realm_county_count"], style=table_cell_style),
                html.Td(title["creation_gold_cost"] or "-", style=table_cell_style),
            ]
        )
        for title in trial["titles"]
    ]
    county_headers = ["County", "Duchy", "Scope", "Holder", "Control", "Dev", "Culture", "Faith"]
    county_rows = [
        html.Tr(
            [
                html.Td(county["county_name"], style=table_cell_style),
                html.Td(county["duchy_id"], style=table_cell_style),
                html.Td(county["ownership_scope"], style=table_cell_style),
                html.Td(county["county_holder_type"], style=table_cell_style),
                html.Td(county["control"], style=table_cell_style),
                html.Td(county["development"], style=table_cell_style),
                html.Td(county["culture"], style=table_cell_style),
                html.Td(county["faith"], style=table_cell_style),
            ]
        )
        for county in trial["county_observations"]
    ]
    vassal_headers = [
        "County",
        "Duchy",
        "Holder",
        "Role",
        "Control",
        "Dev",
        "Popular Opinion",
        "Culture",
        "Faith",
    ]
    vassal_rows = [
        html.Tr(
            [
                html.Td(county["county_name"], style=table_cell_style),
                html.Td(county["duchy_id"], style=table_cell_style),
                html.Td(county["county_holder_name"], style=table_cell_style),
                html.Td(county["county_holder_role"], style=table_cell_style),
                html.Td(county["control"], style=table_cell_style),
                html.Td(county["development"], style=table_cell_style),
                html.Td(county["popular_opinion"], style=table_cell_style),
                html.Td(county["culture"], style=table_cell_style),
                html.Td(county["faith"], style=table_cell_style),
            ]
        )
        for county in trial["county_observations"]
        if county["ownership_scope"] == "realm"
    ]
    holding_headers = ["Barony", "County", "Duchy", "Type", "Holder", "Tax", "Levies", "Capital"]
    holding_rows = [
        html.Tr(
            [
                html.Td(holding["barony_name"], style=table_cell_style),
                html.Td(holding["county_id"], style=table_cell_style),
                html.Td(holding["duchy_id"], style=table_cell_style),
                html.Td(holding["holding_type"], style=table_cell_style),
                html.Td(holding["holder_type"], style=table_cell_style),
                html.Td(holding["tax"], style=table_cell_style),
                html.Td(holding["levies"], style=table_cell_style),
                html.Td("Yes" if holding["is_county_capital"] else "No", style=table_cell_style),
            ]
        )
        for holding in trial["holding_observations"]
    ]

    def proof_table(headers: list[str], rows: list) -> html.Table:
        return html.Table(
            [
                html.Thead(html.Tr([html.Th(header, style=table_header_style) for header in headers])),
                html.Tbody(rows),
            ],
            style={
                "width": "100%",
                "marginTop": "0.75rem",
                "borderCollapse": "collapse",
                "tableLayout": "fixed",
                "color": TEXT,
            },
        )

    return html.Div(
        [
            html.H1("Dashboard", style={"color": TEXT}),

            html.Div(
                [
                    html.Div(f"Baronies: {summary['domain_size']}", style=DARK_CARD_STYLE),
                    html.Div(f"Counties (Domain): {summary['counties_total']}", style=DARK_CARD_STYLE),
                    html.Div(f"Duchies (Held/Total): {summary['duchies_held']}", style=DARK_CARD_STYLE),
                    html.Div(f"Total Income: {summary['total_tax']}", style=DARK_CARD_STYLE),
                    html.Div(f"Levies: {summary['total_levies']}", style=DARK_CARD_STYLE),
                    html.Div(f"Control ≤25: {summary['control_low_count']}", style=DARK_CARD_STYLE),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(6, 1fr)",
                    "gap": "1rem"
                }
            ),

            html.Hr(style={"borderColor": ACCENT, "marginTop": "2rem"}),

            html.Div(
                [
                    html.H2("Parquet Trial Proof", style={"color": TEXT, "margin": 0}),
                    html.Span(
                        "[VALIDATED]" if trial_validated else "[CHECK FAILED]",
                        style={
                            "color": "#9be28f" if trial_validated else "#ff8c8c",
                            "fontWeight": "bold",
                            "marginLeft": "1rem",
                        },
                    ),
                ],
                style={"display": "flex", "alignItems": "center"},
            ),
            html.P(
                f"{trial['playthrough']['game_version']} | {trial['playthrough']['snapshot_label']}",
                style={"color": TEXT},
            ),
            html.Div(
                [
                    html.Div(f"Domain Baronies: {trial['domain_barony_count']}", style=DARK_CARD_STYLE),
                    html.Div(f"Realm Baronies: {trial['realm_barony_count']}", style=DARK_CARD_STYLE),
                    html.Div(f"Domain Counties: {trial['domain_county_count']}", style=DARK_CARD_STYLE),
                    html.Div(f"Realm Counties: {trial['realm_county_count']}", style=DARK_CARD_STYLE),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(4, 1fr)",
                    "gap": "1rem",
                },
            ),
            proof_table(trial_headers, trial_rows),
            html.H3("Vassal County Detail", style={"color": TEXT, "marginTop": "2rem"}),
            proof_table(vassal_headers, vassal_rows),
            html.H3("County Observations", style={"color": TEXT, "marginTop": "2rem"}),
            proof_table(county_headers, county_rows),
            html.H3("Holding Observations", style={"color": TEXT, "marginTop": "2rem"}),
            proof_table(holding_headers, holding_rows),
        ],
        style=DARK_PAGE_STYLE
    )

