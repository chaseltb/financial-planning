"""Click-a-row-to-edit table for simple record lists (income, expenses, assets,
liabilities): rows are plain, read-only, and clickable — the whole row opens a
shared modal that handles both editing and deleting that record, instead of
stacking a pencil/trash icon into every row. Native confirm()/alert() dialogs
are never used (Chrome silently stops showing them after a couple of uses on
one page); the delete confirmation is an inline two-step control inside the
modal itself (see render_record_modal_body's delete section).
"""
import math
from typing import Any, Dict, List, Optional

from dash import html
import dash_bootstrap_components as dbc

_ROWS_PER_PAGE = 10


def _format_value(value: Any, kind: str) -> str:
    try:
        num = float(value or 0)
    except (TypeError, ValueError):
        return str(value or "")
    if kind == "money":
        return f"${num:,.0f}"
    if kind == "percent":
        return f"{num * 100:.1f}%"
    return str(value or "")


def render_record_table(
    table_id: str,
    rows: List[Dict[str, Any]],
    columns: List[Dict[str, str]],
    page: int = 0,
    empty_label: str = "entries",
) -> html.Div:
    """columns: [{"id": "amount", "name": "Amount ($/yr)", "type": "money"|"percent"|"text"}, ...]"""
    if not rows:
        return html.Div(
            html.P(f"No {empty_label} yet. Click \"Add Row\" above to add your first entry.",
                   className="text-muted text-center py-4 mb-0", style={"fontSize": "0.9rem"}),
        )

    total_pages = max(1, math.ceil(len(rows) / _ROWS_PER_PAGE))
    page = max(0, min(page, total_pages - 1))
    page_rows = rows[page * _ROWS_PER_PAGE: (page + 1) * _ROWS_PER_PAGE]

    header = html.Thead(html.Tr([html.Th(c["name"]) for c in columns]))
    body = html.Tbody([
        html.Tr(
            [html.Td(_format_value(row.get(c["id"]), c.get("type", "text"))) for c in columns],
            id={"type": "record-row", "table": table_id, "row": page * _ROWS_PER_PAGE + i},
            n_clicks=0,
            className="record-row",
        )
        for i, row in enumerate(page_rows)
    ])
    table = dbc.Table([header, body], bordered=False, hover=False, size="sm",
                       className="themed-table record-table mb-0", responsive=True)

    if total_pages <= 1:
        return html.Div(table)

    pager = html.Div(
        [
            dbc.Button("‹ Prev", id={"type": "record-page-nav", "table": table_id, "dir": "prev"},
                       size="sm", color="secondary", outline=True, disabled=page == 0, className="me-2"),
            html.Span(f"Page {page + 1} of {total_pages}", className="text-muted", style={"fontSize": "0.8rem"}),
            dbc.Button("Next ›", id={"type": "record-page-nav", "table": table_id, "dir": "next"},
                       size="sm", color="secondary", outline=True, disabled=page >= total_pages - 1, className="ms-2"),
        ],
        className="d-flex align-items-center justify-content-end mt-2",
    )
    return html.Div([table, pager])


def render_record_modal(modal_id: str) -> dbc.Modal:
    """Static modal shell — its title/body/footer are filled in dynamically by
    a page-level callback based on which table/row is currently being edited."""
    return dbc.Modal(
        [
            dbc.ModalHeader(html.Span(id=f"{modal_id}-title"), close_button=True),
            dbc.ModalBody(id=f"{modal_id}-body"),
            dbc.ModalFooter(id=f"{modal_id}-footer"),
        ],
        id=modal_id,
        is_open=False,
        centered=True,
    )


def render_field_input(field_def: Dict[str, Any], value: Any) -> html.Div:
    """One labeled form field inside the record modal, keyed by a pattern-matching id."""
    field = field_def["field"]
    if field_def["type"] == "number":
        display_value = float(value or 0.0) * (100.0 if field_def.get("percent") else 1.0)
        control = dbc.Input(
            id={"type": "record-field", "field": field},
            type="number", value=display_value, debounce=True,
        )
    else:
        control = dbc.Input(
            id={"type": "record-field", "field": field},
            type="text", value=value or "", debounce=True,
        )
    return html.Div([dbc.Label(field_def["label"], size="sm"), control], className="mb-3")
