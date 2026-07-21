from typing import Dict, Any, List

def calculate_valuation(
    metrics: Dict[str, float],
    multiples: Dict[str, float],
    custom_method: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Calculates business valuation using multiple methodologies. Metrics should be annualized (e.g. quarterly revenue * 4)."""
    revenue = metrics.get("revenue", 0.0)
    ebitda = metrics.get("ebitda", 0.0)
    net_income = metrics.get("net_income", 0.0)
    owner_salary = metrics.get("owner_salary", 0.0)
    capex = metrics.get("capex", 0.0)
    taxes = metrics.get("taxes", 0.0)
    
    # Calculate SDE (EBITDA + Owner Salary is a standard approximation)
    sde = max(0.0, ebitda + owner_salary)
    # Calculate FCF (EBITDA - CapEx - Taxes)
    fcf = max(0.0, ebitda - capex - taxes)
    
    # Multiples
    mult_rev = multiples.get("revenue", 2.5)
    mult_ebitda = multiples.get("ebitda", 6.0)
    mult_ni = multiples.get("net_income", 8.0)
    mult_sde = multiples.get("sde", 4.5)
    mult_fcf = multiples.get("fcf", 7.0)
    
    # Calculations
    val_rev = revenue * mult_rev
    val_ebitda = ebitda * mult_ebitda
    val_ni = net_income * mult_ni
    val_sde = sde * mult_sde
    val_fcf = fcf * mult_fcf
    
    valuations = {
        "Revenue Multiple": val_rev,
        "EBITDA Multiple": val_ebitda,
        "Net Income Multiple": val_ni,
        "SDE Multiple": val_sde,
        "FCF Multiple": val_fcf
    }
    
    # These render inside an auto-numbering <ol> (see render_explain_panel) —
    # no hardcoded numbers here.
    steps = [
        f"Revenue Multiple Method: Annualized Revenue (${revenue:,.2f}) * Multiple ({mult_rev}) = ${val_rev:,.2f}",
        f"EBITDA Multiple Method: Annualized EBITDA (${ebitda:,.2f}) * Multiple ({mult_ebitda}) = ${val_ebitda:,.2f}",
        f"Net Income Multiple Method: Annualized Net Income (${net_income:,.2f}) * Multiple ({mult_ni}) = ${val_ni:,.2f}",
        f"SDE Multiple Method: SDE [EBITDA (${ebitda:,.2f}) + Owner Salary (${owner_salary:,.2f})] = ${sde:,.2f} | SDE (${sde:,.2f}) * Multiple ({mult_sde}) = ${val_sde:,.2f}",
        f"FCF Multiple Method: FCF [EBITDA (${ebitda:,.2f}) - CapEx (${capex:,.2f}) - Taxes (${taxes:,.2f})] = ${fcf:,.2f} | FCF (${fcf:,.2f}) * Multiple ({mult_fcf}) = ${val_fcf:,.2f}"
    ]

    # Custom Method
    if custom_method:
        name = custom_method.get("name", "Custom Formula")
        metric_val = custom_method.get("metric_value", 0.0)
        multiplier = custom_method.get("multiplier", 1.0)
        val_custom = metric_val * multiplier
        valuations[name] = val_custom
        steps.append(f"Custom Method '{name}': Metric (${metric_val:,.2f}) * Multiplier ({multiplier}) = ${val_custom:,.2f}")
        
    # Default active valuation method is EBITDA Multiple for primary summaries
    primary_value = val_ebitda
    
    return {
        "value": primary_value,
        "valuations": valuations,
        "metrics_used": {
            "annualized_revenue": revenue,
            "annualized_ebitda": ebitda,
            "annualized_net_income": net_income,
            "sde": sde,
            "fcf": fcf,
            "owner_salary": owner_salary
        },
        "multiples_used": multiples,
        "trace": {
            "formula": "Valuation = Financial Metric * Industry Multiple",
            "inputs": {
                "metrics": metrics,
                "multiples": multiples
            },
            "assumptions_used": "Operating metrics are annualized from quarterly figures. Owner salary is added back to EBITDA for SDE.",
            "rules_referenced": "Standard valuation metrics for small-to-medium businesses.",
            "steps": steps
        }
    }


def calculate_sensitivity(
    valuation_result: Dict[str, Any],
    method_name: str,
    range_pct: float = 0.20
) -> Dict[str, Any]:
    """
    Calculates sensitivity range (+/- range_pct) for a selected valuation method.
    """
    base_val = valuation_result["valuations"].get(method_name, valuation_result["value"])

    lower_val = base_val * (1 - range_pct)
    upper_val = base_val * (1 + range_pct)

    # Generate points for a sensitivity curve, scaled to the requested +/- range
    # (previously hardcoded to +/-20% regardless of what the user asked for).
    steps = [-1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0]
    curve = []
    for step in steps:
        pct = step * range_pct
        curve.append({
            "percentage_change": pct,
            "valuation": base_val * (1 + pct)
        })
        
    return {
        "method": method_name,
        "base_value": base_val,
        "lower_value": lower_val,
        "upper_value": upper_val,
        "sensitivity_curve": curve
    }
