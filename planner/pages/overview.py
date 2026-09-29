"""Overview (Dashboard) page — registers its own page-scoped callbacks."""
import dash
from dash import html, dcc, callback, Input, Output, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from planner.components.cards import (
    render_metric_card,
    render_hero_metric_card,
    render_companion_metrics_card,
)
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
            html.Div(id="overview-cards-container", className="overview-hero-row"),
            html.Div(id="overview-charts-container"),
        ],
        fluid=True,
    )




def _render_charts_row(fig_nw, fig_biz, fig_alloc, explain, business_enabled):
    """Asset Allocation normally shares row 2 with the (business-only) trend chart's
    row 3 slot; with business hidden there's nothing left to pair it with there, so
    it moves up to fill the empty spot next to Net Worth instead, and the explain
    panel takes the full width of what would've been its own row."""
    graph_card = lambda graph_id, fig: html.Div(dcc.Graph(id=graph_id, figure=fig), className="glass-card mb-4")

    if business_enabled:
        return [
            dbc.Row(
                [
                    dbc.Col(graph_card("overview-networth-chart", fig_nw), lg=6),
                    dbc.Col(graph_card("overview-business-chart", fig_biz), lg=6, className="business-only"),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(graph_card("overview-allocation-chart", fig_alloc), lg=6),
                    dbc.Col(html.Div(id="overview-explain-container", children=explain), lg=6),
                ]
            ),
        ]

    return [
        dbc.Row(
            [
                dbc.Col(graph_card("overview-networth-chart", fig_nw), lg=6),
                dbc.Col(graph_card("overview-allocation-chart", fig_alloc), lg=6),
            ]
        ),
        dbc.Row(
            dbc.Col(html.Div(id="overview-explain-container", children=explain), lg=12),
        ),
    ]


