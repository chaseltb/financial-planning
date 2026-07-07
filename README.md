MVP Specification
NC Personal & Business Financial Planning Platform (Dash)

Version: MVP v1.0
Target User: Single user (me)
Platform: Local Python application (Plotly Dash)
Storage: JSON/CSV only (no database)
Primary Goal: Accurate financial modeling for North Carolina personal and small business planning with transparent calculations and scenario analysis.

1. Product Vision

Create a desktop-style financial planning application that combines:

Personal finances
Business finances
Tax planning
Business valuation
Net worth tracking
Cash flow forecasting
Scenario analysis

Unlike a budgeting app, this application is a financial modeling tool where every assumption is editable and every calculation is traceable.

2. Core Principles
Transparency

Every calculated value must be explainable.

Every output should have an "Explain" panel showing:

Inputs
Formula
Assumptions
Tax rules used
Accuracy

Tax calculations should use:

Current Federal tax rules
Current North Carolina tax rules
Actual IRS thresholds
Actual NC Department of Revenue rules
Real depreciation schedules where implemented

The engine should be data-driven so annual updates require updating tax rule files rather than calculation logic.

Local First

Everything runs locally.

No cloud.

No login.

No accounts.

Scenario Driven

Nothing is permanent until saved.

Every edit can become a scenario.

Simple Storage

All information lives in JSON or CSV.

Example:

planner/

data/

profile.json

business.json

assets.csv

liabilities.csv

income.csv

expenses.csv

forecast.csv

tax_rules/

2026/

federal.json

north_carolina.json

scenarios/
3. Tech Stack

Python 3.12+

Plotly Dash

Dash Bootstrap Components

Pandas

NumPy

Pydantic

Plotly Graph Objects

OpenPyXL (Excel import/export)

PyYAML (configuration)

4. Project Structure
planner/

app.py

config.py

assets/

pages/

overview.py

personal.py

business.py

taxes.py

valuation.py

forecast.py

scenarios.py

settings.py

engines/

tax/

federal.py

north_carolina.py

payroll.py

depreciation.py

valuation.py

forecast.py

networth.py

scenario.py

cashflow.py

models/

person.py

business.py

income.py

expense.py

asset.py

liability.py

scenario.py

tax.py

components/

cards.py

charts.py

editable_table.py

sidebar.py

header.py

summary.py

data/

profile.json

business.json

income.csv

expenses.csv

forecast.csv

assumptions.json

tax_rules/

2026/

federal.json

north_carolina.json

tests/
5. Application Pages
Overview

Purpose

Financial dashboard.

Widgets

Estimated Personal Tax

Estimated Business Tax

Combined Tax

Net Worth

Business Value

Cash Available

Effective Tax Rate

Charts

Net Worth History

Revenue Trend

Profit Trend

Quarterly Taxes

Cash Flow

Personal

Sections

Income

W-2

1099

Business distributions

Interest

Dividends

Capital gains

Rental income

Other

Retirement

401(k)

Solo 401(k)

SEP IRA

Traditional IRA

Roth IRA

HSA

Assets

Cash

Brokerage

Retirement

Real estate

Vehicles

Business ownership

Crypto

Other

Liabilities

Mortgage

Auto loans

Credit cards

Student loans

Business loans

Outputs

Estimated federal tax

Estimated NC tax

Effective tax rate

Net worth

Asset allocation

Business

Business Information

Entity type

Sole Proprietorship
Single-member LLC
Multi-member LLC
S Corporation
C Corporation

Business Metrics

Revenue

COGS

Gross Profit

Operating Expenses

Payroll

Contractors

Marketing

Rent

Insurance

Software

Travel

Meals

Utilities

Professional Services

Equipment

CapEx

Outputs

EBITDA

Net Income

Operating Margin

Estimated Taxes

Quarterly Cash Flow

Taxes

Purpose

Explain taxes.

Sections

Federal

NC

Payroll

Self-employment

Estimated payments

Taxable income

Tax brackets

Credits

Deductions

Explanation panel

Every line item shows:

Formula

Source

Assumption

Reference tax rule

Net Worth

Assets

Cash

Brokerage

Retirement

Real estate

Business

Vehicles

Crypto

Liabilities

Mortgage

Loans

Credit cards

Charts

Net worth over time

Asset allocation

Debt allocation

Waterfall changes

Valuation

Methods

Revenue Multiple

EBITDA Multiple

Net Income

