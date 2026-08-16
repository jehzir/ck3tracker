# House Page (renamed from Succession)
import dash
from dash import html


dash.register_page(__name__, path="/house", name="House")


def layout():
    return html.Div(
        [
            html.H1("House"),
            html.Div("House succession details will be added here.", style={"padding": "1rem 0"}),
        ],
        style={"padding": "2rem"},
    )
