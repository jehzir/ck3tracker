# Military Page
import dash
from dash import html


dash.register_page(__name__, path="/military", name="Military")


def layout():
    return html.Div(
        [
            html.H1("Military"),
            html.Div("Military details will be added here.", style={"padding": "1rem 0"}),
        ],
        style={"padding": "2rem"},
    )