@callback(
    Output("overview-cards-container", "children"),
    Output("overview-charts-container", "children"),
    Input("project-state-store", "data"),
    Input("explain-target-store", "data"),
    Input("business-mode-store", "data"),
    prevent_initial_call=False,
)
def update_overview(state, explain_target, business_mode_enabled):
    if state is None:
        empty_fig = go.Figure()
        empty_fig = apply_dark_layout(empty_fig, "")
        return [], _render_charts_row(empty_fig, empty_fig, empty_fig, render_empty_explain_panel(), True)

    business_enabled = business_mode_enabled is not False

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
    # Every other slice of Combined Tax — SE tax, employee/employer FICA, and
    # corporate tax — so this always reconciles exactly against combined_tax
    # instead of quietly excluding FICA (personal_tax + other_tax == combined_tax).
    other_tax = (
        fed_tax["se_tax"] + fed_tax["payroll_tax"] + fed_tax["employer_payroll_tax"]
        + fed_tax["corporate_tax"] + nc_tax["corporate_tax"]
    )

    # Four headline numbers instead of six near-duplicate cards: Personal Tax and
    # "everything else" are components of Combined Tax, so they ride as its
    # subtitle rather than getting their own card (still one click away via
    # Combined Tax's explain panel, which has the full step trace). Kept to one
    # short line — a card this narrow wraps almost anything longer.
    combined_tax_subtitle = (
        f"${personal_tax:,.0f} + ${other_tax:,.0f} · {r['effective_rate'] * 100:.1f}%"
        if business_enabled
        else f"{r['effective_rate'] * 100:.1f}% effective"
    )

    if business_enabled:
        hero_card = render_hero_metric_card(
            title="Combined Net Worth",
            value=f"${r['combined_net_worth']:,.0f}",
            subtitle=f"Personal (${nw_result['value']:,.0f}) + ${r['business_equity_value']:,.0f} equity stake",
            color_class="emerald",
            explain_target="combined_net_worth",
        )
        companion_card = render_companion_metrics_card([
            {
                "title": "Combined Tax",
                "value": f"${r['combined_tax']:,.0f}",
                "subtitle": combined_tax_subtitle,
                "color_class": "purple",
                "explain_target": "combined_tax",
            },
            {
                "title": "Personal Net Worth",
                "value": f"${nw_result['value']:,.0f}",
                "subtitle": f"Assets: ${nw_result['total_assets']:,.0f}",
                "color_class": "",
                "explain_target": "net_worth",
            },
            {
                "title": "Business Value",
                "value": f"${val_result['value']:,.0f}",
                "subtitle": f"EBITDA × {multiples.get('ebitda', 6.0)}",
                "color_class": "emerald",
                "explain_target": "business_value",
            },
            {
                "title": "Cash Available",
                "value": f"${float(recent_q['Cash']):,.0f}",
                "subtitle": f"End of {recent_q['Quarter']}",
                "color_class": "",
                "explain_target": "cash_available",
            },
        ])
    else:
        hero_card = render_hero_metric_card(
            title="Personal Net Worth",
            value=f"${nw_result['value']:,.0f}",
            subtitle=f"Assets: ${nw_result['total_assets']:,.0f} · Liabilities: ${nw_result['total_liabilities']:,.0f}",
            color_class="emerald",
            explain_target="net_worth",
        )
        companion_card = render_companion_metrics_card([
            {
                "title": "Combined Tax",
                "value": f"${r['combined_tax']:,.0f}",
                "subtitle": combined_tax_subtitle,
                "color_class": "purple",
                "explain_target": "combined_tax",
            },
            {
                "title": "Cash Available",
                "value": f"${float(recent_q['Cash']):,.0f}",
                "subtitle": f"End of {recent_q['Quarter']}",
                "color_class": "",
                "explain_target": "cash_available",
            },
        ])

    cards = [hero_card, companion_card]

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
            "Personal Net Worth",
            nw_result["trace"]["formula"],
            nw_result["trace"]["inputs"],
            nw_result["trace"]["assumptions_used"],
            nw_result["trace"]["rules_referenced"],
            nw_result["trace"]["steps"],
        ),
    }
    if business_enabled:
        panels["business_value"] = render_explain_panel(
            "Business Valuation (EBITDA Multiple)",
            val_result["trace"]["formula"],
            val_result["trace"]["inputs"],
            val_result["trace"]["assumptions_used"],
            val_result["trace"]["rules_referenced"],
            val_result["trace"]["steps"],
        )
        panels["combined_net_worth"] = render_explain_panel(
            "Combined Net Worth",
            "Combined Net Worth = Personal Net Worth + (Business Value × Ownership %)",
            {
                "Personal Net Worth": r["personal_net_worth"],
                "Business Value": val_result["value"],
                "Business Equity Stake": r["business_equity_value"],
            },
            "Business value is scaled by the owner's ownership percentage before being added to the household balance sheet.",
            "Standard equity-stake accounting for closely-held businesses.",
            [
                f"Personal Net Worth: ${r['personal_net_worth']:,.2f}",
                f"Business Value (EBITDA Multiple): ${val_result['value']:,.2f}",
                f"Business Equity Stake: Business Value (${val_result['value']:,.2f}) × Ownership % = ${r['business_equity_value']:,.2f}",
                f"Combined Net Worth: Personal Net Worth (${r['personal_net_worth']:,.2f}) + Business Equity Stake (${r['business_equity_value']:,.2f}) = ${r['combined_net_worth']:,.2f}",
            ],
        )
    # If a business panel was selected before Business Mode got turned off,
    # fall back instead of rendering a target that's no longer in the dict.
    if target not in panels:
        target = "combined_tax"
    explain = panels.get(target, render_empty_explain_panel())

    return cards, _render_charts_row(fig_nw, fig_biz, fig_alloc, explain, business_enabled)


@callback(
    Output("explain-target-store", "data"),
    Input({"type": "explain-trigger", "target": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def handle_explain_click(n_clicks):
    from dash import callback_context
    import json
    ctx = callback_context
    if not ctx.triggered or not any(n_clicks or []):
        return no_update
    prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
    target = json.loads(prop_id).get("target")
    return target or no_update

