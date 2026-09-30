"""Business Planning page."""
import copy

import dash
from dash import html, dcc, callback, callback_context, Input, Output, State, ALL, no_update
import dash_bootstrap_components as dbc

from planner.components.charts import create_business_trend
from planner.components.business_gate import render_business_gate, register_business_gate
from planner.engines.runner import run_all_engines
from planner.engines.forecast import DEFAULT_SEED
from planner.engines.valuation import get_ownership_fraction
from planner.data_manager import save_or_mark_unsaved, states_equal

dash.register_page(__name__, path="/business", title="Business Planning")

_CONTENT_ID = "business-page-content"


def _compact_card(children, className="glass-card mb-4"):
    """A card whose label+control groups sit in a two-column grid. `children` is the usual flat
    list (heading, intro, then Label / control / Tooltip ... repeating); everything before the first
    Label stays full width, and each Label starts a new field group."""
    prefix, groups = [], []
    for child in children:
        if isinstance(child, html.Label):
            groups.append([child])
        elif groups:
            groups[-1].append(child)
        else:
            prefix.append(child)
    fields = [html.Div(g, className="compact-field") for g in groups]
    trailing = []
    if fields:
        # Non-field elements that follow the last field (e.g. a footer note) stay full width.
        last = groups[-1]
        keep = []
        for el in last:
            (trailing if getattr(el, "id", None) == "biz-deduction-total" else keep).append(el)
        fields[-1] = html.Div(keep, className="compact-field")
    return html.Div([*prefix, html.Div(fields, className="compact-grid"), *trailing], className=className)


# Tax-only business deductions (see engines/records.py business_deduction_totals). Cash expenses
# belong in "Annual Operating Expenses"; these lower TAXABLE profit without changing cash flow.
_DEDUCTION_FIELDS = [
    ("ded_home_office", "Home Office",
     "Your deductible share of rent/mortgage interest, utilities and insurance for a space used regularly and "
     "exclusively for the business (or the simplified $5/sq ft method, up to $1,500). Usually already paid from "
     "personal funds, so it is not part of operating expenses."),
    ("ded_vehicle", "Vehicle & Mileage",
     "Business use of a personal vehicle: business miles x the IRS standard mileage rate, or the actual-expense share."),
    ("ded_depreciation", "Depreciation / Section 179",
     "Annual depreciation or Section 179 expensing on equipment and other business assets. A non-cash deduction, "
     "so it lowers taxable profit but not cash flow."),
    ("ded_health_insurance", "Self-Employed Health Insurance",
     "Health, dental and long-term-care premiums you pay for yourself and family. Deducted from income (AGI), "
     "limited to the business's profit; it does not reduce self-employment tax. Not available while you are "
     "also eligible for an employer-subsidized plan."),
    ("ded_other", "Other Tax Deductions",
     "Anything else deductible that is not already in operating expenses (e.g. professional development, "
     "startup costs amortization)."),
]


def _deduction_card():
    rows = []
    for field, label, tip in _DEDUCTION_FIELDS:
        label_id = f"label-{field.replace('_', '-')}"
        rows += [
            html.Label([html.I(className="bi bi-info-circle me-1 text-muted"), label], id=label_id),
            dbc.InputGroup(
                [
                    dbc.InputGroupText("$"),
                    dbc.Input(id={"type": "business-input", "field": field},
                              type="number", debounce=True, min=0, step=1, value=0),
                    dbc.InputGroupText("/yr"),
                ],
                className="mb-3",
            ),
            dbc.Tooltip(tip, target=label_id),
        ]
    return _compact_card(
        [
            html.H4(
                [
                    "Business Tax Deductions",
                    html.Button(
                        html.I(className="bi bi-info-circle", **{"aria-hidden": "true"}),
                        id="deductions-info-btn",
                        type="button",
                        className="explain-trigger-btn ms-2",
                        title="About these deductions",
                        **{"aria-label": "About business tax deductions"},
                    ),
                ],
                className="mb-2 d-flex align-items-center",
            ),
            dbc.Tooltip(
                "Tax-only deductions that lower taxable profit (income tax, SE tax, QBI) but not cash flow "
                "or valuation. Cash expenses belong in Operating Expenses.",
                target="deductions-info-btn",
            ),
            *rows,
            html.Div(id="biz-deduction-total", className="text-muted", style={"fontSize": "0.85rem"}),
        ],
        className="glass-card mb-4",
    )


