"""Import surface for pasted ruler memories and game-state screenshots."""

from __future__ import annotations

import dash
from dash import Input, Output, State, callback, dcc, html


dash.register_page(__name__, path="/imports", name="Imports")

PAGE_STYLE = {
    "padding": "1.25rem 1.5rem",
    "backgroundColor": "#1e1e1e",
    "color": "#e0e0e0",
    "minHeight": "100vh",
}


def layout():
    return html.Div(
        [
            dcc.Store(id="image-intake-store"),
            dcc.Store(id="memory-import-store"),
            html.H1("Imports", className="dhs-page-heading"),
            html.P(
                "Paste the ruler memory copy here, or attach screenshots as supporting evidence. Review imports before creating events.",
                style={"maxWidth": "64rem", "color": "#b8b8b8"},
            ),
            html.Div(
                [
                    html.H3("Ruler memory copy", className="dhs-section-heading"),
                    dcc.Textarea(
                        id="memory-import-text",
                        placeholder="Paste the copied ruler memory text here...",
                        style={
                            "width": "100%",
                            "minHeight": "16rem",
                            "boxSizing": "border-box",
                            "padding": "0.85rem",
                            "backgroundColor": "#242424",
                            "color": "#e0e0e0",
                            "border": "1px solid #4a4a4a",
                            "fontFamily": "inherit",
                            "fontSize": "1rem",
                        },
                    ),
                    html.Button("Accept pasted memory", id="memory-import-accept", n_clicks=0, className="dhs-action-button", style={"marginTop": "0.75rem"}),
                    html.Div(id="memory-import-status", style={"marginTop": "0.75rem", "color": "#9be28f"}),
                ],
                style={"maxWidth": "64rem", "marginBottom": "1.5rem"},
            ),
            html.H3("Screenshot evidence", className="dhs-section-heading"),
            html.Div(
                dcc.Upload(
                    id="image-intake-upload",
                    children=html.Div(["Drop an image here or ", html.A("select a file")]),
                    accept="image/*",
                    multiple=True,
                    style={
                        "width": "100%",
                        "minHeight": "8rem",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "border": "1px dashed #78b7b0",
                        "borderRadius": "4px",
                        "backgroundColor": "#242424",
                        "color": "#e0e0e0",
                        "cursor": "pointer",
                        "textAlign": "center",
                    },
                ),
                style={"maxWidth": "64rem"},
            ),
            html.Div(id="image-intake-status", style={"marginTop": "1rem", "color": "#9be28f"}),
            html.Div(id="image-intake-previews", style={"marginTop": "1rem"}),
        ],
        style=PAGE_STYLE,
    )


@callback(
    Output("memory-import-store", "data"),
    Output("memory-import-status", "children"),
    Input("memory-import-accept", "n_clicks"),
    State("memory-import-text", "value"),
    prevent_initial_call=True,
)
def accept_memory_copy(n_clicks, text):
    if not n_clicks or not text or not text.strip():
        return None, "Paste ruler memory text before accepting it."
    return {
        "source": "clipboard_text",
        "text": text,
        "status": "needs_review",
    }, f"Accepted {len(text.splitlines())} copied line(s) for review."


@callback(
    Output("image-intake-store", "data"),
    Output("image-intake-status", "children"),
    Output("image-intake-previews", "children"),
    Input("image-intake-upload", "contents"),
    Input("image-intake-upload", "filename"),
    prevent_initial_call=True,
)
def accept_images(contents, filenames):
    if not contents or not filenames:
        return [], "No images selected.", []

    accepted = []
    previews = []
    for content, filename in zip(contents, filenames):
        if not filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
            continue
        accepted.append({"filename": filename, "contents": content})
        previews.append(
            html.Div(
                [
                    html.Strong(filename),
                    html.Img(
                        src=content,
                        style={"display": "block", "maxWidth": "100%", "maxHeight": "28rem", "marginTop": "0.75rem"},
                    ),
                ],
                style={"padding": "1rem", "backgroundColor": "#242424", "border": "1px solid #3a3a3a"},
            )
        )
    return accepted, f"Accepted {len(accepted)} image(s).", previews