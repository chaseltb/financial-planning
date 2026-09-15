"""Personal Finances page — click-to-edit income/expense/asset/liability record lists."""
import copy

import dash
from dash import html, dcc, callback, callback_context, Input, Output, State, ALL, no_update
import dash_bootstrap_components as dbc

from planner.components.record_table import render_record_table, render_record_modal, render_field_input
from planner.components.citations import render_citation_panel
from planner.components.charts import create_allocation_chart
from planner.data_manager import save_or_mark_unsaved
from planner.engines.runner import run_all_engines
from planner.engines.allocation import calculate_budget_allocation

_DEFAULT_BUDGET_ALLOCATION = {"Savings": 34.0, "Liability Paydown": 33.0, "Taxable Brokerage": 33.0}

dash.register_page(__name__, path="/personal", title="Personal Finances")

# Read-only display columns for each record table (see components/record_table.py).
_INCOME_COLS = [
    {"id": "category",    "name": "Category",      "type": "text"},
    {"id": "description", "name": "Description",   "type": "text"},
    {"id": "amount",      "name": "Amount ($/yr)", "type": "money"},
]
_EXPENSE_COLS = _INCOME_COLS
_ASSET_COLS = [
    {"id": "category",    "name": "Category",           "type": "text"},
    {"id": "description", "name": "Description",        "type": "text"},
    {"id": "value",       "name": "Value ($)",          "type": "money"},
    {"id": "growth_rate", "name": "Annual Growth Rate", "type": "percent"},
]
_LIAB_COLS = [
    {"id": "category",        "name": "Category",                "type": "text"},
    {"id": "description",     "name": "Description",             "type": "text"},
    {"id": "value",           "name": "Outstanding Balance ($)", "type": "money"},
    {"id": "interest_rate",   "name": "Interest Rate (APR)",     "type": "percent"},
    {"id": "monthly_payment", "name": "Monthly Payment ($)",     "type": "money"},
]

# Field definitions that drive the shared edit/add modal's form for each table —
# label, input type, and whether the value is stored as a fraction but shown as
# a whole percentage point (matching how percent fields work everywhere else).
_TABLE_FIELD_DEFS = {
    "income": [
        {"field": "category", "label": "Category", "type": "text"},
        {"field": "description", "label": "Description", "type": "text"},
        {"field": "amount", "label": "Amount ($/yr)", "type": "number"},
    ],
    "expenses": [
        {"field": "category", "label": "Category", "type": "text"},
        {"field": "description", "label": "Description", "type": "text"},
        {"field": "amount", "label": "Amount ($/yr)", "type": "number"},
    ],
    "assets": [
        {"field": "category", "label": "Category", "type": "text"},
        {"field": "description", "label": "Description", "type": "text"},
        {"field": "value", "label": "Value ($)", "type": "number"},
        {"field": "growth_rate", "label": "Annual Growth Rate (%)", "type": "number", "percent": True},
    ],
    "liabilities": [
        {"field": "category", "label": "Category", "type": "text"},
        {"field": "description", "label": "Description", "type": "text"},
        {"field": "value", "label": "Outstanding Balance ($)", "type": "number"},
        {"field": "interest_rate", "label": "Interest Rate / APR (%)", "type": "number", "percent": True},
        {"field": "monthly_payment", "label": "Monthly Payment ($)", "type": "number"},
    ],
}
_TABLE_DEFAULTS = {
    "income": {"category": "Other", "description": "New Income Source", "amount": 0.0},
    "expenses": {"category": "Other", "description": "New Expense", "amount": 0.0},
    "assets": {"category": "Investment", "description": "New Asset", "value": 0.0, "growth_rate": 0.05},
    "liabilities": {"category": "Debt", "description": "New Liability",
                     "value": 0.0, "interest_rate": 0.05, "monthly_payment": 0.0},
}
_TABLE_TITLES = {"income": "Income Entry", "expenses": "Expense Entry", "assets": "Asset", "liabilities": "Liability"}
_ADD_BTN_TO_TABLE = {
    "income-table-add-btn": "income",
    "expenses-table-add-btn": "expenses",
    "assets-table-add-btn": "assets",
    "liabilities-table-add-btn": "liabilities",
}


