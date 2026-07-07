"""Taxes & Audit page — full tax breakdown with bracket visualizer and explain panel."""
import dash
from dash import html, dcc, callback, Input, Output, no_update
import dash_bootstrap_components as dbc

from planner.components.summary import render_explain_panel, render_empty_explain_panel
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
                                                    className="text-muted", style={"fontSize": "0.8rem"}
                                                ),
                                                html.H4(id="tax-breakdown-fed"),
                                            ], width=4, className="mb-3"),
                                            dbc.Col([
                                                html.Div(
                                                    [html.I(className="bi bi-geo-alt-fill me-1 text-muted"), "NC State Tax"],
                                                    className="text-muted", style={"fontSize": "0.8rem"}
                                                ),
                                                html.H4(id="tax-breakdown-nc"),
                                            ], width=4, className="mb-3"),
                                            dbc.Col([
                                                html.Div(
                                                    [html.I(className="bi bi-person-badge me-1 text-muted"), "Payroll & SE Tax"],
                                                    className="text-muted", style={"fontSize": "0.8rem"}
                                                ),
                                                html.H4(id="tax-breakdown-payroll"),
                                            ], width=4, className="mb-3"),
                                            dbc.Col([
                                                html.Div(
                                                    [html.I(className="bi bi-building me-1 text-muted"), "Corporate Income Tax"],
                                                    className="text-muted", style={"fontSize": "0.8rem"}
                                                ),
                                                html.H4(id="tax-breakdown-corp"),
                                            ], width=4, className="mb-3"),
                                            dbc.Col([
                                                html.Div(
                                                    [html.I(className="bi bi-calculator me-1 text-muted"), "Combined Total Tax"],
                                                    className="text-muted", style={"fontSize": "0.8rem"}
                                                ),
                                                html.H4(id="tax-breakdown-combined",
                                                         style={"color": "var(--accent-purple)"}),
                                            ], width=4, className="mb-3"),
                                            dbc.Col([
                                                html.Div(
                                                    [html.I(className="bi bi-percent me-1 text-muted"), "Effective Tax Rate"],
                                                    className="text-muted", style={"fontSize": "0.8rem"}
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
                                        className="mb-3"
                                    ),
                                    html.Div(id="tax-brackets-visualizer"),
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
                            className="glass-card",
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
    Output("tax-breakdown-combined",     "children"),
    Output("tax-breakdown-effective-rate","children"),
    Output("tax-overview-text",          "children"),
    Output("tax-brackets-visualizer",    "children"),
    Output("taxes-explain-container",    "children"),
    Input("project-state-store", "data"),
    prevent_initial_call=False,
)
def populate_taxes_page(state):
    if state is None:
        return [no_update] * 9

    r = run_all_engines(state)
    fed = r["fed_tax"]
    nc  = r["nc_tax"]
    filing = r["filing_status"]

    combined = r["combined_tax"]
    effective = r["effective_rate"]

    # Bracket visualizer
    rules = r["fed_rules"]
    brackets = rules.get("brackets", {}).get(filing, [])
    taxable = fed.get("taxable_income", 0.0)

    bar_elements = []
    for br in sorted(brackets, key=lambda x: x["threshold"]):
        filled = taxable > br["threshold"]
        bar_elements.append(html.Div([
            html.Div(
                [
                    html.Span(f"{br['rate']*100:.0f}% bracket",
                              style={"fontSize": "0.85rem", "fontWeight": "600"}),
                    html.Span(f"Threshold: ${br['threshold']:,.0f}",
                              className="text-muted ms-auto",
                              style={"fontSize": "0.8rem"}),
                ],
                style={"display": "flex"},
            ),
            dbc.Progress(
                value=100 if filled else 0,
                color="info" if filled else "secondary",
                style={"height": "8px", "margin": "6px 0 12px 0"},
            ),
        ]))

    overview_text = (
        f"Your Adjusted Gross Income (AGI) is ${fed['agi']:,.0f}. "
        f"After a ${fed.get('qbi_deduction', 0):,.0f} QBI deduction, "
        f"federal taxable income is ${fed['taxable_income']:,.0f}. "
        f"NC taxable income is ${nc.get('nc_taxable_income', 0):,.0f} "
        f"(NC flat rate {nc.get('nc_rate', 0.0399)*100:.2f}%)."
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

    return (
        f"${fed['value']:,.0f}",
        f"${nc['value']:,.0f}",
        f"${fed['se_tax']:,.0f}",
        f"${fed['corporate_tax'] + nc['corporate_tax']:,.0f}",
        f"${combined:,.0f}",
        f"{effective * 100:.1f}%",
        overview_text,
        bar_elements,
        explain,
    )
