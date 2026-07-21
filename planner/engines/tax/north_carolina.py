from typing import Dict, Any, List

def calculate_nc_tax(
    federal_agi: float,
    gross_cap_gains_and_div: float,
    business_net_income: float,
    business_entity: str,
    filing_status: str,
    rules: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculates North Carolina state income tax: Federal AGI minus NC standard deduction, taxed at a flat rate."""
    flat_rate = rules.get("flat_rate", 0.0399)
    corp_rate = rules.get("corporate_rate", 0.025)
    
    std_deduction_dict = rules.get("standard_deduction", {"single": 12750.0, "married": 25500.0})
    std_deduction = std_deduction_dict.get(filing_status.lower(), 12750.0)
    
    # NC Corporate Tax (if C-Corp)
    corporate_tax = 0.0
    if business_entity.strip() == "C Corporation":
        corporate_tax = max(0.0, business_net_income) * corp_rate
        
    # Simplified: ignores minor real-world NC adjustments (e.g. bond interest add-backs).
    nc_taxable_income = max(0.0, federal_agi - std_deduction)
    
    # Calculate state income tax
    nc_personal_tax = nc_taxable_income * flat_rate
    
    combined_nc_tax = nc_personal_tax + corporate_tax
    
    # These render inside the same <ol> as the federal steps (see taxes.py /
    # render_explain_panel), which numbers everything automatically.
    steps = [
        f"NC Starting Income (Federal AGI): ${federal_agi:,.2f}",
        f"NC Standard Deduction: ${std_deduction:,.2f} ({filing_status.capitalize()})",
        f"NC Taxable Income: Starting Income (${federal_agi:,.2f}) - Deduction (${std_deduction:,.2f}) = ${nc_taxable_income:,.2f}",
        f"NC Personal Tax: Taxable Income (${nc_taxable_income:,.2f}) * Flat Rate {flat_rate*100:.2f}% = ${nc_personal_tax:,.2f}"
    ]
    if business_entity.strip() == "C Corporation":
        steps.append(f"NC Corporate Income Tax (C-Corp): Business Profit (${business_net_income:,.2f}) * NC Corporate Rate {corp_rate*100:.2f}% = ${corporate_tax:,.2f}")
        steps.append(f"Combined NC Tax (Personal + Corporate) = ${combined_nc_tax:,.2f}")
        
    return {
        "value": nc_personal_tax,
        "corporate_tax": corporate_tax,
        "combined_tax": combined_nc_tax,
        "nc_taxable_income": nc_taxable_income,
        "effective_rate": nc_personal_tax / federal_agi if federal_agi > 0 else 0.0,
        "trace": {
            "formula": "NC State Tax = (Federal AGI - NC Standard Deduction) * NC Flat Rate",
            "inputs": {
                "federal_agi": federal_agi,
                "business_entity": business_entity,
                "filing_status": filing_status
            },
            "assumptions_used": "Filing-status-specific standard deductions applied. No itemized state deductions modeled.",
            "rules_referenced": f"NC State Tax Rules 2026. Rate: {flat_rate*100:.2f}%. Standard Deduction: ${std_deduction:,.2f}",
            "steps": steps
        }
    }
