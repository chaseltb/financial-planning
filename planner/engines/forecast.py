import pandas as pd
import numpy as np
from typing import Dict, Any, List
from planner.engines.tax.federal import calculate_federal_tax
from planner.engines.tax.north_carolina import calculate_nc_tax

def get_next_quarter(quarter_str: str) -> str:
    """
    Given a string like '2025-Q4', returns '2026-Q1'.
    """
    year, q = quarter_str.split("-Q")
    year = int(year)
    q = int(q)
    if q == 4:
        return f"{year+1}-Q1"
    else:
        return f"{year}-Q{q+1}"


NUMERIC_COLS = [
    "Revenue", "COGS", "Payroll", "Expenses", "Capital expenditures",
    "Owner salary", "Distributions", "Tax estimate", "Cash", "EBITDA", "Business value"
]

DEFAULT_SEED = {
    "Quarter": "2025-Q4",
    "Revenue": 125000.0,
    "COGS": 25000.0,
    "Payroll": 30000.0,
    "Expenses": 15000.0,
    "Capital expenditures": 2000.0,
    "Owner salary": 22500.0,
    "Distributions": 10000.0,
    "Tax estimate": 12000.0,
    "Cash": 35000.0,
    "EBITDA": 55000.0,
    "Business value": 330000.0,
}


