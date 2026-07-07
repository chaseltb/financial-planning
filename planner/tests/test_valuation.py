import pytest
from planner.engines.valuation import calculate_valuation, calculate_sensitivity

def test_valuation():
    metrics = {
        "revenue": 500000.0,
        "ebitda": 100000.0,
        "net_income": 80000.0,
        "owner_salary": 90000.0,
        "capex": 10000.0,
        "taxes": 20000.0
    }
    
    multiples = {
        "revenue": 2.0,
        "ebitda": 5.0,
        "net_income": 7.0,
        "sde": 4.0,
        "fcf": 6.0
    }
    
    res = calculate_valuation(metrics, multiples)
    
    # Revenue value = 500k * 2.0 = 1M
    assert res["valuations"]["Revenue Multiple"] == 1000000.0
    # EBITDA value = 100k * 5.0 = 500k
    assert res["valuations"]["EBITDA Multiple"] == 500000.0
    # Net Income value = 80k * 7.0 = 560k
    assert res["valuations"]["Net Income Multiple"] == 560000.0
    
    # SDE = EBITDA (100k) + Owner Salary (90k) = 190k
    # SDE value = 190k * 4.0 = 760k
    assert res["valuations"]["SDE Multiple"] == 760000.0
    
    # FCF = EBITDA (100k) - CapEx (10k) - Taxes (20k) = 70k
    # FCF value = 70k * 6.0 = 420k
    assert res["valuations"]["FCF Multiple"] == 420000.0


def test_sensitivity():
    metrics = {
        "revenue": 500000.0,
        "ebitda": 100000.0,
        "net_income": 80000.0,
        "owner_salary": 90000.0,
        "capex": 10000.0,
        "taxes": 20000.0
    }
    
    multiples = {
        "revenue": 2.0,
        "ebitda": 5.0,
        "net_income": 7.0,
        "sde": 4.0,
        "fcf": 6.0
    }
    
    val_res = calculate_valuation(metrics, multiples)
    sens = calculate_sensitivity(val_res, "EBITDA Multiple", range_pct=0.20)
    
    assert sens["base_value"] == 500000.0
    assert sens["lower_value"] == 400000.0
    assert sens["upper_value"] == 600000.0
    assert len(sens["sensitivity_curve"]) == 9
