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


def render_metric_card(title: str, value: str, subtitle: str = None, color_class: str = "", explain_target: str = None, primary: bool = False,
                       lg: int = None, xl: int = None):
    """
    Renders a glassmorphic metric card.
    color_class: can be "emerald" or "purple" (default is blue).
    explain_target: if provided, the card has an info button to trigger the Explain panel.
    primary: if True, applies subtle primary highlight styling while maintaining equal dimensions.
    """
    card_class = f"glass-card metric-card {color_class}" + (" metric-card-primary" if primary else "")
    value_class = "metric-value-lg mb-1" if primary else "metric-value mb-1"

    # Optional info/explain icon button
    header_children = [html.Div(title, className="metric-title")]
    if explain_target:
        header_children.append(
            html.Button(
                html.I(className="bi bi-info-circle", **{"aria-hidden": "true"}),
                id={"type": "explain-trigger", "target": explain_target},
                className="explain-trigger-btn",
                n_clicks=0,
                title=f"Show how {title} is calculated",
                **{"aria-label": f"Show how {title} is calculated"},
            )
        )

    return dbc.Col(
        html.Div(
            [
                html.Div(header_children, style={"display": "flex", "alignItems": "center", "width": "100%"}),
                html.Div(value, className=value_class),
                html.Div(subtitle or "—", className="text-muted", style={"fontSize": "0.8rem"})
            ],
            className=card_class
        ),
        xs=12, sm=12 if primary else 6, md=12 if primary else 6,
        lg=lg if lg is not None else (12 if primary else 3),
        xl=xl if xl is not None else (6 if primary else 3),
        className="mb-4"
    )


def render_kpi_strip(items):
    """One card holding every headline metric, separated by thin dividers, instead of
    a row of separate small cards. items: [{"title", "value", "subtitle", "color_class",
    "explain_target", "primary", "business_only"}, ...]. The primary item is rendered
    larger; business-only items drop out (and the rest re-flow) when Business Mode is off."""
    cells = []
    for item in items:
        primary = item.get("primary", False)
        header = [html.Div(item["title"], className="metric-title")]
        if item.get("explain_target"):
            header.append(
                html.Button(
                    html.I(className="bi bi-info-circle", **{"aria-hidden": "true"}),
                    id={"type": "explain-trigger", "target": item["explain_target"]},
                    className="explain-trigger-btn",
                    n_clicks=0,
                    title=f"Show how {item['title']} is calculated",
                    **{"aria-label": f"Show how {item['title']} is calculated"},
                )
            )
        classes = "kpi-item metric-card " + item.get("color_class", "")
        if primary:
            classes += " kpi-item-primary"
        if item.get("business_only"):
            classes += " business-only"
        cells.append(
            html.Div(
                [
                    html.Div(header, className="kpi-header"),
                    html.Div(item["value"], className="metric-value-lg" if primary else "metric-value"),
                    html.Div(item.get("subtitle") or "\u2014", className="kpi-subtitle"),
                ],
                className=classes,
            )
        )
    return html.Div(cells, className="glass-card kpi-strip")
