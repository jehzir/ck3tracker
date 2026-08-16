# Holdings Page
import dash
from dash import html, dash_table
from schemas.holdings_schema import holdings_columns

dash.register_page(__name__, path="/holdings", name="Holdings")

def layout():
    summary_ready = True

    if not summary_ready:
        return html.Div("Holdings summary not ready.", style={"padding": "2rem"})

    return html.Div(
        [
            html.H1("Holdings"),

            dash_table.DataTable(
                id="holdings-table",
                columns=holdings_columns,
                data=[],  # No seed data yet
                page_size=20,
                style_table={"overflowX": "auto"},
                style_cell={"padding": "6px"}
            ),

            html.Hr(),
            html.Div("Holding Entry will activate once building logic is added.")
        ],
        style={"padding": "2rem"}
    )
