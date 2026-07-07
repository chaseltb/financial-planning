from typing import Dict, Any

def calculate_payroll_tax(wages: float, filing_status: str, rules: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates employee-side payroll taxes (FICA): Social Security and Medicare.
    """
    ss_rate = rules.get("social_security_rate", 0.062)
    ss_limit = rules.get("social_security_limit", 184500.0)
    med_rate = rules.get("medicare_rate", 0.0145)
    add_med_rate = rules.get("additional_medicare_rate", 0.009)
    
    thresholds = rules.get("additional_medicare_threshold", {"single": 200000.0, "married": 250000.0})
    add_med_threshold = thresholds.get(filing_status.lower(), 200000.0)
    
    # Social Security
    ss_taxable = min(wages, ss_limit)
    ss_tax = ss_taxable * ss_rate
    
    # Medicare
    med_tax = wages * med_rate
    
    # Additional Medicare
    add_med_taxable = max(0.0, wages - add_med_threshold)
    add_med_tax = add_med_taxable * add_med_rate
    
    total_tax = ss_tax + med_tax + add_med_tax
    
    steps = [
        f"Social Security Tax: 6.2% of taxable wages up to ${ss_limit:,.2f} -> 6.2% of ${ss_taxable:,.2f} = ${ss_tax:,.2f}",
        f"Medicare Tax: 1.45% of total wages -> 1.45% of ${wages:,.2f} = ${med_tax:,.2f}",
    ]
    if add_med_tax > 0:
        steps.append(
            f"Additional Medicare Tax: 0.9% of wages over ${add_med_threshold:,.2f} -> 0.9% of ${add_med_taxable:,.2f} = ${add_med_tax:,.2f}"
        )
    else:
        steps.append(
            f"Additional Medicare Tax: Wages do not exceed ${add_med_threshold:,.2f} threshold (no additional tax)"
        )
        
    return {
        "value": total_tax,
        "social_security": ss_tax,
        "medicare": med_tax,
        "additional_medicare": add_med_tax,
        "trace": {
            "formula": "Total Payroll Tax = Social Security + Medicare + Additional Medicare",
            "inputs": {"wages": wages, "filing_status": filing_status},
            "assumptions_used": f"Filing status standard thresholds applied.",
            "rules_referenced": f"2026 SS Cap: ${ss_limit:,.2f}, SS Rate: {ss_rate*100}%, Med Rate: {med_rate*100}%, Add Med Rate: {add_med_rate*100}% over ${add_med_threshold:,.2f}",
            "steps": steps
        }
    }


def calculate_self_employment_tax(net_earnings: float, filing_status: str, rules: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Self-Employment Tax: Social Security and Medicare for self-employed individuals.
    Net profit is reduced by 7.65% (multiplied by 92.35%) to find net self-employment earnings.
    """
    se_factor = 0.9235
    se_earnings = net_earnings * se_factor
    
    ss_rate = rules.get("social_security_rate", 0.062) * 2  # 12.4%
    ss_limit = rules.get("social_security_limit", 184500.0)
    med_rate = rules.get("medicare_rate", 0.0145) * 2  # 2.9%
    add_med_rate = rules.get("additional_medicare_rate", 0.009)
    
    thresholds = rules.get("additional_medicare_threshold", {"single": 200000.0, "married": 250000.0})
    add_med_threshold = thresholds.get(filing_status.lower(), 200000.0)
    
    # SS portion
    ss_taxable = min(se_earnings, ss_limit)
    ss_tax = ss_taxable * ss_rate
    
    # Medicare portion
    med_tax = se_earnings * med_rate
    
    # Additional Medicare
    add_med_taxable = max(0.0, se_earnings - add_med_threshold)
    add_med_tax = add_med_taxable * add_med_rate
    
    total_se_tax = ss_tax + med_tax + add_med_tax
    deductible_se_tax = total_se_tax * 0.5
    
    steps = [
        f"Net Self-Employment Earnings: Net Profit (${net_earnings:,.2f}) * 92.35% = ${se_earnings:,.2f}",
        f"Self-Employment Social Security Tax: 12.4% of taxable earnings up to ${ss_limit:,.2f} -> 12.4% of ${ss_taxable:,.2f} = ${ss_tax:,.2f}",
        f"Self-Employment Medicare Tax: 2.9% of total earnings -> 2.9% of ${se_earnings:,.2f} = ${med_tax:,.2f}",
    ]
    if add_med_tax > 0:
        steps.append(
            f"Additional Medicare Tax: 0.9% of earnings over ${add_med_threshold:,.2f} -> 0.9% of ${add_med_taxable:,.2f} = ${add_med_tax:,.2f}"
        )
    else:
        steps.append(
            f"Additional Medicare Tax: SE earnings do not exceed ${add_med_threshold:,.2f} threshold (no additional tax)"
        )
    steps.append(
        f"Deductible SE Tax (for AGI adjustment): 50% of Total SE Tax (${total_se_tax:,.2f}) = ${deductible_se_tax:,.2f}"
    )
    
    return {
        "value": total_se_tax,
        "deductible_amount": deductible_se_tax,
        "social_security": ss_tax,
        "medicare": med_tax,
        "additional_medicare": add_med_tax,
        "trace": {
            "formula": "Total SE Tax = SE Social Security + SE Medicare + SE Additional Medicare",
            "inputs": {"net_earnings": net_earnings, "filing_status": filing_status},
            "assumptions_used": "Self-Employment net earnings adjustment of 92.35% applied.",
            "rules_referenced": f"2026 SE SS Cap: ${ss_limit:,.2f}, SS Rate: 12.4%, Medicare Rate: 2.9%, Add Medicare Rate: 0.9% over ${add_med_threshold:,.2f}",
            "steps": steps
        }
    }
