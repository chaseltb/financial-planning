"""Taxes & Audit page — full tax breakdown with bracket visualizer and explain panel."""
import dash
from dash import html, dcc, callback, Input, Output, no_update
import dash_bootstrap_components as dbc

from planner.components.summary import render_explain_panel, render_empty_explain_panel
from planner.components.charts import create_bracket_progress_chart
from planner.data_manager import load_tax_rules
from planner.config import DEFAULT_TAX_YEAR, DEFAULT_STATE
from planner.engines.runner import run_all_engines

dash.register_page(__name__, path="/taxes", title="Taxes")


def layout():
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H4(
                                        [html.I(className="bi bi-receipt-cutoff me-2 text-info"), "Tax Liability Breakdown"],
                                        className="mb-4"
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col([
                                                html.Div(
                                                    [html.I(className="bi bi-flag-fill me-1 text-muted"), "Federal Personal Tax"],
                                                    id="label-tax-fed",
                                                    className="text-muted", style={"fontSize": "0.8rem"}
                                                ),
                                                dbc.Tooltip(
                                                    "Federal income tax on your taxable income (after deductions), using progressive IRS brackets.",
                                                    target="label-tax-fed",
                                                ),
                                                html.H4(id="tax-breakdown-fed"),
                                            ], width=4, className="mb-3"),
                                            dbc.Col([
                                                html.Div(
                                                    [html.I(className="bi bi-geo-alt-fill me-1 text-muted"), "NC State Tax"],
                                                    id="label-tax-nc",
                                                    className="text-muted", style={"fontSize": "0.8rem"}
                                                ),
                                                dbc.Tooltip(
                                                    "North Carolina's flat-rate income tax, applied to your federal AGI minus the NC standard deduction.",
                                                    target="label-tax-nc",
                                                ),
                                                html.H4(id="tax-breakdown-nc"),
                                            ], width=4, className="mb-3"),
                                            dbc.Col([
                                                html.Div(
                                                    [html.I(className="bi bi-person-badge me-1 text-muted"), "Payroll & SE Tax"],
                                                    id="label-tax-payroll",
                                                    className="text-muted", style={"fontSize": "0.8rem"}
                                                ),
                                                dbc.Tooltip(
                                                    "Social Security & Medicare: withheld from any W-2 wages, owed as self-employment tax on business profit, or both.",
                                                    target="label-tax-payroll",
                                                ),
                                                html.H4(id="tax-breakdown-payroll"),
                                            ], width=4, className="mb-3"),
                                            dbc.Col([
                                                html.Div(
                                                    [html.I(className="bi bi-building me-1 text-muted"), "Corporate Income Tax"],
                                                    id="label-tax-corp",
                                                    className="text-muted", style={"fontSize": "0.8rem"}
                                                ),
                                                dbc.Tooltip(
                                                    "Entity-level tax a C-Corporation pays on its profit, before any dividends reach you personally. Zero for other entity types.",
                                                    target="label-tax-corp",
                                                ),
                                                html.H4(id="tax-breakdown-corp"),
                                            ], id="tax-breakdown-corp-col", width=4, className="mb-3 business-only"),
                                            dbc.Col([
                                                html.Div(
                                                    [html.I(className="bi bi-calculator me-1 text-muted"), "Combined Total Tax"],
                                                    id="label-tax-combined",
                                                    className="text-muted", style={"fontSize": "0.8rem"}
                                                ),
                                                dbc.Tooltip(
                                                    "Every tax above added together — federal, state, payroll/SE, and corporate — your full tax burden.",
                                                    target="label-tax-combined",
                                                ),
                                                html.H4(id="tax-breakdown-combined",
                                                         style={"color": "var(--accent-purple)"}),
                                            ], width=4, className="mb-3"),
                                            dbc.Col([
                                                html.Div(
                                                    [html.I(className="bi bi-percent me-1 text-muted"), "Effective Tax Rate"],
                                                    id="label-tax-effective",
                                                    className="text-muted", style={"fontSize": "0.8rem"}
                                                ),
                                                dbc.Tooltip(
                                                    "Combined tax as a share of your AGI — a truer picture of your real tax burden than any single bracket rate.",
                                                    target="label-tax-effective",
                                                ),
                                                html.H4(id="tax-breakdown-effective-rate",
                                                         style={"color": "var(--accent-emerald)"}),
                                            ], width=4, className="mb-3"),
                                        ]
                                    ),
                                    html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),
                                    html.Div(id="tax-overview-text", className="text-muted",
                                             style={"fontSize": "0.9rem"}),
                                ],
                                className="glass-card mb-4",
                            ),
                            html.Div(
                                [
                                    html.H4(
                                        [html.I(className="bi bi-bar-chart-steps me-2 text-info"), "Progressive Tax Bracket Visualization"],
                                        className="mb-1"
                                    ),
                                    html.Div(
                                        [
                                            html.Span(
                                                [
                                                    html.Span(style={"background": "linear-gradient(135deg, #93c5fd 50%, #1d4ed8 50%)"}),
                                                    " Active bracket",
                                                ],
                                                className="bracket-legend-item",
                                            ),
                                            html.Span([html.Span(style={"backgroundColor": "#10b981"}), " Next bracket"], className="bracket-legend-item"),
                                            html.Span([html.Span(style={"border": "1.5px dashed rgba(148,163,184,0.6)", "backgroundColor": "transparent"}), " Not reached"], className="bracket-legend-item"),
                                        ],
                                        className="bracket-legend mb-2",
                                    ),
                                    dcc.Graph(id="tax-brackets-visualizer", config={"displayModeBar": False}),
                                ],
                                className="glass-card mb-4",
                            ),
                        ],
                        lg=6,
                    ),
                    dbc.Col(
                        html.Div(
                            id="taxes-explain-container",
                            children=render_empty_explain_panel(),
                        ),
                        lg=6,
                    ),
                ]
            ),
        ],
        fluid=True,
    )



