import dash
from dash import html, dcc
from logic.playthroughs_provider import get_all_playthroughs

app = dash.Dash(
    __name__,
    use_pages=True,
    pages_folder="pages",
    suppress_callback_exceptions=True,
)


def build_playthrough_options():
    playthroughs = get_all_playthroughs()
    return [
        {"label": f"{p.ruler_name} [{p.status}] - {p.starting_domain_capital}", "value": p.playthrough_id}
        for p in playthroughs
    ]


def build_top_nav():
    ready_tabs = {
        "Dashboard": "/",
        "Holdings": "/holdings",
        "Reference": "/reference",
    }
    disabled_tabs = ["Ruler", "House", "Economy", "Military", "Innovations", "Council", "Goals"]

    nav_items = []
    for label, path in ready_tabs.items():
        nav_items.append(
            html.A(
                label,
                id=f"nav-{label.lower()}",
                href=path,
                style={
                    "padding": "0.7rem 1rem",
                    "marginRight": "0.5rem",
                    "backgroundColor": "#2b2b2b",
                    "color": "#e0e0e0",
                    "textDecoration": "none",
                    "borderRadius": "6px",
                    "border": "1px solid #3a3a3a",
                    "cursor": "pointer",
                },
            )
        )

    for label in disabled_tabs:
        nav_items.append(
            html.Div(
                label,
                style={
                    "padding": "0.7rem 1rem",
                    "marginRight": "0.5rem",
                    "backgroundColor": "#1f1f1f",
                    "color": "#7a7a7a",
                    "borderRadius": "6px",
                    "border": "1px solid #3a3a3a",
                    "cursor": "not-allowed",
                    "opacity": "0.7",
                },
            )
        )

    nav_items.append(
        html.A(
            "Imports",
            id="nav-imports",
            href="/imports",
            style={
                "padding": "0.7rem 1rem",
                "marginRight": "0.5rem",
                "backgroundColor": "#2b2b2b",
                "color": "#e0e0e0",
                "textDecoration": "none",
                "borderRadius": "6px",
                "border": "1px solid #3a3a3a",
                "cursor": "pointer",
            },
        )
    )

    return html.Div(nav_items, style={"display": "flex", "flexWrap": "wrap", "gap": "0.5rem"})


# Header with playthrough selector
def create_header():
    playthroughs = get_all_playthroughs()
    selected_playthrough = playthroughs[0].playthrough_id if playthroughs else None

    return html.Div(
        [
            dcc.Store(
                id="app-state",
                data={
                    "playthrough_id": selected_playthrough,
                    "selected_tab": "dashboard",
                },
            ),
            html.Div(
                [
                    html.Span("CK3 Tracker", style={"fontSize": "24px", "fontWeight": "bold"}),
                    dcc.Dropdown(
                        id="playthrough-selector",
                        options=build_playthrough_options(),
                        value=selected_playthrough,
                        style={"width": "400px"}
                    ),
                    html.Button(
                        "Admin",
                        id="admin-button",
                        disabled=True,
                        style={
                            "padding": "8px 16px",
                            "backgroundColor": "#4b4b4b",
                            "color": "#b5b5b5",
                            "border": "1px solid #5c5c5c",
                            "borderRadius": "4px",
                            "cursor": "not-allowed",
                            "fontSize": "14px",
                            "opacity": "0.8"
                        }
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "20px",
                    "padding": "1rem 2rem",
                    "backgroundColor": "#2b2b2b",
                    "borderBottom": "1px solid #3a3a3a",
                },
            ),
            html.Div(
                build_top_nav(),
                style={
                    "padding": "0.75rem 1rem 0.5rem 1rem",
                    "backgroundColor": "#1e1e1e",
                    "borderBottom": "1px solid #3a3a3a",
                },
            ),
            dash.page_container,
        ],
        style={"height": "100vh", "display": "flex", "flexDirection": "column"},
    )


app.layout = create_header

if __name__ == "__main__":
    app.run(debug=True)
