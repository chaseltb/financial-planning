"""
NC Personal & Business Financial Planning Platform
Main Dash application — entry point, layout, and globally-persistent callbacks.

Architecture:
  - app.layout holds ALL persistent DOM nodes (stores, sidebar, header).
  - Page layouts contain only page-specific DOM.
  - app.py callbacks only reference IDs that are ALWAYS in the layout.
  - Page-specific callbacks live inside each page file using @dash.callback.
"""
import dash
from dash import html, dcc, Input, Output, callback_context
import dash_bootstrap_components as dbc

from planner.data_manager import load_project_state, get_scenarios_list
from planner.components.sidebar import render_sidebar
from planner.components.header import render_header

# ─────────────────────────────────────────────────────────────────────────────
# App init
# ─────────────────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.SLATE, 
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css"
    ],
    suppress_callback_exceptions=False,
    update_title=None,
)
app.title = "Personal & Business Financial Planner"

# ─────────────────────────────────────────────────────────────────────────────
# Root layout — ALL persistent IDs live here, not in pages
# ─────────────────────────────────────────────────────────────────────────────
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        # ── Persistent session stores ──────────────────────────────────────
        dcc.Store(id="project-state-store", storage_type="session"),
        dcc.Store(id="active-scenario-store", data="Baseline", storage_type="session"),
        dcc.Store(id="explain-target-store", data="combined_tax", storage_type="session"),
        # Settings stores consumed by page callbacks
        dcc.Store(id="forecast-horizon-store", data=8, storage_type="session"),
        dcc.Store(id="sensitivity-method-store", data="EBITDA Multiple", storage_type="session"),
        dcc.Store(id="sensitivity-range-store", data=0.20, storage_type="session"),
        # Display/behavior preferences set on the Settings page — persisted in the
        # browser (not the JSON backend) since they're this device's UI prefs.
        dcc.Store(id="theme-store", data="dark", storage_type="local"),
        dcc.Store(id="autosave-enabled-store", data=True, storage_type="local"),
        html.Div(id="theme-applier", style={"display": "none"}),

        # ── Chrome (always visible) ────────────────────────────────────────
        render_sidebar(),
        html.Div(
            [
                render_header(),          # header-scenario-dropdown, save-status-indicator
                dash.page_container,      # page content swapped here on navigation
            ],
            className="main-content",
        ),
    ]
)

# Applies the chosen theme to <html data-theme="..."> so CSS variable overrides
# in assets/styles.css take effect immediately, including on first load.
app.clientside_callback(
    """
    function(theme) {
        document.documentElement.setAttribute('data-theme', theme || 'dark');
        return '';
    }
    """,
    Output("theme-applier", "data-theme"),
    Input("theme-store", "data"),
)


# ─────────────────────────────────────────────────────────────────────────────
# Callback: Update page title dynamically
# ─────────────────────────────────────────────────────────────────────────────
@app.callback(
    Output("page-title", "children"),
    Input("url", "pathname")
)
def update_page_title(pathname):
    titles = {
        "/": "Financial Overview",
        "/personal": "Personal Finances",
        "/business": "Business Planning",
        "/taxes": "Tax Planning & Auditing",
        "/networth": "Net Worth Tracking",
        "/valuation": "Business Valuation",
        "/forecast": "Financial Projections & Spreadsheet",
        "/scenarios": "Scenario Manager",
        "/settings": "Settings & Backup"
    }
    return titles.get(pathname, "Financial Planner")



# ─────────────────────────────────────────────────────────────────────────────
# Callback: Synchronize scenario state and dropdown
#           Combines inputs and outputs for active-scenario-store and header-scenario-dropdown
#           to prevent any static dependency cycles.
# ─────────────────────────────────────────────────────────────────────────────
@app.callback(
    Output("project-state-store", "data"),
    Output("header-scenario-dropdown", "options"),
    Output("header-scenario-dropdown", "value"),
    Output("active-scenario-store", "data"),
    Input("header-scenario-dropdown", "value"),
    Input("active-scenario-store", "data"),
    prevent_initial_call=False,
)
def sync_scenario_and_state(dropdown_val, active_scenario):
    ctx = callback_context
    triggered_id = ctx.triggered[0]["prop_id"] if ctx.triggered else ""

    # Defaults
    active_scenario = active_scenario or "Baseline"
    dropdown_val = dropdown_val or "Baseline"

    current_scenario = active_scenario
    if "header-scenario-dropdown" in triggered_id:
        current_scenario = dropdown_val
    elif "active-scenario-store" in triggered_id:
        current_scenario = active_scenario

    scenario_list = get_scenarios_list()
    options = [{"label": s, "value": s} for s in scenario_list]

    state = load_project_state(current_scenario)

    return state, options, current_scenario, current_scenario



# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=8050)
