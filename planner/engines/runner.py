"""
Shared calculation runner used by every page callback.

All page callbacks import `run_all_engines` from here so the logic is
defined once and engines are only invoked on demand.
"""
from typing import Dict, Any
import pandas as pd

from planner.data_manager import load_tax_rules
from planner.config import DEFAULT_TAX_YEAR, DEFAULT_STATE
from planner.engines.tax.federal import calculate_federal_tax
from planner.engines.tax.north_carolina import calculate_nc_tax
from planner.engines.networth import calculate_net_worth, project_net_worth
from planner.engines.valuation import calculate_valuation, calculate_sensitivity
from planner.engines.forecast import run_forecast, DEFAULT_SEED, NUMERIC_COLS


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
    rules = load_tax_rules(DEFAULT_TAX_YEAR, DEFAULT_STATE)
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

    recent_q = forecast_df.iloc[-1]
    ebitda_q = float(recent_q["EBITDA"])
    revenue_q = float(recent_q["Revenue"])
    capex_q = float(recent_q["Capital expenditures"])
    owner_salary = float(state["business"].get("owner_salary", 0.0))
    entity_type = state["business"].get("entity_type", "Sole Proprietorship")
    filing_status = state["profile"].get("filing_status", "single")

    # ── Personal income map ───────────────────────────────────────────────
    personal_income_map: Dict[str, float] = {}
    for inc in state["income"]:
        cat = inc.get("category", "Other")
        # Avoid double-counting the owner salary added below
        if cat == "W-2" and inc.get("description") == "Business Owner Salary":
            continue
        personal_income_map[cat] = personal_income_map.get(cat, 0.0) + float(inc.get("amount", 0.0))
    personal_income_map["W-2"] = personal_income_map.get("W-2", 0.0) + owner_salary

    annual_net_biz_income = (ebitda_q - owner_salary / 4.0) * 4.0

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
        "owner_salary": owner_salary,
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

    # ── Net Worth ─────────────────────────────────────────────────────────
    nw_result = calculate_net_worth(state["assets"], state["liabilities"])
    nw_proj_df = pd.DataFrame(project_net_worth(state["assets"], state["liabilities"], quarters=8))

    combined_tax = fed_tax["combined_tax"] + nc_tax["combined_tax"]

    return {
        # Tax
        "fed_tax": fed_tax,
        "nc_tax": nc_tax,
        "combined_tax": combined_tax,
        "effective_rate": fed_tax.get("combined_effective_tax_rate", 0.0),
        # Business
        "ebitda_q": ebitda_q,
        "revenue_q": revenue_q,
        "capex_q": capex_q,
        "annual_net_biz_income": annual_net_biz_income,
        "owner_salary": owner_salary,
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
    }
