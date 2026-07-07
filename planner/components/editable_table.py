from dash import dash_table, html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
from typing import List, Dict, Any

def render_editable_table(
    table_id: str,
    df: pd.DataFrame,
    columns_config: List[Dict[str, Any]],
    add_row_btn: bool = True
) -> html.Div:
    """
    Renders an interactive, editable table matching the dashboard theme.
    columns_config: E.g. [{"name": "Description", "id": "description", "editable": True}]
    """
    columns = []
    for col in columns_config:
        col_type = col.get("type", "numeric")
        c = {
            "name": col["name"],
            "id": col["id"],
            "editable": col.get("editable", True),
            "type": col_type
        }
        if col_type == "numeric":
            # Growth rate, interest rate, tax rate, etc. should be percentage
            if "rate" in col["id"] or "growth" in col["id"] or "pct" in col["id"]:
                c["format"] = {"specifier": ".1%"}
            else:
                c["format"] = {"specifier": "$,.0f"}
        columns.append(c)

        
    table = dash_table.DataTable(
        id=table_id,
        columns=columns,
        data=df.to_dict("records"),
        editable=True,
        row_deletable=True,
        style_as_list_view=True,
        style_table={
            "overflowX": "auto",
            "minWidth": "100%",
        },
        style_cell={
            "backgroundColor": "#1e293b",
            "color": "#f8fafc",
            "border": "1px solid rgba(255, 255, 255, 0.08)",
            "padding": "10px 14px",
            "fontFamily": "Inter, sans-serif",
            "fontSize": "0.85rem",
            "textAlign": "left",
            "whiteSpace": "normal",
            "height": "auto",
        },
        style_header={
            "backgroundColor": "#0b0f19",
            "color": "#94a3b8",
            "border": "1px solid rgba(255, 255, 255, 0.08)",
            "fontWeight": "600",
            "textTransform": "uppercase",
            "fontSize": "0.75rem",
            "letterSpacing": "0.05em",
            "padding": "12px 14px"
        },
        style_data_conditional=[
            {
                "if": {"state": "active"},
                "backgroundColor": "#3b82f6 !important",
                "border": "1px solid #2563eb !important",
                "color": "#ffffff"
            }
        ],
        dropdown_conditional=[],
        persistence=True,
        persisted_props=["data"],
        persistence_type="session"
    )
    
    children = [table]
    if add_row_btn:
        children.append(
            dbc.Button(
                "+ Add Row",
                id=f"{table_id}-add-btn",
                n_clicks=0,
                color="secondary",
                className="mt-2",
                size="sm"
            )
        )
        
    return html.Div(children)
