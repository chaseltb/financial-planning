"""Net Worth Tracking page."""
import dash
from dash import html, dcc, callback, Input, Output, no_update
import dash_bootstrap_components as dbc
import pandas as pd

from planner.components.charts import create_net_worth_trend, create_allocation_chart
from planner.engines.runner import run_all_engines

dash.register_page(__name__, path="/networth", title="Net Worth")


def layout():
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.H4("Balance Sheet Aggregates", className="mb-4"),
                                dbc.Row(
                                    [
                                        dbc.Col([html.Div("Total Assets", className="text-muted", style={"fontSize": "0.8rem"}),
                                                 html.H3(id="nw-total-assets", style={"color": "var(--accent-emerald)"})], width=4),
                                        dbc.Col([html.Div("Total Liabilities", className="text-muted", style={"fontSize": "0.8rem"}),
                                                 html.H3(id="nw-total-liab", style={"color": "var(--accent-blue)"})], width=4),
                                        dbc.Col([html.Div("Net Worth", className="text-muted", style={"fontSize": "0.8rem"}),
                                                 html.H3(id="nw-net-worth", style={"color": "var(--accent-purple)"})], width=4),
                                    ]
                                ),
                                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)"}),
                                html.Div(id="networth-assets-table-container", className="mb-4"),
                                html.Div(id="networth-liab-table-container"),
                            ],
                            className="glass-card mb-4",
                        ),
                        lg=6,
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H4("Asset & Liability Allocations", className="mb-3"),
                                    dbc.Row(
                                        [
                                            dbc.Col(dcc.Graph(id="networth-asset-pie"), width=6),
                                            dbc.Col(dcc.Graph(id="networth-debt-pie"), width=6),
                                        ]
                                    ),
                                ],
                                className="glass-card mb-4",
                            ),
                            html.Div(
                                [html.H4("8-Quarter Net Worth Projection", className="mb-3"),
                                 dcc.Graph(id="networth-projection-chart")],
                                className="glass-card mb-4",
                            ),
                        ],
                        lg=6,
                    ),
                ]
            ),
        ],
        fluid=True,
    )


@callback(
    Output("nw-total-assets",             "children"),
    Output("nw-total-liab",               "children"),
    Output("nw-net-worth",                "children"),
    Output("networth-asset-pie",          "figure"),
    Output("networth-debt-pie",           "figure"),
    Output("networth-projection-chart",   "figure"),
    Output("networth-assets-table-container", "children"),
    Output("networth-liab-table-container",   "children"),
    Input("project-state-store", "data"),
    prevent_initial_call=False,
)
def populate_networth_page(state):
    if state is None:
        return [no_update] * 8

    r = run_all_engines(state)
    nw = r["nw_result"]
    proj_df = r["nw_proj_df"]

    debt_alloc = nw["debt_allocation"] if nw["debt_allocation"] else {"No Liabilities": 0}

    assets_tbl = [
        html.Small("Assets Ledger", className="text-muted d-block mb-2"),
        dbc.Table.from_dataframe(
            pd.DataFrame(state["assets"])[["category", "description", "value", "growth_rate"]],
            striped=True, bordered=False, hover=True, size="sm", className="text-white mb-0",
        ),
    ] if state["assets"] else [html.P("No assets entered.", className="text-muted")]

    liab_tbl = [
        html.Small("Liabilities Ledger", className="text-muted d-block mb-2 mt-3"),
        dbc.Table.from_dataframe(
            pd.DataFrame(state["liabilities"])[["category", "description", "value", "interest_rate", "monthly_payment"]],
            striped=True, bordered=False, hover=True, size="sm", className="text-white mb-0",
        ),
    ] if state["liabilities"] else [html.P("No liabilities entered.", className="text-muted")]

    return (
        f"${nw['total_assets']:,.0f}",
        f"${nw['total_liabilities']:,.0f}",
        f"${nw['value']:,.0f}",
        create_allocation_chart(nw["asset_allocation"], "Asset Classes"),
        create_allocation_chart(debt_alloc, "Debt Classes"),
        create_net_worth_trend(proj_df),
        assets_tbl,
        liab_tbl,
    )
