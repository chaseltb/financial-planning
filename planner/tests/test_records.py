import pytest
from planner.engines.records import annualize_records, taxable_income_by_category, is_taxable
from planner.engines.cashflow import calculate_combined_cashflow


def test_annualize_by_frequency_and_idempotent():
    recs = [{"amount": 100, "frequency": "Monthly"}, {"amount": 100, "frequency": "Quarterly"},
            {"amount": 100}, {"amount": "bad"}]
    once = annualize_records(recs)
    assert [r["amount"] for r in once] == [1200, 400, 100, 0]
    assert annualize_records(once) == once
    assert recs[0]["amount"] == 100  # input untouched


def test_taxable_flag_excludes_income_from_tax_map():
    income = [{"category": "W-2", "amount": 1000, "taxable": "True"},
              {"category": "Other", "amount": 500, "taxable": "False"},
              {"category": "W-2", "amount": 10, "frequency": "Monthly"}]
    assert taxable_income_by_category(income) == {"W-2": 1120.0}
    assert not is_taxable({"taxable": False}) and is_taxable({})


def test_cashflow_honors_frequency():
    res = calculate_combined_cashflow(
        personal_income=[{"category": "W-2", "amount": 1000, "frequency": "Monthly"}],
        personal_expenses=[{"category": "Housing", "amount": 500, "frequency": "Monthly"}],
        liabilities=[], retirement_contributions={"roth_ira": 1000.0}, tax_result={"combined_tax": 0.0})
    assert res["total_inflows"] == 12000
    assert res["value"] == pytest.approx(12000 - 6000 - 1000)
