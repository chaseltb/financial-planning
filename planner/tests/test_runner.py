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


def _biz_state(**business):
    st = _state("Sole Proprietorship")
    st["business"].update(business)
    st["forecast"] = [{"Quarter": "2025-Q4", "Revenue": 4000.0, "COGS": 0.0, "Payroll": 0.0, "Expenses": 1500.0,
                       "Capital expenditures": 0.0, "Owner salary": 0.0, "Distributions": 0.0,
                       "Tax estimate": 0.0, "Cash": 0.0, "EBITDA": 2500.0, "Business value": 0.0}]
    return st  # 2,500/qtr EBITDA = 10,000 annual profit


def test_effective_rate_is_total_federal_plus_nc_over_agi():
    r = run_all_engines(_state())
    assert r["effective_rate"] == pytest.approx(r["combined_tax"] / r["fed_tax"]["agi"])
    assert r["effective_rate"] > r["fed_tax"]["combined_effective_tax_rate"]  # NC is included


def test_business_deductions_lower_tax_but_not_cash_or_valuation():
    base = run_all_engines(_biz_state())
    ded = run_all_engines(_biz_state(ded_home_office=1500, ded_vehicle=500))
    assert ded["combined_tax"] < base["combined_tax"]
    # 2,000 less profit: SE tax falls by 2,000 * 0.9235 * 15.3%
    assert base["fed_tax"]["se_tax"] - ded["fed_tax"]["se_tax"] == pytest.approx(2000 * 0.9235 * 0.153)
    assert ded["annual_net_biz_income"] == base["annual_net_biz_income"] == pytest.approx(10000)
    assert ded["val_result"]["value"] == base["val_result"]["value"]


def test_self_employed_health_insurance_is_an_agi_adjustment_not_se_base():
    base = run_all_engines(_biz_state())
    ins = run_all_engines(_biz_state(ded_health_insurance=3000))
    assert ins["fed_tax"]["se_tax"] == pytest.approx(base["fed_tax"]["se_tax"])
    assert base["fed_tax"]["agi"] - ins["fed_tax"]["agi"] == pytest.approx(3000)
    # limited to profit after the SE-tax deduction
    huge = run_all_engines(_biz_state(ded_health_insurance=50000))
    cap = 10000 - base["fed_tax"]["se_tax"] / 2
    assert base["fed_tax"]["agi"] - huge["fed_tax"]["agi"] == pytest.approx(cap)
