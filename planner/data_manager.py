import os
import json
import csv
import copy
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
from dash import html

from planner.config import DATA_DIR, TAX_RULES_DIR, SCENARIOS_DIR, DEFAULT_TAX_YEAR, DEFAULT_STATE

logger = logging.getLogger(__name__)

def _atomic_write(path: Path, write_fn):
    """Write via a temp file in the same directory, then atomically replace the
    target. Guards against a crash or interrupted write leaving a truncated /
    corrupt file on disk (the previous version otherwise wrote straight to the
    real path, so any failure mid-write destroyed the last good save).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
            write_fn(f)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise

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
    _atomic_write(path, lambda f: json.dump(data, f, indent=2))

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
    if not fieldnames and items:
        fieldnames = list(items[0].keys())

    def _write(f):
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow(item)

    _atomic_write(path, _write)

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

_REQUIRED_STATE_KEYS = [
    "profile", "business", "assumptions",
    "income", "expenses", "assets", "liabilities", "forecast",
]

def save_project_state(state: Dict[str, Any], active_scenario: str = "Baseline"):
    missing = [k for k in _REQUIRED_STATE_KEYS if k not in state]
    if missing:
        raise ValueError(f"Refusing to save: state is missing {', '.join(missing)}")

    # If active scenario is baseline, save directly to master files
    if active_scenario == "Baseline":
        writes = [
            (save_json, DATA_DIR / "profile.json", state["profile"]),
            (save_json, DATA_DIR / "business.json", state["business"]),
            (save_json, DATA_DIR / "assumptions.json", state["assumptions"]),
            (save_csv, DATA_DIR / "income.csv", state["income"]),
            (save_csv, DATA_DIR / "expenses.csv", state["expenses"]),
            (save_csv, DATA_DIR / "assets.csv", state["assets"]),
            (save_csv, DATA_DIR / "liabilities.csv", state["liabilities"]),
            (save_csv, DATA_DIR / "forecast.csv", state["forecast"]),
        ]
        for save_fn, path, data in writes:
            try:
                save_fn(path, data)
            except Exception as e:
                raise IOError(f"Failed writing {path.name}: {e}") from e
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

def _save_status_span(icon: str, text: str, color: str):
    return html.Span(
        [html.I(className=f"bi {icon} me-1"), text],
        style={"color": color},
    )

def save_or_mark_unsaved(state: Dict[str, Any], active_scenario: str, autosave_enabled: Any):
    """Persist to disk if autosave is on (the default); otherwise leave the
    edit in-memory only (project-state-store still updates so calculations
    stay live) and tell the user to use the "Save Now" button on Settings.
    Shared by every page's persist-edits callback so the autosave toggle
    actually does something, instead of always saving unconditionally.
    Returns a colored Dash component (not a plain string) so success, the
    autosave-off state, and failure are visually distinct at a glance instead
    of all rendering as the same small gray text.
    """
    if autosave_enabled is False:
        return _save_status_span("bi-cloud-slash", "Not saved (autosave off)", "var(--text-muted, #94a3b8)")
    try:
        save_project_state(state, active_scenario)
        timestamp = datetime.now().strftime("%I:%M:%S %p")
        return _save_status_span("bi-cloud-check-fill", f"Saved {timestamp}", "var(--accent-emerald, #10b981)")
    except Exception as e:
        logger.exception("Failed to save project state (scenario=%s)", active_scenario)
        return _save_status_span("bi-exclamation-triangle-fill", f"Save failed: {e}", "var(--accent-red, #ef4444)")


def load_tax_rules(year: int = DEFAULT_TAX_YEAR, state_code: str = DEFAULT_STATE) -> Dict[str, Any]:
    fed_path = TAX_RULES_DIR / str(year) / "federal.json"
    nc_path = TAX_RULES_DIR / str(year) / "north_carolina.json"
    
    fed_rules = load_json(fed_path)
    nc_rules = load_json(nc_path)
    
    return {
        "federal": fed_rules,
        "north_carolina": nc_rules
    }
