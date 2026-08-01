from dash import html
import dash_bootstrap_components as dbc


def _nav_link(icon_class, label, href):
    # The label is its own element (not a bare string) so the collapsed
    # (icon-only) state can hide just the text via CSS, without touching the
    # icon — keeping every icon's position identical whether the sidebar is
    # expanded or collapsed.
    return dbc.NavLink(
        [
            html.I(className=f"bi {icon_class} sidebar-nav-icon"),
            html.Span(label, className="sidebar-nav-label"),
        ],
        href=href, active="exact", className="sidebar-nav-link",
    )


def render_sidebar():
    return html.Div(
        [
            html.Div(
                [
                    # Placeholder brand mark — swap for a real logo later.
                    html.I(className="bi bi-bar-chart-steps sidebar-logo-icon"),
                    html.Button(
                        html.I(className="bi bi-layout-sidebar"),
                        id="sidebar-collapse-toggle",
                        n_clicks=0,
                        className="sidebar-collapse-btn",
                        title="Collapse sidebar",
                    ),
                ],
                className="sidebar-brand-row",
            ),
            html.Hr(className="sidebar-divider"),
            dbc.Nav(
                [
                    _nav_link("bi-speedometer2", "Overview", "/"),
                    _nav_link("bi-person-fill", "Personal Finances", "/personal"),
                    _nav_link("bi-briefcase-fill", "Business Planning", "/business"),
                    _nav_link("bi-calculator-fill", "Tax Planning", "/taxes"),
                    _nav_link("bi-bank2", "Net Worth Tracking", "/networth"),
                    _nav_link("bi-cash-coin", "Business Valuation", "/valuation"),
                    _nav_link("bi-grid-3x3-gap-fill", "Forecast Spreadsheet", "/forecast"),
                    _nav_link("bi-sliders2", "Scenario Manager", "/scenarios"),
                    _nav_link("bi-gear-fill", "Settings", "/settings"),
                ],
                vertical=True,
                pills=True,
            ),
        ],
        id="app-sidebar",
        className="sidebar-container",
        n_clicks=0,
    )