def layout():
    return dbc.Container(
        [
            render_business_gate(_CONTENT_ID, "Business Planning"),
            html.Div(id=_CONTENT_ID, children=[
            dbc.Alert(
                id="business-empty-alert",
                children=[
                    html.I(className="bi bi-info-circle me-2"),
                    "No business activity has been entered yet — the numbers below are all zero. "
                    "Fill in your revenue, expenses, and other run-rate financials below to model "
                    "your own business.",
                ],
                color="secondary",
                className="mb-3",
                style={"fontSize": "0.85rem", "display": "none"},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                        _compact_card(
                            [
                                html.H4("Entity Choice & Growth Settings", className="mb-3"),
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "Business Entity Type"],
                                    id="label-entity-type"
                                ),
                                # Native <select>: renders instantly (dcc.Dropdown loads lazily and showed up blank
                                # in places), and is themed by the same .form-select rules as the other inputs.
                                dbc.Select(
                                    id={"type": "business-input", "field": "entity_type"},
                                    options=[
                                        {"label": "Sole Proprietorship",  "value": "Sole Proprietorship"},
                                        {"label": "Single-member LLC",    "value": "Single-member LLC"},
                                        {"label": "Multi-member LLC",     "value": "Multi-member LLC"},
                                        {"label": "S Corporation",        "value": "S Corporation"},
                                        {"label": "C Corporation",        "value": "C Corporation"},
                                    ],
                                    value="Sole Proprietorship",
                                    size="sm",
                                ),
                                dbc.Tooltip("Entity structure affects payroll requirements, self-employment taxes, and corporate rates.", target="label-entity-type"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "W-2 Owner's Salary"],
                                    id="label-owner-salary"
                                ),
                                # Wrapper div is the tooltip target: a disabled input fires no hover events.
                                html.Div(
                                    dbc.InputGroup(
                                        [
                                            dbc.InputGroupText("$"),
                                            dbc.Input(
                                                id={"type": "business-input", "field": "owner_salary"},
                                                type="number", debounce=True, min=0, step=1, value=0
                                            ),
                                            dbc.InputGroupText("/yr"),
                                        ],
                                        className="mb-1"
                                    ),
                                    id="owner-salary-field-wrap",
                                ),
                                dbc.Tooltip(id="tooltip-owner-salary-field", children="", target="owner-salary-field-wrap"),
                                html.Div(
                                    id="owner-salary-inapplicable-note",
                                    className="text-warning mb-3",
                                    style={"fontSize": "0.8rem", "display": "none"},
                                ),
                                dbc.Tooltip(
                                    id="tooltip-owner-salary",
                                    children="Annual W-2 wages paid to the owner. S-Corps require a 'reasonable W-2 salary' under IRS rules.",
                                    target="label-owner-salary",
                                ),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "Your Ownership %"],
                                    id="label-ownership-pct"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.Input(
                                            id={"type": "business-input", "field": "ownership_pct"},
                                            type="number", debounce=True, min=1, max=100, step=1, value=100
                                        ),
                                        dbc.InputGroupText("%"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip(
                                    "Your stake in the business. Owner profit distributions are calculated automatically "
                                    "as this % of net income after owner salary — not entered manually. If you own less "
                                    "than 100%, only your pro-rata share of K-1/dividend income and self-employment tax "
                                    "applies to your personal return; the rest belongs to other partners/shareholders.",
                                    target="label-ownership-pct",
                                ),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "Quarterly Revenue Growth"],
                                    id="label-revenue-growth"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.Input(
                                            id={"type": "business-input", "field": "revenue_growth"},
                                            type="number", debounce=True, step=0.01, value=5
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
                                            type="number", debounce=True, step=0.01, value=3
                                        ),
                                        dbc.InputGroupText("% / quarter"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip("Compounding quarterly growth rate applied to project operating expenses forward.", target="label-expense-growth"),
                            ],
                            className="glass-card mb-4",
                        ),
                        _compact_card(
                            [
                                html.H4("Business Run-Rate Financials (Annualized)", className="mb-3"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "Annual Revenue"],
                                    id="label-biz-rev"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText("$"),
                                        dbc.Input(
                                            id={"type": "business-financials-input", "field": "revenue"},
                                            type="number", debounce=True, min=0, step=1, value=0
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
                                            type="number", debounce=True, min=0, step=1, value=0
                                        ),
                                        dbc.InputGroupText("/yr"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip("Annual Cost of Goods Sold (direct manufacturing, labor, or production costs).", target="label-biz-cogs"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "Annual Payroll (non-owner)"],
                                    id="label-biz-pay"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText("$"),
                                        dbc.Input(
                                            id={"type": "business-financials-input", "field": "payroll"},
                                            type="number", debounce=True, min=0, step=1, value=0
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
                                            type="number", debounce=True, min=0, step=1, value=0
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
                                            type="number", debounce=True, min=0, step=1, value=0
                                        ),
                                        dbc.InputGroupText("/yr"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip("Annual investments in fixed assets like machinery, real estate, or vehicles.", target="label-biz-capex"),
                            ],
                            className="glass-card mb-4",
                        ),
                            _deduction_card(),
                        ],
                        lg=5,
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
                                            dbc.Col([html.Div("EBITDA (Current Quarter, Annualized)", className="text-muted", style={"fontSize": "0.85rem"}),
                                                     html.H3(id="biz-ebitda-val", style={"color": "var(--accent-emerald)", "fontWeight": "bold"})], width=4),
                                            dbc.Col([html.Div("Net Income (After Owner Salary)", className="text-muted", style={"fontSize": "0.85rem"}),
                                                     html.H3(id="biz-netincome-val", style={"color": "var(--accent-blue)", "fontWeight": "bold"})], width=4),
                                            dbc.Col([html.Div("Operating Margin", className="text-muted", style={"fontSize": "0.85rem"}),
                                                     html.H3(id="biz-margin-val", style={"fontWeight": "bold"})], width=4),
                                        ],
                                        className="mb-4",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col([html.Div("Owner Distributions (Your Share)", className="text-muted", style={"fontSize": "0.85rem"}),
                                                     html.H3(id="biz-distributions-val", style={"fontWeight": "bold"})], width=4),
                                            dbc.Col([html.Div("Employer Payroll Tax (FICA Match)", className="text-muted", style={"fontSize": "0.85rem"}),
                                                     html.H3(id="biz-employer-payroll-val", style={"color": "var(--accent-purple)", "fontWeight": "bold"})], width=4),
                                            dbc.Col([html.Div("Est. Business Tax Burden (Fed + NC)", className="text-muted", style={"fontSize": "0.85rem"}),
                                                     html.H3(id="biz-combined-tax-val", style={"fontWeight": "bold"})], width=4),
                                        ],
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
                        lg=7,
                    ),
                ]
            ),
            ]),
        ],
        fluid=True,
    )


