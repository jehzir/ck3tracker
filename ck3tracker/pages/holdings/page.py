# Holdings Page
import dash
from dash import html, dash_table
from schemas.holdings_schema import holdings_columns
from logic.holdings_provider import get_holdings

dash.register_page(__name__, path="/holdings", name="Holdings")

def layout():
    holdings = get_holdings()

    return html.Div(
        [
            html.H1("Holdings", style={"marginBottom": "1rem"}),

            dash_table.DataTable(
                id="holdings-table",
                columns=holdings_columns,
                data=holdings,
                page_size=20,
                style_table={
                    "overflowX": "auto",
                    "borderRadius": "8px",
                    "overflowY": "auto",
                    "maxHeight": "640px",
                    "backgroundColor": "#2b2b2b",
                    "color": "#e0e0e0",
                },
                style_header={
                    "backgroundColor": "#2b2b2b",
                    "color": "#e0e0e0",
                    "fontWeight": "bold",
                    "border": "1px solid #3a3a3a",
                },
                style_cell={
                    "padding": "8px 10px",
                    "backgroundColor": "#2b2b2b",
                    "color": "#e0e0e0",
                    "border": "1px solid #3a3a3a",
                    "minWidth": "90px",
                    "maxWidth": "180px",
                },
                style_data_conditional=[
                    {
                        "if": {"filter_query": "{Status} eq 'domain'"},
                        "backgroundColor": "#1f2d2d",
                    },
                    {
                        "if": {"filter_query": "{Status} eq 'leased'"},
                        "backgroundColor": "#2d241d",
                    },
                    {
                        "if": {"filter_query": "{Status} eq 'vassal'"},
                        "backgroundColor": "#22272d",
                    },
                    {
                        "if": {"filter_query": "{Special} eq True"},
                        "backgroundColor": "#3a2d1d",
                    },
                ],
            ),

            html.Hr(style={"marginTop": "1.5rem"}),
            html.Div("Holding summary is active and ready for real data wiring.", style={"color": "#d0d0d0"})
        ],
        style={"padding": "2rem", "backgroundColor": "#1e1e1e", "color": "#e0e0e0", "minHeight": "100vh"}
    )
