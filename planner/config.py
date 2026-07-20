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

# The "Baseline" scenario's internal key never changes (scenario diffing,
# load/save routing, and the "can't rename/delete this one" guards all key
# off the literal string "Baseline"). This is just the label shown for it
# anywhere it appears in the UI, since its shipped default data models a
# median North Carolina personal income (no business) rather than a blank
# slate. The other starter scenarios (side hustle, junior/senior SWE) are
# layered on top of this one as diffs — see planner/data/scenarios/.
BASELINE_DISPLAY_NAME = "NC Median Income 2024 (Baseline)"
