"""Generates tailored, rule-based tax-strategy suggestions from the current
project state and the latest run_all_engines() result. These are educational
starting points for a conversation with a CPA, not filed tax advice — every
tip says so explicitly.
"""
from typing import Any, Dict, List

from planner.engines.tax.federal import calculate_bracket_tax

# Contribution limits by tax year. 2026 figures are IRS-announced amounts;
# treat them as best-known estimates, not authoritative for years not yet finalized.
_RETIREMENT_LIMITS = {
    2024: {"401k": 23000.0, "401k_catchup": 7500.0, "ira": 7000.0, "hsa_self": 4150.0, "hsa_family": 8300.0, "solo": 69000.0},
    2025: {"401k": 23500.0, "401k_catchup": 7500.0, "ira": 7000.0, "hsa_self": 4300.0, "hsa_family": 8550.0, "solo": 70000.0},
    2026: {"401k": 24500.0, "401k_catchup": 8000.0, "ira": 7500.0, "hsa_self": 4400.0, "hsa_family": 8750.0, "solo": 72000.0},
}
_DEFAULT_LIMITS = _RETIREMENT_LIMITS[2025]

# Traditional IRA deduction phase-out (MAGI) when the taxpayer IS covered by a
# workplace retirement plan. Approximate — actual phase-out also depends on
# whether a *spouse* is covered, which this app doesn't track separately.
_IRA_DEDUCTION_PHASEOUT = {
    2024: {"single": (77000.0, 87000.0), "married": (123000.0, 143000.0)},
    2025: {"single": (79000.0, 89000.0), "married": (126000.0, 146000.0)},
    2026: {"single": (81000.0, 91000.0), "married": (129000.0, 149000.0)},
}

# QBI phase-IN range where the wage/UBIA limitation and the SSTB (specified
# service trade or business — consulting, law, health, financial services,
# etc.) phase-out start to bite. This app doesn't model either limitation
# (see tips below), so the QBI deduction it shows can overstate the real one
# once taxable income clears the start of this range.
_QBI_PHASEIN = {
    2024: {"single": (191950.0, 241950.0), "married": (383900.0, 483900.0)},
    2025: {"single": (197300.0, 247300.0), "married": (394600.0, 494600.0)},
    2026: {"single": (201850.0, 251850.0), "married": (403550.0, 503550.0)},
}

_PASS_THROUGH_ENTITIES = ("Sole Proprietorship", "Single-member LLC", "Multi-member LLC")

_CAP_GAINS_0PCT_THRESHOLD_DEFAULT = {"single": 47025.0, "married": 94050.0}


def _combined_tax_savings(deduction_amount: float, taxable_ordinary: float, brackets: List[Dict[str, float]], nc_flat_rate: float) -> float:
    """Actual Federal + NC tax saved by reducing taxable ordinary income by
    `deduction_amount`, computed by re-running the real progressive bracket
    calculation rather than multiplying by a single flat marginal rate — a
    flat-rate estimate silently overstates savings whenever the deduction is
    large enough to cross down into a lower bracket."""
    if deduction_amount <= 0:
        return 0.0
    fed_before, _ = calculate_bracket_tax(taxable_ordinary, brackets)
    fed_after, _ = calculate_bracket_tax(max(0.0, taxable_ordinary - deduction_amount), brackets)
    fed_savings = fed_before - fed_after
    # NC is a flat rate, so its savings are linear regardless of bracket position.
    nc_savings = deduction_amount * nc_flat_rate
    return fed_savings + nc_savings


