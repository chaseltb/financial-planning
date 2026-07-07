"""Business Valuation page — 6-method valuations with sensitivity chart."""
import copy

import dash
from dash import html, dcc, callback, callback_context, Input, Output, State, ALL, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from planner.components.cards import render_metric_card
from planner.components.charts import create_sensitivity_chart, apply_dark_layout
from planner.engines.runner import run_all_engines
from planner.data_manager import save_project_state

dash.register_page(__name__, path="/valuation", title="Valuation")

def layout():
    return dbc.Container(
        [
            dbc.Row(id="valuation-cards-row", className="mb-4"),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.H4("Valuation Multiples Settings", className="mb-4"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "Revenue Multiple"],
                                    id="label-rev-mult"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.Input(id={"type": "valuation-input", "field": "revenue_mult"},
                                                  type="number", step=0.1, value=2.5),
                                        dbc.InputGroupText("x"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip("Gross revenue multiplier, typically used for SaaS/fast-growing firms (1x - 5x).", target="label-rev-mult"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "EBITDA Multiple"],
                                    id="label-ebitda-mult"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.Input(id={"type": "valuation-input", "field": "ebitda_mult"},
                                                  type="number", step=0.1, value=6.0),
                                        dbc.InputGroupText("x"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip("EBITDA multiplier, the standard baseline for mid-market business valuation (4x - 8x).", target="label-ebitda-mult"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "Net Income Multiple"],
                                    id="label-ni-mult"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.Input(id={"type": "valuation-input", "field": "net_income_mult"},
                                                  type="number", step=0.1, value=8.0),
                                        dbc.InputGroupText("x"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip("Net Income multiplier, accounts for all taxes and debt payments (6x - 12x).", target="label-ni-mult"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "SDE Multiple"],
                                    id="label-sde-mult"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.Input(id={"type": "valuation-input", "field": "sde_mult"},
                                                  type="number", step=0.1, value=4.5),
                                        dbc.InputGroupText("x"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip("Seller's Discretionary Earnings (SDE = EBITDA + Owner Salary). Standard for small firms (2x - 5x).", target="label-sde-mult"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "FCF Multiple"],
                                    id="label-fcf-mult"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.Input(id={"type": "valuation-input", "field": "fcf_mult"},
                                                  type="number", step=0.1, value=7.0),
                                        dbc.InputGroupText("x"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip("Free Cash Flow multiplier (EBITDA - CapEx - Taxes). Reflects actual cash yield (5x - 10x).", target="label-fcf-mult"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "Custom Method Name"],
                                    id="label-custom-name"
                                ),
                                dbc.Input(id={"type": "valuation-input", "field": "custom_name"},
                                          type="text", value="Custom Multiplier", className="mb-3"),
                                dbc.Tooltip("Label for your custom valuation methodology.", target="label-custom-name"),
                                
                                html.Label(
                                    [html.I(className="bi bi-info-circle me-1 text-muted"), "Custom Multiplier"],
                                    id="label-custom-mult"
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.Input(id={"type": "valuation-input", "field": "custom_mult"},
                                                  type="number", step=0.1, value=3.0),
                                        dbc.InputGroupText("x"),
                                    ],
                                    className="mb-3"
                                ),
                                dbc.Tooltip("Multiplier to apply to annual EBITDA for the custom valuation.", target="label-custom-mult"),
                            ],
                            className="glass-card mb-4",
                        ),
                        lg=4,
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                [html.H4("Methodology Comparison", className="mb-3"),
                                 dcc.Graph(id="valuation-comparison-chart")],
                                className="glass-card mb-4",
                            ),
                            html.Div(
                                [
                                    html.H4("Sensitivity Analysis", className="mb-3"),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.Label("Base Method"),
                                                    dcc.Dropdown(
                                                        id="valuation-sensitivity-method",
                                                        options=[
                                                            {"label": "Revenue Multiple",    "value": "Revenue Multiple"},
                                                            {"label": "EBITDA Multiple",     "value": "EBITDA Multiple"},
                                                            {"label": "Net Income Multiple", "value": "Net Income Multiple"},
                                                            {"label": "SDE Multiple",        "value": "SDE Multiple"},
                                                            {"label": "FCF Multiple",        "value": "FCF Multiple"},
                                                        ],
                                                        value="EBITDA Multiple",
                                                        clearable=False,
                                                        className="mb-3",
                                                        style={"color": "#0f172a"},
                                                    ),
                                                ],
                                                width=6,
                                            ),
                                            dbc.Col(
                                                [
                                                    html.Label("Sensitivity Range (+/- %)"),
                                                    dbc.Input(
                                                        id="valuation-sensitivity-range",
                                                        type="number", min=0.01, max=0.99, step=0.05, value=0.20,
                                                        className="mb-3",
                                                    ),
                                                ],
                                                width=6,
                                            ),
                                        ]
                                    ),
                                    dcc.Graph(id="valuation-sensitivity-chart"),
                                ],
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
    Output("valuation-cards-row",       "children"),
    Output("valuation-comparison-chart","figure"),
    Output("valuation-sensitivity-chart","figure"),
    Output({"type": "valuation-input", "field": "revenue_mult"},     "value"),
    Output({"type": "valuation-input", "field": "ebitda_mult"},      "value"),
    Output({"type": "valuation-input", "field": "net_income_mult"},  "value"),
    Output({"type": "valuation-input", "field": "sde_mult"},         "value"),
    Output({"type": "valuation-input", "field": "fcf_mult"},         "value"),
    Output({"type": "valuation-input", "field": "custom_name"},      "value"),
    Output({"type": "valuation-input", "field": "custom_mult"},      "value"),
    Input("project-state-store",       "data"),
    Input("sensitivity-method-store",  "data"),
    Input("sensitivity-range-store",   "data"),
    Input("valuation-sensitivity-method", "value"),
    Input("valuation-sensitivity-range",  "value"),
    prevent_initial_call=False,
)
def populate_valuation_page(state, stored_method, stored_range, dropdown_method, input_range):
    if state is None:
        return [no_update] * 10

    # Page-local inputs take priority over stored defaults
    sens_method = dropdown_method or stored_method or "EBITDA Multiple"
    sens_range  = input_range or stored_range or 0.20

    r = run_all_engines(state, sensitivity_method=sens_method, sensitivity_range=float(sens_range))
    val = r["val_result"]
    multiples = r["multiples"]
    custom = r["custom_method"]
    sens = r["sensitivity"]

    cards = [
        render_metric_card("Revenue Multiple",
                           f"${val['valuations']['Revenue Multiple']:,.0f}",
                           f"× {multiples.get('revenue', 2.5)}"),
        render_metric_card("EBITDA Multiple",
                           f"${val['valuations']['EBITDA Multiple']:,.0f}",
                           f"× {multiples.get('ebitda', 6.0)}", "emerald"),
        render_metric_card("Net Income Multiple",
                           f"${val['valuations']['Net Income Multiple']:,.0f}",
                           f"× {multiples.get('net_income', 8.0)}"),
        render_metric_card("SDE Multiple",
                           f"${val['valuations']['SDE Multiple']:,.0f}",
                           f"× {multiples.get('sde', 4.5)}"),
        render_metric_card("FCF Multiple",
                           f"${val['valuations']['FCF Multiple']:,.0f}",
                           f"× {multiples.get('fcf', 7.0)}", "purple"),
        render_metric_card(custom["name"],
                           f"${val['valuations'].get(custom['name'], 0):,.0f}",
                           f"× {custom['multiplier']}"),
    ]

    fig_comp = go.Figure(data=[go.Bar(
        x=list(val["valuations"].keys()),
        y=list(val["valuations"].values()),
        marker_color=["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b", "#ef4444", "#ec4899"],
    )])
    fig_comp = apply_dark_layout(fig_comp, "Valuation Methodology Comparison")
    fig_comp.update_yaxes(title_text="Estimated Value ($)")

    fig_sens = create_sensitivity_chart(sens["sensitivity_curve"], sens_method)

    return (
        cards, fig_comp, fig_sens,
        float(multiples.get("revenue", 2.5)),
        float(multiples.get("ebitda", 6.0)),
        float(multiples.get("net_income", 8.0)),
        float(multiples.get("sde", 4.5)),
        float(multiples.get("fcf", 7.0)),
        custom["name"],
        custom["multiplier"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Callback: Persist edits from this page's valuation inputs
# ─────────────────────────────────────────────────────────────────────────────
@callback(
    Output("project-state-store", "data", allow_duplicate=True),
    Output("save-status-indicator", "children", allow_duplicate=True),
    Input({"type": "valuation-input", "field": ALL}, "value"),
    State({"type": "valuation-input", "field": ALL}, "id"),
    State("project-state-store", "data"),
    State("active-scenario-store", "data"),
    prevent_initial_call=True,
)
def persist_valuation_edits(val_vals, val_ids, current_state, active_scenario):
    if current_state is None:
        return no_update, no_update

    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update

    mult_map = {
        "revenue_mult": "revenue", "ebitda_mult": "ebitda",
        "net_income_mult": "net_income", "sde_mult": "sde", "fcf_mult": "fcf",
    }
    new_state = copy.deepcopy(current_state)
    for vid, val in zip(val_ids, val_vals):
        if val is None:
            continue
        field = vid["field"]
        if field in mult_map:
            try:
                val = max(0.0, min(50.0, float(val or 0.0)))
            except ValueError:
                val = 0.0
            new_state["assumptions"]["valuation_multiples"][mult_map[field]] = val
        elif field == "custom_name":
            new_state["assumptions"]["custom_valuation_name"] = str(val)
        elif field == "custom_mult":
            try:
                val = max(0.0, min(50.0, float(val or 0.0)))
            except ValueError:
                val = 0.0
            new_state["assumptions"]["custom_valuation_multiplier"] = val

    try:
        save_project_state(new_state, active_scenario)
        label = "● Saved"
    except Exception as e:
        label = f"⚠ {e}"

    return new_state, label


# ─────────────────────────────────────────────────────────────────────────────
# Callback: Sensitivity method/range inputs → stores (page-local controls)
# ─────────────────────────────────────────────────────────────────────────────
@callback(
    Output("sensitivity-method-store", "data"),
    Input("valuation-sensitivity-method", "value"),
    prevent_initial_call=True,
)
def update_sens_method(val):
    return val or "EBITDA Multiple"


@callback(
    Output("sensitivity-range-store", "data"),
    Input("valuation-sensitivity-range", "value"),
    prevent_initial_call=True,
)
def update_sens_range(val):
    return val or 0.20
