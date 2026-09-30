import json
import pytest
from planner import data_manager as dm


@pytest.fixture
def tmp_data(tmp_path, monkeypatch):
    data = tmp_path / "data"
    (data / "scenarios").mkdir(parents=True)
    monkeypatch.setattr(dm, "DATA_DIR", data)
    monkeypatch.setattr(dm, "SCENARIOS_DIR", data / "scenarios")
    return data


def test_seed_copies_missing_files_but_never_overwrites(tmp_data):
    dm.ensure_seed_data()
    assert (tmp_data / "profile.json").exists()
    (tmp_data / "profile.json").write_text('{"mine": true}')
    dm.ensure_seed_data()
    assert json.loads((tmp_data / "profile.json").read_text()) == {"mine": True}


def test_csv_round_trip(tmp_data):
    rows = [{"id": "a", "amount": "5"}, {"id": "b", "amount": "6"}]
    dm.save_csv(tmp_data / "x.csv", rows)
    assert dm.load_csv(tmp_data / "x.csv") == rows
    assert dm.load_csv(tmp_data / "missing.csv") == []


def test_scenario_save_stores_only_diffs_and_leaves_baseline_alone(tmp_data):
    dm.ensure_seed_data()
    base = dm.load_project_state("Baseline")
    scenario = json.loads(json.dumps(base))
    scenario["business"]["owner_salary"] = 12345
    dm.save_project_state(scenario, "My Scenario")
    assert dm.load_scenario("My Scenario")["changes"] == {"business.owner_salary": 12345}
    assert dm.load_project_state("Baseline")["business"] == base["business"]
    assert dm.load_project_state("My Scenario")["business"]["owner_salary"] == 12345


def test_save_refuses_incomplete_state(tmp_data):
    with pytest.raises(ValueError):
        dm.save_project_state({"profile": {}}, "Baseline")


def test_baseline_scenario_cannot_be_deleted(tmp_data):
    dm.delete_scenario("Baseline")
    assert "Baseline" in dm.get_scenarios_list()


def test_states_equal_ignores_numeric_string_differences():
    assert dm.states_equal({"a": "0.0", "b": [1, "2"]}, {"a": 0, "b": [1.0, 2]})
    assert not dm.states_equal({"a": "0.0"}, {"a": 1})
    assert not dm.states_equal({"a": "x"}, {"a": "y"})


def test_save_csv_handles_rows_with_different_columns(tmp_data):
    rows = [{"category": "W-2", "amount": "1"}, {"id": "x", "category": "Other", "amount": "2", "frequency": "Annual", "taxable": "True"}]
    dm.save_csv(tmp_data / "mixed.csv", rows)
    loaded = dm.load_csv(tmp_data / "mixed.csv")
    assert loaded[0]["id"] == "" and loaded[1]["taxable"] == "True" and len(loaded) == 2
