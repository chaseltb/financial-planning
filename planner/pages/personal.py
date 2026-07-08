"""Personal Finances page — editable income/expense/asset/liability tables."""
import copy

import dash
from dash import html, dcc, callback, callback_context, Input, Output, State, ALL, no_update
import dash_bootstrap_components as dbc
import pandas as pd

from planner.components.editable_table import render_editable_table
from planner.data_manager import save_project_state

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
                                dbc.Tooltip("Individual employee 401(k) contribution limit for 2026 is $23,500 (plus $7,500 catch-up if 50+).", target="label-401k"),
                                
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
                                dbc.Tooltip("Traditional/Roth IRA contribution limit for 2026 is $7,000 (plus $1,000 catch-up if 50+).", target="label-ira"),
                                
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
        ],
        fluid=True,
    )


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
    Input("project-state-store", "data"),
    prevent_initial_call=False,
)
def populate_personal_page(state):
    if state is None:
        return [no_update] * 9

    p = state.get("profile", {})
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
    )


# ─────────────────────────────────────────────────────────────────────────────
# Callback: Persist edits from this page's profile inputs & tables
# ─────────────────────────────────────────────────────────────────────────────
@callback(
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input({"type": "profile-input", "field": ALL}, "value"),
    Input("income-table",      "data"),
    Input("expenses-table",    "data"),
    Input("assets-table",      "data"),
    Input("liabilities-table", "data"),
    State({"type": "profile-input", "field": ALL}, "id"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    prevent_initial_call=True,
)
def persist_personal_edits(
    profile_vals, inc_data, exp_data, ast_data, liab_data,
    profile_ids, current_state, active_scenario,
):
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
    elif "income-table" in triggered:
        # inc_data is None when the table is in empty-state (no DataTable rendered).
        # In that case, data is already empty — only persist if we have actual data.
        if inc_data is not None:
            new_state["income"] = [r for r in inc_data if r]
        else:
            return no_update, no_update
    elif "expenses-table" in triggered:
        if exp_data is not None:
            new_state["expenses"] = [r for r in exp_data if r]
        else:
            return no_update, no_update
    elif "assets-table" in triggered:
        if ast_data is not None:
            new_state["assets"] = [r for r in ast_data if r]
        else:
            return no_update, no_update
    elif "liabilities-table" in triggered:
        if liab_data is not None:
            new_state["liabilities"] = [r for r in liab_data if r]
        else:
            return no_update, no_update
    else:
        return no_update, no_update

    try:
        save_project_state(new_state, active_scenario)
        label = "● Saved"
    except Exception as e:
        label = f"⚠ {e}"

    return new_state, label


# ─────────────────────────────────────────────────────────────────────────────
# Callbacks: Add rows to this page's editable tables
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# Add-row callbacks: output to project-state-store so the container re-renders
# with a real DataTable that the user can then edit.
# ─────────────────────────────────────────────────────────────────────────────
@callback(
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input("income-table-add-btn", "n_clicks"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    prevent_initial_call=True,
)
def add_income_row(n, state, active_scenario):
    if not n or state is None:
        return no_update, no_update
    new_state = copy.deepcopy(state)
    rows = list(new_state.get("income", []))
    rows.append({"category": "Other", "description": "New Income Source", "amount": 0.0})
    new_state["income"] = rows
    save_project_state(new_state, active_scenario)
    return new_state, "● Saved"


@callback(
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input("expenses-table-add-btn", "n_clicks"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    prevent_initial_call=True,
)
def add_expense_row(n, state, active_scenario):
    if not n or state is None:
        return no_update, no_update
    new_state = copy.deepcopy(state)
    rows = list(new_state.get("expenses", []))
    rows.append({"category": "Other", "description": "New Expense", "amount": 0.0})
    new_state["expenses"] = rows
    save_project_state(new_state, active_scenario)
    return new_state, "● Saved"


@callback(
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input("assets-table-add-btn", "n_clicks"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    prevent_initial_call=True,
)
def add_asset_row(n, state, active_scenario):
    if not n or state is None:
        return no_update, no_update
    new_state = copy.deepcopy(state)
    rows = list(new_state.get("assets", []))
    rows.append({"category": "Investment", "description": "New Asset", "value": 0.0, "growth_rate": 0.05})
    new_state["assets"] = rows
    save_project_state(new_state, active_scenario)
    return new_state, "● Saved"


@callback(
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input("liabilities-table-add-btn", "n_clicks"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    prevent_initial_call=True,
)
def add_liability_row(n, state, active_scenario):
    if not n or state is None:
        return no_update, no_update
    new_state = copy.deepcopy(state)
    rows = list(new_state.get("liabilities", []))
    rows.append({"category": "Debt", "description": "New Liability",
                 "value": 0.0, "interest_rate": 0.05, "monthly_payment": 0.0})
    new_state["liabilities"] = rows
    save_project_state(new_state, active_scenario)
    return new_state, "● Saved"
