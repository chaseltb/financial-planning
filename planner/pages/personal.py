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
                                html.Label("Filing Status"),
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
                                html.Label("401(k) Contribution ($/yr)"),
                                dbc.Input(id={"type": "profile-input", "field": "retirement_401k"},
                                          type="number", value=0, className="mb-3"),
                                html.Label("IRA Contribution ($/yr)"),
                                dbc.Input(id={"type": "profile-input", "field": "retirement_ira"},
                                          type="number", value=0, className="mb-3"),
                                html.Label("HSA Contribution ($/yr)"),
                                dbc.Input(id={"type": "profile-input", "field": "retirement_hsa"},
                                          type="number", value=0, className="mb-3"),
                                html.Label("Solo 401(k) / SEP IRA ($/yr)"),
                                dbc.Input(id={"type": "profile-input", "field": "solo_401k"},
                                          type="number", value=0, className="mb-3"),
                            ],
                            className="glass-card mb-4",
                        ),
                        lg=4,
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                [html.H4("Income Streams (Annual)", className="mb-3"),
                                 html.Div(id="personal-income-table-container")],
                                className="glass-card mb-4",
                            ),
                            html.Div(
                                [html.H4("Living Expenses (Annual)", className="mb-3"),
                                 html.Div(id="personal-expenses-table-container")],
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
                            [html.H4("Assets", className="mb-3"),
                             html.Div(id="personal-assets-table-container")],
                            className="glass-card mb-4",
                        ),
                        lg=6,
                    ),
                    dbc.Col(
                        html.Div(
                            [html.H4("Liabilities", className="mb-3"),
                             html.Div(id="personal-liabilities-table-container")],
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
        render_editable_table("income-table",      pd.DataFrame(state.get("income",       [])), _INCOME_COLS),
        render_editable_table("expenses-table",    pd.DataFrame(state.get("expenses",     [])), _EXPENSE_COLS),
        render_editable_table("assets-table",      pd.DataFrame(state.get("assets",       [])), _ASSET_COLS),
        render_editable_table("liabilities-table", pd.DataFrame(state.get("liabilities",  [])), _LIAB_COLS),
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
                new_state["profile"][pid["field"]] = val
    elif "income-table" in triggered and inc_data is not None:
        new_state["income"] = inc_data
    elif "expenses-table" in triggered and exp_data is not None:
        new_state["expenses"] = exp_data
    elif "assets-table" in triggered and ast_data is not None:
        new_state["assets"] = ast_data
    elif "liabilities-table" in triggered and liab_data is not None:
        new_state["liabilities"] = liab_data
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
@callback(
    Output("income-table", "data", allow_duplicate=True),
    Input("income-table-add-btn", "n_clicks"),
    State("income-table", "data"),
    prevent_initial_call=True,
)
def add_income_row(n, rows):
    rows = rows or []
    if n:
        rows.append({"id": f"inc_{len(rows)+1}", "category": "Other", "description": "New Source", "amount": 0.0})
    return rows


@callback(
    Output("expenses-table", "data", allow_duplicate=True),
    Input("expenses-table-add-btn", "n_clicks"),
    State("expenses-table", "data"),
    prevent_initial_call=True,
)
def add_expense_row(n, rows):
    rows = rows or []
    if n:
        rows.append({"id": f"exp_{len(rows)+1}", "category": "Other", "description": "New Expense", "amount": 0.0})
    return rows


@callback(
    Output("assets-table", "data", allow_duplicate=True),
    Input("assets-table-add-btn", "n_clicks"),
    State("assets-table", "data"),
    prevent_initial_call=True,
)
def add_asset_row(n, rows):
    rows = rows or []
    if n:
        rows.append({"id": f"ast_{len(rows)+1}", "category": "Other", "description": "New Asset", "value": 0.0, "growth_rate": 0.05})
    return rows


@callback(
    Output("liabilities-table", "data", allow_duplicate=True),
    Input("liabilities-table-add-btn", "n_clicks"),
    State("liabilities-table", "data"),
    prevent_initial_call=True,
)
def add_liability_row(n, rows):
    rows = rows or []
    if n:
        rows.append({"id": f"liab_{len(rows)+1}", "category": "Other", "description": "New Liability",
                     "value": 0.0, "interest_rate": 0.05, "monthly_payment": 0.0})
    return rows
