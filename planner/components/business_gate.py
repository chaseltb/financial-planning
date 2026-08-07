"""Shared guard for pages that only make sense when Business Mode is on.

Hiding the sidebar link isn't enough by itself — the route is still reachable
by a direct URL or a bookmark. Each business-only page wraps its real content
in a container and calls register_business_gate(content_id) once at module
level; when business-mode-store is off, the content is swapped for a notice
instead (not deleted — no calculation or state is affected, so turning
Business Mode back on immediately restores the page).
"""
from dash import html, callback, Input, Output

_NOTICE_ID_SUFFIX = "-business-gate-notice"


def render_business_gate(content_id: str, page_label: str):
    """Returns (notice_div, content_wrapper_start) — call once in a page's
    layout(): put the notice first, then wrap the page's real content in a
    html.Div(id=content_id, children=[...]).
    """
    notice = html.Div(
        [
            html.I(className="bi bi-toggle-off display-4 text-muted mb-3 d-block"),
            html.P("Business Mode is turned off.", className="text-muted mb-1",
                   style={"fontSize": "1.1rem", "fontWeight": "600"}),
            html.P(
                [f"{page_label} is a business feature, hidden while this planner is in personal-only mode. ",
                 html.A("Turn it back on in Settings", href="/settings"),
                 " to use it again — none of your business data was affected."],
                className="text-muted mb-0", style={"fontSize": "0.9rem"},
            ),
        ],
        id=f"{content_id}{_NOTICE_ID_SUFFIX}",
        className="glass-card text-center py-5 mb-4",
        style={"display": "none"},
    )
    return notice


def register_business_gate(content_id: str):
    """Registers the visibility-toggle callback for one business-only page."""
    notice_id = f"{content_id}{_NOTICE_ID_SUFFIX}"

    @callback(
        Output(content_id, "style"),
        Output(notice_id, "style"),
        Input("business-mode-store", "data"),
        prevent_initial_call=False,
    )
    def _toggle_business_gate(business_mode_enabled):
        enabled = business_mode_enabled is not False
        return (
            {} if enabled else {"display": "none"},
            {"display": "none"} if enabled else {},
        )

    return _toggle_business_gate
