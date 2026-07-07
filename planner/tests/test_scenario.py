import pytest
from planner.engines.scenario import compile_scenario

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
