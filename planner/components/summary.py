from dash import html
import dash_bootstrap_components as dbc
from typing import List, Dict, Any

def render_explain_panel(
    title: str,
    formula: str,
    inputs: Dict[str, Any],
    assumptions: str,
    rules: str,
    steps: List[str]
) -> html.Div:
    """
    Renders an Explanation Panel detailing calculations, rules, and formulas.
    """
    input_badges = []
    for k, v in inputs.items():
        if isinstance(v, dict):
            # Just print the counts or summary
            val_str = f"{len(v)} items"
        elif isinstance(v, float) or isinstance(v, int):
            val_str = f"${v:,.2f}" if v > 100 else str(v)
        else:
            val_str = str(v)
        input_badges.append(
            dbc.Badge(f"{k}: {val_str}", color="secondary", className="me-2 mb-2")
        )
        
    step_elements = []
    for step in steps:
        step_elements.append(html.Li(step, className="mb-2", style={"fontSize": "0.9rem", "lineHeight": "1.4"}))
        
    return html.Div(
        [
            html.Div(
                [
                    html.Span("ℹ️", className="me-2", style={"fontSize": "1.2rem"}),
                    html.Span(f"Calculation Audit: {title}", className="explain-header-title")
                ],
                className="explain-header"
            ),
            html.Div(
                [
                    html.Label("Formula / Methodology:", className="text-muted mb-1", style={"fontSize": "0.8rem", "textTransform": "uppercase"}),
                    html.Div(formula, style={"fontFamily": "monospace", "fontSize": "1.0rem", "color": "var(--accent-purple)", "marginBottom": "16px"}),
                    
                    html.Label("Inputs Used:", className="text-muted mb-1", style={"fontSize": "0.8rem", "textTransform": "uppercase"}),
                    html.Div(input_badges, className="mb-3"),
                    
                    html.Label("Assumptions Applied:", className="text-muted mb-1", style={"fontSize": "0.8rem", "textTransform": "uppercase"}),
                    html.Div(assumptions, className="mb-3", style={"fontSize": "0.9rem"}),
                    
                    html.Label("Tax Rules Referenced:", className="text-muted mb-1", style={"fontSize": "0.8rem", "textTransform": "uppercase"}),
                    html.Div(rules, className="mb-3", style={"fontSize": "0.9rem"}),
                    
                    html.Label("Step-by-step Calculation Trace:", className="text-muted mb-1", style={"fontSize": "0.8rem", "textTransform": "uppercase"}),
                    html.Ol(step_elements, className="ps-3 mb-0")
                ]
            )
        ],
        className="explain-panel"
    )

def render_empty_explain_panel():
    return html.Div(
        [
            html.Div(
                [
                    html.Span("ℹ️", className="me-2", style={"fontSize": "1.2rem"}),
                    html.Span("Calculation Audit Panel", className="explain-header-title")
                ],
                className="explain-header"
            ),
            html.P(
                "Click the information icon (ⓘ) on any metric card to trace its formula, inputs, assumptions, and rules.",
                className="text-muted mb-0",
                style={"fontSize": "0.95rem", "fontStyle": "italic"}
            )
        ],
        className="explain-panel",
        style={"borderLeftColor": "var(--text-secondary)"}
    )
