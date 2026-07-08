"""Net Worth Tracking page."""
import dash
from dash import html, dcc, callback, Input, Output, no_update
import dash_bootstrap_components as dbc

from planner.components.charts import create_net_worth_trend, create_allocation_chart
from planner.engines.runner import run_all_engines

dash.register_page(__name__, path="/networth", title="Net Worth")

_ASSET_LEDGER_COLS = [
    ("category",    "Category",      "text"),
    ("description", "Description",  "text"),
    ("value",       "Value",        "money"),
    ("growth_rate", "Annual Growth", "percent"),
]
_LIAB_LEDGER_COLS = [
    ("category",         "Category",         "text"),
    ("description",      "Description",      "text"),
    ("value",            "Balance",          "money"),
    ("interest_rate",    "Interest Rate",    "percent"),
    ("monthly_payment",  "Monthly Payment",  "money"),
]


def _render_readonly_ledger(rows, col_spec):
    """Read-only summary table with the same look as the editable tables
    elsewhere in the app (Title Case headers, $/% formatting) — this page
    only displays the ledger; edit it on the Personal Finances page."""
    def fmt(val, kind):
        val = float(val or 0)
        if kind == "money":
            return f"${val:,.0f}"
        if kind == "percent":
            return f"{val * 100:.1f}%"
        return val

    header = html.Thead(html.Tr([html.Th(label) for _, label, _ in col_spec]))
    body = html.Tbody([
        html.Tr([
            html.Td(fmt(row.get(key, ""), kind) if kind != "text" else row.get(key, ""))
            for key, _, kind in col_spec
        ])
        for row in rows
    ])
    return dbc.Table([header, body], striped=True, bordered=False, hover=True,
                      size="sm", className="text-white mb-0", responsive=True)


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
        html.Small(
            ["Assets Ledger ", html.A("(edit on Personal Finances)", href="/personal", className="text-muted")],
            className="text-muted d-block mb-2"
        ),
        _render_readonly_ledger(state["assets"], _ASSET_LEDGER_COLS),
    ] if state["assets"] else [html.P("No assets entered yet — add some on the Personal Finances page.", className="text-muted")]

    liab_tbl = [
        html.Small(
            ["Liabilities Ledger ", html.A("(edit on Personal Finances)", href="/personal", className="text-muted")],
            className="text-muted d-block mb-2 mt-3"
        ),
        _render_readonly_ledger(state["liabilities"], _LIAB_LEDGER_COLS),
    ] if state["liabilities"] else [html.P("No liabilities entered yet — add some on the Personal Finances page.", className="text-muted")]

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
