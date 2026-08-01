from typing import List, Dict, Any

def calculate_net_worth(
    assets: List[Dict[str, Any]],
    liabilities: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculates Net Worth, asset allocations, debt allocations, and provides an explanation trace.
    """
    total_assets = sum(float(a.get("value", 0.0)) for a in assets)
    total_liabilities = sum(float(l.get("value", 0.0)) for l in liabilities)
    net_worth = total_assets - total_liabilities
    
    # Asset Allocation
    asset_allocation = {}
    for a in assets:
        cat = a.get("category", "Other")
        val = float(a.get("value", 0.0))
        asset_allocation[cat] = asset_allocation.get(cat, 0.0) + val
        
    asset_pct = {}
    for cat, val in asset_allocation.items():
        asset_pct[cat] = val / total_assets if total_assets > 0 else 0.0
        
    # Debt Allocation
    debt_allocation = {}
    for l in liabilities:
        cat = l.get("category", "Other")
        val = float(l.get("value", 0.0))
        debt_allocation[cat] = debt_allocation.get(cat, 0.0) + val
        
    debt_pct = {}
    for cat, val in debt_allocation.items():
        debt_pct[cat] = val / total_liabilities if total_liabilities > 0 else 0.0
        
    steps = [
        f"Total Assets: Sum of all assets = ${total_assets:,.2f}",
        f"Total Liabilities: Sum of all liabilities = ${total_liabilities:,.2f}",
        f"Net Worth: Total Assets (${total_assets:,.2f}) - Total Liabilities (${total_liabilities:,.2f}) = ${net_worth:,.2f}"
    ]
    
    # Add details to steps
    steps.append("Asset Breakdown:")
    for a in assets:
        steps.append(f"  - {a.get('description', 'Unnamed')} ({a.get('category')}): ${float(a.get('value', 0.0)):,.2f} (Growth: {float(a.get('growth_rate', 0.0))*100:.1f}%)")
        
    steps.append("Liability Breakdown:")
    for l in liabilities:
        steps.append(f"  - {l.get('description', 'Unnamed')} ({l.get('category')}): ${float(l.get('value', 0.0)):,.2f} (Interest: {float(l.get('interest_rate', 0.0))*100:.1f}%)")
        
    return {
        "value": net_worth,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "asset_allocation": asset_allocation,
        "asset_pct": asset_pct,
        "debt_allocation": debt_allocation,
        "debt_pct": debt_pct,
        "trace": {
            "formula": "Net Worth = Total Assets - Total Liabilities",
            "inputs": {
                "asset_count": len(assets),
                "liability_count": len(liabilities)
            },
            "assumptions_used": "Assets and liabilities are priced at fair market value.",
            "rules_referenced": "Basic double-entry ledger valuation rules.",
            "steps": steps
        }
    }


def project_net_worth(
    assets: List[Dict[str, Any]],
    liabilities: List[Dict[str, Any]],
    quarters: int = 8,
    quarterly_allocation: Dict[str, float] = None,
) -> List[Dict[str, Any]]:
    """
    Projects Net Worth forward quarterly based on annual asset growth rates and
    liability interest payments. quarterly_allocation (if given) layers in the
    user's chosen split of each quarter's leftover cash flow: "Savings" and
    "Taxable Brokerage" amounts are contributed into the matching asset category
    (or a new bucket at a sensible default growth rate, if no such asset exists
    yet) so they compound forward like any other asset; "Liability Paydown" pays
    down the highest-interest liability first (debt avalanche), on top of each
    liability's own scheduled monthly payments.
    """
    quarterly_allocation = quarterly_allocation or {}
    savings_alloc = max(0.0, float(quarterly_allocation.get("Savings", 0.0)))
    brokerage_alloc = max(0.0, float(quarterly_allocation.get("Taxable Brokerage", 0.0)))
    liability_paydown_alloc = max(0.0, float(quarterly_allocation.get("Liability Paydown", 0.0)))

    projection = []

    current_assets = [dict(a) for a in assets]
    current_liabilities = [dict(l) for l in liabilities]

    def _find_or_create_bucket(category_keyword, label, default_growth_rate):
        for a in current_assets:
            if category_keyword in str(a.get("category", "")).lower():
                return a
        bucket = {"category": label, "description": f"{label} (from allocated budget)",
                  "value": 0.0, "growth_rate": default_growth_rate}
        current_assets.append(bucket)
        return bucket

    savings_bucket = _find_or_create_bucket("cash", "Cash", 0.02) if savings_alloc > 0 else None
    brokerage_bucket = _find_or_create_bucket("brokerage", "Brokerage", 0.07) if brokerage_alloc > 0 else None

    # Calculate initial net worth
    nw_calc = calculate_net_worth(current_assets, current_liabilities)
    projection.append({
        "Quarter": "Current",
        "Assets": nw_calc["total_assets"],
        "Liabilities": nw_calc["total_liabilities"],
        "Net Worth": nw_calc["value"]
    })

    for q in range(1, quarters + 1):
        # Grow assets by quarterly rate (annual growth rate / 4)
        for a in current_assets:
            g_rate = float(a.get("growth_rate", 0.05))
            a["value"] = float(a["value"]) * (1.0 + g_rate / 4.0)

        # Contribute this quarter's allocated savings/brokerage split (after
        # growth, so a fresh contribution doesn't earn a partial quarter of return).
        if savings_bucket is not None:
            savings_bucket["value"] = float(savings_bucket["value"]) + savings_alloc
        if brokerage_bucket is not None:
            brokerage_bucket["value"] = float(brokerage_bucket["value"]) + brokerage_alloc

        # Amortize liabilities (interest accrued, scheduled payments made)
        for l in current_liabilities:
            val = float(l["value"])
            if val <= 0:
                continue
            i_rate = float(l.get("interest_rate", 0.05))
            monthly_pay = float(l.get("monthly_payment", 0.0))

            # Quarterly payments: 3 months of interest and payment
            for _ in range(3):
                interest_accrued = val * (i_rate / 12.0)
                val = max(0.0, val + interest_accrued - monthly_pay)

            l["value"] = val

        # Extra principal paydown from the allocated budget: debt avalanche
        # (highest interest rate first), on top of the scheduled payments above.
        remaining_paydown = liability_paydown_alloc
        if remaining_paydown > 0:
            for l in sorted(current_liabilities, key=lambda l: -float(l.get("interest_rate", 0.0))):
                if remaining_paydown <= 0:
                    break
                val = float(l["value"])
                if val <= 0:
                    continue
                pay = min(val, remaining_paydown)
                l["value"] = val - pay
                remaining_paydown -= pay

        nw_calc = calculate_net_worth(current_assets, current_liabilities)
        projection.append({
            "Quarter": f"Q{q}",
            "Assets": nw_calc["total_assets"],
            "Liabilities": nw_calc["total_liabilities"],
            "Net Worth": nw_calc["value"]
        })

    return projection
