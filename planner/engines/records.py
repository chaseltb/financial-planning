"""Helpers that normalize raw income/expense records before any engine uses them."""
from typing import Any, Dict, List

PERIODS_PER_YEAR = {
    "annual": 1.0, "annually": 1.0, "yearly": 1.0, "year": 1.0,
    "semiannual": 2.0, "semi-annual": 2.0,
    "quarterly": 4.0,
    "monthly": 12.0,
    "biweekly": 26.0, "bi-weekly": 26.0,
    "weekly": 52.0,
}


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def annualize_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Returns copies of income/expense records with "amount" converted to a
    yearly figure based on each record's "frequency" (default Annual) and the
    frequency reset to "Annual". Idempotent, so it is safe to apply repeatedly."""
    out = []
    for rec in records or []:
        rec = dict(rec)
        freq = str(rec.get("frequency") or "Annual").strip().lower()
        rec["amount"] = _to_float(rec.get("amount", 0.0)) * PERIODS_PER_YEAR.get(freq, 1.0)
        rec["frequency"] = "Annual"
        out.append(rec)
    return out


def is_taxable(record: Dict[str, Any]) -> bool:
    """Income records default to taxable unless explicitly flagged False/0/No."""
    return str(record.get("taxable", True)).strip().lower() not in ("false", "0", "no", "n")


def taxable_income_by_category(income: List[Dict[str, Any]]) -> Dict[str, float]:
    """Sums annualized taxable income per category."""
    totals: Dict[str, float] = {}
    for inc in annualize_records(income):
        if not is_taxable(inc):
            continue
        cat = inc.get("category", "Other")
        totals[cat] = totals.get(cat, 0.0) + inc["amount"]
    return totals
