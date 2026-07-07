import pytest
from planner.engines.networth import calculate_net_worth, project_net_worth

def test_net_worth():
    assets = [
        {"category": "Cash", "description": "Savings", "value": 50000.0, "growth_rate": 0.02},
        {"category": "Brokerage", "description": "Stocks", "value": 150000.0, "growth_rate": 0.08}
    ]
    liabilities = [
        {"category": "Auto loans", "description": "Car Loan", "value": 20000.0, "interest_rate": 0.05, "monthly_payment": 400.0}
    ]

    res = calculate_net_worth(assets, liabilities)

    assert res["total_assets"] == 200000.0
    assert res["total_liabilities"] == 20000.0
    assert res["value"] == 180000.0
    assert pytest.approx(res["asset_pct"]["Cash"]) == 0.25
    assert pytest.approx(res["asset_pct"]["Brokerage"]) == 0.75
    assert res["debt_pct"]["Auto loans"] == 1.0


def test_projection():
    assets = [
        {"category": "Cash", "description": "Savings", "value": 10000.0, "growth_rate": 0.04}
    ]
    liabilities = [
        {"category": "Other", "description": "No-interest Loan", "value": 2000.0,
         "interest_rate": 0.0, "monthly_payment": 200.0}
    ]

    proj = project_net_worth(assets, liabilities, quarters=4)

    # Current net worth: 10000 - 2000 = 8000
    assert proj[0]["Net Worth"] == 8000.0
    # Q1: Cash = 10000 * (1 + 0.04/4) = 10100
    # Loan: 3 months of $200 payments, $0 interest -> 2000 - 600 = 1400
    # Q1 Net Worth = 10100 - 1400 = 8700
    assert pytest.approx(proj[1]["Net Worth"]) == 8700.0

