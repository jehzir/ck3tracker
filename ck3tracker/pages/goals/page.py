# Goals Page
import dash
from dash import html


dash.register_page(__name__, path="/goals", name="Goals")


def layout():
    return html.Div(
        [
            html.H1("Goals"),
            html.Div("Goals details will be added here.", style={"padding": "1rem 0"}),
        ],
        style={"padding": "2rem"},
    )
