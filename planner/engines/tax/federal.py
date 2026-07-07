from typing import Dict, Any, List
from planner.engines.tax.payroll import calculate_self_employment_tax

def calculate_bracket_tax(taxable_ordinary: float, brackets: List[Dict[str, float]]) -> tuple[float, List[str]]:
    """
    Calculates tax using progressive brackets.
    """
    tax = 0.0
    steps = []
    
    # Sort brackets by threshold ascending
    sorted_brackets = sorted(brackets, key=lambda x: x["threshold"])
    
    for i, br in enumerate(sorted_brackets):
        rate = br["rate"]
        threshold = br["threshold"]
        
        # Determine upper limit for this bracket
        if i + 1 < len(sorted_brackets):
            upper = sorted_brackets[i + 1]["threshold"]
        else:
            upper = float("inf")
            
        if taxable_ordinary > threshold:
            taxable_in_bracket = min(taxable_ordinary - threshold, upper - threshold)
            tax_in_bracket = taxable_in_bracket * rate
            tax += tax_in_bracket
            steps.append(
                f"Bracket {rate*100:.0f}%: taxed ${taxable_in_bracket:,.2f} of income between ${threshold:,.2f} and ${upper:,.2f} -> Tax = ${tax_in_bracket:,.2f}"
            )
        else:
            break
            
    return tax, steps


def calculate_cap_gains_tax(cap_gains_and_div: float, ordinary_taxable: float, filing_status: str) -> tuple[float, List[str]]:
    """
    Calculates capital gains tax based on 2026 capital gains brackets:
    0% rate up to $47,000 (Single) / $94,000 (MFJ)
    15% rate up to $518,000 (Single) / $583,000 (MFJ)
    20% rate above that.
    """
    if cap_gains_and_div <= 0:
        return 0.0, ["No capital gains or qualified dividends to tax."]
        
    thresholds_0 = {"single": 47000.0, "married": 94000.0}
    thresholds_15 = {"single": 518000.0, "married": 583000.0}
    
    th_0 = thresholds_0.get(filing_status.lower(), 47000.0)
    th_15 = thresholds_15.get(filing_status.lower(), 518000.0)
    
    # Capital gains tax is stacked on top of ordinary income
    tax = 0.0
    steps = []
    
    remaining_gains = cap_gains_and_div
    current_income = ordinary_taxable
    
    # 0% Bracket portion
    gains_in_0 = max(0.0, min(th_0 - current_income, remaining_gains))
    if gains_in_0 > 0:
        steps.append(f"Capital Gains 0% Bracket: ${gains_in_0:,.2f} taxed at 0% -> Tax = $0.00")
        remaining_gains -= gains_in_0
        current_income += gains_in_0
        
    # 15% Bracket portion
    gains_in_15 = max(0.0, min(th_15 - current_income, remaining_gains))
    if gains_in_15 > 0:
        tax_15 = gains_in_15 * 0.15
        tax += tax_15
        steps.append(f"Capital Gains 15% Bracket: ${gains_in_15:,.2f} taxed at 15% -> Tax = ${tax_15:,.2f}")
        remaining_gains -= gains_in_15
        current_income += gains_in_15
        
    # 20% Bracket portion
    if remaining_gains > 0:
        tax_20 = remaining_gains * 0.20
        tax += tax_20
        steps.append(f"Capital Gains 20% Bracket: ${remaining_gains:,.2f} taxed at 20% -> Tax = ${tax_20:,.2f}")
        
    return tax, steps


