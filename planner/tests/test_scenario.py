import pytest
from planner.engines.scenario import compile_scenario, apply_scenario_changes

def test_scenario_overlay():
    baseline = {
        "profile": {
            "filing_status": "single",
            "retirement_401k": 20000.0
        },
        "business": {
            "entity_type": "Sole Proprietorship",
            "owner_salary": 50000.0
        }
    }
    
    scenario = {
        "name": "Hire Help",
        "changes": {
            "profile.filing_status": "married",
            "business.owner_salary": 80000.0,
            "new_field": "test"
        }
    }
    
    compiled = compile_scenario(baseline, scenario)
    
    # Check that changed fields are updated
    assert compiled["profile"]["filing_status"] == "married"
    assert compiled["business"]["owner_salary"] == 80000.0
    
    # Check that unchanged fields remain baseline
    assert compiled["profile"]["retirement_401k"] == 20000.0
    assert compiled["business"]["entity_type"] == "Sole Proprietorship"
    
    # Check new field addition
    assert compiled["new_field"] == "test"


def test_scenario_with_no_changes_returns_equal_but_independent_copy():
    baseline = {"profile": {"filing_status": "single"}}

    compiled = compile_scenario(baseline, {"name": "No-op", "changes": {}})

    assert compiled == baseline
    # Must be a deep copy, not the same object, so editing one doesn't affect the other
    compiled["profile"]["filing_status"] = "married"
    assert baseline["profile"]["filing_status"] == "single"


def test_scenario_dot_notation_creates_missing_nested_section():
    baseline = {"profile": {"filing_status": "single"}}

    compiled = apply_scenario_changes(baseline, {"assumptions.inflation_rate": 0.03})

    assert compiled["assumptions"]["inflation_rate"] == 0.03
    # Original baseline section list is untouched
    assert "assumptions" not in baseline


def test_scenario_missing_changes_key_defaults_to_no_changes():
    baseline = {"profile": {"filing_status": "single"}}

    compiled = compile_scenario(baseline, {"name": "Untouched"})

    assert compiled == baseline
