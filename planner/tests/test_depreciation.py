import pytest
from planner.engines.tax.depreciation import calculate_depreciation


def test_straight_line_stops_after_useful_life():
    assert calculate_depreciation(10000, 5, "Straight Line", 0, 5)["value"] == pytest.approx(2000)
    late = calculate_depreciation(10000, 5, "Straight Line", 0, 6)
    assert late["value"] == 0.0
    assert late["book_value_end"] == 0.0


def test_straight_line_respects_salvage():
    res = calculate_depreciation(10000, 4, "Straight Line", 2000, 4)
    assert res["value"] == pytest.approx(2000)
    assert res["book_value_end"] == pytest.approx(2000)


@pytest.mark.parametrize("method,years", [("MACRS 5-Year", 6), ("MACRS 7-Year", 8)])
def test_macrs_totals_full_basis_then_zero(method, years):
    total = sum(calculate_depreciation(10000, years, method, 0, y)["value"] for y in range(1, years + 1))
    assert total == pytest.approx(10000, abs=1.0)
    assert calculate_depreciation(10000, years, method, 0, years + 1)["value"] == 0.0


def test_macrs_first_year_rate():
    assert calculate_depreciation(10000, 5, "MACRS 5-Year", 0, 1)["value"] == pytest.approx(2000)
