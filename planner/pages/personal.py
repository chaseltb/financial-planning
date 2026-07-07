"""Personal Finances page — editable income/expense/asset/liability tables."""
import dash
from dash import html, dcc, callback, Input, Output, no_update
import dash_bootstrap_components as dbc
import pandas as pd

from planner.components.editable_table import render_editable_table

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