def layout():
    return dbc.Container(
        [
            dcc.Store(id="record-modal-store"),
            dcc.Store(id="record-table-pages", data={}),
            render_record_modal("record-edit-modal"),
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
                                            type="number", debounce=True, min=-100000, max=100000, step=1, value=0
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
                                            type="number", debounce=True, min=-50000, max=50000, step=1, value=0
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
                                            type="number", debounce=True, min=-20000, max=20000, step=1, value=0
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
                                            type="number", debounce=True, min=-150000, max=150000, step=1, value=0
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
                                    html.Div(
                                        [
                                            html.H4(
                                                [html.I(className="bi bi-wallet2 me-2 text-primary"), "Income Streams (Annual)"],
                                                className="mb-0"
                                            ),
                                            dbc.Button(
                                                [html.I(className="bi bi-plus-circle me-1"), "Add Row"],
                                                id="income-table-add-btn", n_clicks=0,
                                                color="primary", size="sm",
                                            ),
                                        ],
                                        className="d-flex justify-content-between align-items-center mb-3",
                                    ),
                                    html.Div(id="personal-income-table-container")
                                ],
                                className="glass-card mb-4",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.H4(
                                                [html.I(className="bi bi-cart4 me-2 text-danger"), "Living Expenses (Annual)"],
                                                className="mb-0"
                                            ),
                                            dbc.Button(
                                                [html.I(className="bi bi-plus-circle me-1"), "Add Row"],
                                                id="expenses-table-add-btn", n_clicks=0,
                                                color="primary", size="sm",
                                            ),
                                        ],
                                        className="d-flex justify-content-between align-items-center mb-3",
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
                                html.Div(
                                    [
                                        html.H4(
                                            [html.I(className="bi bi-gem me-2 text-success"), "Assets"],
                                            className="mb-0"
                                        ),
                                        dbc.Button(
                                            [html.I(className="bi bi-plus-circle me-1"), "Add Row"],
                                            id="assets-table-add-btn", n_clicks=0,
                                            color="primary", size="sm",
                                        ),
                                    ],
                                    className="d-flex justify-content-between align-items-center mb-3",
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
                                html.Div(
                                    [
                                        html.H4(
                                            [html.I(className="bi bi-credit-card-2-front me-2 text-warning"), "Liabilities"],
                                            className="mb-0"
                                        ),
                                        dbc.Button(
                                            [html.I(className="bi bi-plus-circle me-1"), "Add Row"],
                                            id="liabilities-table-add-btn", n_clicks=0,
                                            color="primary", size="sm",
                                        ),
                                    ],
                                    className="d-flex justify-content-between align-items-center mb-3",
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
    Input("record-table-pages", "data"),
    prevent_initial_call=False,
)
def populate_personal_page(state, pages):
    if state is None:
        return [no_update] * 12

    pages = pages or {}
    p = state.get("profile", {})
    allocation_pct = p.get("budget_allocation", _DEFAULT_BUDGET_ALLOCATION)
    return (
        render_record_table("income",      state.get("income",      []), _INCOME_COLS,  page=pages.get("income", 0),      empty_label="income streams"),
        render_record_table("expenses",    state.get("expenses",    []), _EXPENSE_COLS, page=pages.get("expenses", 0),    empty_label="living expenses"),
        render_record_table("assets",      state.get("assets",      []), _ASSET_COLS,   page=pages.get("assets", 0),      empty_label="assets"),
        render_record_table("liabilities", state.get("liabilities", []), _LIAB_COLS,    page=pages.get("liabilities", 0), empty_label="liabilities"),
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
                # Negative values are allowed here on purpose: a negative contribution
                # models a withdrawal from that account (e.g. cashing out a 401k),
                # which should show up as taxable income rather than being clamped away.
                if field in ["retirement_401k", "retirement_ira", "retirement_hsa", "solo_401k"]:
                    try:
                        val = float(val or 0.0)
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


@callback(
    Output("record-table-pages", "data"),
    Input({"type": "record-page-nav", "table": ALL, "dir": ALL}, "n_clicks"),
    State("record-table-pages", "data"),
    prevent_initial_call=True,
)
def paginate_record_tables(_clicks, pages):
    ctx = callback_context
    if not ctx.triggered or not ctx.triggered[0]["value"]:
        return no_update
    triggered_id = ctx.triggered_id
    pages = dict(pages or {})
    table = triggered_id["table"]
    current = pages.get(table, 0)
    pages[table] = current + 1 if triggered_id["dir"] == "next" else max(0, current - 1)
    return pages


@callback(
    Output("record-modal-store", "data"),
    Input({"type": "record-row", "table": ALL, "row": ALL}, "n_clicks"),
    Input("income-table-add-btn", "n_clicks"),
    Input("expenses-table-add-btn", "n_clicks"),
    Input("assets-table-add-btn", "n_clicks"),
    Input("liabilities-table-add-btn", "n_clicks"),
    prevent_initial_call=True,
)
def open_record_modal(_row_clicks, _add_income, _add_expenses, _add_assets, _add_liabilities):
    # Deliberately has NO Input on the modal's own footer buttons (Save/Cancel/
    # Delete/...): those don't exist in the DOM until the modal has been opened
    # once, and a Dash callback silently never fires for ANY of its Inputs if
    # even one declared Input isn't currently present — exactly the failure
    # mode already documented on persist_profile_and_allocation_edits above.
    # Keeping this callback to only always-present components (row cells and
    # the four static "Add Row" buttons) is what makes it actually fire.
    ctx = callback_context
    if not ctx.triggered or not ctx.triggered[0]["value"]:
        # A table re-render (after any save/delete) recreates row components
        # with n_clicks reset to 0, which Dash reports as a "change" and would
        # otherwise re-open the modal as if the row had been clicked again —
        # only a genuine click reports a truthy (nonzero) value.
        return no_update
    triggered_id = ctx.triggered_id

    if isinstance(triggered_id, dict):
        if triggered_id.get("type") == "record-row":
            return {"table": triggered_id["table"], "row": triggered_id["row"], "confirm_delete": False}
        return no_update

    if triggered_id in _ADD_BTN_TO_TABLE:
        return {"table": _ADD_BTN_TO_TABLE[triggered_id], "row": None, "confirm_delete": False}

    return no_update


@callback(
    Output("record-modal-store", "data", allow_duplicate=True),
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input("record-modal-save-btn", "n_clicks"),
    Input("record-modal-cancel-btn", "n_clicks"),
    Input("record-modal-delete-btn", "n_clicks"),
    State("record-modal-store", "data"),
    State({"type": "record-field", "field": ALL}, "value"),
    State({"type": "record-field", "field": ALL}, "id"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    State("autosave-enabled-store", "data"),
    prevent_initial_call=True,
)
def handle_record_modal_main_actions(
    _save, _cancel, _delete, modal_state, field_values, field_ids, project_state, active_scenario, autosave_enabled,
):
    # Separate from open_record_modal above (see its comment): these three
    # buttons only start existing once the modal has opened at least once, so
    # bundling them into the same callback as the always-present row/add-row
    # Inputs would silently block that other callback from ever firing too.
    # They're ALSO kept separate from the delete-confirm sub-state's two
    # buttons below (handle_record_modal_delete_confirm) — Save/Cancel/Delete
    # and Yes-delete-it/Cancel-delete are mutually exclusive in the footer
    # (never both rendered at once), so a callback listing all five as Inputs
    # would itself have "missing" Inputs half the time and never fire at all.
    ctx = callback_context
    if not ctx.triggered or not ctx.triggered[0]["value"]:
        return no_update, no_update, no_update
    triggered_id = ctx.triggered_id

    if triggered_id == "record-modal-cancel-btn":
        return None, no_update, no_update

    if triggered_id == "record-modal-delete-btn":
        if not modal_state:
            return no_update, no_update, no_update
        return {**modal_state, "confirm_delete": True}, no_update, no_update

    if triggered_id == "record-modal-save-btn":
        if not modal_state or project_state is None:
            return no_update, no_update, no_update
        table, row_idx = modal_state["table"], modal_state["row"]
        field_map = {fid["field"]: val for fid, val in zip(field_ids, field_values)}
        row = {}
        for fdef in _TABLE_FIELD_DEFS[table]:
            field = fdef["field"]
            raw = field_map.get(field)
            if fdef["type"] == "number":
                try:
                    num = float(raw or 0.0)
                except (TypeError, ValueError):
                    num = 0.0
                row[field] = num / 100.0 if fdef.get("percent") else num
            else:
                row[field] = raw or ""
        new_state = copy.deepcopy(project_state)
        rows = list(new_state.get(table, []))
        if row_idx is not None and 0 <= row_idx < len(rows):
            rows[row_idx] = row
        else:
            rows.append(row)
        new_state[table] = rows
        label = save_or_mark_unsaved(new_state, active_scenario, autosave_enabled)
        return None, new_state, label

    return no_update, no_update, no_update


@callback(
    Output("record-modal-store", "data", allow_duplicate=True),
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input("record-modal-delete-confirm-btn", "n_clicks"),
    Input("record-modal-delete-cancel-btn", "n_clicks"),
    State("record-modal-store", "data"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    State("autosave-enabled-store", "data"),
    prevent_initial_call=True,
)
def handle_record_modal_delete_confirm(_confirm, _cancel, modal_state, project_state, active_scenario, autosave_enabled):
    ctx = callback_context
    if not ctx.triggered or not ctx.triggered[0]["value"]:
        return no_update, no_update, no_update
    triggered_id = ctx.triggered_id

    if triggered_id == "record-modal-delete-cancel-btn":
        if not modal_state:
            return no_update, no_update, no_update
        return {**modal_state, "confirm_delete": False}, no_update, no_update

    if triggered_id == "record-modal-delete-confirm-btn":
        if not modal_state or project_state is None:
            return no_update, no_update, no_update
        table, row_idx = modal_state["table"], modal_state["row"]
        new_state = copy.deepcopy(project_state)
        rows = list(new_state.get(table, []))
        if row_idx is not None and 0 <= row_idx < len(rows):
            rows.pop(row_idx)
        new_state[table] = rows
        label = save_or_mark_unsaved(new_state, active_scenario, autosave_enabled)
        return None, new_state, label

    return no_update, no_update, no_update


@callback(
    Output("record-edit-modal", "is_open"),
    Output("record-edit-modal-title", "children"),
    Output("record-edit-modal-body", "children"),
    Output("record-edit-modal-footer", "children"),
    Input("record-modal-store", "data"),
    State("project-state-store", "data"),
    prevent_initial_call=True,
)
def render_record_modal_content(modal_state, project_state):
    if not modal_state or project_state is None:
        return False, no_update, no_update, no_update

    table, row_idx = modal_state["table"], modal_state["row"]
    confirm_delete = modal_state.get("confirm_delete", False)
    rows = project_state.get(table, [])
    is_new = row_idx is None or not (0 <= row_idx < len(rows))
    row_data = _TABLE_DEFAULTS[table] if is_new else rows[row_idx]
    title = f"Add {_TABLE_TITLES[table]}" if is_new else f"Edit {_TABLE_TITLES[table]}"

    body = [render_field_input(fdef, row_data.get(fdef["field"])) for fdef in _TABLE_FIELD_DEFS[table]]

    if confirm_delete:
        footer = [
            html.Span(
                "Delete this entry? This can't be undone.",
                className="text-danger me-auto", style={"fontSize": "0.85rem", "fontWeight": 600, "alignSelf": "center"},
            ),
            dbc.Button("Cancel", id="record-modal-delete-cancel-btn", color="secondary", outline=True, className="me-2"),
            dbc.Button("Yes, delete it", id="record-modal-delete-confirm-btn", color="danger"),
        ]
    else:
        footer = [dbc.Button("Cancel", id="record-modal-cancel-btn", color="secondary", outline=True, className="me-auto")]
        if not is_new:
            footer.append(dbc.Button("Delete", id="record-modal-delete-btn", color="danger", outline=True, className="me-2"))
        footer.append(dbc.Button("Save Changes", id="record-modal-save-btn", color="primary"))

    return True, title, body, footer
