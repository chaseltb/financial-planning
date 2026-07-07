from typing import Dict, Any, List

def calculate_combined_cashflow(
    personal_income: List[Dict[str, Any]],
    personal_expenses: List[Dict[str, Any]],
    liabilities: List[Dict[str, Any]],
    retirement_contributions: Dict[str, float],
    tax_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Computes annualized personal inflows, outflows, and net cash flow.
    """
    # Inflows
    w2 = 0.0
    consulting_1099 = 0.0
    dividends = 0.0
    interest = 0.0
    rental = 0.0
    other_inflow = 0.0
    
    for inc in personal_income:
        cat = inc.get("category")
        amt = float(inc.get("amount", 0.0))
        if cat == "W-2":
            w2 += amt
        elif cat == "1099":
            consulting_1099 += amt
        elif cat == "Dividends":
            dividends += amt
        elif cat == "Interest":
            interest += amt
        elif cat == "Rental income":
            rental += amt
        else:
            other_inflow += amt
            
    total_inflows = w2 + consulting_1099 + dividends + interest + rental + other_inflow
    
    # Outflows
    housing = 0.0
    other_expenses = 0.0
    for exp in personal_expenses:
        cat = exp.get("category")
        amt = float(exp.get("amount", 0.0))
        if cat == "Housing":
            housing += amt
        else:
            other_expenses += amt
            
    # Add debt service payments (excluding mortgage if it is already counted in housing)
    debt_service = 0.0
    for liab in liabilities:
        cat = liab.get("category")
        monthly_pay = float(liab.get("monthly_payment", 0.0))
        # Avoid double-counting mortgage if housing expenses already include it
        if cat == "Mortgage" and housing > 0:
            continue
        debt_service += monthly_pay * 12.0
        
    # Pre-tax retirement contributions (outflow from gross cash, though it goes to assets)
    retirement_outflow = sum(retirement_contributions.values())
    
    # Taxes (FICA, SE Tax, personal income tax, etc. from tax engine)
    total_tax_outflow = tax_result.get("combined_tax", tax_result.get("value", 0.0))
    
    total_outflows = housing + other_expenses + debt_service + retirement_outflow + total_tax_outflow
    
    net_cash_flow = total_inflows - total_outflows
    
    steps = [
        f"1. Cash Inflows: W-2 (${w2:,.2f}) + 1099 (${consulting_1099:,.2f}) + Dividends/Interest (${dividends+interest:,.2f}) + Rental (${rental:,.2f}) + Other (${other_inflow:,.2f}) = ${total_inflows:,.2f}",
        f"2. Cash Outflows:",
        f"   - Housing expenses: ${housing:,.2f}",
        f"   - Other personal expenses: ${other_expenses:,.2f}",
        f"   - Non-housing debt service (annualized): ${debt_service:,.2f}",
        f"   - Retirement savings (401k, IRA, HSA): ${retirement_outflow:,.2f}",
        f"   - Combined taxes (Federal, NC, FICA/SE): ${total_tax_outflow:,.2f}",
        f"   - Total Outflows: ${total_outflows:,.2f}",
        f"3. Net Cash Flow: Inflows (${total_inflows:,.2f}) - Outflows (${total_outflows:,.2f}) = ${net_cash_flow:,.2f}"
    ]
    
    return {
        "value": net_cash_flow,
        "total_inflows": total_inflows,
        "total_outflows": total_outflows,
        "breakdown": {
            "inflows": {
                "W-2 Wages": w2,
                "1099 Consulting": consulting_1099,
                "Dividends": dividends,
                "Interest": interest,
                "Rental Income": rental,
                "Other": other_inflow
            },
            "outflows": {
                "Housing": housing,
                "Living Expenses": other_expenses,
                "Debt Service": debt_service,
                "Retirement Contributions": retirement_outflow,
                "Taxes": total_tax_outflow
            }
        },
        "trace": {
            "formula": "Net Cash Flow = Inflows - Outflows",
            "inputs": {
                "income_items_count": len(personal_income),
                "expense_items_count": len(personal_expenses)
            },
            "assumptions_used": "Combined cash flow aggregates personal W-2 salary and business pass-through distributions. Non-housing debt service is annualized from monthly payments.",
            "rules_referenced": "Standard personal financial budgeting principles.",
            "steps": steps
        }
    }
