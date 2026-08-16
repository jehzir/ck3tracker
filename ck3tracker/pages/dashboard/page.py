import dash
from dash import html
from schemas.dashboard_schema import dashboard_summary_fields
from theme import DARK_PAGE_STYLE, DARK_CARD_STYLE, TEXT, ACCENT


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

from data.dashboard_summary import compute_dashboard_summary
from theme import DARK_PAGE_STYLE, DARK_CARD_STYLE, TEXT, ACCENT

def layout():
    summary = compute_dashboard_summary()

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


    s = dashboard_summary_fields

    return html.Div(
        [
            html.H1(
                "Dashboard",
                style={"color": TEXT, "marginBottom": "1rem"}
            ),

            html.Div(
                [
                    html.Div(
                        f"Counties / Goal: {s['counties_total']} / {s['counties_goal']}",
                        style={"backgroundColor": CARD_BG, "padding": "1rem", "borderRadius": "6px"}
                    ),
                    html.Div(
                        f"Duchies Held: {s['duchies_held']}",
                        style={"backgroundColor": CARD_BG, "padding": "1rem", "borderRadius": "6px"}
                    ),
                    html.Div(
                        f"Domain: {s['domain_size']}",
                        style={"backgroundColor": CARD_BG, "padding": "1rem", "borderRadius": "6px"}
                    ),
                    html.Div(
                        f"Total Tax: {s['total_tax']}",
                        style={"backgroundColor": CARD_BG, "padding": "1rem", "borderRadius": "6px"}
                    ),
                    html.Div(
                        f"Total Levies: {s['total_levies']}",
                        style={"backgroundColor": CARD_BG, "padding": "1rem", "borderRadius": "6px"}
                    ),
                    html.Div(
                        f"Control ≤25: {s['control_low_count']}",
                        style={"backgroundColor": CARD_BG, "padding": "1rem", "borderRadius": "6px"}
                    ),
                    html.Div(
                        f"Development Avg: {s['development_avg']}",
                        style={"backgroundColor": CARD_BG, "padding": "1rem", "borderRadius": "6px"}
                    ),
                    html.Div(
                        f"Terrain Distribution: {s['terrain_distribution']}",
                        style={"backgroundColor": CARD_BG, "padding": "1rem", "borderRadius": "6px"}
                    ),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(4, 1fr)",
                    "gap": "1rem",
                    "color": TEXT
                }
            ),

            html.Hr(style={"borderColor": ACCENT, "marginTop": "2rem"}),

            html.Div(
                "Dashboard will expand as other tabs become ready.",
                style={"color": TEXT, "marginTop": "1rem"}
            )
        ],
        style={"padding": "2rem", "backgroundColor": BACKGROUND, "minHeight": "100vh"}
    )
