import pytest
from planner.engines.tax.payroll import calculate_payroll_tax, calculate_self_employment_tax
from planner.engines.tax.federal import calculate_federal_tax, calculate_bracket_tax, calculate_cap_gains_tax
from planner.engines.tax.north_carolina import calculate_nc_tax

# Dummy tax rules for test
fed_rules_2026 = {
    "tax_year": 2026,
    "standard_deduction": {"single": 16100.0, "married": 32200.0},
    "brackets": {
        "single": [
            {"rate": 0.10, "threshold": 0.0},
            {"rate": 0.12, "threshold": 12400.0},
            {"rate": 0.22, "threshold": 50400.0},
            {"rate": 0.24, "threshold": 107550.0}
        ],
        "married": [
            {"rate": 0.10, "threshold": 0.0},
            {"rate": 0.12, "threshold": 24800.0}
        ]
    },
    "corporate_rate": 0.21,
    "social_security_rate": 0.062,
    "social_security_limit": 184500.0,
    "medicare_rate": 0.0145,
    "additional_medicare_threshold": {"single": 200000.0, "married": 250000.0},
    "additional_medicare_rate": 0.009
}

nc_rules_2026 = {
    "tax_year": 2026,
    "standard_deduction": {"single": 12750.0, "married": 25500.0},
    "flat_rate": 0.0399,
    "corporate_rate": 0.025
}

def test_bracket_tax():
    # Ordinary progressive tax test
    # Taxable income = $20,000 (Single)
    # First bracket: 10% on $12,400 -> $1,240
    # Second bracket: 12% on ($20,000 - $12,400) = $7,600 -> $912
    # Total = $2,152
    tax, steps = calculate_bracket_tax(20000.0, fed_rules_2026["brackets"]["single"])
    assert pytest.approx(tax) == 2152.0
    assert len(steps) == 2


def test_payroll_tax():
    # Payroll tax on $100,000 (Single)
    # SS = $100,000 * 6.2% = $6,200
    # Med = $100,000 * 1.45% = $1,450
    # Add Med = $0 (below $200,000)
    # Total = $7,650
    res = calculate_payroll_tax(100000.0, "single", fed_rules_2026)
    assert pytest.approx(res["value"]) == 7650.0
    assert pytest.approx(res["social_security"]) == 6200.0
    assert pytest.approx(res["medicare"]) == 1450.0
    assert res["additional_medicare"] == 0.0


def test_payroll_tax_high_income():
    # Payroll tax on $250,000 (Single)
    # SS limit = $184,500 * 6.2% = $11,439.00
    # Med = $250,000 * 1.45% = $3,625
    # Add Med = ($250,000 - $200,000) * 0.9% = $50,000 * 0.009 = $450
    # Total = $15,514.00
    res = calculate_payroll_tax(250000.0, "single", fed_rules_2026)
    assert pytest.approx(res["value"]) == 15514.0
    assert pytest.approx(res["social_security"]) == 11439.0
    assert pytest.approx(res["medicare"]) == 3625.0
    assert pytest.approx(res["additional_medicare"]) == 450.0


def test_self_employment_tax():
    # Net SE profit = $100,000 (Single)
    # Net SE earnings = $100,000 * 92.35% = $92,350
    # SE SS = $92,350 * 12.4% = $11,451.40
    # SE Med = $92,350 * 2.9% = $2,678.15
    # Total SE tax = $14,129.55
    res = calculate_self_employment_tax(100000.0, "single", fed_rules_2026)
    assert pytest.approx(res["value"]) == 14129.55
    assert pytest.approx(res["deductible_amount"]) == 7064.775


def test_nc_state_tax():
    # Federal AGI = $80,000 (Single)
    # NC Standard Deduction = $12,750
    # NC Taxable = $67,250
    # NC Tax = $67,250 * 3.99% = $2,683.275
    res = calculate_nc_tax(80000.0, 0.0, 0.0, "Sole Proprietorship", "single", nc_rules_2026)
    assert pytest.approx(res["value"]) == 2683.275


