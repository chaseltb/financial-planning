import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, List

# Common chart layout adjustments. Backgrounds are transparent so the chart
# blends with its card, which IS theme-aware — but Plotly renders to canvas/SVG
# and can't read CSS variables, so text/gridline colors are picked to stay
# legible against both the dark and light theme's card color rather than
# hardcoded to one theme.
_CHART_TEXT_COLOR = "#64748b"       # slate-500: readable on near-black and near-white
_CHART_TITLE_COLOR = "#64748b"
_CHART_GRIDLINE_COLOR = "rgba(128, 128, 128, 0.18)"


def apply_dark_layout(fig, title_text: str):
    fig.update_layout(
        title={
            "text": title_text,
            "font": {"family": "Outfit", "size": 18, "color": _CHART_TITLE_COLOR},
            "x": 0.05
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter", "color": _CHART_TEXT_COLOR},
        legend={
            "font": {"size": 11, "color": _CHART_TEXT_COLOR},
            "orientation": "h",
            "xanchor": "center",
            "x": 0.5,
            "y": -0.2
        },
        margin={"t": 60, "b": 60, "l": 50, "r": 20},
        xaxis={
            "gridcolor": _CHART_GRIDLINE_COLOR,
            "zeroline": False,
            "tickfont": {"size": 11, "color": _CHART_TEXT_COLOR}
        },
        yaxis={
            "gridcolor": _CHART_GRIDLINE_COLOR,
            "zeroline": False,
            "tickfont": {"size": 11, "color": _CHART_TEXT_COLOR}
        }
    )
    return fig


def create_net_worth_trend(projection_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=projection_df["Quarter"],
            y=projection_df["Net Worth"],
            mode="lines+markers",
            name="Net Worth",
            line={"width": 3, "color": "#8b5cf6"},
            marker={"size": 8, "color": "#a78bfa"}
        )
    )
    fig.add_trace(
        go.Bar(
            x=projection_df["Quarter"],
            y=projection_df["Assets"],
            name="Assets",
            marker={"color": "rgba(16, 185, 129, 0.4)"}
        )
    )
    fig.add_trace(
        go.Bar(
            x=projection_df["Quarter"],
            y=-projection_df["Liabilities"],
            name="Liabilities",
            marker={"color": "rgba(239, 68, 68, 0.4)"}
        )
    )
    fig.update_layout(barmode="relative")
    return apply_dark_layout(fig, "Net Worth Projection")


def create_business_trend(forecast_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=forecast_df["Quarter"],
            y=forecast_df["Revenue"],
            mode="lines+markers",
            name="Revenue",
            line={"width": 3, "color": "#3b82f6"}
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast_df["Quarter"],
            y=forecast_df["EBITDA"],
            mode="lines+markers",
            name="EBITDA",
            line={"width": 2, "color": "#10b981", "dash": "dash"}
        )
    )
    fig.add_trace(
        go.Bar(
            x=forecast_df["Quarter"],
            y=forecast_df["Cash"],
            name="Cash Available",
            marker={"color": "rgba(59, 130, 246, 0.2)"}
        )
    )
    return apply_dark_layout(fig, "Business Cash Flow & Revenue Trend")


def create_allocation_chart(allocation_dict: Dict[str, float], title: str) -> go.Figure:
    labels = list(allocation_dict.keys())
    values = list(allocation_dict.values())
    
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                textinfo="percent+label",
                marker={"colors": ["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b", "#ef4444", "#ec4899", "#6366f1", "#14b8a6"]}
            )
        ]
    )
    return apply_dark_layout(fig, title)


def create_sensitivity_chart(sensitivity_curve: List[Dict[str, Any]], base_method: str) -> go.Figure:
    df = pd.DataFrame(sensitivity_curve)
    df["percentage_change"] = df["percentage_change"] * 100
    
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["percentage_change"],
            y=df["valuation"],
            mode="lines+markers",
            name="Valuation Range",
            line={"width": 3, "color": "#10b981"},
            marker={"size": 8, "color": "#34d399"}
        )
    )
    fig.update_xaxes(title_text="% Change in Metric", tickformat=".0f")
    fig.update_yaxes(title_text="Valuation ($)")
    return apply_dark_layout(fig, f"Valuation Sensitivity for {base_method}")


def create_scenario_comparison(comparison_data: List[Dict[str, Any]]) -> go.Figure:
    # comparison_data: [{"Metric": "Tax", "Baseline": 12000, "Scenario": 15000}, ...]
    df = pd.DataFrame(comparison_data)
    
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["Metric"],
            y=df["Baseline"],
            name="Baseline",
            marker={"color": "#3b82f6"}
        )
    )
    fig.add_trace(
        go.Bar(
            x=df["Metric"],
            y=df["Scenario"],
            name="Selected Scenario",
            marker={"color": "#8b5cf6"}
        )
    )
    return apply_dark_layout(fig, "Scenario Comparison")
