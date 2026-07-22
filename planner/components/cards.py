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


def render_metric_card(title: str, value: str, subtitle: str = None, color_class: str = "", explain_target: str = None):
    """
    Renders a glassmorphic metric card.
    color_class: can be "emerald" or "purple" (default is blue).
    explain_target: if provided, the card can have an info button or click behavior to trigger the Explain panel.
    """
    card_class = f"glass-card metric-card {color_class}"
    
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
        
    return dbc.Col(
        html.Div(
            [
                html.Div(header_children, style={"display": "flex", "alignItems": "center", "width": "100%"}),
                html.Div(value, className="metric-value mb-1"),
                html.Div(subtitle or "—", className="text-muted", style={"fontSize": "0.8rem"})
            ],
            className=card_class
        ),
        xs=12, sm=6, md=4, lg=3,
        className="mb-4"
    )
