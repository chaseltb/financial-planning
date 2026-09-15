import pytest
from planner.engines.tax_tips import generate_tax_tips, _combined_tax_savings
from planner.engines.tax.federal import calculate_bracket_tax

_BRACKETS = [
    {"rate": 0.10, "threshold": 0.0},
    {"rate": 0.12, "threshold": 11600.0},
    {"rate": 0.22, "threshold": 47150.0},
]


def _make_r(**overrides):
    base = {
        "fed_tax": {
            "agi": 40000.0, "taxable_income": 20000.0, "taxable_ordinary": 20000.0,
            "taxable_cap_gains": 0.0, "se_tax": 0.0, "qbi_deduction": 0.0,
            "corporate_tax": 0.0,
        },
        "nc_tax": {"flat_rate": 0.045, "value": 0.0, "corporate_tax": 0.0},
        "fed_rules": {"brackets": {"single": _BRACKETS}, "standard_deduction": {"single": 14600.0}},
        "filing_status": "single",
        "entity_type": "Sole Proprietorship",
        "tax_year": 2024,
        "annual_net_biz_income": 0.0,
        "owner_w2_salary": 0.0,
        "business_attributable_tax": 0.0,
    }
    base.update(overrides)
    return base


def _make_state(**overrides):
    base = {
        "profile": {"retirement_401k": 0.0, "retirement_ira": 0.0, "retirement_hsa": 0.0, "solo_401k": 0.0},
        "business": {"owner_salary": 0.0},
        "income": [],
        "liabilities": [],
        "forecast": [],
    }
    base.update(overrides)
    return base


def test_combined_tax_savings_crosses_bracket_correctly():
    # $19,487 taxable ordinary income, a $20,300 deduction wipes it out entirely —
    # savings must be the FULL tax on $19,487, not $20,300 * the top marginal rate.
    savings = _combined_tax_savings(20300.0, 19487.0, _BRACKETS, 0.045)
    fed_tax_before, _ = calculate_bracket_tax(19487.0, _BRACKETS)
    expected = fed_tax_before + 20300.0 * 0.045
    assert pytest.approx(savings) == expected
    # A flat marginal-rate estimate at 12% would have overstated this.
    flat_rate_estimate = 20300.0 * (0.12 + 0.045)
    assert savings < flat_rate_estimate


def test_401k_headroom_tip_requires_w2_income():
    state = _make_state(income=[])
    r = _make_r()
    tips = generate_tax_tips(state, r)
    assert not any("401(k)" in t["title"] for t in tips)

    state_with_w2 = _make_state(income=[{"category": "W-2", "amount": 60000.0}])
    tips_with_w2 = generate_tax_tips(state_with_w2, r)
    assert any("401(k)" in t["title"] for t in tips_with_w2)


def test_ira_phaseout_caveat_appears_at_high_agi():
    state = _make_state()
    r = _make_r(**{"fed_tax": {**_make_r()["fed_tax"], "agi": 100000.0}})
    tips = generate_tax_tips(state, r)
    ira_tip = next(t for t in tips if "IRA" in t["title"])
    assert "not be deductible" in ira_tip["body"].lower() or "not" in ira_tip["body"].lower()


def test_s_corp_election_tip_uses_full_se_rate_on_distribution_share():
    state = _make_state(business={"owner_salary": 0.0})
    r = _make_r(
        entity_type="Single-member LLC",
        annual_net_biz_income=250000.0,
        fed_tax={**_make_r()["fed_tax"], "se_tax": 23434.0},
    )
    tips = generate_tax_tips(state, r)
    s_corp_tip = next(t for t in tips if "S-Corp election" in t["title"])
    expected_savings = 250000.0 * 0.153 * 0.9235 * 0.5
    assert f"${expected_savings:,.0f}" in s_corp_tip["body"]


def test_quarterly_estimated_tax_tip_gated_on_business_attributable_tax():
    state = _make_state()
    r = _make_r(business_attributable_tax=500.0)
    assert not any("quarterly estimated" in t["title"].lower() for t in generate_tax_tips(state, r))

    r_high = _make_r(business_attributable_tax=8000.0)
    tips = generate_tax_tips(state, r_high)
    quarterly_tip = next(t for t in tips if "quarterly estimated" in t["title"].lower())
    assert "$2,000" in quarterly_tip["body"]  # 8000 / 4


def test_capital_loss_harvesting_tip_only_on_net_loss():
    state = _make_state(income=[{"category": "Capital gains", "amount": -4000.0}])
    r = _make_r()
    tips = generate_tax_tips(state, r)
    assert any("investment losses" in t["title"].lower() for t in tips)


def test_itemizing_tip_gated_on_mortgage_interest_relative_to_standard_deduction():
    state = _make_state(liabilities=[
        {"category": "Mortgage", "value": 350000.0, "interest_rate": 0.06, "monthly_payment": 2000.0}
    ])
    r = _make_r()
    tips = generate_tax_tips(state, r)
    assert any("itemizing" in t["title"].lower() for t in tips)
