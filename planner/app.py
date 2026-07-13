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
from dash import html, dcc, Input, Output, State, callback_context
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
    # Several pages (personal, forecast) build tables like "income-table" and
    # "forecast-spreadsheet" inside a callback rather than the initial layout,
    # so callbacks that reference them must not be validated against layout at
    # startup.
    suppress_callback_exceptions=True,
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
        dcc.Store(id="mobile-nav-open-store", data=False),
        html.Div(id="theme-applier", style={"display": "none"}),

        # ── Chrome (always visible) ────────────────────────────────────────
        render_sidebar(),
        # Tap-outside-to-close overlay for the mobile nav drawer — a sibling of
        # the sidebar (not nested inside it), since the sidebar gets a CSS
        # `transform` for its slide-in animation, and that creates a new
        # containing block that would break a nested `position: fixed` child.
        html.Div(id="mobile-nav-backdrop", n_clicks=0, className="mobile-nav-backdrop"),
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

# Mobile nav drawer: the hamburger button toggles it open/closed; navigating to
# a new page or tapping the backdrop always closes it (whichever fired last
# wins, since this reads current state from the store rather than counting
# clicks — a plain odd/even click count breaks once a second closing trigger
# is mixed in).
app.clientside_callback(
    """
    function(toggleClicks, pathname, backdropClicks, isOpen) {
        const trigger = window.dash_clientside.callback_context.triggered;
        const triggeredId = trigger.length ? trigger[0].prop_id.split('.')[0] : '';
        if (triggeredId === 'mobile-nav-toggle') {
            return !isOpen;
        }
        return false;
    }
    """,
    Output("mobile-nav-open-store", "data"),
    Input("mobile-nav-toggle", "n_clicks"),
    Input("url", "pathname"),
    Input("mobile-nav-backdrop", "n_clicks"),
    State("mobile-nav-open-store", "data"),
    prevent_initial_call=True,
)

app.clientside_callback(
    """
    function(isOpen) {
        return [
            isOpen ? 'sidebar-container mobile-open' : 'sidebar-container',
            isOpen ? 'mobile-nav-backdrop visible' : 'mobile-nav-backdrop'
        ];
    }
    """,
    Output("app-sidebar", "className"),
    Output("mobile-nav-backdrop", "className"),
    Input("mobile-nav-open-store", "data"),
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
