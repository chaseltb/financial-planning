from dash import dash_table, html
from dash.dash_table.Format import Format, Scheme, Group, Symbol
import dash_bootstrap_components as dbc
import pandas as pd
from typing import List, Dict, Any, Optional

_MONEY_FORMAT = Format(scheme=Scheme.fixed, precision=0, group=Group.yes, symbol=Symbol.yes, symbol_prefix="$")
# Percent columns are stored internally as fractions (0.07) but shown/edited as whole
# percentage points (7), matching how percent fields elsewhere in the app already work
# (see business.py/valuation.py). Dash DataTable's Scheme.percentage format only ever
# multiplies by 100 for DISPLAY — it doesn't do the reverse when a value is typed in, so
# pairing it directly with a fraction-valued column meant 0.06 correctly showed "6.0%" on
# load, but typing "6" (expecting 6%) got taken as the literal fraction 6 and redisplayed
# as "600.0%". Converting to whole-percentage-point values before rendering (and back to
# a fraction on save) keeps what's typed and what's shown consistent.
_PERCENT_FORMAT = Format(scheme=Scheme.fixed, precision=1, symbol=Symbol.yes, symbol_suffix="%")
_PERCENT_COLUMN_KEYWORDS = ("rate", "growth", "pct")


def is_percent_column(col_id: str) -> bool:
    return any(k in col_id for k in _PERCENT_COLUMN_KEYWORDS)


# Matched by column id across every table using this component.
_COLUMN_TOOLTIPS = {
    "category": "Groups this entry for reporting. Pick the closest match, or use 'Other' if nothing fits.",
    "description": "A short label so you can tell entries apart. Doesn't affect any calculations.",
    "amount": "Enter the full yearly amount, not a monthly one.",
    "value": "Current balance or market value, as of today.",
    "growth_rate": "Expected annual growth, as a whole percentage (7 = 7% per year).",
    "interest_rate": "Annual Percentage Rate (APR) on this debt, as a whole percentage (5 = 5%).",
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
    # ── Empty-state: meaningful placeholder shown instead of the table ───────────
    # The DataTable itself is still rendered below (hidden via CSS, not omitted) —
    # a Dash callback with an Input on this component's id errors out and never
    # fires for ANY of its inputs if the component isn't currently present in the
    # layout at all. Previously this branch returned early with a totally different
    # html.Div (no DataTable, no matching id), so as soon as one table's list went
    # empty, every callback that included it as an Input — even ones for unrelated
    # fields on the same page — silently stopped firing.
    is_empty = df is None or df.empty or len(df) == 0
    noun = empty_label or "entries"
    empty_placeholder = html.Div(
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
        style={} if is_empty else {"display": "none"},
    )

    if df is None or df.empty:
        df = pd.DataFrame(columns=[c["id"] for c in columns_config])

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
            if is_percent_column(col["id"]):
                c["format"] = _PERCENT_FORMAT
            else:
                c["format"] = _MONEY_FORMAT
        columns.append(c)

    # Ensure all column IDs exist in the dataframe to avoid KeyError
    df = df.copy()
    for col in columns_config:
        if col["id"] not in df.columns:
            df[col["id"]] = None

    # Percent columns: convert stored fractions to whole percentage points for display/edit.
    for col in columns_config:
        if is_percent_column(col["id"]):
            df[col["id"]] = pd.to_numeric(df[col["id"]], errors="coerce").fillna(0.0) * 100.0

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
            **({"display": "none"} if is_empty else {}),
        },
        style_cell={
            # CSS custom properties, not hardcoded hex — these need to track the
            # light/dark theme toggle (data-theme on <html>, see styles.css), not
            # stay pinned to dark-mode colors regardless of the active theme.
            "backgroundColor": "var(--bg-secondary)",
            "color": "var(--text-primary)",
            "border": "1px solid var(--border-glass)",
            "padding": "10px 14px",
            "fontFamily": "Inter, sans-serif",
            "fontSize": "0.85rem",
            "textAlign": "left",
            "whiteSpace": "normal",
            "height": "auto",
            "minWidth": "80px",
        },
        style_header={
            "backgroundColor": "var(--bg-sidebar)",
            "color": "var(--text-secondary)",
            "border": "1px solid var(--border-glass)",
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
                "backgroundColor": "var(--bg-secondary)",
                "border": "2px solid var(--accent-blue)",
                "color": "var(--text-primary)",
            },
            {
                "if": {"state": "selected"},
                "backgroundColor": "var(--bg-secondary)",
                "border": "1px solid var(--accent-blue)",
            },
        ],
    )

    children = [empty_placeholder, table]
    if add_row_btn:
        button_label = f"Add {noun.rstrip('s').title()}" if is_empty else "Add Row"
        children.append(
            dbc.Button(
                [html.I(className="bi bi-plus-circle me-1"), button_label],
                id=f"{table_id}-add-btn",
                n_clicks=0,
                color="primary" if is_empty else "secondary",
                className="mt-1" if is_empty else "mt-2",
                size="sm",
            )
        )

    return html.Div(children)
