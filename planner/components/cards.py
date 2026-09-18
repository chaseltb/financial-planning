from dash import html
import dash_bootstrap_components as dbc


def render_chip_row(items):
    """
    A single dense strip of small stat chips (title/value/subtitle), for cases
    where several metrics belong together but a full glass-card per metric
    (see render_metric_card) is too much visual weight — e.g. six valuation
    methods that are already charted below and don't each need their own card.
    items: [{"title", "value", "subtitle", "color_class"}, ...]
    """
    return html.Div(
        [
            html.Div(
                [
                    html.Div(item["title"], className="chip-title"),
                    html.Div(item["value"], className="chip-value"),
                    html.Div(item.get("subtitle") or "—", className="chip-subtitle"),
                ],
                className=f"valuation-chip {item.get('color_class', '')}",
            )
            for item in items
        ],
        className="glass-card valuation-chip-row mb-4",
    )


def render_hero_metric_card(title: str, value: str, subtitle: str = None, color_class: str = "emerald", explain_target: str = None):
    """
    Renders a prominent, larger hero metric card for the primary headline metric.
    """
    header_children = [html.Div(title, className="hero-title")]
    if explain_target:
        header_children.append(
            html.Span(
                "ⓘ",
                id={"type": "explain-trigger", "target": explain_target},
                className="ms-auto text-muted cursor-pointer",
                style={"fontSize": "0.95rem", "cursor": "pointer", "float": "right"}
            )
        )

    return html.Div(
        [
            html.Div(header_children, style={"display": "flex", "alignItems": "center", "width": "100%"}),
            html.Div(value, className="hero-value"),
            html.Div(subtitle or "—", className="hero-subtitle"),
        ],
        className=f"glass-card hero-metric-card {color_class}",
    )


def render_companion_metrics_card(metrics: list):
    """
    Combines supporting metrics into a single balanced card with equal-width
    stat columns and subtle vertical dividers, keeping the top section on 1 line.
    metrics: [{"title", "value", "subtitle", "color_class", "explain_target"}, ...]
    """
    stat_items = []
    for m in metrics:
        header = [html.Div(m["title"], className="metric-title")]
        if m.get("explain_target"):
            header.append(
                html.Span(
                    "ⓘ",
                    id={"type": "explain-trigger", "target": m["explain_target"]},
                    className="ms-auto text-muted cursor-pointer",
                    style={"fontSize": "0.85rem", "cursor": "pointer", "marginLeft": "auto"}
                )
            )
        stat_items.append(
            html.Div(
                [
                    html.Div(header, style={"display": "flex", "alignItems": "center", "width": "100%"}),
                    html.Div(m["value"], className=f"metric-value {m.get('color_class', '')}"),
                    html.Div(m.get("subtitle") or "—", className="metric-subtitle"),
                ],
                className="companion-stat-item",
            )
        )

    return html.Div(
        html.Div(stat_items, className="companion-stats-grid"),
        className="glass-card companion-metrics-card",
    )


def render_metric_card(title: str, value: str, subtitle: str = None, color_class: str = "", explain_target: str = None, primary: bool = False):
    """
    Renders a glassmorphic metric card.
    color_class: can be "emerald" or "purple" (default is blue).
    explain_target: if provided, the card has an info button to trigger the Explain panel.
    primary: if True, applies subtle primary highlight styling while maintaining equal dimensions.
    """
    card_class = f"glass-card metric-card {color_class}" + (" metric-card-primary" if primary else "")

    # Optional info/explain icon button
    header_children = [html.Div(title, className="metric-title")]
    if explain_target:
        header_children.append(
            html.Span(
                "ⓘ",
                id={"type": "explain-trigger", "target": explain_target},
                className="ms-auto text-muted cursor-pointer",
                style={"fontSize": "0.9rem", "cursor": "pointer", "float": "right"}
            )
        )

    return html.Div(
        [
            html.Div(header_children, style={"display": "flex", "alignItems": "center", "width": "100%"}),
            html.Div(value, className="metric-value mb-1"),
            html.Div(subtitle or "—", className="text-muted metric-subtitle", style={"fontSize": "0.8rem"})
        ],
        className=card_class
    )


