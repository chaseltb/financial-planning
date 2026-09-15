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
    # Outflows: Housing (24,000) + Food (6,000) + all debt service (400+1500)*12=22,800
    #   + retirement (5,000) + taxes (15,000) = 72,800
    # A liability's monthly_payment is always counted: it's the single authoritative
    # source for that debt's payment, regardless of what's logged under "Housing"
    # (rent, property tax, insurance, HOA — never the mortgage payment itself).
    assert res["total_outflows"] == 72800.0
    assert res["value"] == 7700.0
    assert res["breakdown"]["outflows"]["Debt Service"] == 22800.0


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


def test_combined_cashflow_mortgage_and_other_housing_costs_both_count():
    # A homeowner logging property tax/insurance/HOA under "Housing" (never the
    # mortgage payment itself, which lives on the Liabilities ledger) must still
    # have the mortgage's own monthly_payment counted as debt service.
    personal_income = [{"category": "W-2", "amount": 100000.0}]
    personal_expenses = [{"category": "Housing", "amount": 6000.0}]  # property tax/insurance/HOA
    liabilities = [{"category": "Mortgage", "monthly_payment": 2000.0}]

    res = calculate_combined_cashflow(personal_income, personal_expenses, liabilities, {}, {"combined_tax": 0.0})

    assert res["breakdown"]["outflows"]["Debt Service"] == 24000.0
    assert res["total_outflows"] == 30000.0


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
