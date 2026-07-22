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


def create_bracket_progress_chart(brackets: List[Dict[str, float]], taxable_income: float) -> go.Figure:
    """
    Single horizontal stacked bar spanning $0 through one bracket past the
    taxpayer's current one. Each segment is one tax bracket, colored by status
    (already used / current / not yet reached) rather than by rate, since status
    is what "progression" actually means here — rate and dollar range are
    direct-labeled instead. Brackets beyond that are folded into one final
    "further brackets" segment so the relevant (usually low/mid) part of the
    scale isn't squeezed into a sliver by a $600k+ top bracket almost no one hits.
    """
    n = len(brackets)
    lowers = [br["threshold"] for br in brackets]
    uppers = lowers[1:] + [None]  # None = open-ended top bracket

    current_index = next((i for i in range(n) if uppers[i] is None or taxable_income < uppers[i]), n - 1)
    visible_count = min(current_index + 2, n)  # current bracket + one bracket of headroom
    folded_brackets = brackets[visible_count:]

    passed_color = "#3b82f6"     # accent-blue — matches app's existing brand accent
    current_color = "#10b981"    # accent-emerald — matches app's existing brand accent
    future_fill = "rgba(148, 163, 184, 0.08)"
    future_line = "rgba(148, 163, 184, 0.45)"
    gap_line = "rgba(148, 163, 184, 0.35)"

    # Give the last visible bracket a finite width: its own span if it has an
    # upper bound, otherwise (open-ended, or about to be folded away) match the
    # previous bracket's span, padded out if income actually reaches that far.
    def segment_width(i):
        if uppers[i] is not None:
            return uppers[i] - lowers[i]
        prev_span = (lowers[i] - lowers[i - 1]) if i > 0 else max(lowers[i], 1.0)
        return max(prev_span, (taxable_income - lowers[i]) * 1.15)

    widths = [segment_width(i) for i in range(visible_count)]
    fold_width = max(widths[-1], sum(widths) * 0.25) if folded_brackets else 0.0
    total_span = sum(widths) + fold_width

    fig = go.Figure()
    for i in range(visible_count):
        lower, width = lowers[i], widths[i]
        upper = lower + width
        is_open_ended = uppers[i] is None

        if i < current_index:
            status, fill, used = "passed", passed_color, width
        elif i == current_index:
            status, fill, used = "current", current_color, taxable_income - lower
        else:
            status, fill, used = "future", future_fill, 0.0

        range_label = f"${lower:,.0f}-${upper:,.0f}" if not is_open_ended else f"${lower:,.0f}+"
        if status == "future":
            detail = f"Not reached yet (starts at ${lower:,.0f})"
        elif is_open_ended:
            detail = f"${used:,.0f} taxed at this rate so far"
        else:
            detail = f"${used:,.0f} of ${width:,.0f} used"

        show_label = (width / total_span) > 0.07
        fig.add_trace(go.Bar(
            x=[width], y=["bracket"], orientation="h",
            marker={
                "color": fill,
                "line": {"color": future_line if status == "future" else gap_line, "width": 1.5},
            },
            text=f"{brackets[i]['rate']*100:.0f}%" if show_label else "",
            textposition="inside",
            insidetextfont={"color": "#f8fafc" if status != "future" else _CHART_TEXT_COLOR, "size": 13},
            customdata=[f"{brackets[i]['rate']*100:.0f}% bracket ({range_label})<br>{detail}"],
            hovertemplate="%{customdata}<extra></extra>",
            showlegend=False,
        ))

    if folded_brackets:
        fold_rates = f"{folded_brackets[0]['rate']*100:.0f}-{folded_brackets[-1]['rate']*100:.0f}%"
        fig.add_trace(go.Bar(
            x=[fold_width], y=["bracket"], orientation="h",
            marker={"color": future_fill, "line": {"color": future_line, "width": 1.5}},
            text=f"{fold_rates}" if (fold_width / total_span) > 0.1 else "",
            textposition="inside",
            insidetextfont={"color": _CHART_TEXT_COLOR, "size": 12},
            customdata=[f"Higher brackets ({fold_rates}) start above ${lowers[visible_count]:,.0f}"],
            hovertemplate="%{customdata}<extra></extra>",
            showlegend=False,
        ))

    marker_pct = min(taxable_income, total_span) / total_span
    label_anchor = "left" if marker_pct < 0.15 else ("right" if marker_pct > 0.85 else "center")

    fig.update_layout(
        barmode="stack",
        bargap=0,
        height=110,
        margin={"t": 34, "b": 30, "l": 10, "r": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis={
            "range": [0, total_span],
            "tickfont": {"size": 11, "color": _CHART_TEXT_COLOR},
            "tickprefix": "$",
            "gridcolor": _CHART_GRIDLINE_COLOR,
            "zeroline": False,
        },
        yaxis={"visible": False},
    )
    fig.add_shape(
        type="line", x0=taxable_income, x1=taxable_income, y0=0, y1=1, yref="paper",
        line={"color": _CHART_TEXT_COLOR, "width": 1.5, "dash": "dot"},
    )
    fig.add_annotation(
        x=taxable_income, y=1, yref="paper", yanchor="bottom",
        xanchor=label_anchor,
        text=f"Taxable income: ${taxable_income:,.0f}",
        showarrow=False,
        font={"color": _CHART_TEXT_COLOR, "size": 12},
    )
    return fig


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
