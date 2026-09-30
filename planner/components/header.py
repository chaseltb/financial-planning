"""Persistent app header, rendered once in app.layout (not per-page)."""
from dash import html
import dash_bootstrap_components as dbc

from planner.config import BASELINE_DISPLAY_NAME


def render_header():
    """Returns the top-of-page header bar; placed once in app.layout so its IDs always exist."""
    return html.Header(
        [
            html.Div(
                [
                    html.Button(
                        html.I(className="bi bi-list", **{"aria-hidden": "true"}),
                        id="mobile-nav-toggle",
                        className="btn btn-secondary mobile-nav-toggle-btn",
                        n_clicks=0,
                        title="Open navigation menu",
                        **{"aria-label": "Open navigation menu"},
                    ),
                    html.Div(
                        [
                            html.H1(
                                id="page-title",
                                children="Financial Overview",
                                className="mb-0",
                            ),
                            html.P(
                                "Personal + Business Financial Planner",
                                className="text-muted mb-0",
                                style={"fontSize": "0.9rem"},
                            ),
                        ]
                    ),
                ],
                style={"display": "flex", "alignItems": "center", "gap": "12px"},
            ),
            html.Div(
                [
                    html.Label("Scenario:", htmlFor="header-scenario-dropdown", className="text-muted mb-0",
                               style={"fontSize": "0.9rem"}),
                    dbc.Select(
                        id="header-scenario-dropdown",
                        options=[{"label": BASELINE_DISPLAY_NAME, "value": "Baseline"}],
                        value="Baseline",
                        style={"width": "260px", "display": "inline-block"},
                    ),
                    # role="status" so screen readers announce save results.
                    html.Span(
                        [html.I(className="bi bi-cloud-check-fill me-1", **{"aria-hidden": "true"}), "Auto-saved"],
                        id="save-status-indicator",
                        className="save-status",
                        role="status",
                        style={"fontSize": "0.85rem", "color": "var(--accent-emerald)"},
                    ),
                ],
                className="header-controls",
            ),
        ],
        className="app-header",
    )
