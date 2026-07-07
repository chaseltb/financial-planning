"""Business Planning page."""
import copy

import dash
from dash import html, dcc, callback, callback_context, Input, Output, State, ALL, no_update
import dash_bootstrap_components as dbc

from planner.components.charts import create_business_trend
from planner.engines.runner import run_all_engines
from planner.engines.forecast import DEFAULT_SEED
from planner.data_manager import save_project_state

dash.register_page(__name__, path="/business", title="Business Planning")


def layout():
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                        html.Div(
                            [
                                html.H4("Entity Choice & Growth Settings", className="mb-4"),
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "Business Entity Type"],
                                    id="label-entity-type"
                                ),
                                dcc.Dropdown(
                                    id={"type": "business-input", "field": "entity_type"},
                                    options=[
                                        {"label": "Sole Proprietorship",  "value": "Sole Proprietorship"},
                                        {"label": "Single-member LLC",    "value": "Single-member LLC"},
                                        {"label": "Multi-member LLC",     "value": "Multi-member LLC"},
                                        {"label": "S Corporation",        "value": "S Corporation"},
                                        {"label": "C Corporation",        "value": "C Corporation"},
                                    ],
                                    value="Sole Proprietorship",
                                    clearable=False,
                                    className="mb-3",
                                    style={"color": "#0f172a"},
                                ),
                                dbc.Tooltip("Entity structure affects payroll requirements, self-employment taxes, and corporate rates.", target="label-entity-type"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "W-2 Owner's Salary"],
                                    id="label-owner-salary"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText("$"),
                                        dbc.Input(
                                            id={"type": "business-input", "field": "owner_salary"},
                                            type="number", min=0, step=1000, value=0
                                        ),
                                        dbc.InputGroupText("/yr"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip("Annual W-2 wages paid to the owner. S-Corps require a 'reasonable W-2 salary' under IRS rules.", target="label-owner-salary"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "Owner Profit Distributions"],
                                    id="label-distributions"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText("$"),
                                        dbc.Input(
                                            id={"type": "business-input", "field": "distributions"},
                                            type="number", min=0, step=1000, value=0
                                        ),
                                        dbc.InputGroupText("/yr"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip("Annual dividends or cash distributions to the owner, not subject to self-employment tax.", target="label-distributions"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "Quarterly Revenue Growth"],
                                    id="label-revenue-growth"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.Input(
                                            id={"type": "business-input", "field": "revenue_growth"},
                                            type="number", step=0.01, value=0.05
                                        ),
                                        dbc.InputGroupText("% / quarter"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip("Compounding quarterly growth rate applied to project revenue forward.", target="label-revenue-growth"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "Quarterly Expense Growth"],
                                    id="label-expense-growth"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.Input(
                                            id={"type": "business-input", "field": "expense_growth"},
                                            type="number", step=0.01, value=0.03
                                        ),
                                        dbc.InputGroupText("% / quarter"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip("Compounding quarterly growth rate applied to project operating expenses forward.", target="label-expense-growth"),
                            ],
                            className="glass-card mb-4",
                        ),
                        html.Div(
                            [
                                html.H4("Business Run-Rate Financials (Annualized)", className="mb-4"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "Annual Revenue"],
                                    id="label-biz-rev"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText("$"),
                                        dbc.Input(
                                            id={"type": "business-financials-input", "field": "revenue"},
                                            type="number", min=0, step=1000, value=0
                                        ),
                                        dbc.InputGroupText("/yr"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip("Total annualized gross revenue generated by the business operations.", target="label-biz-rev"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "Annual COGS"],
                                    id="label-biz-cogs"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText("$"),
                                        dbc.Input(
                                            id={"type": "business-financials-input", "field": "cogs"},
                                            type="number", min=0, step=1000, value=0
                                        ),
                                        dbc.InputGroupText("/yr"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip("Annual Cost of Goods Sold (direct manufacturing, labor, or production costs).", target="label-biz-cogs"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "Annual Payroll (Non-Owner staff)"],
                                    id="label-biz-pay"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText("$"),
                                        dbc.Input(
                                            id={"type": "business-financials-input", "field": "payroll"},
                                            type="number", min=0, step=1000, value=0
                                        ),
                                        dbc.InputGroupText("/yr"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip("Annual gross wages and payroll tax paid to non-owner employees.", target="label-biz-pay"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "Annual Operating Expenses"],
                                    id="label-biz-exp"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText("$"),
                                        dbc.Input(
                                            id={"type": "business-financials-input", "field": "expenses"},
                                            type="number", min=0, step=1000, value=0
                                        ),
                                        dbc.InputGroupText("/yr"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip("Annual overhead expenses (rent, utilities, software, marketing, insurance, legal).", target="label-biz-exp"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "Annual Capital Expenditures"],
                                    id="label-biz-capex"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText("$"),
                                        dbc.Input(
                                            id={"type": "business-financials-input", "field": "capex"},
                                            type="number", min=0, step=1000, value=0
                                        ),
                                        dbc.InputGroupText("/yr"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip("Annual investments in fixed assets like machinery, real estate, or vehicles.", target="label-biz-capex"),
                            ],
                            className="glass-card mb-4",
                        ),
                        ],
                        lg=4,
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H4(
                                        [html.I(className="bi bi-calculator me-2 text-primary"), "Business Operating Summary"],
                                        className="mb-3"
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col([html.Div("EBITDA", className="text-muted", style={"fontSize": "0.85rem"}),
                                                     html.H3(id="biz-ebitda-val", style={"color": "var(--accent-emerald)", "fontWeight": "bold"})], width=4),
                                            dbc.Col([html.Div("Net Income", className="text-muted", style={"fontSize": "0.85rem"}),
                                                     html.H3(id="biz-netincome-val", style={"color": "var(--accent-blue)", "fontWeight": "bold"})], width=4),
                                            dbc.Col([html.Div("Operating Margin", className="text-muted", style={"fontSize": "0.85rem"}),
                                                     html.H3(id="biz-margin-val", style={"fontWeight": "bold"})], width=4),
                                        ],
                                        className="mb-4",
                                    ),
                                ],
                                className="glass-card mb-4",
                            ),
                            html.Div(
                                [
                                    html.H4(
                                        [html.I(className="bi bi-graph-up-arrow me-2 text-success"), "Operating Trends"],
                                        className="mb-3"
                                    ),
                                    dcc.Graph(id="business-forecast-trend-chart")
                                ],
                                className="glass-card mb-4",
                            ),
                        ],
                        lg=8,
                    ),
                ]
            ),
        ],
        fluid=True,
    )


