"""Visual inspection surface for candidate CK3 reference data."""

from __future__ import annotations

import dash
from dash import ALL, Input, Output, State, callback, ctx, dcc, html

from logic.reference_inspector_provider import (
    TITLE_RANKS,
    get_baseline_bookmarks,
    get_inspection_baselines,
    get_inspection_title_options,
    get_promotion_readiness,
    get_title_inspection,
)


dash.register_page(__name__, path="/reference", name="Reference Inspector")

DEFAULT_TITLE_ID = "c_ucinaa"
RANK_LABELS = {rank: rank.title() for rank in TITLE_RANKS}


def layout():
    baselines = get_inspection_baselines()
    if not baselines:
        return html.Main(
            [html.H1("Reference Inspector"), html.P("No reference baseline is loaded.")],
            className="ref-page",
        )
    baseline = baselines[0]
    baseline_id = baseline["baseline_id"]
    readiness = get_promotion_readiness(baseline_id)
    options = get_inspection_title_options(baseline_id, "county")
    selected = DEFAULT_TITLE_ID if any(item["value"] == DEFAULT_TITLE_ID for item in options) else options[0]["value"]
    return html.Main(
        [
            html.Header(
                [
                    html.Div(
                        [
                            html.P("CK3 REFERENCE / 867", className="ref-eyebrow"),
                            html.H1("Reference Inspector"),
                            html.P(
                                "Installed Scribe evidence, resolved into stable titles and historical state.",
                                className="ref-subtitle",
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            html.Span("CANDIDATE", className="ref-candidate-mark"),
                            html.Span("Read only", className="ref-readonly-mark"),
                        ],
                        className="ref-status-marks",
                    ),
                ],
                className="ref-header",
            ),
            html.Section(
                [
                    _metric("Titles", f"{baseline['title_count']:,}"),
                    _metric("Canonical", f"{baseline['selectable_count']:,}"),
                    _metric("Game", baseline["game_version"]),
                    _metric("Steam build", baseline["steam_build_id"] or "Unknown"),
                    _metric("Baseline", str(baseline["baseline_date"])),
                ],
                className="ref-metric-strip",
                **{"aria-label": "Reference summary"},
            ),
            _readiness_panel(readiness),
            html.Section(
                [
                    html.Div(
                        [
                            html.P("DATE PROFILE", className="ref-eyebrow"),
                            html.H2("867 start themes"),
                        ],
                        className="ref-theme-heading",
                    ),
                    html.Div(
                        _bookmark_cards(get_baseline_bookmarks(baseline_id)),
                        className="ref-theme-list",
                    ),
                ],
                className="ref-themes",
            ),
            html.Section(
                [
                    html.Div(
                        [
                            html.Label("Snapshot", htmlFor="ref-baseline"),
                            dcc.Dropdown(
                                id="ref-baseline",
                                options=[
                                    {
                                        "label": f"{item['label']} / {item['game_version']} / {item['support_status']}",
                                        "value": item["baseline_id"],
                                    }
                                    for item in baselines
                                ],
                                value=baseline_id,
                                clearable=False,
                                className="ref-dropdown",
                            ),
                        ],
                        className="ref-control ref-control-wide",
                    ),
                    html.Div(
                        [
                            html.Label("Rank"),
                            dcc.RadioItems(
                                id="ref-rank",
                                options=[{"label": RANK_LABELS[rank], "value": rank} for rank in TITLE_RANKS],
                                value="county",
                                inline=True,
                                className="ref-rank-control",
                            ),
                        ],
                        className="ref-control",
                    ),
                    html.Div(
                        [
                            html.Label("Title", htmlFor="ref-title"),
                            dcc.Dropdown(
                                id="ref-title",
                                options=options,
                                value=selected,
                                clearable=False,
                                searchable=True,
                                className="ref-dropdown",
                            ),
                        ],
                        className="ref-control ref-control-title",
                    ),
                ],
                className="ref-toolbar",
            ),
            dcc.Loading(
                html.Div(id="ref-detail", children=_render_detail(baseline_id, selected)),
                type="circle",
                color="#f4c95d",
            ),
        ],
        className="ref-page",
    )


@callback(
    Output("ref-title", "options"),
    Output("ref-title", "value"),
    Input("ref-baseline", "value"),
    Input("ref-rank", "value"),
    State("ref-title", "value"),
)
def update_title_options(baseline_id: str, title_rank: str, current_title: str | None):
    options = get_inspection_title_options(baseline_id, title_rank)
    preferred = DEFAULT_TITLE_ID if title_rank == "county" else None
    option_ids = {item["value"] for item in options}
    value = (
        current_title
        if current_title in option_ids
        else preferred
        if preferred in option_ids
        else options[0]["value"]
        if options
        else None
    )
    return options, value


@callback(
    Output("ref-detail", "children"),
    Input("ref-baseline", "value"),
    Input("ref-title", "value"),
)
def update_detail(baseline_id: str, title_id: str | None):
    if not title_id:
        return html.Div("No title is available at this rank.", className="ref-empty")
    return _render_detail(baseline_id, title_id)


@callback(
    Output("ref-rank", "value", allow_duplicate=True),
    Output("ref-title", "value", allow_duplicate=True),
    Input({"type": "ref-title-link", "title_id": ALL, "rank": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def follow_title(_clicks):
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict):
        return dash.no_update, dash.no_update
    return triggered["rank"], triggered["title_id"]


def _render_detail(baseline_id: str, title_id: str):
    detail = get_title_inspection(baseline_id, title_id)
    if detail is None:
        return html.Div("Title not found in this baseline.", className="ref-empty")
    return html.Div(
        [
            html.Section(
                [
                    html.Div(
                        [
                            html.Span(detail["title_rank"].upper(), className="ref-rank-label"),
                            html.H2(detail["display_name"]),
                            html.Code(detail["title_id"]),
                        ]
                    ),
                    _status_badge(
                        "Canonical" if detail["selectable"] else "Review required",
                        "valid" if detail["selectable"] else "warning",
                    ),
                ],
                className="ref-title-heading",
            ),
            html.Nav(
                _chain_nodes(detail["chain"]),
                className="ref-chain",
                **{"aria-label": "Title hierarchy"},
            ),
            html.Div(
                [
                    html.Section(
                        [
                            _section_heading("867 title state", detail["history_validation_status"]),
                            html.Div(
                                [
                                    _fact("Holder", detail["holder_name"] or detail["holder_character_id"] or "No declaration"),
                                    _fact("Government", detail["government_id"] or "No declaration"),
                                    _fact("Succession laws", _law_state_text(detail["laws"])),
                                    _fact("Development", _value(detail["development_level"], detail["development_status"])),
                                    _fact("Liege", detail["liege_title_id"] or _status_text(detail["liege_status"])),
                                    _fact("Static de jure parent", detail["parent_title_id"] or "None"),
                                    _fact("867 de jure parent", _de_jure_text(detail)),
                                    _fact("Capital", detail["capital_title_id"] or _status_text(detail["capital_status"])),
                                    _fact("Capital source", _status_text(detail["capital_status"])),
                                    _fact("Holder status", _status_text(detail["holder_lifecycle_status"] or detail["holder_status"])),
                                    _fact("Holder source", _holder_source_text(detail)),
                                ],
                                className="ref-fact-grid",
                            ),
                        ],
                        className="ref-panel ref-state-panel",
                    ),
                    html.Section(
                        [
                            _section_heading("Holder identity", detail["holder_validation_status"]),
                            _holder_content(detail),
                        ],
                        className="ref-panel ref-holder-panel",
                    ),
                    html.Section(
                        [
                            _section_heading("Evidence", detail["hierarchy_validation_status"]),
                            html.Div(
                                [
                                    _fact("Title source", detail["source_path"] or "Unknown"),
                                    _fact("Source line", detail["source_line"] or "Unknown"),
                                    _fact("History source", _history_source_text(detail["history_blocks"])),
                                    _fact("History conflict", _history_conflict_text(detail["history_blocks"])),
                                    _fact("Law evidence", _law_source_text(detail["laws"])),
                                    _fact("Snapshot", detail["reference_snapshot_id"]),
                                    _fact("Validation", detail["hierarchy_validation_status"] or "Unknown"),
                                ],
                                className="ref-evidence-list",
                            ),
                        ],
                        className="ref-panel ref-evidence-panel",
                    ),
                ],
                className="ref-detail-grid",
            ),
            _warning_section(detail["warnings"]),
            _children_section(detail["children"]),
        ],
        className="ref-inspection",
    )


def _holder_content(detail):
    if not detail["holder_character_id"]:
        return html.Div(
            [html.Strong("No direct holder"), html.Span(_status_text(detail["holder_status"]))],
            className="ref-no-holder",
        )
    return html.Div(
        [
            html.Div(
                [
                    html.Strong(detail["holder_name"] or detail["holder_character_id"]),
                    html.Code(detail["holder_character_id"]),
                ],
                className="ref-holder-name",
            ),
            html.Div(
                [
                    _fact("Culture", detail["culture_id"] or "Unknown"),
                    _fact("Faith", detail["faith_id"] or "Unknown"),
                    _fact("Dynasty", detail["dynasty_id"] or detail["dynasty_house_id"] or "Unknown"),
                    _fact("Life", f"{detail['birth_date'] or '?'} to {detail['death_date'] or '?'}"),
                ],
                className="ref-holder-facts",
            ),
        ]
    )


def _holder_source_text(detail):
    if not detail["holder_evidence_kind"]:
        return "Installed title history"
    return (
        f"Immediate save; declared {detail['declared_holder_character_id']}; "
        f"SHA-256 {detail['holder_evidence_sha256']}"
    )


def _history_source_text(blocks):
    if not blocks:
        return "No declaration"
    return "; ".join(
        f"{block['source_block_order']}: {block['source_path']} ({block['resolution_status']})"
        for block in blocks
    )


def _history_conflict_text(blocks):
    fields = next(
        (
            block["baseline_conflict_fields"]
            for block in blocks
            if block["baseline_conflict_fields"]
        ),
        None,
    )
    if fields is None:
        return "None"
    classification = blocks[0]["duplicate_classification"].replace("_", " ")
    return f"{classification}: {fields}"


def _law_state_text(laws):
    if not laws:
        return "No explicit title law"
    return "; ".join(
        f"{law['law_id']} ({law['law_group_id']}, from {law['effective_date']})"
        for law in laws
    )


def _law_source_text(laws):
    if not laws:
        return "No active law declaration"
    return "; ".join(
        f"#{law['source_declaration_order']} -> {law['source_path']}:{law['source_line_start']}"
        for law in laws
    )


def _de_jure_text(detail):
    status = detail["de_jure_liege_status"]
    if status is None:
        return "No dated override"
    if status == "explicit_clear":
        value = "Explicit clear"
    else:
        value = detail["de_jure_liege_title_id"]
    return (
        f"{value} (from {detail['de_jure_effective_date']}, "
        f"declaration #{detail['de_jure_source_declaration_order']})"
    )


def _chain_nodes(chain):
    nodes = []
    for index, item in enumerate(chain):
        if index:
            nodes.append(html.Span(">", className="ref-chain-arrow", **{"aria-hidden": "true"}))
        nodes.append(
            html.Button(
                [html.Span(item["title_rank"]), html.Strong(item["display_name"])],
                id={"type": "ref-title-link", "title_id": item["title_id"], "rank": item["title_rank"]},
                n_clicks=0,
                className="ref-chain-node" + (" ref-chain-warning" if not item["selectable"] else ""),
                title=item["title_id"],
            )
        )
    return nodes


def _children_section(children):
    if not children:
        return html.Section(
            [_section_heading("Direct vassal titles"), html.P("No child titles in the landed-title hierarchy.")],
            className="ref-children",
        )
    return html.Section(
        [
            _section_heading(f"Direct vassal titles ({len(children)})"),
            html.Div(
                [
                    html.Button(
                        [
                            html.Span(child["title_rank"].upper()),
                            html.Strong(child["display_name"]),
                            html.Code(child["title_id"]),
                        ],
                        id={"type": "ref-title-link", "title_id": child["title_id"], "rank": child["title_rank"]},
                        n_clicks=0,
                        className="ref-child-row" + (" ref-child-warning" if not child["selectable"] else ""),
                    )
                    for child in children
                ],
                className="ref-child-list",
            ),
        ],
        className="ref-children",
    )


def _warning_section(warnings):
    if not warnings:
        return html.Section(
            [html.Strong("No title-level warnings"), html.Span("Cross-source checks passed for this record.")],
            className="ref-warning-band ref-warning-clear",
        )
    return html.Section(
        [html.Strong(f"Review notes ({len(warnings)})"), html.Ul([html.Li(item) for item in warnings])],
        className="ref-warning-band",
    )


def _metric(label, value):
    return html.Div([html.Span(label), html.Strong(value)], className="ref-metric")


def _bookmark_cards(bookmarks):
    return [
        html.Div(
            [
                html.Strong(bookmark["display_name"]),
                html.Code(bookmark["bookmark_id"]),
                html.Div(
                    [
                        html.Span(f"{bookmark['featured_count']} featured rulers"),
                        html.Span(
                            bookmark["dlc_requirements"] or "Core game",
                            className="ref-theme-dlc" if bookmark["dlc_requirements"] else "",
                        ),
                    ],
                ),
            ],
            className="ref-theme-item",
        )
        for bookmark in bookmarks
    ]


def _readiness_panel(report):
    if report is None:
        return html.Section(
            [html.Strong("Promotion report not generated")],
            className="ref-readiness ref-readiness-empty",
        )
    counts = report["counts"]
    ordered_findings = sorted(
        report["findings"],
        key=lambda item: (
            ("blocking", "accepted_exception", "informational", "passed").index(
                item["classification"]
            ),
            item["code"],
        ),
    )
    return html.Section(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.P("PROMOTION READINESS", className="ref-eyebrow"),
                            html.H2("Blocked" if report["overall_status"] == "blocked" else "Ready for review"),
                            html.P(
                                (
                                    f"Evidence {report['evidence_status']}: {report['evidence_detail']} "
                                    "Promotion remains a separate explicit transaction."
                                ),
                                className="ref-readiness-note",
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            _readiness_count("Blocking", counts["blocking"], "blocking"),
                            _readiness_count("Accepted", counts["accepted_exception"], "accepted_exception"),
                            _readiness_count("Passed", counts["passed"], "passed"),
                        ],
                        className="ref-readiness-counts",
                    ),
                ],
                className="ref-readiness-header",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                finding["classification"].replace("_", " "),
                                className=f"ref-finding-class ref-finding-{finding['classification']}",
                            ),
                            html.Strong(finding["summary"]),
                            html.Span(
                                f"{finding['subject_count']:,}",
                                className="ref-finding-count",
                            ),
                            html.P(finding["detail"]),
                        ],
                        className="ref-finding-row",
                    )
                    for finding in ordered_findings
                ],
                className="ref-findings",
            ),
        ],
        className=f"ref-readiness ref-readiness-{report['overall_status']}",
        **{"aria-label": "Promotion readiness report"},
    )


def _readiness_count(label, count, classification):
    return html.Div(
        [html.Span(label), html.Strong(str(count))],
        className=f"ref-readiness-count ref-readiness-count-{classification}",
    )


def _fact(label, value):
    return html.Div([html.Span(label), html.Strong(str(value))], className="ref-fact")


def _section_heading(text, status=None):
    children = [html.H3(text)]
    if status:
        children.append(_status_badge(status.replace("_", " ").title(), status))
    return html.Div(children, className="ref-section-heading")


def _status_badge(text, status):
    return html.Span(text, className=f"ref-badge ref-badge-{status or 'unknown'}")


def _status_text(value):
    return str(value or "Unknown").replace("_", " ").title()


def _value(value, status):
    return value if value is not None else _status_text(status)