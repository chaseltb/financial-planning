import pytest
from planner.engines.allocation import calculate_budget_allocation


def test_split_normalizes_percentages():
    res = calculate_budget_allocation(1000.0, {"A": 1, "B": 3})
    assert res["amounts"] == {"A": pytest.approx(250.0), "B": pytest.approx(750.0)}


def test_shortfall_allocates_nothing():
    res = calculate_budget_allocation(-500.0, {"A": 50, "B": 50})
    assert res["has_shortfall"] and sum(res["amounts"].values()) == 0.0


def test_all_zero_percentages_allocate_nothing():
    assert calculate_budget_allocation(100.0, {"A": 0})["amounts"] == {"A": 0.0}
