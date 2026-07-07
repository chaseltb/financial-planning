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
    quarters: int = 8
) -> List[Dict[str, Any]]:
    """
    Projects Net Worth forward quarterly based on annual asset growth rates and liability interest payments.
    """
    projection = []
    
    current_assets = [dict(a) for a in assets]
    current_liabilities = [dict(l) for l in liabilities]
    
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
            
        # Amortize liabilities (interest accrued, payments made)
        for l in current_liabilities:
            val = float(l["value"])
            if val <= 0:
                continue
            i_rate = float(l.get("interest_rate", 0.05))
            monthly_pay = float(l.get("monthly_payment", 0.0))
            
            # Quarterly payments: 3 months of interest and payment
            quarterly_payment = monthly_pay * 3
            for _ in range(3):
                interest_accrued = val * (i_rate / 12.0)
                val = max(0.0, val + interest_accrued - monthly_pay)
                
            l["value"] = val
            
        nw_calc = calculate_net_worth(current_assets, current_liabilities)
        projection.append({
            "Quarter": f"Q{q}",
            "Assets": nw_calc["total_assets"],
            "Liabilities": nw_calc["total_liabilities"],
            "Net Worth": nw_calc["value"]
        })
        
    return projection