def generate_tax_tips(state: Dict[str, Any], r: Dict[str, Any]) -> List[Dict[str, str]]:
    """Returns a list of {"category", "title", "body"} tip dicts, most-impactful first."""
    tips: List[Dict[str, str]] = []

    profile = state.get("profile", {})
    business = state.get("business", {})
    income = state.get("income", [])
    liabilities = state.get("liabilities", [])

    fed = r["fed_tax"]
    nc = r["nc_tax"]
    filing = r.get("filing_status", "single")
    entity_type = r.get("entity_type", "Sole Proprietorship")
    tax_year = int(r.get("tax_year", 2025))
    limits = _RETIREMENT_LIMITS.get(tax_year, _DEFAULT_LIMITS)

    brackets = r.get("fed_rules", {}).get("brackets", {}).get(filing, [])
    taxable_income = fed.get("taxable_income", 0.0)
    # The ordinary-income slice of taxable income, net of any capital gains
    # already stacked on top of it — this is what actually runs through the
    # progressive brackets (see calculate_federal_tax's own taxable_ordinary).
    taxable_ordinary = fed.get("taxable_ordinary", taxable_income)
    existing_taxable_cap_gains = fed.get("taxable_cap_gains", 0.0)
    nc_flat_rate = nc.get("flat_rate", 0.0399)
    agi = fed.get("agi", 0.0)

    annual_net_biz_income = r.get("annual_net_biz_income", 0.0)
    has_w2 = any(i.get("category") == "W-2" and float(i.get("amount", 0.0)) > 0 for i in income) \
        or r.get("owner_w2_salary", 0.0) > 0

    # ── Retirement contribution headroom ────────────────────────────────────
    def _headroom_tip(field: str, label: str, limit: float, category: str = "Personal", note: str = "", extra: str = ""):
        current = float(profile.get(field, 0.0) or 0.0)
        headroom = limit - current
        if headroom <= 500:
            return
        est_savings = _combined_tax_savings(headroom, taxable_ordinary, brackets, nc_flat_rate)
        if est_savings <= 0:
            return
        tips.append({
            "category": category,
            "title": f"Room left in your {label} for {tax_year}",
            "body": (
                f"You're contributing ${current:,.0f} of the ${limit:,.0f} {tax_year} limit"
                f"{note}. Adding the remaining ${headroom:,.0f} would lower your taxable income "
                f"and could save roughly ${est_savings:,.0f} in Federal + NC tax this year."
                f"{extra}"
            ),
        })

    if has_w2:
        _headroom_tip("retirement_401k", "401(k)", limits["401k"], note=" (+ catch-up if you're 50+)")

    # IRA: flag the deduction phase-out instead of assuming full deductibility —
    # it only applies if you (or a spouse) are covered by a workplace plan, which
    # this app doesn't track, so this is a caveat, not a hard gate.
    phaseout_lo, phaseout_hi = _IRA_DEDUCTION_PHASEOUT.get(tax_year, _IRA_DEDUCTION_PHASEOUT[2025]).get(filing, (0.0, 0.0))
    ira_extra = ""
    if agi >= phaseout_hi:
        ira_extra = (
            f" Note: at your AGI, a traditional IRA contribution is likely NOT deductible if you (or a "
            f"spouse) are covered by a workplace retirement plan — a non-deductible traditional "
            f"contribution converted to Roth (\"backdoor Roth\") may be a better route in that case."
        )
    elif agi >= phaseout_lo:
        ira_extra = (
            f" Note: your AGI falls in the phase-out range (${phaseout_lo:,.0f}-${phaseout_hi:,.0f}) for "
            f"deducting this if you're covered by a workplace plan — only part of the contribution may "
            f"be deductible."
        )
    _headroom_tip("retirement_ira", "IRA", limits["ira"], extra=ira_extra)

    hsa_limit_label = "HSA (self-only coverage)"
    _headroom_tip(
        "retirement_hsa", hsa_limit_label, limits["hsa_self"], category="Personal",
        note=" for self-only HDHP coverage",
        extra=f" (Family HDHP coverage raises the limit to ${limits['hsa_family']:,.0f}.) Only "
              f"applies if you're actually enrolled in a qualifying high-deductible health plan.",
    )

    # For a Schedule-C-style pass-through, the contribution base is net self-employment
    # income; for an S-Corp it's the owner's W-2 wages, not the entity's net profit
    # (distributions aren't earned income for retirement-plan purposes).
    solo_contribution_base = (
        r.get("owner_w2_salary", 0.0) if entity_type == "S Corporation" else annual_net_biz_income
    )
    if entity_type in _PASS_THROUGH_ENTITIES + ("S Corporation",) and solo_contribution_base > 0:
        solo_limit = min(limits["solo"], max(0.0, solo_contribution_base) * 0.25)
        current_solo = float(profile.get("solo_401k", 0.0) or 0.0)
        headroom = solo_limit - current_solo
        if headroom > 500:
            est_savings = _combined_tax_savings(headroom, taxable_ordinary, brackets, nc_flat_rate)
            tips.append({
                "category": "Business",
                "title": "Self-employed retirement plan headroom",
                "body": (
                    f"Based on your {'W-2 wages from the business' if entity_type == 'S Corporation' else 'net self-employment income'}, "
                    f"a Solo 401(k) or SEP IRA could shelter up to ~${solo_limit:,.0f} this year "
                    f"(roughly 25% of that base, capped at ${limits['solo']:,.0f}); you're using "
                    f"${current_solo:,.0f}. A Solo 401(k) usually "
                    f"beats a SEP IRA at the same income because it also allows an employee-deferral "
                    f"portion on top of the profit-sharing amount. The unused ${headroom:,.0f} of "
                    f"headroom could save roughly ${est_savings:,.0f} in combined tax."
                ),
            })

    # ── S-Corp election for high SE tax ─────────────────────────────────────
    se_tax = fed.get("se_tax", 0.0)
    if entity_type in _PASS_THROUGH_ENTITIES and annual_net_biz_income > 40000 and se_tax > 0:
        # A more careful illustration than a flat percentage: the DISTRIBUTION
        # share pays $0 SE tax / FICA at all under an S-Corp (vs. the ~14.13%
        # effective SE-tax rate — 15.3% of the 92.35% SE-earnings base — it would
        # pay as 100% self-employment income), while the SALARY share still pays
        # FICA (employer + employee, ~15.3% combined) either way, so it isn't a
        # source of savings. Only the wage-base-independent portion below the SS
        # cap is modeled; this is still a rough illustration, not a filing figure.
        illustrative_salary_share = 0.5
        se_effective_rate = 0.153 * 0.9235
        illustrative_savings = annual_net_biz_income * se_effective_rate * (1 - illustrative_salary_share)
        tips.append({
            "category": "Business",
            "title": "Consider an S-Corp election to cut self-employment tax",
            "body": (
                f"As a {entity_type}, your entire ${annual_net_biz_income:,.0f} of net business income is "
                f"subject to 15.3% self-employment tax (${se_tax:,.0f} this year). Electing S-Corp tax "
                f"treatment lets you split profit into a \"reasonable\" W-2 salary (subject to FICA) and "
                f"distributions (not subject to SE tax or FICA at all). As a rough illustration, paying "
                f"about half your profit as salary and half as distributions could save on the order of "
                f"${illustrative_savings:,.0f} a year — offset by payroll setup/administration costs and "
                f"the extra corporate tax filing. This is usually worth it once net profit clears roughly "
                f"$40,000-$60,000/year. Get a CPA to set a defensible \"reasonable compensation\" figure "
                f"before electing — too low a salary is the most common way this strategy gets challenged."
            ),
        })

    # ── S-Corp reasonable-compensation compliance risk ──────────────────────
    owner_salary = float(business.get("owner_salary", 0.0) or 0.0)
    if entity_type in ("S Corporation", "C Corporation") and owner_salary <= 0 and annual_net_biz_income > 0:
        tips.append({
            "category": "Business",
            "title": "Set a reasonable W-2 salary for yourself",
            "body": (
                f"As a {entity_type} owner-employee actively working in the business, the IRS expects you "
                f"to pay yourself a \"reasonable\" W-2 salary before taking distributions — $0 salary with "
                f"active profit is a common audit trigger and can get distributions reclassified as wages "
                f"(with back payroll tax and penalties). Set a salary comparable to what you'd pay someone "
                f"else to do your job."
            ),
        })

    # ── C-Corp double taxation ───────────────────────────────────────────────
    if entity_type == "C Corporation":
        corp_tax = fed.get("corporate_tax", 0.0) + nc.get("corporate_tax", 0.0)
        tips.append({
            "category": "Business",
            "title": "C-Corp profit is taxed twice — confirm that's still the right structure",
            "body": (
                f"This year's structure pays ${corp_tax:,.0f} in corporate income tax before any "
                f"dividends reach you personally, which are then taxed again on your return. Unless "
                f"you have a specific reason to stay a C-Corp (raising outside investment, retaining "
                f"earnings for growth, Qualified Small Business Stock treatment), an S-Corp or LLC "
                f"pass-through structure usually results in less combined family tax for a closely-held "
                f"business. Also consider keeping profit below the salary+distribution level needed "
                f"personally, retaining the rest at the 21% corporate rate, if you're reinvesting heavily."
            ),
        })

    # ── NC Pass-Through Entity Tax (PTET) SALT-cap workaround ───────────────
    # Available to entities that file their own partnership/S-corp return — not
    # sole props or single-member LLCs, which are disregarded/Schedule C filers.
    if entity_type in ("S Corporation", "Multi-member LLC") and nc.get("value", 0.0) > 0:
        tips.append({
            "category": "Business",
            "title": "Look into North Carolina's Pass-Through Entity Tax election",
            "body": (
                "North Carolina lets S-Corps and multi-member LLCs elect to pay state income tax at the "
                "entity level (PTET) instead of passing it through to your personal return. Because the "
                "$10,000 federal cap on state-and-local-tax (SALT) deductions applies to individuals but "
                "not to a business's own tax payments, this can let you deduct the full NC tax as a "
                "business expense federally instead of losing part of it to the SALT cap. Worth a "
                "conversation with a CPA if you're already itemizing or close to the SALT cap."
            ),
        })

    # ── Quarterly estimated tax payments ─────────────────────────────────────
    # W-2 withholding generally covers the tax on wages automatically; the tax
    # attributable specifically to self-employment/business activity usually
    # isn't withheld by anyone and has to be paid quarterly (Form 1040-ES) to
    # avoid an IRS underpayment penalty.
    business_attributable_tax = r.get("business_attributable_tax", 0.0)
    if business_attributable_tax > 1000:
        quarterly_amount = business_attributable_tax / 4.0
        tips.append({
            "category": "Business",
            "title": "Pay quarterly estimated taxes to avoid an underpayment penalty",
            "body": (
                f"About ${business_attributable_tax:,.0f} of your total tax bill this year is caused by "
                f"your business activity — SE tax, corporate tax, and any tax on profit above what your "
                f"outside income alone would owe. Unlike W-2 withholding, nothing is automatically paid "
                f"in on this throughout the year, so the IRS (and NC DOR) expect quarterly estimated "
                f"payments (Form 1040-ES), roughly ${quarterly_amount:,.0f}/quarter, or you can owe an "
                f"underpayment penalty at filing time even though you'll eventually pay the right amount. "
                f"A common safe harbor: pay in at least 100% of last year's total tax liability (110% if "
                f"last year's AGI was over $150,000) spread across the four due dates."
            ),
        })

    # ── QBI phase-out / SSTB caution for higher incomes ─────────────────────
    qbi_deduction = fed.get("qbi_deduction", 0.0)
    phasein_lo, phasein_hi = _QBI_PHASEIN.get(tax_year, _QBI_PHASEIN[2025]).get(filing, (0.0, 0.0))
    if qbi_deduction > 0 and taxable_income > phasein_lo:
        tips.append({
            "category": "Business",
            "title": "Your QBI deduction may be smaller than shown at this income level",
            "body": (
                f"This app applies a straight 20% Qualified Business Income deduction, but real QBI rules "
                f"start limiting that at ${phasein_lo:,.0f} of taxable income for your filing status "
                f"(fully phased in by ${phasein_hi:,.0f}): a wage/UBIA-of-property limitation kicks in for "
                f"every pass-through business, and \"specified service\" businesses (consulting, law, "
                f"health, financial/investment services, and similar) can lose the deduction entirely "
                f"above that range. Your taxable income (${taxable_income:,.0f}) is in or above that "
                f"range, so get an accountant to check whether your real QBI deduction is smaller than "
                f"what's shown here."
            ),
        })

    # ── Home office deduction reminder ──────────────────────────────────────
    if entity_type in _PASS_THROUGH_ENTITIES and annual_net_biz_income > 0:
        tips.append({
            "category": "Business",
            "title": "Don't forget the home office deduction",
            "body": (
                "If you regularly use part of your home exclusively for this business, you can deduct a "
                "share of rent/mortgage interest, utilities, insurance, and depreciation (or use the "
                "simplified $5/sq ft method, capped at 300 sq ft = $1,500/year) — an easy deduction that's "
                "often skipped because it feels like it will trigger an audit. It won't, as long as the "
                "space is genuinely used regularly and exclusively for business."
            ),
        })

    # ── Equipment purchases: Section 179 / bonus depreciation ───────────────
    forecast = state.get("forecast", [])
    latest_capex = float(forecast[-1].get("Capital expenditures", 0.0) or 0.0) if forecast else 0.0
    if latest_capex > 0:
        tips.append({
            "category": "Business",
            "title": "Accelerate deductions on equipment purchases",
            "body": (
                f"You're running about ${latest_capex * 4:,.0f}/year in capital expenditures. Section 179 "
                f"expensing (and bonus depreciation) can let you deduct qualifying equipment purchases "
                f"in full in the year you buy them, rather than depreciating them over several years — "
                f"pulling that deduction forward into the highest-tax year makes sense if you expect this "
                f"year's marginal rate to be your highest for a while."
            ),
        })

    # ── Itemizing vs. the standard deduction ─────────────────────────────────
    # This app always models the standard deduction. Mortgage interest alone
    # getting close to it is a decent signal that itemizing (mortgage interest +
    # SALT up to $10k + charitable giving) might actually beat it.
    std_deduction = r.get("fed_rules", {}).get("standard_deduction", {}).get(filing, 0.0)
    est_mortgage_interest = sum(
        float(l.get("value", 0.0)) * float(l.get("interest_rate", 0.0))
        for l in liabilities if l.get("category") == "Mortgage"
    )
    if std_deduction > 0 and est_mortgage_interest > std_deduction * 0.6:
        tips.append({
            "category": "Personal",
            "title": "Check whether itemizing beats the standard deduction",
            "body": (
                f"This app always assumes the standard deduction (${std_deduction:,.0f} for your filing "
                f"status), but your estimated mortgage interest alone (~${est_mortgage_interest:,.0f}/year) "
                f"is already a big share of that. Add state/local taxes (capped at $10,000) and any "
                f"charitable giving, and itemizing could genuinely reduce your real tax bill below what "
                f"this app shows — worth running the numbers both ways."
            ),
        })

    # ── Capital gains: 0% bracket harvesting ────────────────────────────────
    cg_brackets = r.get("fed_rules", {}).get("capital_gains_brackets", {}).get(filing, {})
    threshold_0pct = cg_brackets.get("0pct_top", _CAP_GAINS_0PCT_THRESHOLD_DEFAULT.get(filing, 47025.0))
    # Gains already recognized this year already occupy part of the 0% bracket
    # (they stack on top of ordinary income), so they reduce remaining headroom too.
    stacked_top = taxable_ordinary + existing_taxable_cap_gains
    if 0 < stacked_top < threshold_0pct:
        headroom = threshold_0pct - stacked_top
        tips.append({
            "category": "Investing",
            "title": "You may have room in the 0% capital gains bracket",
            "body": (
                f"Between your taxable ordinary income (${taxable_ordinary:,.0f}) and any capital gains "
                f"already recognized (${existing_taxable_cap_gains:,.0f}), you have about ${headroom:,.0f} "
                f"of room left before long-term capital gains start being taxed at all this year (the 0% "
                f"bracket runs up to ${threshold_0pct:,.0f} of taxable income for your filing status). "
                f"Realizing gains up to that room — even just selling and immediately rebuying appreciated "
                f"long-term holdings to reset your cost basis higher — can be entirely tax-free."
            ),
        })

    # ── Capital loss harvesting ──────────────────────────────────────────────
    cap_gains_amount = sum(
        float(i.get("amount", 0.0)) for i in income if i.get("category") == "Capital gains"
    )
    if cap_gains_amount < 0:
        tips.append({
            "category": "Investing",
            "title": "Use this year's investment losses",
            "body": (
                f"You've logged a net capital loss of ${abs(cap_gains_amount):,.0f}. Up to $3,000/year of "
                f"net capital losses can offset ordinary income (the rest carries forward indefinitely to "
                f"future years) — make sure any realized losses are actually reported so you don't leave "
                f"that offset on the table. Watch the wash-sale rule if you plan to rebuy the same "
                f"security within 30 days."
            ),
        })

    return tips
