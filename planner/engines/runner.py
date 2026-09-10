"""Shared calculation runner used by every page callback."""
from typing import Dict, Any
import pandas as pd

from planner.data_manager import load_tax_rules
from planner.config import DEFAULT_TAX_YEAR, DEFAULT_STATE
from planner.engines.tax.federal import calculate_federal_tax
from planner.engines.tax.north_carolina import calculate_nc_tax
from planner.engines.networth import calculate_net_worth, project_net_worth
from planner.engines.valuation import calculate_valuation, calculate_sensitivity
from planner.engines.forecast import run_forecast, DEFAULT_SEED, NUMERIC_COLS
from planner.engines.cashflow import calculate_combined_cashflow
from planner.engines.allocation import calculate_budget_allocation


def run_all_engines(
    state: Dict[str, Any],
    horizon: int = 8,
    sensitivity_method: str = "EBITDA Multiple",
    sensitivity_range: float = 0.20,
) -> Dict[str, Any]:
    """
    Run every calculation engine against a state dict.
    Returns a flat dict of results consumed by page callbacks.
    """
    tax_year = int(state.get("assumptions", {}).get("tax_year", DEFAULT_TAX_YEAR))
    rules = load_tax_rules(tax_year, DEFAULT_STATE)
    fed_rules = rules["federal"]
    nc_rules = rules["north_carolina"]

    # ── Forecast ──────────────────────────────────────────────────────────
    history_df = pd.DataFrame(state.get("forecast", []))
    for col in NUMERIC_COLS:
        if col in history_df.columns:
            history_df[col] = pd.to_numeric(history_df[col], errors="coerce").fillna(0.0)

    overrides = state.get("assumptions", {}).get("forecast_overrides", {})

    forecast_results = run_forecast(
        history_df=history_df,
        business_profile=state["business"],
        personal_profile=state["profile"],
        personal_income_list=state["income"],
        assumptions=state["assumptions"],
        fed_rules=fed_rules,
        nc_rules=nc_rules,
        horizon=horizon,
        overrides=overrides,
    )
    forecast_df = forecast_results["forecast_df"]
    only_forecast_df = forecast_results["only_forecast_df"]

    # recent_q is the forward-projected quarter; current-state figures must use current_q instead, or they'd silently be a future projection.
    recent_q = forecast_df.iloc[-1]
    current_q = forecast_results["history_df"].iloc[-1]
    ebitda_q = float(current_q["EBITDA"])
    revenue_q = float(current_q["Revenue"])
    capex_q = float(current_q["Capital expenditures"])

    owner_salary = float(state["business"].get("owner_salary", 0.0))
    entity_type = state["business"].get("entity_type", "Sole Proprietorship")
    # Only S-Corps/C-Corps can legally run payroll for the owner; others take a draw instead.
    owner_w2_salary = owner_salary if entity_type in ("S Corporation", "C Corporation") else 0.0
    ownership_pct = max(0.0, min(1.0, float(state["business"].get("ownership_pct", 100.0)) / 100.0))
    filing_status = state["profile"].get("filing_status", "single")

    # ── Personal income map ───────────────────────────────────────────────
    personal_income_map: Dict[str, float] = {}
    for inc in state["income"]:
        cat = inc.get("category", "Other")
        personal_income_map[cat] = personal_income_map.get(cat, 0.0) + float(inc.get("amount", 0.0))
    personal_income_map["W-2"] = personal_income_map.get("W-2", 0.0) + owner_w2_salary

    annual_net_biz_income = (ebitda_q - owner_w2_salary / 4.0) * 4.0

    retirement = {
        "retirement_401k": float(state["profile"].get("retirement_401k", 0.0)),
        "retirement_ira": float(state["profile"].get("retirement_ira", 0.0)),
        "retirement_hsa": float(state["profile"].get("retirement_hsa", 0.0)),
        "solo_401k": float(state["profile"].get("solo_401k", 0.0)),
        "sep_ira": float(state["profile"].get("sep_ira", 0.0)),
    }

    # ── Federal Tax ───────────────────────────────────────────────────────
    fed_tax = calculate_federal_tax(
        personal_income=personal_income_map,
        business_net_income=annual_net_biz_income,
        business_entity=entity_type,
        owner_w2_salary=owner_w2_salary,
        ownership_pct=ownership_pct,
        retirement_contributions=retirement,
        filing_status=filing_status,
        rules=fed_rules,
    )

    # ── NC State Tax ──────────────────────────────────────────────────────
    nc_tax = calculate_nc_tax(
        federal_agi=fed_tax["agi"],
        gross_cap_gains_and_div=(
            personal_income_map.get("Capital gains", 0.0)
            + personal_income_map.get("Dividends", 0.0)
        ),
        business_net_income=annual_net_biz_income,
        business_entity=entity_type,
        filing_status=filing_status,
        rules=nc_rules,
    )

    # ── Valuation ─────────────────────────────────────────────────────────
    multiples = state["assumptions"].get("valuation_multiples", {})
    metrics_val = {
        "revenue": revenue_q * 4.0,
        "ebitda": ebitda_q * 4.0,
        "net_income": annual_net_biz_income,
        "owner_salary": owner_w2_salary,
        "capex": capex_q * 4.0,
        "taxes": fed_tax["corporate_tax"] + nc_tax["corporate_tax"],
    }
    custom_method = {
        "name": state["assumptions"].get("custom_valuation_name", "Custom Multiplier"),
        "metric_value": ebitda_q * 4.0,
        "multiplier": float(state["assumptions"].get("custom_valuation_multiplier", 3.0)),
    }
    val_result = calculate_valuation(metrics_val, multiples, custom_method)
    sensitivity = calculate_sensitivity(val_result, sensitivity_method, float(sensitivity_range))

    combined_tax = fed_tax["combined_tax"] + nc_tax["combined_tax"]

    # Tax the BUSINESS itself is responsible for: total household tax minus what
    # this taxpayer would owe with no business activity at all (just their outside
    # W-2 job, interest, dividends, etc.). Without this, a business summary card
    # showing the raw combined_tax bundles in personal tax that has nothing to do
    # with the business and would be owed regardless of whether it existed.
    baseline_income_map = dict(personal_income_map)
    baseline_income_map["W-2"] = personal_income_map.get("W-2", 0.0) - owner_w2_salary
    baseline_fed_tax = calculate_federal_tax(
        personal_income=baseline_income_map,
        business_net_income=0.0,
        business_entity=entity_type,
        owner_w2_salary=0.0,
        ownership_pct=ownership_pct,
        retirement_contributions=retirement,
        filing_status=filing_status,
        rules=fed_rules,
    )
    baseline_nc_tax = calculate_nc_tax(
        federal_agi=baseline_fed_tax["agi"],
        gross_cap_gains_and_div=(
            personal_income_map.get("Capital gains", 0.0)
            + personal_income_map.get("Dividends", 0.0)
        ),
        business_net_income=0.0,
        business_entity=entity_type,
        filing_status=filing_status,
        rules=nc_rules,
    )
    baseline_combined_tax = baseline_fed_tax["combined_tax"] + baseline_nc_tax["combined_tax"]
    business_attributable_tax = max(0.0, combined_tax - baseline_combined_tax)

    # ── Cash Flow & Budget Allocation ────────────────────────────────────────
    cashflow = calculate_combined_cashflow(
        personal_income=state["income"],
        personal_expenses=state["expenses"],
        liabilities=state["liabilities"],
        retirement_contributions=retirement,
        tax_result={"combined_tax": combined_tax},
    )
    default_allocation_pct = {"Savings": 34.0, "Liability Paydown": 33.0, "Taxable Brokerage": 33.0}
    allocation_pct = state["profile"].get("budget_allocation", default_allocation_pct)
    budget_allocation = calculate_budget_allocation(cashflow["value"], allocation_pct)

    # ── Net Worth ─────────────────────────────────────────────────────────
    # The allocated surplus (savings/brokerage contributions, extra liability
    # paydown) feeds forward into the projection so it actually shows up in
    # future net worth, not just as a standalone budget-page number.
    quarterly_allocation = {k: v / 4.0 for k, v in budget_allocation["amounts"].items()}
    nw_result = calculate_net_worth(state["assets"], state["liabilities"])
    nw_proj_df = pd.DataFrame(project_net_worth(
        state["assets"], state["liabilities"], quarters=8,
        quarterly_allocation=quarterly_allocation,
    ))

    return {
        # Tax
        "fed_tax": fed_tax,
        "nc_tax": nc_tax,
        "combined_tax": combined_tax,
        "business_attributable_tax": business_attributable_tax,
        "effective_rate": fed_tax.get("combined_effective_tax_rate", 0.0),
        # Cash Flow / Budget Allocation
        "cashflow": cashflow,
        "budget_allocation": budget_allocation,
        # Business
        "ebitda_q": ebitda_q,
        "revenue_q": revenue_q,
        "capex_q": capex_q,
        "annual_net_biz_income": annual_net_biz_income,
        "owner_salary": owner_salary,
        "owner_w2_salary": owner_w2_salary,
        "entity_type": entity_type,
        "filing_status": filing_status,
        "personal_income_map": personal_income_map,
        "retirement": retirement,
        # Valuation
        "val_result": val_result,
        "sensitivity": sensitivity,
        "multiples": multiples,
        "custom_method": custom_method,
        "metrics_val": metrics_val,
        # Net Worth
        "nw_result": nw_result,
        "nw_proj_df": nw_proj_df,
        # Forecast
        "forecast_df": forecast_df,
        "only_forecast_df": only_forecast_df,
        "recent_q": recent_q,
        # Tax rules (for bracket visualizer)
        "fed_rules": fed_rules,
        "nc_rules": nc_rules,
        "tax_year": tax_year,
    }
