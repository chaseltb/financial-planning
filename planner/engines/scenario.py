from typing import Dict, Any, List

def apply_scenario_changes(
    baseline_data: Dict[str, Any],
    changes: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Applies scenario changes (diffs) to baseline data recursively or by flat keys.
    Flat keys can use dot-notation, e.g. "business.owner_salary" or "personal.filing_status".
    """
    import copy
    compiled = copy.deepcopy(baseline_data)
    
    for key, value in changes.items():
        if "." in key:
            # Nested dot notation: "business.owner_salary"
            parts = key.split(".")
            current = compiled
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        else:
            # Flat key: "payroll" -> apply to business or root
            if isinstance(compiled, dict):
                compiled[key] = value
                
    return compiled


def compile_scenario(
    baseline: Dict[str, Any],
    scenario: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Given the full baseline data (containing personal, business, assumptions, assets, liabilities, etc.)
    and a scenario dictionary, returns the compiled scenario data.
    """
    changes = scenario.get("changes", {})
    return apply_scenario_changes(baseline, changes)
