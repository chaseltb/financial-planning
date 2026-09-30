from typing import Dict, Any

def calculate_depreciation(
    cost_basis: float,
    useful_life: int,
    method: str = "Straight Line",
    salvage_value: float = 0.0,
    year_index: int = 1
) -> Dict[str, Any]:
    """
    Calculates depreciation expense for a business asset.
    Methods: "Straight Line", "MACRS 5-Year", "MACRS 7-Year".
    """
    depreciation_expense = 0.0
    book_value_start = cost_basis
    book_value_end = cost_basis
    
    macrs_5_rates = [0.20, 0.32, 0.192, 0.1152, 0.1152, 0.0576]
    macrs_7_rates = [0.1429, 0.2449, 0.1749, 0.1249, 0.0893, 0.0892, 0.0893, 0.0446]
    
    steps = [
        f"Cost Basis: ${cost_basis:,.2f}",
        f"Salvage Value: ${salvage_value:,.2f}",
        f"Useful Life: {useful_life} years",
        f"Depreciation Method: {method}"
    ]
    
    if method == "Straight Line":
        annual_expense = max(0.0, (cost_basis - salvage_value) / useful_life) if useful_life > 0 else 0.0
        # No depreciation once the asset's useful life has been fully expensed.
        depreciation_expense = annual_expense if 1 <= year_index <= useful_life else 0.0
        accumulated_depreciation = annual_expense * min(max(year_index, 0), useful_life)
        book_value_end = max(salvage_value, cost_basis - accumulated_depreciation)
        book_value_start = max(salvage_value, cost_basis - (annual_expense * min(max(year_index - 1, 0), useful_life)))
        
        steps.append("Formula: (Cost Basis - Salvage Value) / Useful Life")
        steps.append(f"Calculation: (${cost_basis:,.2f} - ${salvage_value:,.2f}) / {useful_life} = ${annual_expense:,.2f} per year")
        steps.append(f"Year {year_index} Book Value: Start: ${book_value_start:,.2f} | End: ${book_value_end:,.2f}")
        
    elif "MACRS 5-Year" in method:
        # Beyond the last table year the asset is fully depreciated: rate is 0, not a repeat of the last rate.
        idx = year_index - 1
        rate = macrs_5_rates[idx] if 0 <= idx < len(macrs_5_rates) else 0.0
        depreciation_expense = cost_basis * rate
        
        accumulated_dep = sum(macrs_5_rates[:max(idx + 1, 0)]) * cost_basis
        book_value_end = max(0.0, cost_basis - accumulated_dep)
        book_value_start = max(0.0, cost_basis - sum(macrs_5_rates[:max(idx, 0)]) * cost_basis)
        
        steps.append(f"Formula: Cost Basis * MACRS 5-Year Rate for Year {year_index}")
        steps.append(f"Calculation: ${cost_basis:,.2f} * {rate*100:.2f}% = ${depreciation_expense:,.2f}")
        steps.append(f"Year {year_index} Book Value: Start: ${book_value_start:,.2f} | End: ${book_value_end:,.2f}")
        
    elif "MACRS 7-Year" in method:
        # Beyond the last table year the asset is fully depreciated: rate is 0, not a repeat of the last rate.
        idx = year_index - 1
        rate = macrs_7_rates[idx] if 0 <= idx < len(macrs_7_rates) else 0.0
        depreciation_expense = cost_basis * rate
        
        accumulated_dep = sum(macrs_7_rates[:max(idx + 1, 0)]) * cost_basis
        book_value_end = max(0.0, cost_basis - accumulated_dep)
        book_value_start = max(0.0, cost_basis - sum(macrs_7_rates[:max(idx, 0)]) * cost_basis)
        
        steps.append(f"Formula: Cost Basis * MACRS 7-Year Rate for Year {year_index}")
        steps.append(f"Calculation: ${cost_basis:,.2f} * {rate*100:.2f}% = ${depreciation_expense:,.2f}")
        steps.append(f"Year {year_index} Book Value: Start: ${book_value_start:,.2f} | End: ${book_value_end:,.2f}")
        
    return {
        "value": depreciation_expense,
        "book_value_start": book_value_start,
        "book_value_end": book_value_end,
        "trace": {
            "formula": f"Method: {method} Depreciation",
            "inputs": {
                "cost_basis": cost_basis,
                "useful_life": useful_life,
                "salvage_value": salvage_value,
                "year_index": year_index
            },
            "assumptions_used": "IRS depreciation schedules (MACRS half-year convention default rates applied).",
            "rules_referenced": "IRS MACRS Table A-1 Rates",
            "steps": steps
        }
    }
