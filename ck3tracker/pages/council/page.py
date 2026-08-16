# Council Page
import dash
from dash import html


dash.register_page(__name__, path="/council", name="Council")


def layout():
    return html.Div(
        [
            html.H1("Council"),
            html.Div("Council details will be added here.", style={"padding": "1rem 0"}),
        ],
        style={"padding": "2rem"},
    )
