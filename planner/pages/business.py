"""Business Planning page."""
import dash
from dash import html, dcc, callback, Input, Output, no_update
import dash_bootstrap_components as dbc

from planner.components.charts import create_business_trend
from planner.engines.runner import run_all_engines

dash.register_page(__name__, path="/business", title="Business Planning")


def layout():
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.H4("Entity Choice & Growth Settings", className="mb-4"),
                                html.Label("Business Entity Type"),
                                dcc.Dropdown(
                                    id={"type": "business-input", "field": "entity_type"},
                                    options=[
                                        {"label": "Sole Proprietorship",  "value": "Sole Proprietorship"},
                                        {"label": "Single-member LLC",    "value": "Single-member LLC"},
                                        {"label": "Multi-member LLC",     "value": "Multi-member LLC"},
                                        {"label": "S Corporation",        "value": "S Corporation"},
                                        {"label": "C Corporation",        "value": "C Corporation"},
                                    ],
                                    value="Sole Proprietorship",
                                    clearable=False,
                                    className="mb-3",
                                    style={"color": "#0f172a"},
                                ),
                                html.Label("Owner W-2 Salary ($/yr)"),
                                dbc.Input(id={"type": "business-input", "field": "owner_salary"},
                                          type="number", value=0, className="mb-3"),
                                html.Label("Owner Profit Distributions ($/yr)"),
                                dbc.Input(id={"type": "business-input", "field": "distributions"},
                                          type="number", value=0, className="mb-3"),
                                html.Label("Quarterly Revenue Growth"),
                                dbc.Input(id={"type": "business-input", "field": "revenue_growth"},
                                          type="number", step=0.01, value=0.05, className="mb-3"),
                                html.Label("Quarterly Expense Growth"),
                                dbc.Input(id={"type": "business-input", "field": "expense_growth"},
                                          type="number", step=0.01, value=0.03, className="mb-3"),
                            ],
                            className="glass-card mb-4",
                        ),
                        lg=4,
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H4("Business Operating Summary", className="mb-3"),
                                    dbc.Row(
                                        [
                                            dbc.Col([html.Div("EBITDA", className="text-muted", style={"fontSize": "0.8rem"}),
                                                     html.H3(id="biz-ebitda-val", style={"color": "var(--accent-emerald)"})], width=4),
                                            dbc.Col([html.Div("Net Income", className="text-muted", style={"fontSize": "0.8rem"}),
                                                     html.H3(id="biz-netincome-val", style={"color": "var(--accent-blue)"})], width=4),
                                            dbc.Col([html.Div("Operating Margin", className="text-muted", style={"fontSize": "0.8rem"}),
                                                     html.H3(id="biz-margin-val")], width=4),
                                        ],
                                        className="mb-4",
                                    ),
                                ],
                                className="glass-card mb-4",
                            ),
                            html.Div(
                                [html.H4("Operating Trends", className="mb-3"),
                                 dcc.Graph(id="business-forecast-trend-chart")],
                                className="glass-card mb-4",
                            ),
                        ],
                        lg=8,
                    ),
                ]
            ),
        ],
        fluid=True,
    )


@callback(
    Output({"type": "business-input", "field": "entity_type"},    "value"),
    Output({"type": "business-input", "field": "owner_salary"},   "value"),
    Output({"type": "business-input", "field": "distributions"},  "value"),
    Output({"type": "business-input", "field": "revenue_growth"}, "value"),
    Output({"type": "business-input", "field": "expense_growth"}, "value"),
    Output("biz-ebitda-val",    "children"),
    Output("biz-netincome-val", "children"),
    Output("biz-margin-val",    "children"),
    Output("business-forecast-trend-chart", "figure"),
    Input("project-state-store", "data"),
    prevent_initial_call=False,
)
def populate_business_page(state):
    if state is None:
        return [no_update] * 9

    r = run_all_engines(state)
    b = state.get("business", {})
    annual_ebitda = r["ebitda_q"] * 4.0
    annual_ni = r["annual_net_biz_income"]
    margin = (r["ebitda_q"] / r["revenue_q"] * 100) if r["revenue_q"] > 0 else 0.0

    return (
        b.get("entity_type", "Sole Proprietorship"),
        b.get("owner_salary", 0),
        b.get("distributions", 0),
        b.get("revenue_growth", 0.05),
        b.get("expense_growth", 0.03),
        f"${annual_ebitda:,.0f}",
        f"${annual_ni:,.0f}",
        f"{margin:.1f}%",
        create_business_trend(r["forecast_df"]),
    )