Seller's Discretionary Earnings (SDE)

Free Cash Flow

Custom Formula

Inputs

Current metric

Custom multiplier

Forecast quarter

Sensitivity range

Outputs

Business Value

Sensitivity graph

Historical valuation

Forecast valuation

Forecast

Editable spreadsheet.

Columns

Quarter

Revenue

COGS

Payroll

Expenses

Capital expenditures

Owner salary

Distributions

Tax estimate

Cash

EBITDA

Business value

Charts

Revenue

Profit

Cash

Taxes

Business Value

Forecast horizon

4 quarters

8 quarters

12 quarters

20 quarters

Scenario Manager

Scenario List

Baseline

Current

Scenario A

Scenario B

Scenario C

Actions

Create

Duplicate

Rename

Delete

Compare

Comparison

Metric	Baseline	Scenario
Tax		
Profit		
Cash		
Value		
Net Worth		
Settings

Tax year

State

Business defaults

Theme

Currency

Autosave

Import

Export

6. Calculation Engines
Tax Engine

Inputs

Income

Business income

Capital gains

Retirement

Deductions

Business deductions

Outputs

Federal tax

NC tax

Payroll tax

Self-employment tax

Effective rate

Marginal rate

Taxable income

Net Worth Engine

Calculates

Assets

Liabilities

Net worth

Allocation

Growth

Valuation Engine

Methods

Revenue

EBITDA

SDE

Net Income

FCF

Custom

Returns

Business Value

Sensitivity

Historical trend

Forecast

Forecast Engine

Uses

Historical quarters

Growth assumptions

Expense assumptions

Hiring assumptions

Returns

Quarterly projections

Cash

Tax

Business value

Scenario Engine

Stores only changes.

Example

{
  "name": "Hire Engineer",
  "changes": {
    "payroll": 120000,
    "marketing": 15000
  }
}

Everything else comes from Baseline.

7. Tax Rule System

Rules stored separately.

tax_rules/

2026/

federal.json

north_carolina.json

social_security.json

depreciation.json

Example

{
  "tax_year": 2026,
  "standard_deduction": {
    "single": 16000,
    "married": 32000
  },
  "brackets": [
    ...
  ]
}

Engine reads these dynamically.

8. Charts

Overview

Revenue

Expenses

Profit

Cash Flow

Taxes

Net Worth

Business Value

Asset Allocation

Debt Allocation

Tax Breakdown

Forecast

Scenario Comparison

Sensitivity Analysis

9. Import / Export

Import

CSV

Excel

JSON

Export

CSV

Excel

JSON

PDF report (future enhancement)

10. Browser State

Store in dcc.Store

Current page

Selected scenario

Filters

Theme

Unsaved edits

Everything else saved to JSON.

11. Performance Goals

Startup < 2 seconds

Recalculation < 200 ms

Forecast update < 100 ms

Scenario switch < 100 ms

Support 20+ years of quarterly history without noticeable lag.

12. Testing

Unit tests for every calculation engine.

Golden test cases using known IRS and NC examples.

Regression tests to ensure tax calculations don't change unexpectedly.

Validation tests for every import file.

13. Future Enhancements (Out of Scope for MVP)
Quarterly estimated tax payment planner
Roth conversion optimizer
Capital gains harvesting
Monte Carlo forecasting
Retirement withdrawal simulation
Loan amortization modeling
Real estate portfolio analysis
AI-powered "what changed?" summaries
Automatic updates to tax rule data
Direct imports from QuickBooks, Xero, or brokerage exports
14. Definition of Done

The MVP is complete when a user can:

Create a personal and business financial profile.
Enter historical and projected quarterly financial data.
Estimate federal and North Carolina personal and business tax liabilities for a selected tax year using transparent, data-driven rules.
Track personal net worth over time.
Estimate business value using multiple valuation methodologies and customizable assumptions.
Create, save, compare, and delete planning scenarios without duplicating underlying data.
View interactive charts that update immediately as assumptions change.
Import and export all financial data as JSON and CSV.
Run entirely offline from a local Python environment with no database, user accounts, or cloud dependencies.
Key Non-Functional Requirement

The codebase should prioritize correctness, maintainability, and transparency over feature count. All financial logic should be isolated from the Dash UI, tax rules should be externalized into versioned data files, and every calculated value should be traceable back to its inputs and governing assumptions. This creates a foundation that can be confidently extended as tax laws change or additional planning modules are added.