import pytest
from planner.engines.cashflow import calculate_combined_cashflow


def test_combined_cashflow():
    personal_income = [
        {"category": "W-2", "amount": 80000.0},
        {"category": "Interest", "amount": 500.0},
    ]
    personal_expenses = [
        {"category": "Housing", "amount": 24000.0},
        {"category": "Food", "amount": 6000.0},
    ]
    liabilities = [
        {"category": "Auto loans", "monthly_payment": 400.0},
        {"category": "Mortgage", "monthly_payment": 1500.0},
    ]
    retirement_contributions = {"retirement_401k": 5000.0}
    tax_result = {"combined_tax": 15000.0}

    res = calculate_combined_cashflow(
        personal_income, personal_expenses, liabilities, retirement_contributions, tax_result
    )

    # Inflows: W-2 (80,000) + Interest (500) = 80,500
    assert res["total_inflows"] == 80500.0
    # Outflows: Housing (24,000) + Food (6,000) + non-mortgage debt (400*12=4,800)
    #   + retirement (5,000) + taxes (15,000) = 54,800
    # Mortgage payment is excluded from debt service since Housing expenses are already present.
    assert res["total_outflows"] == 54800.0
    assert res["value"] == 25700.0
    assert res["breakdown"]["outflows"]["Debt Service"] == 4800.0


def test_combined_cashflow_negative():
    personal_income = [{"category": "W-2", "amount": 30000.0}]
    personal_expenses = [{"category": "Housing", "amount": 40000.0}]

    res = calculate_combined_cashflow(personal_income, personal_expenses, [], {}, {"combined_tax": 5000.0})

    assert res["value"] == -15000.0


def test_combined_cashflow_no_housing_includes_mortgage():
    # Without a Housing expense entry, mortgage payments count as debt service instead
    personal_income = [{"category": "W-2", "amount": 60000.0}]
    liabilities = [{"category": "Mortgage", "monthly_payment": 1000.0}]

    res = calculate_combined_cashflow(personal_income, [], liabilities, {}, {"combined_tax": 0.0})

    assert res["breakdown"]["outflows"]["Debt Service"] == 12000.0
    assert res["value"] == 48000.0


def test_combined_cashflow_empty_inputs():
    res = calculate_combined_cashflow([], [], [], {}, {})

    assert res["total_inflows"] == 0.0
    assert res["total_outflows"] == 0.0
    assert res["value"] == 0.0


def test_combined_cashflow_uses_value_fallback_when_no_combined_tax():
    # tax_result may only carry "value" (e.g. a single tax engine's result rather than combined)
    res = calculate_combined_cashflow(
        [{"category": "W-2", "amount": 50000.0}], [], [], {}, {"value": 4000.0}
    )

    assert res["breakdown"]["outflows"]["Taxes"] == 4000.0
