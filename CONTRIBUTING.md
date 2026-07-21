# Contributing

Thanks for taking a look at this project. It's a small, local-first financial planning tool, and contributions of any size (a typo fix, a bug fix, a new tax rule, a new page) are welcome.

## Ground rules

- **Keep it local-first.** No telemetry, no external API calls, no cloud sync. If a feature needs to phone home, it doesn't belong here (or needs to be strictly opt-in).
- **Cite your sources.** Tax brackets, standard deductions, median income figures, etc. should link to the source and note the tax year they apply to (see `planner/components/citations.py` for the existing pattern).
- **This is not financial advice**, and nothing added should present itself as such.

## Getting set up

Follow the "Getting the code" and "Setting up" sections in the [README](README.md). Once dependencies are installed:

```
pip install -r requirements.txt
python run.py
```

## Running tests

```
python -m pytest planner/tests
```

Please add or update tests in `planner/tests/` for any change to `planner/engines/` (tax, cash flow, net worth, valuation, forecast, scenario). These are the calculations people are trusting with their real numbers, so regressions here matter more than anywhere else in the app.

## Code layout (where to make a change)

- `planner/models/`: data shapes (income, expense, asset, liability, business, person, scenario, tax)
- `planner/engines/`: the actual math (cash flow, net worth, forecast, valuation, scenario diffing, and tax calculation in `engines/tax/`, backed by `planner/tax_rules/<year>/`)
- `planner/pages/`: one Dash page per sidebar item
- `planner/components/`: shared UI pieces (cards, charts, tables, header, sidebar, citations)
- `planner/data_manager.py`: read/write of the JSON/CSV files in `planner/data/`
- `planner/config.py`: app-wide settings

If you're adding a new tax year, add a new folder under `planner/tax_rules/` following the existing year's structure rather than branching logic in the engine.

## Submitting changes

1. Fork/branch, make your change, add/update tests.
2. Run the test suite and manually click through any page you touched (Dash errors don't always show up in tests).
3. Open a PR describing what changed and why. Screenshots are helpful for UI changes.

Small, focused PRs are easier to review than large ones. If you find yourself touching five unrelated things, consider splitting it up.

## Roadmap / ways to help

This is a side project, so the plan below is directional, not a promise of when things land. Rough priority order:

### Near term
- **More states.** Tax logic currently only covers North Carolina (`planner/tax_rules/2026`). Adding a state means: bracket/rate data with citations, a new folder under `tax_rules/`, and wiring it into `engines/tax/`. This is probably the single highest-value contribution right now.
- **More tax years.** Once a second year's federal/state numbers are published, add a new `tax_rules/<year>/` folder so people aren't stuck on stale brackets.
- **Test coverage for edge cases.** Negative cash flow, zero-income scenarios, mid-year business start, multiple owners: the engines should be checked against unusual inputs, not just the happy path.

### Medium term
- **More starter scenarios.** Beyond median income and a couple of SWE levels, more built-in comparison scenarios (different professions, regions, life stages) make the tool useful to more people out of the box.
- **Multi-owner / partnership support** for the Business page, if there's demand. Right now it assumes a single owner.
- **Import from common formats** (e.g. a basic CSV/bank export importer for income/expenses) to reduce manual data entry.
- **Accessibility pass** on the Dash UI (keyboard navigation, contrast, screen reader labels). `planner/assets/styles.css` and the component layer are the places to start.

### Longer term / exploratory
- **Historical tracking.** Right now the app is forward-looking (forecasts, projections); storing periodic snapshots of net worth/cash flow over time would let people see actual trend lines, not just projected ones.
- **Packaging.** A simpler distribution path (e.g. a one-command installer or a packaged executable) so non-technical users don't need to set up Python/git themselves.
- **Plugin-style tax rules.** If the number of states/years grows a lot, consider whether `tax_rules/` needs a more formal schema/loader instead of ad hoc per-year modules.

If you want to work on something not listed here, open an issue first to talk through the approach, especially for anything touching the tax engines, since correctness there is the whole point of the app.