@callback(
    Output({"type": "business-input", "field": "entity_type"},    "value"),
    Output({"type": "business-input", "field": "owner_salary"},   "value"),
    Output({"type": "business-input", "field": "distributions"},  "value"),
    Output({"type": "business-input", "field": "revenue_growth"}, "value"),
    Output({"type": "business-input", "field": "expense_growth"}, "value"),
    Output("biz-ebitda-val",    "children"),
    Output("biz-netincome-val", "children"),
    Output("biz-margin-val",    "children"),
    Output("business-forecast-trend-chart", "figure"),
    Input("project-state-store", "data"),
    prevent_initial_call=False,
)
def populate_business_page(state):
    if state is None:
        return [no_update] * 9

    r = run_all_engines(state)
    b = state.get("business", {})
    annual_ebitda = r["ebitda_q"] * 4.0
    annual_ni = r["annual_net_biz_income"]
    margin = (r["ebitda_q"] / r["revenue_q"] * 100) if r["revenue_q"] > 0 else 0.0

    return (
        b.get("entity_type", "Sole Proprietorship"),
        b.get("owner_salary", 0),
        b.get("distributions", 0),
        b.get("revenue_growth", 0.05),
        b.get("expense_growth", 0.03),
        f"${annual_ebitda:,.0f}",
        f"${annual_ni:,.0f}",
        f"{margin:.1f}%",
        create_business_trend(r["forecast_df"]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Callback: Persist edits from this page's business inputs
# ─────────────────────────────────────────────────────────────────────────────
@callback(
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input({"type": "business-input", "field": ALL}, "value"),
    State({"type": "business-input", "field": ALL}, "id"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    prevent_initial_call=True,
)
def persist_business_edits(biz_vals, biz_ids, current_state, active_scenario):
    if current_state is None:
        return no_update, no_update

    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update

    new_state = copy.deepcopy(current_state)
    for bid, val in zip(biz_ids, biz_vals):
        if val is not None:
            field = bid["field"]
            if field in ["owner_salary", "distributions"]:
                try:
                    val = max(0.0, float(val or 0.0))
                except ValueError:
                    val = 0.0
            elif field in ["revenue_growth", "expense_growth"]:
                try:
                    val = max(-1.0, min(5.0, float(val or 0.0)))
                except ValueError:
                    val = 0.0
            new_state["business"][field] = val

    try:
        save_project_state(new_state, active_scenario)
        label = "● Saved"
    except Exception as e:
        label = f"⚠ {e}"

    return new_state, label


# ─────────────────────────────────────────────────────────────────────────────
# Callback: Populate this page's revenue/expense inputs from the latest
#           historical forecast quarter (annualized)
# ─────────────────────────────────────────────────────────────────────────────
@callback(
    Output({"type": "business-financials-input", "field": "revenue"},  "value"),
    Output({"type": "business-financials-input", "field": "cogs"},     "value"),
    Output({"type": "business-financials-input", "field": "payroll"},  "value"),
    Output({"type": "business-financials-input", "field": "expenses"}, "value"),
    Output({"type": "business-financials-input", "field": "capex"},    "value"),
    Input("project-state-store", "data"),
    prevent_initial_call=False,
)
def populate_business_financials(state):
    if state is None:
        return [no_update] * 5

    forecast = state.get("forecast", [])
    last = forecast[-1] if forecast else DEFAULT_SEED

    return (
        float(last.get("Revenue", 0) or 0) * 4,
        float(last.get("COGS", 0) or 0) * 4,
        float(last.get("Payroll", 0) or 0) * 4,
        float(last.get("Expenses", 0) or 0) * 4,
        float(last.get("Capital expenditures", 0) or 0) * 4,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Callback: Persist edits from this page's revenue/expense inputs into the
#           latest historical forecast quarter
# ─────────────────────────────────────────────────────────────────────────────
@callback(
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input({"type": "business-financials-input", "field": ALL}, "value"),
    State({"type": "business-financials-input", "field": ALL}, "id"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    prevent_initial_call=True,
)
def persist_business_financials(vals, ids, current_state, active_scenario):
    if current_state is None:
        return no_update, no_update

    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update

    field_map = {fid["field"]: val for fid, val in zip(ids, vals) if val is not None}
    if not field_map:
        return no_update, no_update

    new_state = copy.deepcopy(current_state)
    forecast = new_state.get("forecast", [])
    if not forecast:
        forecast = [dict(DEFAULT_SEED)]
    last = dict(forecast[-1])

    col_by_field = {
        "revenue": "Revenue", "cogs": "COGS", "payroll": "Payroll",
        "expenses": "Expenses", "capex": "Capital expenditures",
    }
    for field, col in col_by_field.items():
        if field in field_map:
            try:
                val = max(0.0, float(field_map[field] or 0.0))
            except ValueError:
                val = 0.0
            last[col] = val / 4.0

    revenue = float(last.get("Revenue", 0) or 0)
    cogs = float(last.get("COGS", 0) or 0)
    payroll = float(last.get("Payroll", 0) or 0)
    expenses = float(last.get("Expenses", 0) or 0)
    ebitda = revenue - cogs - payroll - expenses
    last["EBITDA"] = ebitda

    ebitda_mult = float(new_state.get("assumptions", {}).get("valuation_multiples", {}).get("ebitda", 6.0))
    last["Business value"] = max(0.0, ebitda * 4.0 * ebitda_mult)

    forecast[-1] = last
    new_state["forecast"] = forecast

    try:
        save_project_state(new_state, active_scenario)
        label = "● Saved"
    except Exception as e:
        label = f"⚠ {e}"

    return new_state, label
