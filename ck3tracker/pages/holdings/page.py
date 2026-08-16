# Holdings Page
import dash
from dash import html, dash_table, Input, Output, callback
from schemas.holdings_schema import holdings_columns
from logic.holdings_provider import get_holdings
from pages.holdings.updater_ui import create_updater_panel

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
                filter_action="native",
                sort_action="native",
                   row_selectable="single",
                selected_rows=[],
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
                style_cell_conditional=[
                    {
                        "if": {"column_id": "Barony_Name"},
                        "fontWeight": "bold",
                    }
                ],
                style_data_conditional=[
                    {
                        "if": {"state": "selected"},
                        "backgroundColor": "#4a5f6f",
                        "border": "1px solid #6a8f9f",
                    },
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

            # Updater Panel Container
            html.Div(id="holdings-updater-container", style={"marginTop": "1.5rem"}),
        ],
        style={"padding": "2rem", "backgroundColor": "#1e1e1e", "color": "#e0e0e0", "minHeight": "100vh"}
    )


@callback(
    Output("holdings-updater-container", "children"),
    Input("holdings-table", "selected_rows"),
    prevent_initial_call=True
)
def update_holding_updater(selected_rows):
    """Update the updater panel when a row is selected."""
    holdings = get_holdings()
    
    if not selected_rows or len(selected_rows) == 0:
        # No row selected
        return create_updater_panel(selected_row=None, selected_holding=None)
    
    # Get the first selected row (single selection for now)
    row_index = selected_rows[0]
    if row_index < len(holdings):
        selected_holding = holdings[row_index]
        return create_updater_panel(selected_row=row_index, selected_holding=selected_holding)
    
    return create_updater_panel(selected_row=None, selected_holding=None)
