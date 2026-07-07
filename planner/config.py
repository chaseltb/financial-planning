import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TAX_RULES_DIR = BASE_DIR / "tax_rules"
SCENARIOS_DIR = DATA_DIR / "scenarios"

# Ensure directories exist
for path in [DATA_DIR, TAX_RULES_DIR, SCENARIOS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Theme configuration
THEMES = {
    "dark": "slate",  # Bootstrap dark theme slate
    "light": "flatly"
}

# General Settings Defaults
DEFAULT_TAX_YEAR = 2026
DEFAULT_STATE = "NC"
DEFAULT_CURRENCY = "USD"
