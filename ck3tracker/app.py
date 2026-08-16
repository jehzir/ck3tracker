import dash
from dash import html, dcc
from logic.playthroughs_provider import get_all_playthroughs
from theme import DARK_PAGE_STYLE

app = dash.Dash(
    __name__,
    use_pages=True,
    pages_folder="pages"   # CRITICAL
)

# Header with playthrough selector
def create_header():
    playthroughs = get_all_playthroughs()
    playthrough_options = [
        {"label": str(p), "value": p.playthrough_id}
        for p in playthroughs
    ]
    
    return html.Div(
        [
            html.Div(
                [
                    html.Span("CK3 Tracker", style={"fontSize": "24px", "fontWeight": "bold"}),
                    dcc.Dropdown(
                        id="playthrough-selector",
                        options=playthrough_options,
                        value=playthroughs[0].playthrough_id if playthroughs else None,
                        style={"width": "400px"}
                    ),
                    html.Button(
                        "+ New Run",
                        id="new-run-button",
                        style={
                            "padding": "8px 16px",
                            "backgroundColor": "#ff9500",
                            "color": "#fff",
                            "border": "none",
                            "borderRadius": "4px",
                            "cursor": "pointer",
                            "fontSize": "14px"
                        }
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "20px",
                    "padding": "1rem 2rem",
                    "backgroundColor": "#2b2b2b",
                    "borderBottom": "1px solid #3a3a3a"
                }
            ),
            dash.page_container,
        ],
        style={"height": "100vh", "display": "flex", "flexDirection": "column"}
    )


app.layout = create_header

if __name__ == "__main__":
    app.run(debug=True)