def run_forecast(
    history_df: pd.DataFrame,
    business_profile: Dict[str, Any],
    personal_profile: Dict[str, Any],
    personal_income_list: List[Dict[str, Any]],
    assumptions: Dict[str, Any],
    fed_rules: Dict[str, Any],
    nc_rules: Dict[str, Any],
    horizon: int = 8,
    overrides: Dict[str, Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Projects business metrics, EBITDA, cash balance, tax estimates, and business value forward.
    Support overrides like { '2026-Q1': { 'Revenue': 150000 } }.
    """
    if overrides is None:
        overrides = {}

    # Coerce numeric columns
    for col in NUMERIC_COLS:
        if col in history_df.columns:
            history_df[col] = pd.to_numeric(history_df[col], errors="coerce").fillna(0.0)

    # If history is empty or missing Quarter, seed with defaults
    if history_df.empty or "Quarter" not in history_df.columns:
        history_df = pd.DataFrame([DEFAULT_SEED])

    # Sort history by quarter
    history_df = history_df.sort_values("Quarter").reset_index(drop=True)
    
    # Calculate historical ratios to use as defaults
    avg_cogs_pct = 0.20
    if not history_df.empty:
        non_zero_rev = history_df[history_df["Revenue"] > 0]
        if not non_zero_rev.empty:
            avg_cogs_pct = (non_zero_rev["COGS"] / non_zero_rev["Revenue"]).mean()
            
    # Start from last historical quarter
    last_row = history_df.iloc[-1]
    
    current_quarter = last_row["Quarter"]
    prev_rev = float(last_row["Revenue"])
    prev_cogs = float(last_row["COGS"])
    prev_payroll = float(last_row["Payroll"])
    prev_expenses = float(last_row["Expenses"])
    prev_capex = float(last_row["Capital expenditures"])
    prev_cash = float(last_row["Cash"])
    
    revenue_growth = float(business_profile.get("revenue_growth", 0.05))
    expense_growth = float(business_profile.get("expense_growth", 0.03))
    
    ebitda_mult = float(assumptions.get("valuation_multiples", {}).get("ebitda", 6.0))
    entity_type = business_profile.get("entity_type", "Sole Proprietorship")
    
    forecast_rows = []
    
    # Personal profile and non-business income for tax calculations
    personal_income_base = {}
    for inc in personal_income_list:
        category = inc.get("category")
        # Exclude W-2 if it's the owner salary (which is updated dynamically from S-Corp/C-Corp owner_salary)
        if category == "W-2" and inc.get("description") == "Business Owner Salary":
            continue
        personal_income_base[category] = personal_income_base.get(category, 0.0) + float(inc.get("amount", 0.0))
        
    retirement_contributions = {
        "retirement_401k": float(personal_profile.get("retirement_401k", 0.0)),
        "retirement_ira": float(personal_profile.get("retirement_ira", 0.0)),
        "retirement_hsa": float(personal_profile.get("retirement_hsa", 0.0)),
        "solo_401k": float(personal_profile.get("solo_401k", 0.0)),
        "sep_ira": float(personal_profile.get("sep_ira", 0.0)),
    }
    
    filing_status = personal_profile.get("filing_status", "single")
    
    for _ in range(horizon):
        next_q = get_next_quarter(current_quarter)
        q_overrides = overrides.get(next_q, {})
        
        # 1. Project metrics (respecting overrides)
        rev = q_overrides.get("Revenue", prev_rev * (1 + revenue_growth))
        cogs = q_overrides.get("COGS", rev * avg_cogs_pct)
        payroll = q_overrides.get("Payroll", prev_payroll * (1 + expense_growth))
        expenses = q_overrides.get("Expenses", prev_expenses * (1 + expense_growth))
        capex = q_overrides.get("Capital expenditures", prev_capex)
        
        owner_salary = q_overrides.get("Owner salary", float(business_profile.get("owner_salary", 0.0)) / 4.0)
        distributions = q_overrides.get("Distributions", float(business_profile.get("distributions", 0.0)) / 4.0)
        
        # Calculate EBITDA
        ebitda = rev - cogs - payroll - expenses
        
        # 2. Estimate taxes dynamically using engines
        # Business net profit for the quarter (quarterly profit before tax and owner salary for pass-throughs,
        # but for S-Corp/C-Corp, owner salary is an expense reducing business net profit)
        # Note: EBITDA is revenue - cogs - payroll - expenses.
        # Payroll usually includes standard employee payroll. Owner salary is separate or part of payroll.
        # Let's assume payroll does NOT include owner salary, so business net income = EBITDA - Owner Salary.
        net_biz_income_quarter = ebitda - owner_salary
        
        # Annualize net profit and owner salary to run tax engine
        annual_net_biz_income = net_biz_income_quarter * 4
        annual_owner_salary = owner_salary * 4
        
        # Update personal income dict for tax engine (injecting owner salary W-2 if applicable)
        personal_income_tax_run = dict(personal_income_base)
        personal_income_tax_run["W-2"] = personal_income_tax_run.get("W-2", 0.0) + annual_owner_salary
        
        # Run Federal Tax Engine
        fed_tax_calc = calculate_federal_tax(
            personal_income=personal_income_tax_run,
            business_net_income=annual_net_biz_income,
            business_entity=entity_type,
            retirement_contributions=retirement_contributions,
            filing_status=filing_status,
            rules=fed_rules
        )
        
        # Run NC State Tax Engine
        nc_tax_calc = calculate_nc_tax(
            federal_agi=fed_tax_calc["agi"],
            gross_cap_gains_and_div=personal_income_tax_run.get("Capital gains", 0.0) + personal_income_tax_run.get("Dividends", 0.0),
            business_net_income=annual_net_biz_income,
            business_entity=entity_type,
            filing_status=filing_status,
            rules=nc_rules
        )
        
        # Combined annualized tax / 4 to get quarterly tax estimate
        annual_combined_tax = fed_tax_calc["combined_tax"] + nc_tax_calc["combined_tax"]
        tax_estimate = q_overrides.get("Tax estimate", annual_combined_tax / 4.0)
        
        # 3. Project Cash
        # Cash Flow = Revenue - COGS - Payroll - Expenses - CapEx - Owner salary - Distributions - Tax estimate
        cash_flow = rev - cogs - payroll - expenses - capex - owner_salary - distributions - tax_estimate
        cash = q_overrides.get("Cash", prev_cash + cash_flow)
        
        # 4. Valuation
        biz_val = max(0.0, ebitda * 4.0 * ebitda_mult)
        
        row = {
            "Quarter": next_q,
            "Revenue": rev,
            "COGS": cogs,
            "Payroll": payroll,
            "Expenses": expenses,
            "Capital expenditures": capex,
            "Owner salary": owner_salary,
            "Distributions": distributions,
            "Tax estimate": tax_estimate,
            "Cash": cash,
            "EBITDA": ebitda,
            "Business value": biz_val
        }
        
        forecast_rows.append(row)
        
        # Prepare for next iteration
        current_quarter = next_q
        prev_rev = rev
        prev_cogs = cogs
        prev_payroll = payroll
        prev_expenses = expenses
        prev_capex = capex
        prev_cash = cash
        
    forecast_df = pd.DataFrame(forecast_rows)
    combined_df = pd.concat([history_df, forecast_df], ignore_index=True)
    
    steps = [
        f"Historical quarters analyzed: {len(history_df)}",
        f"Forecasting {horizon} quarters forward starting from {history_df.iloc[-1]['Quarter']}.",
        f"EBITDA Multiple applied: {ebitda_mult} (Annualized EBITDA * Multiple).",
        f"Average COGS/Revenue ratio from history: {avg_cogs_pct*100:.1f}%.",
        f"Quarterly tax estimates computed dynamically by annualizing EBITDA and running combined Federal + NC tax engines."
    ]
    
    return {
        "forecast_df": combined_df,
        "only_forecast_df": forecast_df,
        "trace": {
            "formula": "Future Cash = Prev Cash + Quarterly Operating Cash Flow - Distributions - Taxes",
            "inputs": {
                "horizon": horizon,
                "revenue_growth": revenue_growth,
                "expense_growth": expense_growth
            },
            "assumptions_used": f"COGS set to {avg_cogs_pct*100:.1f}% of Revenue. Taxes are combined Fed+NC state estimates.",
            "rules_referenced": "Standard cash flow waterfall and financial projection rules.",
            "steps": steps
        }
    }
