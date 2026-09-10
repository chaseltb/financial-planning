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


def test_net_worth_empty_portfolio():
    res = calculate_net_worth([], [])

    assert res["total_assets"] == 0.0
    assert res["total_liabilities"] == 0.0
    assert res["value"] == 0.0
    assert res["asset_pct"] == {}
    assert res["debt_pct"] == {}


def test_net_worth_negative_when_debt_exceeds_assets():
    assets = [{"category": "Cash", "description": "Savings", "value": 5000.0, "growth_rate": 0.0}]
    liabilities = [
        {"category": "Student loans", "description": "Loan", "value": 30000.0,
         "interest_rate": 0.05, "monthly_payment": 300.0}
    ]

    res = calculate_net_worth(assets, liabilities)

    assert res["value"] == -25000.0


def test_projection_routes_savings_and_brokerage_allocation_into_matching_assets():
    assets = [
        {"category": "Cash", "description": "Savings", "value": 10000.0, "growth_rate": 0.0},
        {"category": "Brokerage", "description": "Index Funds", "value": 5000.0, "growth_rate": 0.0},
    ]
    liabilities = []

    proj = project_net_worth(
        assets, liabilities, quarters=2,
        quarterly_allocation={"Savings": 1000.0, "Taxable Brokerage": 500.0},
    )

    # Each quarter's allocated contribution compounds into next quarter's total.
    assert proj[1]["Assets"] == pytest.approx(10000.0 + 1000.0 + 5000.0 + 500.0)
    assert proj[2]["Assets"] == pytest.approx(10000.0 + 2000.0 + 5000.0 + 1000.0)


def test_projection_creates_bucket_when_no_matching_asset_category_exists():
    # No "Cash" or "Brokerage" category asset exists yet — allocation should still
    # show up in the projection via a new bucket, not silently disappear.
    assets = [{"category": "Retirement", "description": "401k", "value": 20000.0, "growth_rate": 0.0}]

    proj = project_net_worth(
        assets, [], quarters=1,
        quarterly_allocation={"Savings": 300.0, "Taxable Brokerage": 200.0},
    )

    assert proj[1]["Assets"] == pytest.approx(20000.0 + 300.0 + 200.0)


def test_projection_pays_down_highest_interest_liability_first():
    liabilities = [
        {"category": "Auto loans", "description": "Car", "value": 5000.0,
         "interest_rate": 0.05, "monthly_payment": 0.0},
        {"category": "Credit cards", "description": "Card", "value": 3000.0,
         "interest_rate": 0.20, "monthly_payment": 0.0},
    ]

    proj = project_net_worth(
        [], liabilities, quarters=1,
        quarterly_allocation={"Liability Paydown": 1000.0},
    )

    # $1000 extra paydown must hit the 20% APR card before the 5% APR auto loan.
    # Auto loan still accrues a quarter of interest untouched by the extra payment.
    expected_auto = 5000.0 * (1 + 0.05 / 12.0) ** 3
    expected_card = 3000.0 * (1 + 0.20 / 12.0) ** 3 - 1000.0
    assert proj[1]["Liabilities"] == pytest.approx(expected_auto + expected_card, rel=1e-3)

