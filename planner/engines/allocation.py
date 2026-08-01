from typing import Dict, Any


def calculate_budget_allocation(net_cash_flow: float, allocation_pct: Dict[str, float]) -> Dict[str, Any]:
    """
    Splits any leftover cash flow (income minus expenses, debt service, retirement
    contributions, and taxes) across user-chosen destinations — e.g. additional
    savings, extra liability paydown, taxable brokerage contributions. Percentages
    are normalized to sum to 100 so the split is always well-defined even if the
    raw inputs don't add up exactly. Negative cash flow means there's a shortfall,
    not a surplus to allocate, so nothing is distributed in that case.
    """
    available = max(0.0, net_cash_flow)

    total_pct = sum(max(0.0, float(v)) for v in allocation_pct.values())
    if total_pct <= 0:
        normalized = {k: 0.0 for k in allocation_pct}
    else:
        normalized = {k: max(0.0, float(v)) / total_pct * 100.0 for k, v in allocation_pct.items()}

    amounts = {k: available * (pct / 100.0) for k, pct in normalized.items()}

    return {
        "net_cash_flow": net_cash_flow,
        "available_to_allocate": available,
        "has_shortfall": net_cash_flow < 0,
        "normalized_pct": normalized,
        "amounts": amounts,
    }
