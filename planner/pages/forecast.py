"""Forecast Spreadsheet page."""
import copy

import dash
from dash import html, dcc, callback, callback_context, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd

from planner.components.charts import apply_dark_layout
from planner.components.editable_table import render_editable_table
from planner.data_manager import load_tax_rules, save_or_mark_unsaved
from planner.config import DEFAULT_TAX_YEAR, DEFAULT_STATE
from planner.engines.forecast import run_forecast, NUMERIC_COLS

dash.register_page(__name__, path="/forecast", title="Business Financial Projection Spreadsheet")

_FC_COLS = [
    {"name": "Quarter",          "id": "Quarter",               "editable": False, "type": "text"},
    {"name": "Revenue ($)",      "id": "Revenue",               "type": "numeric"},
    {"name": "COGS ($)",         "id": "COGS",                  "type": "numeric"},
    {"name": "Payroll ($)",      "id": "Payroll",               "type": "numeric"},
    {"name": "Expenses ($)",     "id": "Expenses",              "type": "numeric"},
    {"name": "CapEx ($)",        "id": "Capital expenditures",  "type": "numeric"},
    {"name": "Owner Salary ($)", "id": "Owner salary",          "type": "numeric"},
    {"name": "Distributions ($)","id": "Distributions",         "type": "numeric"},
    {"name": "Tax Est. ($)",     "id": "Tax estimate",          "type": "numeric"},
    {"name": "Cash ($)",         "id": "Cash",                  "type": "numeric"},
    {"name": "EBITDA ($)",       "id": "EBITDA",                "type": "numeric"},
    {"name": "Biz Value ($)",    "id": "Business value",        "type": "numeric"},
]


def layout():
    return dbc.Container(
        [
            dbc.Row(
                dbc.Col(
                    html.Div(
                        [
                            html.H4(
                                [html.I(className="bi bi-graph-up-arrow me-2 text-info"), "Forecast Settings"],
                                className="mb-3"
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label(
                                                [html.I(className="bi bi-calendar-range me-1 text-muted"), "Forecast Horizon"],
                                                id="label-forecast-horizon",
                                                className="form-label",
                                            ),
                                            dcc.Dropdown(
                                                id="forecast-horizon-dropdown",
                                                options=[
                                                    {"label": "4 Quarters (1 Year)",  "value": 4},
                                                    {"label": "8 Quarters (2 Years)", "value": 8},
                                                    {"label": "12 Quarters (3 Years)","value": 12},
                                                    {"label": "16 Quarters (4 Years)","value": 16},
                                                    {"label": "20 Quarters (5 Years)","value": 20},
                                                    {"label": "40 Quarters (10 Years)","value": 40},
                                                ],
                                                value=8,
                                                clearable=False,
                                                style={"color": "#0f172a"},
                                            ),
                                            dbc.Tooltip(
                                                "Choose how many quarters to project forward. Projections grow from your current business profile using your quarterly growth rate assumption.",
                                                target="label-forecast-horizon",
                                            ),
                                        ],
                                        md=5,
                                    ),
                                    dbc.Col(
                                        html.P(
                                            [
                                                html.I(className="bi bi-info-circle me-1"),
                                                "Future quarters are projected from your current business profile. "
                                                "Edit any cell to override individual quarter assumptions.",
                                            ],
                                            className="text-muted mb-0 mt-md-4",
                                            style={"fontSize": "0.85rem"},
                                        ),
                                        md=7,
                                    ),
                                ]
                            ),
                        ],
                        className="glass-card mb-4",
                    ),
                    width=12,
                )
            ),
            dbc.Row(
                dbc.Col(
                    html.Div(id="forecast-spreadsheet-container", className="mb-4"),
                    width=12,
                )
            ),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [html.H4("Revenue & Profit Projections", className="mb-3"),
                             dcc.Graph(id="forecast-chart-operating")],
                            className="glass-card mb-4",
                        ),
                        lg=6,
                    ),
                    dbc.Col(
                        html.Div(
                            [html.H4("Cash & Tax Projections", className="mb-3"),
                             dcc.Graph(id="forecast-chart-cash")],
                            className="glass-card mb-4",
                        ),
                        lg=6,
                    ),
                ]
            ),
        ],
        fluid=True,
    )


def _run_forecast(state, horizon):
    tax_year = int(state.get("assumptions", {}).get("tax_year", DEFAULT_TAX_YEAR))
    rules = load_tax_rules(tax_year, DEFAULT_STATE)
    history_df = pd.DataFrame(state.get("forecast", []))
    for col in NUMERIC_COLS:
        if col in history_df.columns:
            history_df[col] = pd.to_numeric(history_df[col], errors="coerce").fillna(0.0)
    overrides = state.get("assumptions", {}).get("forecast_overrides", {})
    return run_forecast(
        history_df=history_df,
        business_profile=state["business"],
        personal_profile=state["profile"],
        personal_income_list=state["income"],
        assumptions=state["assumptions"],
        fed_rules=rules["federal"],
        nc_rules=rules["north_carolina"],
        horizon=horizon,
        overrides=overrides,
    )


