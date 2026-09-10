"""Personal Finances page — editable income/expense/asset/liability tables."""
import copy

import dash
from dash import html, dcc, callback, callback_context, Input, Output, State, ALL, no_update
import dash_bootstrap_components as dbc
import pandas as pd

from planner.components.editable_table import render_editable_table
from planner.components.citations import render_citation_panel
from planner.components.charts import create_allocation_chart
from planner.data_manager import save_or_mark_unsaved
from planner.engines.runner import run_all_engines
from planner.engines.allocation import calculate_budget_allocation

_DEFAULT_BUDGET_ALLOCATION = {"Savings": 34.0, "Liability Paydown": 33.0, "Taxable Brokerage": 33.0}

dash.register_page(__name__, path="/personal", title="Personal Finances")

_INCOME_COLS = [
    {"name": "Category",       "id": "category"},
    {"name": "Description",    "id": "description"},
    {"name": "Amount ($/yr)",  "id": "amount", "type": "numeric"},
]
_EXPENSE_COLS = [
    {"name": "Category",       "id": "category"},
    {"name": "Description",    "id": "description"},
    {"name": "Amount ($/yr)",  "id": "amount", "type": "numeric"},
]
_ASSET_COLS = [
    {"name": "Category",           "id": "category"},
    {"name": "Description",        "id": "description"},
    {"name": "Value ($)",          "id": "value",       "type": "numeric"},
    {"name": "Annual Growth Rate", "id": "growth_rate", "type": "numeric"},
]
_LIAB_COLS = [
    {"name": "Category",               "id": "category"},
    {"name": "Description",            "id": "description"},
    {"name": "Outstanding Balance ($)", "id": "value",           "type": "numeric"},
    {"name": "Interest Rate (APR)",    "id": "interest_rate",   "type": "numeric"},
    {"name": "Monthly Payment ($)",    "id": "monthly_payment", "type": "numeric"},
]


