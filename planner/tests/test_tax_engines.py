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
