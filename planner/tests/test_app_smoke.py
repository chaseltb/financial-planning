import importlib

from planner.data_manager import get_scenarios_list, load_project_state
from planner.engines.runner import run_all_engines


def test_every_scenario_runs_through_all_engines():
    for name in get_scenarios_list():
        r = run_all_engines(load_project_state(name))
        assert r["fed_tax"]["combined_tax"] >= 0
        assert r["val_result"]["value"] >= 0
        assert len(r["nw_proj_df"]) == 9


def test_app_and_all_page_layouts_build():
    from planner import app as app_module
    for page in ("overview", "personal", "business", "taxes", "networth", "valuation", "forecast", "scenarios", "settings"):
        mod = importlib.import_module(f"planner.pages.{page}")
        assert mod.layout() is not None
    assert app_module.app.layout is not None


def test_app_makes_no_external_requests():
    """Local-first: theme, icons, and fonts are bundled, so no asset points off-machine."""
    import re
    from pathlib import Path
    from planner import app as app_module
    assets = Path(app_module.__file__).parent / "assets"
    assert all(str(u).startswith("/") for u in app_module.app.config.external_stylesheets)
    css = (assets / "styles.css").read_text(encoding="utf-8")
    assert not re.search(r"(@import\s+url\(|url\()\s*['\"]?https?://", css)
    for name in ("bootstrap-slate.min.css", "bootstrap-icons/bootstrap-icons.min.css"):
        assert (assets / "vendor" / name).exists()
