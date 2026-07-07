import os
import json
import csv
import copy
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

from planner.config import DATA_DIR, TAX_RULES_DIR, SCENARIOS_DIR, DEFAULT_TAX_YEAR, DEFAULT_STATE

def load_json(path: Path, default: Dict[str, Any] = None) -> Dict[str, Any]:
    if default is None:
        default = {}
    if not path.exists():
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def load_csv(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    items = []
    try:
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                items.append(dict(row))
    except Exception:
        pass
    return items

def save_csv(path: Path, items: List[Dict[str, Any]], fieldnames: List[str] = None):
    if not items and not fieldnames:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if not fieldnames and items:
        fieldnames = list(items[0].keys())
    
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow(item)

# Scenarios manager
def get_scenarios_list() -> List[str]:
    scenarios = ["Baseline"]
    for path in SCENARIOS_DIR.glob("*.json"):
        if path.stem != "Baseline":
            scenarios.append(path.stem)
    return scenarios

def load_scenario(name: str) -> Dict[str, Any]:
    if name == "Baseline":
        return {"name": "Baseline", "changes": {}}
    path = SCENARIOS_DIR / f"{name}.json"
    return load_json(path, {"name": name, "changes": {}})

def save_scenario(name: str, scenario_data: Dict[str, Any]):
    path = SCENARIOS_DIR / f"{name}.json"
    save_json(path, scenario_data)

def delete_scenario(name: str):
    if name == "Baseline":
        return
    path = SCENARIOS_DIR / f"{name}.json"
    if path.exists():
        path.unlink()

def duplicate_scenario(src: str, dest: str):
    src_data = load_scenario(src)
    dest_data = copy.deepcopy(src_data)
    dest_data["name"] = dest
    save_scenario(dest, dest_data)

# Combined full project state loader/saver
def load_project_state(active_scenario: str = "Baseline") -> Dict[str, Any]:
    # 1. Load Baseline Data
    state = {
        "profile": load_json(DATA_DIR / "profile.json"),
        "business": load_json(DATA_DIR / "business.json"),
        "assumptions": load_json(DATA_DIR / "assumptions.json"),
        "income": load_csv(DATA_DIR / "income.csv"),
        "expenses": load_csv(DATA_DIR / "expenses.csv"),
        "assets": load_csv(DATA_DIR / "assets.csv"),
        "liabilities": load_csv(DATA_DIR / "liabilities.csv"),
        "forecast": load_csv(DATA_DIR / "forecast.csv")
    }
    
    # 2. Compile Scenario if active
    if active_scenario != "Baseline":
        scenario = load_scenario(active_scenario)
        # Apply scenario changes
        from planner.engines.scenario import compile_scenario
        state = compile_scenario(state, scenario)
        
    return state

def save_project_state(state: Dict[str, Any], active_scenario: str = "Baseline"):
    # If active scenario is baseline, save directly to master files
    if active_scenario == "Baseline":
        save_json(DATA_DIR / "profile.json", state["profile"])
        save_json(DATA_DIR / "business.json", state["business"])
        save_json(DATA_DIR / "assumptions.json", state["assumptions"])
        save_csv(DATA_DIR / "income.csv", state["income"])
        save_csv(DATA_DIR / "expenses.csv", state["expenses"])
        save_csv(DATA_DIR / "assets.csv", state["assets"])
        save_csv(DATA_DIR / "liabilities.csv", state["liabilities"])
        save_csv(DATA_DIR / "forecast.csv", state["forecast"])
    else:
        # Save baseline data
        baseline_state = load_project_state("Baseline")
        
        # We need to compute diffs and save them to the scenario json
        diffs = {}
        
        # Helper to diff dicts
        def diff_dicts(base, active, prefix=""):
            for k, v in active.items():
                full_key = f"{prefix}{k}"
                if k not in base:
                    diffs[full_key] = v
                elif isinstance(v, dict) and isinstance(base[k], dict):
                    diff_dicts(base[k], v, f"{full_key}.")
                elif v != base[k]:
                    diffs[full_key] = v
                    
        diff_dicts(baseline_state["profile"], state["profile"], "profile.")
        diff_dicts(baseline_state["business"], state["business"], "business.")
        diff_dicts(baseline_state["assumptions"], state["assumptions"], "assumptions.")
        
        # For CSV items, simple representation of differences is harder;
        # let's store changed CSVs in the scenario directly if they differ
        # E.g. {"income": state["income"]}
        if state["income"] != baseline_state["income"]:
            diffs["income"] = state["income"]
        if state["expenses"] != baseline_state["expenses"]:
            diffs["expenses"] = state["expenses"]
        if state["assets"] != baseline_state["assets"]:
            diffs["assets"] = state["assets"]
        if state["liabilities"] != baseline_state["liabilities"]:
            diffs["liabilities"] = state["liabilities"]
        if state["forecast"] != baseline_state["forecast"]:
            diffs["forecast"] = state["forecast"]
            
        scenario = {
            "name": active_scenario,
            "changes": diffs
        }
        save_scenario(active_scenario, scenario)

def load_tax_rules(year: int = DEFAULT_TAX_YEAR, state_code: str = DEFAULT_STATE) -> Dict[str, Any]:
    fed_path = TAX_RULES_DIR / str(year) / "federal.json"
    nc_path = TAX_RULES_DIR / str(year) / "north_carolina.json"
    
    fed_rules = load_json(fed_path)
    nc_rules = load_json(nc_path)
    
    return {
        "federal": fed_rules,
        "north_carolina": nc_rules
    }