def test_bracket_tax_below_first_threshold():
    # Taxable income entirely inside the 0%-start bracket still gets taxed at that bracket's rate
    tax, steps = calculate_bracket_tax(5000.0, fed_rules_2026["brackets"]["single"])
    assert pytest.approx(tax) == 500.0
    assert len(steps) == 1


def test_bracket_tax_zero_income():
    tax, steps = calculate_bracket_tax(0.0, fed_rules_2026["brackets"]["single"])
    assert tax == 0.0
    assert steps == []


def test_cap_gains_tax_zero_gains():
    tax, steps = calculate_cap_gains_tax(0.0, 50000.0, "single")
    assert tax == 0.0
    assert steps == ["No capital gains or qualified dividends to tax."]


def test_federal_tax_sole_proprietorship():
    # $100k net business profit, no personal W-2, no retirement contributions
    res = calculate_federal_tax({}, 100000.0, "Sole Proprietorship", {}, "single", fed_rules_2026)
    assert pytest.approx(res["se_tax"]) == 14129.55
    assert pytest.approx(res["agi"]) == 92935.225
    assert pytest.approx(res["taxable_income"]) == 61468.18
    assert pytest.approx(res["value"]) == 8234.9996
    assert pytest.approx(res["combined_tax"]) == 22364.5496
    # Sole props owe SE tax on the full profit; no employer/employee payroll tax applies
    assert res["payroll_tax"] == 0.0
    assert res["employer_payroll_tax"] == 0.0
    assert res["corporate_tax"] == 0.0


def test_federal_tax_s_corporation():
    # $60k reasonable W-2 salary, $200k total business profit before that salary
    res = calculate_federal_tax(
        {"W-2": 60000.0}, 200000.0, "S Corporation", {}, "single", fed_rules_2026,
        owner_w2_salary=60000.0, ownership_pct=1.0,
    )
    # No self-employment tax on S-Corp K-1 distributions
    assert res["se_tax"] == 0.0
    assert res["corporate_tax"] == 0.0
    # Both employee-side and employer-side FICA apply to the W-2 salary
    assert pytest.approx(res["payroll_tax"]) == 4590.0
    assert pytest.approx(res["employer_payroll_tax"]) == 4590.0
    assert pytest.approx(res["agi"]) == 255410.0
    assert pytest.approx(res["combined_tax"]) == 49795.72


def test_federal_tax_c_corporation_with_partial_ownership():
    # $100k business profit, 50% ownership stake; corporate tax always applies to the full 100%
    res = calculate_federal_tax(
        {}, 100000.0, "C Corporation", {}, "single", fed_rules_2026,
        owner_w2_salary=0.0, ownership_pct=0.5,
    )
    assert pytest.approx(res["corporate_tax"]) == 21000.0
    assert pytest.approx(res["combined_tax"]) == 21000.0
    assert res["se_tax"] == 0.0


def test_federal_tax_zero_income():
    res = calculate_federal_tax({}, 0.0, "Sole Proprietorship", {}, "single", fed_rules_2026)
    assert res["value"] == 0.0
    assert res["agi"] == 0.0
    assert res["taxable_income"] == 0.0
    assert res["combined_tax"] == 0.0


def test_nc_c_corporation_tax():
    # Federal AGI $90k (Single) + $100k business profit, C-Corp
    # NC Personal: (90,000 - 12,750) * 3.99% = 3,082.275
    # NC Corporate: 100,000 * 2.5% = 2,500.00
    res = calculate_nc_tax(90000.0, 0.0, 100000.0, "C Corporation", "single", nc_rules_2026)
    assert pytest.approx(res["value"]) == 3082.275
    assert pytest.approx(res["corporate_tax"]) == 2500.0
    assert pytest.approx(res["combined_tax"]) == 5582.275


def test_nc_state_tax_zero_income():
    res = calculate_nc_tax(0.0, 0.0, 0.0, "Sole Proprietorship", "single", nc_rules_2026)
    assert res["value"] == 0.0
    assert res["effective_rate"] == 0.0
