"""Main Dash application — entry point, layout, and globally-persistent callbacks."""
import dash
from dash import html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc

from planner.data_manager import load_project_state, get_scenarios_list
from planner.config import BASELINE_DISPLAY_NAME
from planner.components.sidebar import render_sidebar
from planner.components.header import render_header

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.SLATE, 
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css"
    ],
    # Some page tables are built inside callbacks rather than the initial layout.
    suppress_callback_exceptions=True,
    update_title=None,
)
app.title = "Personal & Business Financial Planner"

# All persistent IDs live here, not in individual pages.
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="project-state-store", storage_type="session"),
        dcc.Store(id="active-scenario-store", data="Baseline", storage_type="session"),
        dcc.Store(id="explain-target-store", data="combined_tax", storage_type="session"),
        dcc.Store(id="forecast-horizon-store", data=8, storage_type="session"),
        dcc.Store(id="sensitivity-method-store", data="EBITDA Multiple", storage_type="session"),
        dcc.Store(id="sensitivity-range-store", data=0.20, storage_type="session"),
        # Theme/autosave prefs persist in the browser, not the JSON backend, since they're device-local.
        dcc.Store(id="theme-store", data="dark", storage_type="local"),
        dcc.Store(id="autosave-enabled-store", data=True, storage_type="local"),
        dcc.Store(id="mobile-nav-open-store", data=False),
        html.Div(id="theme-applier", style={"display": "none"}),

        render_sidebar(),
        # Sibling of the sidebar, not nested: the sidebar's CSS `transform` creates a
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

# Applies the theme to <html data-theme="..."> so CSS variable overrides in assets/styles.css take effect.
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

# Reads current state rather than toggling a click count, since a plain odd/even
# count breaks once a second closing trigger (nav or backdrop) is mixed in.
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



# Combines inputs/outputs for active-scenario-store and header-scenario-dropdown to avoid a dependency cycle.
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
    options = [
        {"label": BASELINE_DISPLAY_NAME if s == "Baseline" else s, "value": s}
        for s in scenario_list
    ]

    state = load_project_state(current_scenario)

    return state, options, current_scenario, current_scenario



if __name__ == "__main__":
    app.run(debug=True, port=8050)
