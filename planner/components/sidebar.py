from dash import html
import dash_bootstrap_components as dbc

def render_sidebar():
    return html.Div(
        [
            html.Div("NC Dash Plan", className="sidebar-brand"),
            html.Hr(style={"borderColor": "rgba(255,255,255,0.08)", "margin": "0 0 20px 0"}),
            dbc.Nav(
                [
                    dbc.NavLink("Overview", href="/", active="exact", className="sidebar-nav-link"),
                    dbc.NavLink("Personal Finances", href="/personal", active="exact", className="sidebar-nav-link"),
                    dbc.NavLink("Business Planning", href="/business", active="exact", className="sidebar-nav-link"),
                    dbc.NavLink("Taxes & Tracing", href="/taxes", active="exact", className="sidebar-nav-link"),
                    dbc.NavLink("Net Worth Tracking", href="/networth", active="exact", className="sidebar-nav-link"),
                    dbc.NavLink("Business Valuation", href="/valuation", active="exact", className="sidebar-nav-link"),
                    dbc.NavLink("Forecast Spreadsheet", href="/forecast", active="exact", className="sidebar-nav-link"),
                    dbc.NavLink("Scenario Manager", href="/scenarios", active="exact", className="sidebar-nav-link"),
                    dbc.NavLink("Settings", href="/settings", active="exact", className="sidebar-nav-link"),
                ],
                vertical=True,
                pills=True,
            ),
        ],
        className="sidebar-container",
    )
