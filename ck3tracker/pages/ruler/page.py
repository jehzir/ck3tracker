# Ruler Page
import dash
from dash import html


dash.register_page(__name__, path="/ruler", name="Ruler")


def layout():
    return html.Div(
        [
            html.H1("Ruler"),
            html.Div("Ruler details will be added here.", style={"padding": "1rem 0"}),
        ],
        style={"padding": "2rem"},
    )
