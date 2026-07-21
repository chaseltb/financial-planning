from dash import dash_table, html
from dash.dash_table.Format import Format, Scheme, Group, Symbol
import dash_bootstrap_components as dbc
import pandas as pd
from typing import List, Dict, Any, Optional

_MONEY_FORMAT = Format(scheme=Scheme.fixed, precision=0, group=Group.yes, symbol=Symbol.yes, symbol_prefix="$")
_PERCENT_FORMAT = Format(scheme=Scheme.percentage, precision=1)

# Matched by column id across every table using this component.
_COLUMN_TOOLTIPS = {
    "category": "Groups this entry for reporting. Pick the closest match, or use 'Other' if nothing fits.",
    "description": "A short label so you can tell entries apart. Doesn't affect any calculations.",
    "amount": "Enter the full yearly amount, not a monthly one.",
    "value": "Current balance or market value, as of today.",
    "growth_rate": "Expected annual growth, entered as a decimal (0.07 = 7% per year).",
    "interest_rate": "Annual Percentage Rate (APR) on this debt, entered as a decimal (0.05 = 5%).",
    "monthly_payment": "The regular monthly payment you make toward this debt.",
}


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
        col_type = col.get("type", "text")
        c = {
            "name": col["name"],
            "id": col["id"],
            "editable": col.get("editable", True),
            "type": col_type,
        }
        if col_type == "numeric":
            if "rate" in col["id"] or "growth" in col["id"] or "pct" in col["id"]:
                c["format"] = _PERCENT_FORMAT
            else:
                c["format"] = _MONEY_FORMAT
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
        # Disabled: browser-level persistence would override fresh data on scenario switch.
        persistence=False,
        tooltip_header={
            col["id"]: {"value": _COLUMN_TOOLTIPS[col["id"]], "type": "text"}
            for col in columns_config
            if col["id"] in _COLUMN_TOOLTIPS
        },
        tooltip_delay=300,
        tooltip_duration=None,
        css=[
            # Header tooltip icon so it's obvious a hint is available.
            {"selector": ".dash-table-tooltip", "rule": "max-width: 260px; white-space: normal;"},
        ],
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
        # Active-cell border only (not a solid fill) so typed text stays readable.
        style_data_conditional=[
            {
                "if": {"state": "active"},
                "backgroundColor": "#1e293b",
                "border": "2px solid #3b82f6",
                "color": "#f8fafc",
            },
            {
                "if": {"state": "selected"},
                "backgroundColor": "#1e293b",
                "border": "1px solid #3b82f6",
            },
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