def layout():
    return dbc.Container(
        [
            render_citation_panel(),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.H4("Tax Filing & Retirement Savings", className="mb-4"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "Filing Status"],
                                    id="label-filing"
                                ),
                                dcc.Dropdown(
                                    id={"type": "profile-input", "field": "filing_status"},
                                    options=[
                                        {"label": "Single",                   "value": "single"},
                                        {"label": "Married Filing Jointly",   "value": "married"},
                                    ],
                                    value="single",
                                    clearable=False,
                                    className="mb-3",
                                    style={"color": "#0f172a"},
                                ),
                                dbc.Tooltip("Filing status affects federal & state progressive tax brackets and standard deductions.", target="label-filing"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "401(k) Contribution"],
                                    id="label-401k"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText("$"),
                                        dbc.Input(
                                            id={"type": "profile-input", "field": "retirement_401k"},
                                            type="number", debounce=True, min=0, max=100000, step=1, value=0
                                        ),
                                        dbc.InputGroupText("/yr"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip(
                                    "Individual employee 401(k) contribution limit for 2026 is $23,500 (plus $7,500 "
                                    "catch-up if 50+). The default here ($2,700/yr) is 7% of the median NC salary, "
                                    "the typical employee contribution rate reported by Fidelity (2024).",
                                    target="label-401k",
                                ),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "IRA Contribution"],
                                    id="label-ira"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText("$"),
                                        dbc.Input(
                                            id={"type": "profile-input", "field": "retirement_ira"},
                                            type="number", debounce=True, min=0, max=50000, step=1, value=0
                                        ),
                                        dbc.InputGroupText("/yr"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip(
                                    "Traditional/Roth IRA contribution limit for 2026 is $7,000 (plus $1,000 "
                                    "catch-up if 50+). The default here ($2,000/yr) is a modest planning assumption, "
                                    "not from a specific cited source.",
                                    target="label-ira",
                                ),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "HSA Contribution"],
                                    id="label-hsa"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText("$"),
                                        dbc.Input(
                                            id={"type": "profile-input", "field": "retirement_hsa"},
                                            type="number", debounce=True, min=0, max=20000, step=1, value=0
                                        ),
                                        dbc.InputGroupText("/yr"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip("HSA 2026 limits: $4,300 for individuals, $8,550 for family coverage.", target="label-hsa"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "Solo 401(k) / SEP IRA"],
                                    id="label-solo"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText("$"),
                                        dbc.Input(
                                            id={"type": "profile-input", "field": "solo_401k"},
                                            type="number", debounce=True, min=0, max=150000, step=1, value=0
                                        ),
                                        dbc.InputGroupText("/yr"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip("Self-employed retirement contributions (Solo 401k profit-sharing / SEP IRA limits up to $69,000 in 2026).", target="label-solo"),
                            ],
                            className="glass-card mb-4",
                        ),
                        lg=4,
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H4(
                                        [html.I(className="bi bi-wallet2 me-2 text-primary"), "Income Streams (Annual)"],
                                        className="mb-3"
                                    ),
                                    html.Div(id="personal-income-table-container")
                                ],
                                className="glass-card mb-4",
                            ),
                            html.Div(
                                [
                                    html.H4(
                                        [html.I(className="bi bi-cart4 me-2 text-danger"), "Living Expenses (Annual)"],
                                        className="mb-3"
                                    ),
                                    html.Div(id="personal-expenses-table-container")
                                ],
                                className="glass-card mb-4",
                            ),
                        ],
                        lg=8,
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.H4(
                                    [html.I(className="bi bi-gem me-2 text-success"), "Assets"],
                                    className="mb-3"
                                ),
                                html.Div(id="personal-assets-table-container")
                            ],
                            className="glass-card mb-4",
                        ),
                        lg=6,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.H4(
                                    [html.I(className="bi bi-credit-card-2-front me-2 text-warning"), "Liabilities"],
                                    className="mb-3"
                                ),
                                html.Div(id="personal-liabilities-table-container")
                            ],
                            className="glass-card mb-4",
                        ),
                        lg=6,
                    ),
                ]
            ),
            dbc.Row(
                dbc.Col(
                    html.Div(
                        [
                            html.H4(
                                [html.I(className="bi bi-piggy-bank me-2 text-info"), "Allocate Leftover Budget"],
                                className="mb-3"
                            ),
                            html.P(
                                "After income, expenses, debt service, retirement contributions, and taxes, "
                                "split whatever cash is left over across these goals. This split feeds "
                                "forward into your Net Worth projection: Savings and Taxable Brokerage "
                                "amounts compound quarterly, and Liability Paydown pays down your "
                                "highest-interest debt first.",
                                className="text-muted mb-3", style={"fontSize": "0.9rem"},
                            ),
                            html.Div(id="budget-allocation-summary", className="mb-3"),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label("Savings (%)"),
                                            dbc.Input(
                                                id={"type": "budget-alloc-input", "field": "Savings"},
                                                type="number", min=0, max=100, step=1, debounce=True,
                                            ),
                                        ],
                                        md=4,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Label("Liability Paydown (%)"),
                                            dbc.Input(
                                                id={"type": "budget-alloc-input", "field": "Liability Paydown"},
                                                type="number", min=0, max=100, step=1, debounce=True,
                                            ),
                                        ],
                                        md=4,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Label("Taxable Brokerage (%)"),
                                            dbc.Input(
                                                id={"type": "budget-alloc-input", "field": "Taxable Brokerage"},
                                                type="number", min=0, max=100, step=1, debounce=True,
                                            ),
                                        ],
                                        md=4,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            dcc.Graph(id="budget-allocation-chart", config={"displayModeBar": False}),
                        ],
                        className="glass-card mb-4",
                    ),
                    lg=12,
                )
            ),
        ],
        fluid=True,
    )