@callback(
    Output("forecast-spreadsheet-container", "children"),
    Output("forecast-chart-operating",       "figure"),
    Output("forecast-chart-cash",            "figure"),
    Input("project-state-store",      "data"),
    Input("forecast-horizon-dropdown","value"),
    prevent_initial_call=False,
)
def populate_forecast_page(state, horizon):
    if state is None:
        return no_update, no_update, no_update

    horizon = horizon or 8
    results = _run_forecast(state, horizon)
    forecast_df = results["forecast_df"]
    only_df = results["only_forecast_df"]

    spreadsheet = render_editable_table(
        "forecast-spreadsheet", forecast_df, _FC_COLS,
        add_row_btn=False,
        empty_label="quarterly records",
    )

    fig_op = go.Figure()
    fig_op.add_trace(go.Bar(x=only_df["Quarter"], y=only_df["Revenue"],
                            name="Revenue", marker_color="#3b82f6"))
    fig_op.add_trace(go.Bar(x=only_df["Quarter"], y=only_df["EBITDA"],
                            name="EBITDA", marker_color="#10b981"))
    fig_op = apply_dark_layout(fig_op, "Projected Revenue and EBITDA")

    fig_cash = go.Figure()
    fig_cash.add_trace(go.Scatter(x=only_df["Quarter"], y=only_df["Cash"],
                                  mode="lines+markers", name="Cash Balance",
                                  line={"color": "#8b5cf6", "width": 3}))
    fig_cash.add_trace(go.Bar(x=only_df["Quarter"], y=only_df["Tax estimate"],
                              name="Quarterly Tax", marker_color="rgba(239,68,68,0.4)"))
    fig_cash = apply_dark_layout(fig_cash, "Cash Balance and Quarterly Taxes")

    return spreadsheet, fig_op, fig_cash


@callback(
    Output("forecast-horizon-store", "data"),
    Input("forecast-horizon-dropdown", "value"),
    prevent_initial_call=True,
)
def update_horizon_store(val):
    return val or 8


_OVERRIDE_FIELDS = ["Revenue", "COGS", "Payroll", "Expenses",
                    "Capital expenditures", "Owner salary", "Distributions"]


@callback(
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input("forecast-spreadsheet", "data"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    State("autosave-enabled-store", "data"),
    State("forecast-horizon-dropdown", "value"),
    prevent_initial_call=True,
)
def persist_forecast_edits(forecast_data, current_state, active_scenario, autosave_enabled, horizon):
    # forecast_data is None when the table is in empty-state mode (no DataTable rendered)
    if current_state is None or forecast_data is None or not forecast_data:
        return no_update, no_update

    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update

    new_state = copy.deepcopy(current_state)
    horizon = horizon or 8

    # Historical quarters are whatever's actually stored as history, not a hardcoded
    # year — a hardcoded "2025" check would misclassify every quarter once history
    # accumulates rows in 2026+ years, and would freeze *every* still-projected
    # quarter (not just the one the user actually touched) as a permanent override
    # the moment any cell in the table was edited, since the DataTable reports the
    # full grid on every edit. That's what silently stopped revenue from carrying
    # forward: a single edit would snapshot every future quarter at its
    # already-displayed value forever, regardless of growth-rate changes afterward.
    hist_rows_by_quarter = {r.get("Quarter"): dict(r) for r in new_state.get("forecast", [])}
    hist_quarters = set(hist_rows_by_quarter.keys())

    for row in forecast_data:
        q = row.get("Quarter")
        if q in hist_quarters:
            merged = hist_rows_by_quarter[q]
            for col in NUMERIC_COLS:
                if col in row and row[col] is not None:
                    try:
                        merged[col] = float(row[col])
                    except (TypeError, ValueError):
                        pass
    new_state["forecast"] = [hist_rows_by_quarter[q] for q in sorted(hist_quarters)]

    # Recompute a clean (override-free) projection to diff the edited grid against,
    # so only cells the user actually changed become overrides — every other future
    # quarter keeps recomputing from the growth-rate assumptions.
    tax_year = int(new_state.get("assumptions", {}).get("tax_year", DEFAULT_TAX_YEAR))
    rules = load_tax_rules(tax_year, DEFAULT_STATE)
    history_df = pd.DataFrame(new_state["forecast"])
    for col in NUMERIC_COLS:
        if col in history_df.columns:
            history_df[col] = pd.to_numeric(history_df[col], errors="coerce").fillna(0.0)

    baseline = run_forecast(
        history_df=history_df,
        business_profile=new_state["business"],
        personal_profile=new_state["profile"],
        personal_income_list=new_state["income"],
        assumptions=new_state["assumptions"],
        fed_rules=rules["federal"],
        nc_rules=rules["north_carolina"],
        horizon=horizon,
        overrides={},
    )
    baseline_by_quarter = {r["Quarter"]: r for r in baseline["only_forecast_df"].to_dict("records")}

    overrides = {}
    for row in forecast_data:
        q = row.get("Quarter")
        if q in hist_quarters:
            continue
        baseline_row = baseline_by_quarter.get(q)
        if baseline_row is None:
            continue
        q_overrides = {}
        for field in _OVERRIDE_FIELDS:
            try:
                edited_val = float(row.get(field, 0) or 0)
            except (TypeError, ValueError):
                continue
            if abs(edited_val - float(baseline_row.get(field, 0.0))) > 0.005:
                q_overrides[field] = edited_val
        if q_overrides:
            overrides[q] = q_overrides
    new_state["assumptions"]["forecast_overrides"] = overrides

    label = save_or_mark_unsaved(new_state, active_scenario, autosave_enabled)
    return new_state, label