def calculate_federal_tax(
    personal_income: Dict[str, float],
    business_net_income: float,
    business_entity: str,
    retirement_contributions: Dict[str, float],
    filing_status: str,
    rules: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculates Federal Income Taxes for Personal and Business combined.
    """
    # 1. Determine Personal Income by Category
    w2_personal = personal_income.get("W-2", 0.0)
    consulting_1099 = personal_income.get("1099", 0.0)
    dividends = personal_income.get("Dividends", 0.0)
    interest = personal_income.get("Interest", 0.0)
    cap_gains = personal_income.get("Capital gains", 0.0)
    rental_income = personal_income.get("Rental income", 0.0)
    other_income = personal_income.get("Other", 0.0)
    
    # 2. Add Business Flow-through Income based on entity type
    se_tax = 0.0
    se_deduction = 0.0
    qbi_qualified_income = 0.0
    corporate_tax = 0.0
    business_to_personal_w2 = 0.0
    business_to_personal_distributions = 0.0
    
    entity = business_entity.strip()
    
    business_steps = []
    
    if entity in ["Sole Proprietorship", "Single-member LLC"]:
        # All net profit flows to personal Schedule C, subject to SE tax
        se_calc = calculate_self_employment_tax(business_net_income, filing_status, rules)
        se_tax = se_calc["value"]
        se_deduction = se_calc["deductible_amount"]
        qbi_qualified_income = business_net_income
        business_steps.append(f"Sole Proprietorship/LLC flow-through: Net Profit ${business_net_income:,.2f} is added to ordinary income.")
        business_steps.append(f"Self-Employment Tax computed: ${se_tax:,.2f} (Deductible portion: ${se_deduction:,.2f})")
        
    elif entity == "Multi-member LLC":
        # Multi-member LLC is treated as partnership. Net profit flows to personal K-1, subject to SE tax
        se_calc = calculate_self_employment_tax(business_net_income, filing_status, rules)
        se_tax = se_calc["value"]
        se_deduction = se_calc["deductible_amount"]
        qbi_qualified_income = business_net_income
        business_steps.append(f"Partnership (Multi-member LLC) flow-through: Net Profit ${business_net_income:,.2f} flows to K-1.")
        business_steps.append(f"Self-Employment Tax computed: ${se_tax:,.2f} (Deductible portion: ${se_deduction:,.2f})")
        
    elif entity == "S Corporation":
        # S-Corp pays owner salary (W-2), and remainder flows through as K-1 distributions (no SE tax)
        # Owner salary is already a W-2 expense for the business. Let's make sure it's counted on personal side.
        # But we assume the personal income csv might or might not have it. Let's assume the business owner W-2
        # is part of the wages. If it's already in w2_personal, we don't double count.
        # Let's count S-Corp profit distributions as K-1 ordinary income (eligible for QBI)
        # Note: business_net_income is after owner salary.
        qbi_qualified_income = max(0.0, business_net_income)
        business_to_personal_distributions = max(0.0, business_net_income)
        business_steps.append(f"S-Corp flow-through: Net income after owner salary ${business_net_income:,.2f} flows to K-1 distributions (no self-employment tax).")
        
    elif entity == "C Corporation":
        # C-Corp net income is taxed at corporate rate. Personal dividends are taxed on personal return.
        corp_rate = rules.get("corporate_rate", 0.21)
        corporate_tax = max(0.0, business_net_income) * corp_rate
        # Distributions from C-Corp flow to personal as qualified dividends
        business_to_personal_distributions = max(0.0, business_net_income - corporate_tax) # Assume all net profit is distributed
        business_steps.append(f"C-Corp Corporate Income Tax: ${business_net_income:,.2f} * {corp_rate*100}% = ${corporate_tax:,.2f}")
        business_steps.append(f"C-Corp net profit after tax (${business_to_personal_distributions:,.2f}) flows to personal as dividends.")
        
    # 3. Sum up total personal ordinary income
    # Note: 1099 is also subject to SE tax
    personal_1099_se_tax = 0.0
    personal_1099_se_deduction = 0.0
    if consulting_1099 > 0:
        se_calc_1099 = calculate_self_employment_tax(consulting_1099, filing_status, rules)
        personal_1099_se_tax = se_calc_1099["value"]
        personal_1099_se_deduction = se_calc_1099["deductible_amount"]
        business_steps.append(f"Personal 1099 consulting SE Tax: ${personal_1099_se_tax:,.2f} (Deductible: ${personal_1099_se_deduction:,.2f})")
        
    total_se_tax = se_tax + personal_1099_se_tax
    total_se_deduction = se_deduction + personal_1099_se_deduction
    
    # Calculate Gross Income
    # If Sole Prop/LLC, business profit is included. If S-Corp, distributions are ordinary K-1.
    # If C-Corp, dividends are capital gains.
    ordinary_flow_through = 0.0
    if entity in ["Sole Proprietorship", "Single-member LLC", "Multi-member LLC"]:
        ordinary_flow_through = business_net_income
    elif entity == "S Corporation":
        ordinary_flow_through = business_net_income
        
    gross_ordinary = w2_personal + consulting_1099 + interest + rental_income + other_income + ordinary_flow_through
    gross_cap_gains = cap_gains + dividends
    if entity == "C Corporation":
        # Add corporate dividend distributions to personal dividends
        gross_cap_gains += business_to_personal_distributions
        
    gross_income = gross_ordinary + gross_cap_gains
    
    # 4. Retirement Deductions (reduces ordinary income)
    total_retirement_deductions = sum([
        retirement_contributions.get("retirement_401k", 0.0),
        retirement_contributions.get("retirement_ira", 0.0),
        retirement_contributions.get("retirement_hsa", 0.0),
        retirement_contributions.get("solo_401k", 0.0),
        retirement_contributions.get("sep_ira", 0.0),
    ])
    
    # 5. Adjusted Gross Income (AGI)
    # AGI = Gross Ordinary + Gross Cap Gains - Retirement Deductions - SE Tax Deduction
    agi = max(0.0, gross_income - total_retirement_deductions - total_se_deduction)
    
    # 6. Deductions (Standard Deduction)
    std_deduction_dict = rules.get("standard_deduction", {"single": 16100.0, "married": 32200.0})
    std_deduction = std_deduction_dict.get(filing_status.lower(), 16100.0)
    
    # 7. QBI Deduction (20% of qualified business income)
    # Basic QBI is limited to 20% of (taxable ordinary income - net capital gains)
    qbi_deduction = 0.0
    if qbi_qualified_income > 0:
        qbi_deduction = qbi_qualified_income * 0.20
        # QBI deduction cannot exceed 20% of taxable ordinary income minus net capital gains
        limit = max(0.0, (gross_ordinary - total_retirement_deductions - total_se_deduction - std_deduction) * 0.20)
        qbi_deduction = min(qbi_deduction, limit)
        
    total_deductions = std_deduction + qbi_deduction
    
    # 8. Taxable Income
    taxable_income = max(0.0, agi - total_deductions)
    
    # Ordinary Taxable Income vs Capital Gains Taxable Income
    # Capital gains are taxed at capital gains rates, and ordinary income is taxed at ordinary brackets.
    # Taxable ordinary income = Taxable Income - Gross Cap Gains (if positive)
    taxable_cap_gains = min(taxable_income, gross_cap_gains)
    taxable_ordinary = max(0.0, taxable_income - taxable_cap_gains)
    
    # 9. Calculate Taxes
    brackets = rules.get("brackets", {}).get(filing_status.lower(), [])
    ordinary_tax, ordinary_tax_steps = calculate_bracket_tax(taxable_ordinary, brackets)
    cap_gains_tax, cap_gains_tax_steps = calculate_cap_gains_tax(taxable_cap_gains, taxable_ordinary, filing_status)
    
    total_personal_income_tax = ordinary_tax + cap_gains_tax
    
    # Total combined tax (personal income tax + payroll/SE taxes + corporate taxes)
    combined_tax = total_personal_income_tax + total_se_tax + corporate_tax
    
    # Effective Tax Rates
    effective_rate = total_personal_income_tax / agi if agi > 0 else 0.0
    combined_effective_rate = combined_tax / (gross_income + (business_net_income if entity == "C Corporation" else 0)) if (gross_income > 0) else 0.0
    
    # Build complete steps for explanation
    steps = [
        f"1. Gross Ordinary Income: W-2 (${w2_personal:,.2f}) + 1099 (${consulting_1099:,.2f}) + Interest (${interest:,.2f}) + Rental (${rental_income:,.2f}) + Pass-through Profit (${ordinary_flow_through:,.2f}) = ${gross_ordinary:,.2f}",
        f"2. Gross Capital Gains & Dividends: Cap Gains/Dividends (${cap_gains + dividends:,.2f}) + C-Corp Dividend Distribution (${business_to_personal_distributions if entity == 'C Corporation' else 0:,.2f}) = ${gross_cap_gains:,.2f}",
        f"3. Total Gross Income: Ordinary (${gross_ordinary:,.2f}) + Capital Gains (${gross_cap_gains:,.2f}) = ${gross_income:,.2f}",
        f"4. Retirement Deductions: Pre-tax Contributions = ${total_retirement_deductions:,.2f}",
        f"5. Self-Employment Tax Deduction: 50% of SE Tax = ${total_se_deduction:,.2f}",
        f"6. Adjusted Gross Income (AGI): Gross Income (${gross_income:,.2f}) - Retirement (${total_retirement_deductions:,.2f}) - SE Deduction (${total_se_deduction:,.2f}) = ${agi:,.2f}",
        f"7. Standard Deduction: ${std_deduction:,.2f} ({filing_status.capitalize()})",
    ]
    
    if qbi_deduction > 0:
        steps.append(f"8. QBI Pass-through Deduction: 20% of eligible QBI (${qbi_qualified_income:,.2f}) = ${qbi_deduction:,.2f}")
    else:
        steps.append(f"8. QBI Pass-through Deduction: $0.00 (No pass-through income or limited by taxable income)")
        
    steps.append(f"9. Taxable Income: AGI (${agi:,.2f}) - Deductions (${total_deductions:,.2f}) = ${taxable_income:,.2f}")
    steps.append(f"10. Taxable Ordinary Income: ${taxable_ordinary:,.2f} | Taxable Capital Gains: ${taxable_cap_gains:,.2f}")
    steps.append("11. Ordinary Tax Bracket Calculations:")
    steps.extend([f"    - {s}" for s in ordinary_tax_steps])
    steps.append(f"    - Total Ordinary Income Tax = ${ordinary_tax:,.2f}")
    
    if taxable_cap_gains > 0:
        steps.append("12. Capital Gains Tax Calculations:")
        steps.extend([f"    - {s}" for s in cap_gains_tax_steps])
        steps.append(f"    - Total Capital Gains Tax = ${cap_gains_tax:,.2f}")
        
    steps.append(f"13. Total Personal Income Tax = ${total_personal_income_tax:,.2f}")
    
    if entity == "C Corporation":
        steps.append(f"14. C-Corp Corporate Tax = ${corporate_tax:,.2f}")
    if total_se_tax > 0:
        steps.append(f"15. Self-Employment Tax = ${total_se_tax:,.2f}")
        
    steps.append(f"16. Combined Total Tax (Personal + SE + Corporate) = ${combined_tax:,.2f}")
    
    return {
        "value": total_personal_income_tax,
        "combined_tax": combined_tax,
        "corporate_tax": corporate_tax,
        "se_tax": total_se_tax,
        "agi": agi,
        "taxable_income": taxable_income,
        "ordinary_tax": ordinary_tax,
        "cap_gains_tax": cap_gains_tax,
        "qbi_deduction": qbi_deduction,
        "effective_tax_rate": effective_rate,
        "combined_effective_tax_rate": combined_effective_rate,
        "trace": {
            "formula": "Federal Tax = Ordinary Bracket Tax + Capital Gains Tax",
            "inputs": {
                "personal_income": personal_income,
                "business_net_income": business_net_income,
                "business_entity": business_entity,
                "retirement_contributions": retirement_contributions,
                "filing_status": filing_status
            },
            "assumptions_used": f"Standard deduction chosen. QBI pass-through rate is 20%.",
            "rules_referenced": f"Filing Status: {filing_status.capitalize()}, Tax Year: {rules.get('tax_year', 2026)}",
            "steps": steps
        }
    }