@callback(
    Output("nc-median-citations-collapse", "is_open"),
    Input("nc-median-citations-toggle", "n_clicks"),
    State("nc-median-citations-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_citations_panel(n_clicks, is_open):
    return not is_open


@callback(
    Output("personal-income-table-container",       "children"),
    Output("personal-expenses-table-container",     "children"),
    Output("personal-assets-table-container",       "children"),
    Output("personal-liabilities-table-container",  "children"),
    Output({"type": "profile-input", "field": "filing_status"},   "value"),
    Output({"type": "profile-input", "field": "retirement_401k"}, "value"),
    Output({"type": "profile-input", "field": "retirement_ira"},  "value"),
    Output({"type": "profile-input", "field": "retirement_hsa"},  "value"),
    Output({"type": "profile-input", "field": "solo_401k"},       "value"),
    Output({"type": "budget-alloc-input", "field": "Savings"},            "value"),
    Output({"type": "budget-alloc-input", "field": "Liability Paydown"},  "value"),
    Output({"type": "budget-alloc-input", "field": "Taxable Brokerage"},  "value"),
    Input("project-state-store", "data"),
    prevent_initial_call=False,
)
def populate_personal_page(state):
    if state is None:
        return [no_update] * 12

    p = state.get("profile", {})
    allocation_pct = p.get("budget_allocation", _DEFAULT_BUDGET_ALLOCATION)
    return (
        render_editable_table("income-table",      pd.DataFrame(state.get("income",       [])), _INCOME_COLS,  empty_label="income streams"),
        render_editable_table("expenses-table",    pd.DataFrame(state.get("expenses",     [])), _EXPENSE_COLS, empty_label="living expenses"),
        render_editable_table("assets-table",      pd.DataFrame(state.get("assets",       [])), _ASSET_COLS,   empty_label="assets"),
        render_editable_table("liabilities-table", pd.DataFrame(state.get("liabilities",  [])), _LIAB_COLS,    empty_label="liabilities"),
        p.get("filing_status",  "single"),
        p.get("retirement_401k", 0),
        p.get("retirement_ira",  0),
        p.get("retirement_hsa",  0),
        p.get("solo_401k",       0),
        allocation_pct.get("Savings", _DEFAULT_BUDGET_ALLOCATION["Savings"]),
        allocation_pct.get("Liability Paydown", _DEFAULT_BUDGET_ALLOCATION["Liability Paydown"]),
        allocation_pct.get("Taxable Brokerage", _DEFAULT_BUDGET_ALLOCATION["Taxable Brokerage"]),
    )


@callback(
    Output("budget-allocation-summary", "children"),
    Output("budget-allocation-chart",   "figure"),
    Input("project-state-store", "data"),
    Input({"type": "budget-alloc-input", "field": ALL}, "value"),
    State({"type": "budget-alloc-input", "field": ALL}, "id"),
    prevent_initial_call=False,
)
def update_budget_allocation_display(state, alloc_vals, alloc_ids):
    if state is None:
        return no_update, no_update

    allocation_pct = {
        aid["field"]: float(val) if val is not None else 0.0
        for aid, val in zip(alloc_ids, alloc_vals)
    }
    if not allocation_pct or sum(allocation_pct.values()) <= 0:
        allocation_pct = dict(_DEFAULT_BUDGET_ALLOCATION)

    r = run_all_engines(state)
    net_cash_flow = r["cashflow"]["value"]
    allocation = calculate_budget_allocation(net_cash_flow, allocation_pct)

    if allocation["has_shortfall"]:
        summary = dbc.Alert(
            f"Cash flow is short by ${-net_cash_flow:,.0f}/yr — there's nothing left over to allocate. "
            "Reduce expenses or debt service, or increase income, to free up a surplus.",
            color="warning",
        )
        fig = create_allocation_chart({"No surplus available": 1}, "Budget Allocation")
    else:
        summary = dbc.Alert(
            [
                f"Net cash flow after taxes, expenses, debt service, and retirement contributions: ",
                html.Strong(f"${net_cash_flow:,.0f}/yr"),
                ". Allocated as: ",
                ", ".join(f"{k} ${v:,.0f}" for k, v in allocation["amounts"].items()),
                ".",
            ],
            color="success",
        )
        fig = create_allocation_chart(allocation["amounts"], "Budget Allocation")

    return summary, fig


@callback(
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input({"type": "profile-input", "field": ALL}, "value"),
    Input({"type": "budget-alloc-input", "field": ALL}, "value"),
    State({"type": "profile-input", "field": ALL}, "id"),
    State({"type": "budget-alloc-input", "field": ALL}, "id"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    State("autosave-enabled-store", "data"),
    prevent_initial_call=True,
)
def persist_profile_and_allocation_edits(
    profile_vals, alloc_vals, profile_ids, alloc_ids, current_state, active_scenario, autosave_enabled,
):
    # Deliberately has NO Input on income/expenses/assets/liabilities tables. Those
    # DataTable components don't exist in the layout when their list is empty (an
    # "empty state" placeholder renders instead) — a Dash callback errors out and
    # never fires at all client-side if ANY of its declared Inputs isn't currently
    # present in the DOM. Previously this callback also listed the four tables as
    # Inputs, so having e.g. zero liabilities silently blocked EVERY edit on this
    # page (profile fields, budget allocation, all of it) from ever reaching the
    # server — the save-status indicator kept showing a stale "Saved"/"Auto-saved"
    # from an earlier state, giving no sign anything was wrong. Splitting the
    # table-triggered saves into their own callbacks below isolates the blast radius
    # to just that one table.
    if current_state is None:
        return no_update, no_update

    ctx = callback_context
    triggered = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
    if not triggered:
        return no_update, no_update

    new_state = copy.deepcopy(current_state)

    if "profile-input" in triggered:
        for pid, val in zip(profile_ids, profile_vals):
            if val is not None:
                field = pid["field"]
                # Input validation: coerce numeric fields to be >= 0
                if field in ["retirement_401k", "retirement_ira", "retirement_hsa", "solo_401k"]:
                    try:
                        val = max(0.0, float(val or 0.0))
                    except ValueError:
                        val = 0.0
                new_state["profile"][field] = val
    elif "budget-alloc-input" in triggered:
        allocation_pct = dict(new_state["profile"].get("budget_allocation", _DEFAULT_BUDGET_ALLOCATION))
        for aid, val in zip(alloc_ids, alloc_vals):
            if val is not None:
                try:
                    allocation_pct[aid["field"]] = max(0.0, float(val))
                except ValueError:
                    pass
        new_state["profile"]["budget_allocation"] = allocation_pct
    else:
        return no_update, no_update

    label = save_or_mark_unsaved(new_state, active_scenario, autosave_enabled)
    return new_state, label


def _persist_table(table_key, table_data, current_state, active_scenario, autosave_enabled, percent_fields=()):
    # table_data is None when the table is in empty-state mode (no DataTable rendered).
    # In that case, data is already empty — only persist if we have actual data.
    if current_state is None or table_data is None:
        return no_update, no_update
    new_state = copy.deepcopy(current_state)
    rows = [dict(r) for r in table_data if r]
    # The table displays/edits these as whole percentage points (7 = 7%) to match
    # what a user actually types; state stores them as fractions (0.07) since every
    # engine (tax, forecast, net worth projection) expects a fraction.
    for row in rows:
        for field in percent_fields:
            if field in row and row[field] not in (None, ""):
                try:
                    row[field] = float(row[field]) / 100.0
                except (TypeError, ValueError):
                    pass
    new_state[table_key] = rows
    label = save_or_mark_unsaved(new_state, active_scenario, autosave_enabled)
    return new_state, label


@callback(
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input("income-table", "data"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    State("autosave-enabled-store", "data"),
    prevent_initial_call=True,
)
def persist_income_table_edits(inc_data, current_state, active_scenario, autosave_enabled):
    return _persist_table("income", inc_data, current_state, active_scenario, autosave_enabled)


@callback(
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input("expenses-table", "data"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    State("autosave-enabled-store", "data"),
    prevent_initial_call=True,
)
def persist_expenses_table_edits(exp_data, current_state, active_scenario, autosave_enabled):
    return _persist_table("expenses", exp_data, current_state, active_scenario, autosave_enabled)


@callback(
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input("assets-table", "data"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    State("autosave-enabled-store", "data"),
    prevent_initial_call=True,
)
def persist_assets_table_edits(ast_data, current_state, active_scenario, autosave_enabled):
    return _persist_table("assets", ast_data, current_state, active_scenario, autosave_enabled,
                           percent_fields=("growth_rate",))


@callback(
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input("liabilities-table", "data"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    State("autosave-enabled-store", "data"),
    prevent_initial_call=True,
)
def persist_liabilities_table_edits(liab_data, current_state, active_scenario, autosave_enabled):
    return _persist_table("liabilities", liab_data, current_state, active_scenario, autosave_enabled,
                           percent_fields=("interest_rate",))


@callback(
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input("income-table-add-btn", "n_clicks"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    State("autosave-enabled-store", "data"),
    prevent_initial_call=True,
)
def add_income_row(n, state, active_scenario, autosave_enabled):
    if not n or state is None:
        return no_update, no_update
    new_state = copy.deepcopy(state)
    rows = list(new_state.get("income", []))
    rows.append({"category": "Other", "description": "New Income Source", "amount": 0.0})
    new_state["income"] = rows
    label = save_or_mark_unsaved(new_state, active_scenario, autosave_enabled)
    return new_state, label


@callback(
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input("expenses-table-add-btn", "n_clicks"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    State("autosave-enabled-store", "data"),
    prevent_initial_call=True,
)
def add_expense_row(n, state, active_scenario, autosave_enabled):
    if not n or state is None:
        return no_update, no_update
    new_state = copy.deepcopy(state)
    rows = list(new_state.get("expenses", []))
    rows.append({"category": "Other", "description": "New Expense", "amount": 0.0})
    new_state["expenses"] = rows
    label = save_or_mark_unsaved(new_state, active_scenario, autosave_enabled)
    return new_state, label


@callback(
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input("assets-table-add-btn", "n_clicks"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    State("autosave-enabled-store", "data"),
    prevent_initial_call=True,
)
def add_asset_row(n, state, active_scenario, autosave_enabled):
    if not n or state is None:
        return no_update, no_update
    new_state = copy.deepcopy(state)
    rows = list(new_state.get("assets", []))
    rows.append({"category": "Investment", "description": "New Asset", "value": 0.0, "growth_rate": 0.05})
    new_state["assets"] = rows
    label = save_or_mark_unsaved(new_state, active_scenario, autosave_enabled)
    return new_state, label


@callback(
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input("liabilities-table-add-btn", "n_clicks"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    State("autosave-enabled-store", "data"),
    prevent_initial_call=True,
)
def add_liability_row(n, state, active_scenario, autosave_enabled):
    if not n or state is None:
        return no_update, no_update
    new_state = copy.deepcopy(state)
    rows = list(new_state.get("liabilities", []))
    rows.append({"category": "Debt", "description": "New Liability",
                 "value": 0.0, "interest_rate": 0.05, "monthly_payment": 0.0})
    new_state["liabilities"] = rows
    label = save_or_mark_unsaved(new_state, active_scenario, autosave_enabled)
    return new_state, label