register_business_gate(_CONTENT_ID)


_OWNER_SALARY_TOOLTIPS = {
    "S Corporation": "Annual W-2 wages paid to the owner through payroll. S-Corps require a 'reasonable W-2 salary' under IRS rules — the remaining profit passes through as K-1 distributions, free of self-employment tax.",
    "C Corporation": "Annual W-2 wages paid to the owner through payroll. Reduces C-Corp taxable income; the business also pays the employer-side FICA match on this amount.",
    "Sole Proprietorship": "Not applicable for a Sole Proprietorship — you can't legally pay yourself W-2 wages. The full business profit is subject to self-employment tax regardless of this field; it is ignored in calculations.",
    "Single-member LLC": "Not applicable for a Single-member LLC (taxed like a Sole Proprietorship) — you can't legally pay yourself W-2 wages. The full business profit is subject to self-employment tax; this field is ignored in calculations.",
    "Multi-member LLC": "Not applicable for a Multi-member LLC (taxed as a partnership) — partners can't be paid W-2 wages by the partnership. The full K-1 profit is subject to self-employment tax; this field is ignored in calculations.",
}


@callback(
    Output({"type": "business-input", "field": "entity_type"},    "value"),
    Output({"type": "business-input", "field": "owner_salary"},   "value"),
    Output({"type": "business-input", "field": "ownership_pct"},  "value"),
    Output({"type": "business-input", "field": "revenue_growth"}, "value"),
    Output({"type": "business-input", "field": "expense_growth"}, "value"),
    *[Output({"type": "business-input", "field": f}, "value") for f, _l, _t in _DEDUCTION_FIELDS],
    Output("biz-deduction-total", "children"),
    Output("tooltip-owner-salary", "children"),
    Output("tooltip-owner-salary-field", "children"),
    Output({"type": "business-input", "field": "owner_salary"}, "disabled"),
    Output("owner-salary-inapplicable-note", "children"),
    Output("owner-salary-inapplicable-note", "style"),
    Output("business-empty-alert", "style"),
    Output("biz-ebitda-val",    "children"),
    Output("biz-netincome-val", "children"),
    Output("biz-margin-val",    "children"),
    Output("biz-distributions-val",    "children"),
    Output("biz-employer-payroll-val", "children"),
    Output("biz-combined-tax-val",     "children"),
    Output("business-forecast-trend-chart", "figure"),
    Input("project-state-store", "data"),
    prevent_initial_call=False,
)
def populate_business_page(state):
    if state is None:
        return [no_update] * (17 + len(_DEDUCTION_FIELDS) + 2)

    r = run_all_engines(state)
    b = state.get("business", {})
    entity_type = b.get("entity_type", "Sole Proprietorship")
    ownership_pct = get_ownership_fraction(b)
    annual_ebitda = r["ebitda_q"] * 4.0
    annual_ni = r["annual_net_biz_income"]
    margin = (r["ebitda_q"] / r["revenue_q"] * 100) if r["revenue_q"] > 0 else 0.0
    employer_payroll_tax = r["fed_tax"].get("employer_payroll_tax", 0.0)
    owner_distributions = max(0.0, annual_ni) * ownership_pct

    # Sole props/LLCs can't legally pay the owner W-2 wages — the field is a
    # no-op for calculations in that case (see _OWNER_SALARY_TOOLTIPS). Rather
    # than silently ignoring whatever the user types with no visible sign why,
    # disable the field and say so inline once the entity type doesn't support it.
    owner_salary_applicable = entity_type in ("S Corporation", "C Corporation")
    # The field is simply disabled; a short tooltip explains why (no inline note, which made the row taller).
    owner_salary_tip = (
        _OWNER_SALARY_TOOLTIPS.get(entity_type, _OWNER_SALARY_TOOLTIPS["S Corporation"])
        if owner_salary_applicable
        else f"Not applicable for a {entity_type} — no effect on the numbers."
    )
    inapplicable_note = ""
    inapplicable_style = {"display": "none"}

    # A business with any real activity shouldn't keep being told it's empty.
    has_business_activity = r["revenue_q"] > 0
    empty_alert_style = {"fontSize": "0.85rem", "display": "none" if has_business_activity else "block"}

    return (
        entity_type,
        b.get("owner_salary", 0),
        b.get("ownership_pct", 100),
        float(b.get("revenue_growth", 0.05)) * 100,
        float(b.get("expense_growth", 0.03)) * 100,
        *[float(b.get(f, 0.0) or 0.0) for f, _l, _t in _DEDUCTION_FIELDS],
        (f"Total deductions entered: ${r['business_tax_deductions']:,.0f}/yr" if r["business_tax_deductions"] > 0 else ""),
        owner_salary_tip,
        owner_salary_tip,
        not owner_salary_applicable,
        inapplicable_note,
        inapplicable_style,
        empty_alert_style,
        f"${annual_ebitda:,.0f}",
        f"${annual_ni:,.0f}",
        f"{margin:.1f}%",
        f"${owner_distributions:,.0f}",
        f"${employer_payroll_tax:,.0f}",
        f"${r['business_attributable_tax']:,.0f}",
        create_business_trend(r["forecast_df"]),
    )


