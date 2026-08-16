# Innovations Page
import dash
from dash import html


dash.register_page(__name__, path="/innovations", name="Innovations")


def layout():
    return html.Div(
        [
            html.H1("Innovations"),
            html.Div("Innovations details will be added here.", style={"padding": "1rem 0"}),
        ],
        style={"padding": "2rem"},
    )
