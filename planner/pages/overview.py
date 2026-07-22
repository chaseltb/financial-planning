"""Overview (Dashboard) page — registers its own page-scoped callbacks."""
import dash
from dash import html, dcc, callback, Input, Output, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from planner.components.cards import render_metric_card
from planner.components.charts import (
    create_net_worth_trend, create_business_trend,
    create_allocation_chart, apply_dark_layout,
)
from planner.components.summary import render_explain_panel, render_empty_explain_panel
from planner.engines.runner import run_all_engines

dash.register_page(__name__, path="/", title="Overview")


def layout():
    return dbc.Container(
        [
            dbc.Row(id="overview-cards-container", className="mb-4"),
            dbc.Row(
                [
                    dbc.Col(html.Div(dcc.Graph(id="overview-networth-chart"), className="glass-card mb-4"), lg=6),
                    dbc.Col(html.Div(dcc.Graph(id="overview-business-chart"), className="glass-card mb-4"), lg=6),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(html.Div(dcc.Graph(id="overview-allocation-chart"), className="glass-card mb-4"), lg=6),
                    dbc.Col(html.Div(id="overview-explain-container", children=render_empty_explain_panel()), lg=6),
                ]
            ),
        ],
        fluid=True,
    )


@callback(
    Output("overview-cards-container", "children"),
    Output("overview-networth-chart", "figure"),
    Output("overview-business-chart", "figure"),
    Output("overview-allocation-chart", "figure"),
    Output("overview-explain-container", "children"),
    Input("project-state-store", "data"),
    Input("explain-target-store", "data"),
    prevent_initial_call=False,
)
def update_overview(state, explain_target):
    if state is None:
        empty_fig = go.Figure()
        empty_fig = apply_dark_layout(empty_fig, "")
        return [], empty_fig, empty_fig, empty_fig, render_empty_explain_panel()

    r = run_all_engines(state)
    fed_tax = r["fed_tax"]
    nc_tax = r["nc_tax"]
    nw_result = r["nw_result"]
    val_result = r["val_result"]
    multiples = r["multiples"]
    recent_q = r["recent_q"]
    nw_proj_df = r["nw_proj_df"]
    forecast_df = r["forecast_df"]

    personal_tax = fed_tax["value"] + nc_tax["value"]
    se_corp_tax = fed_tax["se_tax"] + fed_tax["corporate_tax"] + nc_tax["corporate_tax"]

    # Four headline numbers instead of six near-duplicate cards: Personal Tax and
    # SE/Corp Tax are components of Combined Tax, so they ride as its subtitle
    # rather than getting their own card (still one click away via Combined Tax's
    # explain panel, which already includes both in its step trace).
    cards = [
        render_metric_card(
            "Combined Tax",
            f"${r['combined_tax']:,.0f}",
            f"Personal ${personal_tax:,.0f} + SE/Corp ${se_corp_tax:,.0f} · {r['effective_rate'] * 100:.1f}% effective",
            "purple", "combined_tax",
        ),
        render_metric_card(
            "Net Worth",
            f"${nw_result['value']:,.0f}",
            f"Assets: ${nw_result['total_assets']:,.0f}",
            "", "net_worth",
        ),
        render_metric_card(
            "Business Value",
            f"${val_result['valuations'].get('EBITDA Multiple', 0):,.0f}",
            f"EBITDA × {multiples.get('ebitda', 6.0)}",
            "emerald", "business_value",
        ),
        render_metric_card(
            "Cash Available",
            f"${float(recent_q['Cash']):,.0f}",
            f"End of {recent_q['Quarter']}",
            "", "cash_available",
        ),
    ]

    fig_nw = create_net_worth_trend(nw_proj_df)
    fig_biz = create_business_trend(forecast_df)
    fig_alloc = create_allocation_chart(nw_result["asset_allocation"], "Asset Allocation")

    # Explanation panel
    target = explain_target or "combined_tax"
    tax_year = r["tax_year"]
    panels = {
        "combined_tax": render_explain_panel(
            "Combined Tax Liability",
            "Combined = Personal Tax + SE Tax + Corporate Tax (Fed + NC)",
            {"AGI": fed_tax["agi"], "Net Biz Income": r["annual_net_biz_income"]},
            "All tax layers consolidated — true aggregate burden.",
            f"{tax_year} IRS and NC DOR rules.",
            fed_tax["trace"]["steps"] + nc_tax["trace"]["steps"],
        ),
        "net_worth": render_explain_panel(
            "Net Worth",
            nw_result["trace"]["formula"],
            nw_result["trace"]["inputs"],
            nw_result["trace"]["assumptions_used"],
            nw_result["trace"]["rules_referenced"],
            nw_result["trace"]["steps"],
        ),
        "business_value": render_explain_panel(
            "Business Valuation (EBITDA Multiple)",
            val_result["trace"]["formula"],
            val_result["trace"]["inputs"],
            val_result["trace"]["assumptions_used"],
            val_result["trace"]["rules_referenced"],
            val_result["trace"]["steps"],
        ),
    }
    explain = panels.get(target, render_empty_explain_panel())

    return cards, fig_nw, fig_biz, fig_alloc, explain
