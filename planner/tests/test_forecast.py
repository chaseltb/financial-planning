import pytest
import pandas as pd

from planner.engines.forecast import run_forecast, get_next_quarter, DEFAULT_SEED

fed_rules_2026 = {
    "tax_year": 2026,
    "standard_deduction": {"single": 16100.0, "married": 32200.0},
    "brackets": {
        "single": [
            {"rate": 0.10, "threshold": 0.0},
            {"rate": 0.12, "threshold": 12400.0},
        ],
        "married": [
            {"rate": 0.10, "threshold": 0.0},
        ],
    },
    "social_security_rate": 0.062,
    "social_security_limit": 184500.0,
    "medicare_rate": 0.0145,
    "additional_medicare_rate": 0.009,
    "additional_medicare_threshold": {"single": 200000.0, "married": 250000.0},
    "corporate_rate": 0.21,
}

nc_rules_2026 = {
    "tax_year": 2026,
    "flat_rate": 0.045,
    "corporate_rate": 0.025,
    "standard_deduction": {"single": 12750.0, "married": 25500.0},
}


def _business_profile(revenue_growth):
    return {
        "revenue_growth": revenue_growth,
        "expense_growth": 0.0,
        "entity_type": "Sole Proprietorship",
        "owner_salary": 0.0,
        "ownership_pct": 100.0,
    }


def test_get_next_quarter_rolls_year_forward():
    assert get_next_quarter("2025-Q4") == "2026-Q1"
    assert get_next_quarter("2026-Q1") == "2026-Q2"
    assert get_next_quarter("2026-Q4") == "2027-Q1"


@pytest.mark.parametrize("growth", [0.0, 0.01, -0.01])
def test_revenue_carries_forward_across_quarters_and_years(growth):
    history_df = pd.DataFrame([DEFAULT_SEED])
    result = run_forecast(
        history_df=history_df,
        business_profile=_business_profile(growth),
        personal_profile={},
        personal_income_list=[],
        assumptions={},
        fed_rules=fed_rules_2026,
        nc_rules=nc_rules_2026,
        horizon=8,  # crosses a Dec 31 -> Jan 1 year boundary
    )
    only_df = result["only_forecast_df"]

    # Forecast must carry every quarter forward from the last historical quarter,
    # not restart from the seed or reset at the year boundary.
    expected_quarters = ["2026-Q1", "2026-Q2", "2026-Q3", "2026-Q4",
                         "2027-Q1", "2027-Q2", "2027-Q3", "2027-Q4"]
    assert list(only_df["Quarter"]) == expected_quarters

    seed_revenue = DEFAULT_SEED["Revenue"]
    expected_revenue = seed_revenue
    for i, row_revenue in enumerate(only_df["Revenue"]):
        expected_revenue *= (1 + growth)
        assert row_revenue == pytest.approx(expected_revenue), f"quarter index {i}"

    # Growth must compound across the year rollover exactly like any other quarter —
    # i.e. 2027-Q1 grows from 2026-Q4, not from the original seed.
    q4_2026 = only_df.loc[only_df["Quarter"] == "2026-Q4", "Revenue"].iloc[0]
    q1_2027 = only_df.loc[only_df["Quarter"] == "2027-Q1", "Revenue"].iloc[0]
    assert q1_2027 == pytest.approx(q4_2026 * (1 + growth))


def test_zero_growth_holds_revenue_flat():
    history_df = pd.DataFrame([DEFAULT_SEED])
    result = run_forecast(
        history_df=history_df,
        business_profile=_business_profile(0.0),
        personal_profile={},
        personal_income_list=[],
        assumptions={},
        fed_rules=fed_rules_2026,
        nc_rules=nc_rules_2026,
        horizon=4,
    )
    only_df = result["only_forecast_df"]
    assert (only_df["Revenue"] == DEFAULT_SEED["Revenue"]).all()


def test_declining_revenue_never_goes_negative_and_keeps_compounding():
    history_df = pd.DataFrame([DEFAULT_SEED])
    result = run_forecast(
        history_df=history_df,
        business_profile=_business_profile(-0.01),
        personal_profile={},
        personal_income_list=[],
        assumptions={},
        fed_rules=fed_rules_2026,
        nc_rules=nc_rules_2026,
        horizon=8,
    )
    only_df = result["only_forecast_df"]
    assert (only_df["Revenue"] > 0).all()
    assert (only_df["Revenue"].diff().dropna() < 0).all()  # strictly declining each quarter


def test_manual_override_carries_forward_growth_from_overridden_value():
    # A single manually-overridden quarter should still seed growth for the
    # quarters that follow it, rather than the override being an isolated blip.
    history_df = pd.DataFrame([DEFAULT_SEED])
    result = run_forecast(
        history_df=history_df,
        business_profile=_business_profile(0.10),
        personal_profile={},
        personal_income_list=[],
        assumptions={},
        fed_rules=fed_rules_2026,
        nc_rules=nc_rules_2026,
        horizon=4,
        overrides={"2026-Q2": {"Revenue": 10000.0}},
    )
    only_df = result["only_forecast_df"].set_index("Quarter")
    assert only_df.loc["2026-Q2", "Revenue"] == 10000.0
    assert only_df.loc["2026-Q3", "Revenue"] == pytest.approx(10000.0 * 1.10)
    assert only_df.loc["2026-Q4", "Revenue"] == pytest.approx(10000.0 * 1.10 * 1.10)
