import pytest
from planner.engines.runner import run_all_engines


def _state(entity="Sole Proprietorship", salary=0.0):
    return {
        "profile": {"filing_status": "single", "retirement_401k": 2700, "retirement_ira": 2000},
        "business": {"entity_type": entity, "owner_salary": salary, "ownership_pct": 100.0,
                     "revenue_growth": 0.0, "expense_growth": 0.0},
        "assumptions": {"tax_year": 2024, "valuation_multiples": {"ebitda": 6}, "forecast_overrides": {}},
        "income": [{"category": "W-2", "amount": 38657}, {"category": "Dividends", "amount": 150},
                   {"category": "Interest", "amount": 130}],
        "expenses": [], "assets": [], "liabilities": [],
        "forecast": [{"Quarter": "2025-Q4", "Revenue": 0, "COGS": 0, "Payroll": 0, "Expenses": 0,
                      "Capital expenditures": 0, "Owner salary": 0, "Distributions": 0,
                      "Tax estimate": 0, "Cash": 0, "EBITDA": 0, "Business value": 0}],
    }


def test_no_business_hand_calculated_taxes():
    r = run_all_engines(_state())
    # AGI = 38657 + 130 + 150 - 4700 = 34237; taxable = 34237 - 14600 = 19637
    assert r["fed_tax"]["agi"] == pytest.approx(34237)
    assert r["fed_tax"]["value"] == pytest.approx(1160 + 0.12 * (19487 - 11600))  # 150 of gains taxed at 0%
    assert r["fed_tax"]["payroll_tax"] == pytest.approx(38657 * 0.0765)
    assert r["nc_tax"]["value"] == pytest.approx((34237 - 12750) * 0.045)


def test_s_corp_owner_salary_is_counted_as_cash_inflow():
    r = run_all_engines(_state("S Corporation", 40000))
    assert r["cashflow"]["breakdown"]["inflows"]["Business Pay & Distributions"] >= 40000
