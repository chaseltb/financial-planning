"""
Persistent app header — rendered once in app.layout (not per-page).
Contains the scenario dropdown and save status indicator.
"""
from dash import html, dcc
import dash_bootstrap_components as dbc


def render_header():
    """
    Returns the top-of-page header bar.
    This is placed ONCE in app.layout so its IDs always exist in the DOM.
    """
    return html.Div(
        [
            html.Div(
                [
                    dbc.Button(
                        html.I(className="bi bi-list"),
                        id="mobile-nav-toggle",
                        className="mobile-nav-toggle-btn",
                        color="secondary",
                        n_clicks=0,
                    ),
                    html.Div(
                        [
                            html.H2(
                                id="page-title",
                                children="Financial Overview",
                                className="mb-0",
                                style={"color": "var(--text-primary)"},
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
                    html.Span("Scenario:", className="text-muted me-2", style={"fontSize": "0.9rem"}),
                    dcc.Dropdown(
                        id="header-scenario-dropdown",
                        options=[{"label": "Baseline", "value": "Baseline"}],
                        value="Baseline",
                        clearable=False,
                        style={"width": "180px", "display": "inline-block", "color": "#0f172a"},
                    ),
                    html.Span(
                        [html.I(className="bi bi-cloud-check-fill me-1"), "Auto-saved"],
                        id="save-status-indicator",
                        className="ms-3",
                        style={"fontSize": "0.85rem", "color": "var(--accent-emerald)"},
                    ),
                ],
                style={"display": "flex", "alignItems": "center"},
            ),
        ],
        className="app-header",
    )
