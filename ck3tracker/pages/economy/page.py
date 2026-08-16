# Economy Page
import dash
from dash import html


dash.register_page(__name__, path="/economy", name="Economy")


def layout():
    return html.Div(
        [
            html.H1("Economy"),
            html.Div("Economy details will be added here.", style={"padding": "1rem 0"}),
        ],
        style={"padding": "2rem"},
    )
