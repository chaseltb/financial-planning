from dash import dash_table, html
import dash_bootstrap_components as dbc
import pandas as pd
from typing import List, Dict, Any, Optional


def render_editable_table(
    table_id: str,
    df: pd.DataFrame,
    columns_config: List[Dict[str, Any]],
    add_row_btn: bool = True,
    empty_label: Optional[str] = None,
) -> html.Div:
    """
    Renders an interactive, editable table matching the dashboard theme.

    columns_config: E.g. [{"name": "Description", "id": "description", "editable": True}]
    empty_label: Text shown in empty state. Defaults to "No entries yet".
    """
    # ── Empty-state: meaningful placeholder instead of blank table ───────────
    if df is None or df.empty or len(df) == 0:
        noun = empty_label or "entries"
        children: list = [
            html.Div(
                [
                    html.I(className="bi bi-inbox display-6 text-muted mb-3 d-block"),
                    html.P(
                        f"No {noun} yet.",
                        className="text-muted mb-1",
                        style={"fontSize": "0.95rem", "fontWeight": "600"},
                    ),
                    html.P(
                        f"Click the button below to add your first entry.",
                        className="text-muted mb-3",
                        style={"fontSize": "0.82rem"},
                    ),
                ],
                className="text-center py-4",
            ),
        ]
        if add_row_btn:
            children.append(
                dbc.Button(
                    [html.I(className="bi bi-plus-circle me-1"), f"Add {noun.rstrip('s').title()}"],
                    id=f"{table_id}-add-btn",
                    n_clicks=0,
                    color="primary",
                    size="sm",
                    className="mt-1",
                )
            )
        return html.Div(children)

    # ── Build column config ────────────────────────────────────────────────────
    columns = []
    for col in columns_config:
        col_type = col.get("type", "numeric")
        c = {
            "name": col["name"],
            "id": col["id"],
            "editable": col.get("editable", True),
            "type": col_type,
        }
        if col_type == "numeric":
            if "rate" in col["id"] or "growth" in col["id"] or "pct" in col["id"]:
                c["format"] = {"specifier": ".1%"}
            else:
                c["format"] = {"specifier": "$,.0f"}
        columns.append(c)

    # Ensure all column IDs exist in the dataframe to avoid KeyError
    for col in columns_config:
        if col["id"] not in df.columns:
            df[col["id"]] = None

    table = dash_table.DataTable(
        id=table_id,
        columns=columns,
        data=df.to_dict("records"),
        editable=True,
        row_deletable=True,
        style_as_list_view=True,
        # ── Persistence intentionally disabled ──────────────────────────────
        # State is owned by project-state-store + JSON backend.
        # Browser-level persistence would override fresh data on scenario switch.
        persistence=False,
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
            "minWidth": "80px",
        },
        style_header={
            "backgroundColor": "#0b0f19",
            "color": "#94a3b8",
            "border": "1px solid rgba(255, 255, 255, 0.08)",
            "fontWeight": "600",
            "textTransform": "uppercase",
            "fontSize": "0.75rem",
            "letterSpacing": "0.05em",
            "padding": "12px 14px",
        },
        style_data_conditional=[
            {
                "if": {"state": "active"},
                "backgroundColor": "#3b82f6 !important",
                "border": "1px solid #2563eb !important",
                "color": "#ffffff",
            }
        ],
    )

    children = [table]
    if add_row_btn:
        children.append(
            dbc.Button(
                [html.I(className="bi bi-plus-circle me-1"), "Add Row"],
                id=f"{table_id}-add-btn",
                n_clicks=0,
                color="secondary",
                className="mt-2",
                size="sm",
            )
        )

    return html.Div(children)
