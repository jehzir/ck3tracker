"""Import surface for pasted ruler memories and game-state screenshots."""

from __future__ import annotations

import dash
import base64
import io
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from dash import Input, Output, State, callback, dcc, html

try:
    import pytesseract
except ModuleNotFoundError:
    pytesseract = None

if pytesseract is not None:
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

dash.register_page(__name__, path="/imports", name="Imports")

PAGE_STYLE = {
    "padding": "1.25rem 1.5rem",
    "backgroundColor": "#1e1e1e",
    "color": "#e0e0e0",
    "minHeight": "100vh",
}


def _ocr_screenshot(image: Image.Image) -> str:
    """Extract visible UI text without inferring an expected game target.

    A wrong screenshot is still useful evidence: return its actual text so review
    can identify the mismatch instead of coercing it to the intended county or barony.
    """
    grayscale = ImageOps.grayscale(image)
    enlarged = grayscale.resize((grayscale.width * 3, grayscale.height * 3))
    enhanced = ImageEnhance.Contrast(enlarged).enhance(1.8).filter(ImageFilter.SHARPEN)
    thresholded = enhanced.point(lambda pixel: 255 if pixel > 160 else 0)
    candidates = []
    for variant in (enhanced, thresholded):
        for config in ("--psm 6", "--psm 11"):
            text = pytesseract.image_to_string(variant, config=config).strip()
            if text:
                candidates.append(text)
    return max(candidates, key=lambda text: len(text.split())) if candidates else ""


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
            html.H3("OCR review draft", className="dhs-section-heading"),
            dcc.Textarea(
                id="image-ocr-draft",
                readOnly=False,
                placeholder="Dropped screenshot text will appear here for review...",
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
            html.Div(id="image-ocr-status", style={"marginTop": "0.75rem", "color": "#ffbe2e"}),
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
    Output("image-ocr-draft", "value"),
    Output("image-ocr-status", "children"),
    Output("image-intake-previews", "children"),
    Input("image-intake-upload", "contents"),
    Input("image-intake-upload", "filename"),
    prevent_initial_call=True,
)
def accept_images(contents, filenames):
    if not contents or not filenames:
        return [], "No images selected.", "", "", []

    accepted = []
    previews = []
    extracted_text = []
    ocr_errors = []
    for content, filename in zip(contents, filenames):
        if not filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
            continue
        accepted.append({"filename": filename, "contents": content})
        try:
            _, encoded = content.split(",", 1)
            image = Image.open(io.BytesIO(base64.b64decode(encoded)))
            if pytesseract is None:
                raise RuntimeError("pytesseract is not installed")
            text = _ocr_screenshot(image)
            if text:
                extracted_text.append(f"[{filename}]\n{text}")
            else:
                ocr_errors.append(f"{filename}: no text detected")
        except Exception as error:
            ocr_errors.append(f"{filename}: OCR unavailable ({error})")
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
    draft = "\n\n".join(extracted_text)
    status = f"Accepted {len(accepted)} image(s)."
    ocr_status = "OCR draft needs review."
    if ocr_errors:
        ocr_status += " " + " | ".join(ocr_errors)
    return accepted, status, draft, ocr_status, previews