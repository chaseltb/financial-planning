# Personal & Business Financial Planner

A local, private tool for tracking your personal finances and a small business side by side. It estimates federal and state taxes (just for North Carolina for now), projects cash flow, tracks net worth, and lets you compare "what if" scenarios. Everything runs on your own machine. This app allows you to compare your finances to different circumstances, such as the median income, the average income for a Software Engineer, etc. THis is not financial advice.

## What you need first

- Python 3.11 or newer installed on your machine
- Git installed on your machine
- A terminal (Command Prompt, PowerShell, or similar)

## Clone the repository

   ```
   git clone https://github.com/chaseltb/financial-planning.git
   cd financial-planning
   ```

## Setting up

1. (Optional but recommended) Create a virtual environment so this project's packages stay separate from everything else on your machine:

   ```
   python -m venv venv
   ```

   Then activate it:

   - Windows: `venv\Scripts\activate`
   - Mac or Linux: `source venv/bin/activate`

2. Install the required packages:

   ```
   pip install -r requirements.txt
   ```

## Running the app

From the project's root folder, run:

```
python run.py
```

Then open your browser to:

```
http://127.0.0.1:8050
```


## Using the application

- **Start on the Personal and Business pages.** To start the net worth calculations, fill in your income, expenses, assets, debts, and business numbers. The app comes with example default values (based on North Carolina median figures) so you can see how it works before you enter your own.
- **Check the Taxes page** if a number looks off. Every tax estimation has an explanation panel showing the formula and inputs behind it. If you notice an issue, feel free to fix it and create a PR.
- **Turn on Autosave** (on by default) if you want every edit written to disk right away. You can turn it off in Settings and use the "Save Now" button instead if you'd rather control exactly when your data is saved.
- **Watch the save status indicator** near the top of the screen. It shows a green check when your changes are saved, and a warning if a save fails.
- **Use Scenarios to experiment.** Anything you want to test (a raise, a new hire, a new business, a different tax year) can live in its own scenario so your baseline numbers stay untouched.
- **Export a backup** from Settings before making big changes, so you always have a copy of your data you can restore from.


## How the app is organized

The sidebar has one page per topic:

- **Overview**: A dashboard of your key numbers at a glance (taxes, net worth, business value, cash available).
- **Personal**: Your income, living expenses, assets, and debts, plus retirement contribution fields.
- **Business**: Your business type, revenue, expenses, and owner salary settings.
- **Taxes**: A detailed breakdown of how your federal and NC tax estimates are calculated.
- **Net Worth**: Your assets minus your debts, tracked and projected over time.
- **Valuation**: Estimates of what your business is worth, using a few different methods.
- **Forecast**: An editable spreadsheet projecting your business forward, quarter by quarter.
- **Scenarios**: Save alternate versions of your plan (for example, "what if I get a raise" or "what if I start a business") without losing your baseline numbers.
- **Settings**: Tax year, state, theme, autosave, and backup import/export.


## About your data

All of your financial information is stored in plain JSON and CSV files inside `planner/data/`. Nothing leaves your computer. This folder is intentionally left out of version control (see `.gitignore`), so your personal numbers are never accidentally shared or uploaded. On first run, any missing file is created from the sample starter data in `planner/seed_data/` (median NC figures and example scenarios); your own edits are never overwritten. The median values for comparison are all from the same year and are estimates. 


## Known limitations

The estimates are deliberately simplified. Things the app does **not** model:

- Itemized deductions, credits (child tax credit, etc.), AMT, and NC-specific adjustments to federal AGI.
- The QBI deduction treats the business as a non-specialized-service trade; above the income threshold it is limited by 50% of business W-2 wages, with no property (UBIA) test and no SSTB phase-out to zero.
- Retirement deductions are capped at IRS limits, but income-based phase-outs (e.g. traditional IRA when covered by a workplace plan) are only flagged in the tax tips.
- Net operating loss carryforwards, S-Corp shareholder basis limits, and passive-loss rules.
- Employer 401(k) matching in the net worth projection.

## Development

```
pip install -r requirements-dev.txt
ruff check planner
python -m pytest planner/tests
```

CI (GitHub Actions) runs the same two commands on every push and pull request.
