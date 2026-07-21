# Personal & Business Financial Planner

A local, private tool for tracking your personal finances and a small business side by side. It estimates federal and state taxes (just for North Carolina for now), projects cash flow, tracks net worth, and lets you compare "what if" scenarios. Everything runs on your own machine. This app allows you to compare your finances to different circumstances, such as the median income, the average income for a Software Engineer, etc. THis is not financial advice.

## What you need first

- Python 3.11 or newer installed on your machine
- Git installed on your machine
- A terminal (Command Prompt, PowerShell, or similar)

## Getting the code (git clone)

1. Open a terminal.
2. Go to the folder where you want the project to live.
3. Run:

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

From the project's root folder (the one with `run.py` in it), run:

```
python run.py
```

Then open your browser to:

```
http://127.0.0.1:8050
```

To stop the app, go back to the terminal and press `Ctrl+C`.

## How the app is organized

The sidebar has one page per topic:

- **Overview**: A dashboard of your key numbers at a glance (taxes, net worth, business value, cash available).
- **Personal**: Your income, living expenses, assets, and debts, plus retirement contribution fields.
- **Business**: Your business type, revenue, expenses, and owner salary settings.
- **Taxes**: A detailed breakdown of how your federal and NC tax estimates are calculated.
- **Net Worth**: Your assets minus your debts, tracked and projected over time.
- **Valuation**: Estimates of what your business is worth, using a few different methods.
- **Forecast**: An editable spreadsheet projecting your business forward, quarter by quarter.
- **Scenarios**: Save alternate versions of your plan (for example, "what if I hire someone") without losing your baseline numbers.
- **Settings**: Tax year, state, theme, autosave, and backup import/export.

## Using it correctly

- **Start on the Personal and Business pages.** Fill in your income, expenses, assets, debts, and business numbers. The app ships with example default values (based on North Carolina median figures) so you can see how it works before you enter your own.
- **Check the Taxes page** if a number looks off. Every tax estimation has an explanation panel showing the formula and inputs behind it.
- **Turn on Autosave** (on by default) if you want every edit written to disk right away. You can turn it off in Settings and use the "Save Now" button instead if you'd rather control exactly when your data is saved.
- **Watch the save status indicator** near the top of the screen. It shows a green check when your changes are saved, and a warning if a save fails.
- **Use Scenarios to experiment.** Anything you want to test (a raise, a new hire, a different tax year) can live in its own scenario so your baseline numbers stay untouched.
- **Export a backup** from Settings before making big changes, so you always have a copy of your data you can restore from.

## About your data

All of your financial information is stored in plain JSON and CSV files inside `planner/data/`. Nothing leaves your computer. This folder is intentionally left out of version control (see `.gitignore`), so your personal numbers are never accidentally shared or uploaded.
