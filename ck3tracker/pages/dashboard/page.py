import dash
from dash import html
from schemas.dashboard_schema import dashboard_summary_fields
from theme import DARK_PAGE_STYLE, DARK_CARD_STYLE, TEXT, ACCENT
from logic.dashboard_service import get_dashboard_metrics

dash.register_page(
    __name__,
    path="/",
    name="Dashboard",
    title="CK3 Tracker — Dashboard"
)

# Dark mode colors
BACKGROUND = "#1e1e1e"
CARD_BG = "#2b2b2b"
TEXT = "#e0e0e0"
ACCENT = "#3a3a3a"

def layout():
    summary = get_dashboard_metrics()

    return html.Div(
        [
            html.H1("Dashboard", style={"color": TEXT}),

            html.Div(
                [
                    html.Div(f"Counties / Goal: {summary['counties_total']} / {summary['counties_goal']}", style=DARK_CARD_STYLE),
                    html.Div(f"Duchies Held: {summary['duchies_held']}", style=DARK_CARD_STYLE),
                    html.Div(f"Domain: {summary['domain_size']}", style=DARK_CARD_STYLE),
                    html.Div(f"Total Tax: {summary['total_tax']}", style=DARK_CARD_STYLE),
                    html.Div(f"Total Levies: {summary['total_levies']}", style=DARK_CARD_STYLE),
                    html.Div(f"Control ≤25: {summary['control_low_count']}", style=DARK_CARD_STYLE),
                    html.Div(f"Development Avg: {summary['development_avg']}", style=DARK_CARD_STYLE),
                    html.Div(f"Terrain Distribution: {summary['terrain_distribution']}", style=DARK_CARD_STYLE),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(4, 1fr)",
                    "gap": "1rem"
                }
            ),

            html.Hr(style={"borderColor": ACCENT, "marginTop": "2rem"}),

            html.Div("Dashboard will expand as other tabs become ready.", style={"color": TEXT})
        ],
        style=DARK_PAGE_STYLE
    )

