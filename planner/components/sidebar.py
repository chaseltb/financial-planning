from dash import html
import dash_bootstrap_components as dbc

def render_sidebar():
    return html.Div(
        [
            html.Div("NC Dash Plan", className="sidebar-brand"),
            html.Hr(style={"borderColor": "rgba(255,255,255,0.08)", "margin": "0 0 20px 0"}),
            dbc.Nav(
                [
                    dbc.NavLink(
                        [html.I(className="bi bi-speedometer2 me-2"), "Overview"],
                        href="/", active="exact", className="sidebar-nav-link"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-person-fill me-2"), "Personal Finances"],
                        href="/personal", active="exact", className="sidebar-nav-link"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-briefcase-fill me-2"), "Business Planning"],
                        href="/business", active="exact", className="sidebar-nav-link"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-calculator-fill me-2"), "Taxes & Tracing"],
                        href="/taxes", active="exact", className="sidebar-nav-link"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-bank2 me-2"), "Net Worth Tracking"],
                        href="/networth", active="exact", className="sidebar-nav-link"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-cash-coin me-2"), "Business Valuation"],
                        href="/valuation", active="exact", className="sidebar-nav-link"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-grid-3x3-gap-fill me-2"), "Forecast Spreadsheet"],
                        href="/forecast", active="exact", className="sidebar-nav-link"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-sliders2 me-2"), "Scenario Manager"],
                        href="/scenarios", active="exact", className="sidebar-nav-link"
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-gear-fill me-2"), "Settings"],
                        href="/settings", active="exact", className="sidebar-nav-link"
                    ),
                ],
                vertical=True,
                pills=True,
            ),
        ],
        className="sidebar-container",
    )
