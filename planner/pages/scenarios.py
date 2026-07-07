"""Scenario Manager page — create, duplicate, delete, compare scenarios."""
import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd

from planner.components.charts import apply_dark_layout
from planner.data_manager import (
    get_scenarios_list, load_project_state, save_scenario,
    delete_scenario, duplicate_scenario,
)
from planner.engines.runner import run_all_engines

dash.register_page(__name__, path="/scenarios", title="Scenarios")


def layout():
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.H4("Scenarios Ledger", className="mb-4"),
                                html.Label("Select Scenario to Compare"),
                                dcc.Dropdown(
                                    id="scenarios-list-dropdown",
                                    options=[{"label": "Baseline", "value": "Baseline"}],
                                    value="Baseline",
                                    clearable=False,
                                    className="mb-3",
                                    style={"color": "#0f172a"},
                                ),
                                html.Label("Scenario Name for Operation"),
                                dbc.Input(
                                    id="scenarios-action-input",
                                    type="text",
                                    placeholder="E.g., Hire Engineer",
                                    className="mb-3",
                                ),
                                html.Div(
                                    [
                                        dbc.Button("Create New",       id="scenarios-create-btn",    color="primary",   className="me-2 mb-2"),
                                        dbc.Button("Duplicate Active", id="scenarios-duplicate-btn", color="secondary", className="me-2 mb-2"),
                                        dbc.Button("Rename Active",    id="scenarios-rename-btn",    color="secondary", className="me-2 mb-2"),
                                        dbc.Button("Delete Active",    id="scenarios-delete-btn",    color="danger",    className="me-2 mb-2"),
                                    ],
                                    className="d-flex flex-wrap",
                                ),
                            ],
                            className="glass-card mb-4",
                        ),
                        lg=4,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.H4("Scenario Performance Comparison", className="mb-3"),
                                html.Div(id="scenarios-comparison-table-container", className="mb-4"),
                                dcc.Graph(id="scenarios-comparison-chart"),
                            ],
                            className="glass-card mb-4",
                        ),
                        lg=8,
                    ),
                ]
            ),
        ],
        fluid=True,
    )


@callback(
    Output("scenarios-list-dropdown",             "options"),
    Output("scenarios-list-dropdown",             "value"),
    Output("scenarios-action-input",              "value"),
    Output("scenarios-comparison-table-container","children"),
    Output("scenarios-comparison-chart",          "figure"),
    Input("scenarios-create-btn",    "n_clicks"),
    Input("scenarios-duplicate-btn", "n_clicks"),
    Input("scenarios-rename-btn",    "n_clicks"),
    Input("scenarios-delete-btn",    "n_clicks"),
    Input("scenarios-list-dropdown", "value"),
    State("scenarios-action-input",  "value"),
    prevent_initial_call=False,
)
def handle_scenario_actions(create_c, dup_c, rename_c, delete_c, selected, action_text):
    from dash import callback_context
    ctx = callback_context
    triggered = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
    action_text = action_text or ""

    if "create-btn" in triggered and action_text:
        save_scenario(action_text, {"name": action_text, "changes": {}})
        selected, action_text = action_text, ""
    elif "duplicate-btn" in triggered and action_text and selected:
        duplicate_scenario(selected, action_text)
        selected, action_text = action_text, ""
    elif "rename-btn" in triggered and action_text and selected and selected != "Baseline":
        duplicate_scenario(selected, action_text)
        delete_scenario(selected)
        selected, action_text = action_text, ""
    elif "delete-btn" in triggered and selected and selected != "Baseline":
        delete_scenario(selected)
        selected, action_text = "Baseline", ""

    sc_list = get_scenarios_list()
    selected = selected if selected in sc_list else "Baseline"
    options = [{"label": s, "value": s} for s in sc_list]

    def quick_summary(scenario_name):
        st = load_project_state(scenario_name)
        rr = run_all_engines(st, horizon=4)
        recent = rr["forecast_df"].iloc[-1]
        return {
            "Annual Tax":       rr["combined_tax"],
            "Annual EBITDA":    rr["ebitda_q"] * 4.0,
            "Cash Available":   float(recent["Cash"]),
            "Business Value":   rr["val_result"]["valuations"]["EBITDA Multiple"],
            "Net Worth":        rr["nw_result"]["value"],
        }

    base_s = quick_summary("Baseline")
    active_s = quick_summary(selected)

    rows = [
        {
            "Metric":   m,
            "Baseline": f"${base_s[m]:,.0f}",
            selected:   f"${active_s[m]:,.0f}",
            "Δ":        f"${active_s[m] - base_s[m]:+,.0f}",
        }
        for m in base_s
    ]
    comp_table = dbc.Table.from_dataframe(
        pd.DataFrame(rows),
        striped=True, bordered=False, hover=True, size="sm", className="text-white mb-0",
    )

    metrics_list = list(base_s.keys())
    fig = go.Figure()
    fig.add_trace(go.Bar(x=metrics_list, y=[base_s[m] for m in metrics_list],
                         name="Baseline", marker_color="#3b82f6"))
    fig.add_trace(go.Bar(x=metrics_list, y=[active_s[m] for m in metrics_list],
                         name=selected, marker_color="#8b5cf6"))
    fig = apply_dark_layout(fig, f"Baseline vs {selected}")

    return options, selected, action_text, comp_table, fig