@callback(
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input({"type": "business-input", "field": ALL}, "value"),
    State({"type": "business-input", "field": ALL}, "id"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    State("autosave-enabled-store", "data"),
    prevent_initial_call=True,
)
def persist_business_edits(biz_vals, biz_ids, current_state, active_scenario, autosave_enabled):
    if current_state is None:
        return no_update, no_update

    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update

    new_state = copy.deepcopy(current_state)
    for bid, val in zip(biz_ids, biz_vals):
        if val is not None:
            field = bid["field"]
            if field == "owner_salary":
                try:
                    val = max(0.0, float(val or 0.0))
                except ValueError:
                    val = 0.0
            elif field == "ownership_pct":
                try:
                    val = max(1.0, min(100.0, float(val or 100.0)))
                except ValueError:
                    val = 100.0
            elif field.startswith("ded_"):
                try:
                    val = max(0.0, float(val or 0.0))
                except ValueError:
                    val = 0.0
            elif field in ["revenue_growth", "expense_growth"]:
                # Field displays whole percentage points (5 = 5%); stored as a fraction.
                try:
                    pct_points = max(-100.0, min(500.0, float(val or 0.0)))
                except ValueError:
                    pct_points = 0.0
                val = pct_points / 100.0
            new_state["business"][field] = val

    # Populating inputs on page load fires these callbacks with unchanged values;
    # don't rewrite the data files (or reformat them) when nothing actually changed.
    if states_equal(new_state, current_state):
        return no_update, no_update

    label = save_or_mark_unsaved(new_state, active_scenario, autosave_enabled)
    return new_state, label


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


@callback(
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input({"type": "business-financials-input", "field": ALL}, "value"),
    State({"type": "business-financials-input", "field": ALL}, "id"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    State("autosave-enabled-store", "data"),
    prevent_initial_call=True,
)
def persist_business_financials(vals, ids, current_state, active_scenario, autosave_enabled):
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

    # Populating inputs on page load fires these callbacks with unchanged values;
    # don't rewrite the data files (or reformat them) when nothing actually changed.
    if states_equal(new_state, current_state):
        return no_update, no_update

    label = save_or_mark_unsaved(new_state, active_scenario, autosave_enabled)
    return new_state, label