@callback(
    Output("tax-breakdown-fed",          "children"),
    Output("tax-breakdown-nc",           "children"),
    Output("tax-breakdown-payroll",      "children"),
    Output("tax-breakdown-corp",         "children"),
    Output("tax-breakdown-corp-col",     "style"),
    Output("tax-breakdown-combined",     "children"),
    Output("tax-breakdown-effective-rate","children"),
    Output("tax-overview-text",          "children"),
    Output("tax-brackets-visualizer",    "figure"),
    Output("taxes-explain-container",    "children"),
    Input("project-state-store", "data"),
    Input("business-mode-store", "data"),
    prevent_initial_call=False,
)
def populate_taxes_page(state, business_mode_enabled):
    if state is None:
        return [no_update] * 10

    business_enabled = business_mode_enabled is not False

    r = run_all_engines(state)
    fed = r["fed_tax"]
    nc  = r["nc_tax"]
    filing = r["filing_status"]

    combined = r["combined_tax"]
    effective = r["effective_rate"]

    rules = r["fed_rules"]
    brackets = sorted(rules.get("brackets", {}).get(filing, []), key=lambda x: x["threshold"])
    taxable = fed.get("taxable_income", 0.0)

    bracket_fig = create_bracket_progress_chart(brackets, taxable)

    se_tax = fed.get("se_tax", 0.0)
    payroll_tax = fed.get("payroll_tax", 0.0)
    employer_payroll_tax = fed.get("employer_payroll_tax", 0.0)
    corp_tax_total = fed.get("corporate_tax", 0.0) + nc.get("corporate_tax", 0.0)

    overview_text = (
        f"Your Adjusted Gross Income (AGI) is ${fed['agi']:,.0f}. "
        f"After a ${fed.get('qbi_deduction', 0):,.0f} QBI deduction, "
        f"federal taxable income is ${fed['taxable_income']:,.0f}. "
        f"NC taxable income is ${nc.get('nc_taxable_income', 0):,.0f} "
        f"(NC flat rate {nc.get('flat_rate', 0.0399)*100:.2f}%, {r['tax_year']} rules). "
        f"Federal personal income tax comes to ${fed['value']:,.0f} and NC state tax to ${nc['value']:,.0f}."
    )
    if se_tax > 0:
        # "self-employment income" rather than "business profit" — this can come
        # from personal 1099 income with no registered business entity involved,
        # so the wording holds regardless of the Business Mode toggle.
        overview_text += f" Self-employment tax (Social Security + Medicare on self-employment income) adds ${se_tax:,.0f}."
    if payroll_tax > 0 or employer_payroll_tax > 0:
        # The employer-match clause only ever applies to an S/C-Corp paying the
        # owner a W-2 salary — genuinely business-specific, so it's dropped in
        # personal mode even though the underlying number isn't recalculated.
        show_employer_match = employer_payroll_tax > 0 and business_enabled
        overview_text += (
            f" W-2 payroll (FICA) tax adds ${payroll_tax:,.0f} on the employee side"
            + (f" plus ${employer_payroll_tax:,.0f} in employer match on owner wages." if show_employer_match else ".")
        )
    if corp_tax_total > 0 and business_enabled:
        overview_text += f" Corporate income tax (Federal + NC) adds ${corp_tax_total:,.0f}."
    overview_text += (
        f" Altogether, combined tax liability is ${combined:,.0f}, "
        f"an effective rate of {effective * 100:.1f}% on AGI."
    )

    explain = render_explain_panel(
        "Combined Federal + NC Tax Calculation",
        "Combined = Personal Income Tax + SE Tax + Corporate Tax (Fed + NC)",
        {"AGI": fed["agi"], "Taxable Income": fed["taxable_income"],
         "NC Taxable Income": nc.get("nc_taxable_income", 0),
         "Filing Status": filing},
        fed["trace"]["assumptions_used"],
        fed["trace"]["rules_referenced"],
        fed["trace"]["steps"] + nc["trace"]["steps"],
    )

    # "Payroll & SE Tax" is every non-personal-income, non-corporate slice of the
    # combined total — SE tax, employee-side FICA, and (when applicable) the
    # business's own employer-side FICA match — so the four cards always add up
    # to Combined Total Tax instead of the employee-side FICA vanishing into the
    # narrative text with nothing in the breakdown to show for it.
    payroll_card_total = se_tax + payroll_tax + employer_payroll_tax
    # Corporate tax is only ever nonzero for a C-Corp; showing "$0" for every
    # other entity type is just noise, so the card disappears entirely instead.
    corp_col_style = {} if corp_tax_total > 0 else {"display": "none"}

    return (
        f"${fed['value']:,.0f}",
        f"${nc['value']:,.0f}",
        f"${payroll_card_total:,.0f}",
        f"${corp_tax_total:,.0f}",
        corp_col_style,
        f"${combined:,.0f}",
        f"{effective * 100:.1f}%",
        overview_text,
        bracket_fig,
        explain,
    )
