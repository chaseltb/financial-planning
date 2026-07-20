"""Collapsible "where these numbers come from" panel.

Used on pages whose default data models a real-world median rather than a
blank slate (Personal), so the source of each figure is visible in the UI
instead of only living in a commit message or a data file's description.
"""
from dash import html, dcc
import dash_bootstrap_components as dbc

# (label, value shown, source, year)
NC_MEDIAN_SOURCES = [
    ("Individual income (NC)", "$38,657/yr",  "U.S. Census Bureau, American Community Survey", "2024"),
    ("Gross rent (NC)",         "$1,200/mo",   "U.S. Census Bureau, American Community Survey", "2023"),
    ("Transportation costs (NC)", "$831/mo",   "NC Dept. of Commerce / BLS Consumer Expenditure data", "2024"),
    ("Median 401(k) balance",  "$38,176",      "Industry retirement-plan data (Fidelity/Empower)", "2024"),
    ("Typical 401(k) contribution rate", "~7% of salary", "Fidelity", "2024"),
    ("Average auto loan balance", "$24,297",   "Experian State of the Automotive Finance Market", "2024"),
    ("Average credit card balance", "$6,730",  "Experian State of Credit Cards", "2024"),
    ("Junior Software Engineer salary (national)", "$82,506/yr", "Salary.com", "2025"),
    ("Senior Software Engineer salary (national)", "$125,720/yr", "Salary.com", "2025"),
]

# Figures with no single authoritative source — flagged separately so they
# aren't presented with the same certainty as the cited ones above.
ESTIMATED_ITEMS = [
    "Utilities and healthcare costs (reasonable estimates, not from a single dataset)",
    "IRA contribution amount (a modest, round-number assumption)",
    "The $10k/yr side-hustle business numbers, in the \"NC Median + $10k Side Hustle\" scenario "
    "(a scenario assumption, not Census or industry data)",
]


def render_citation_panel(panel_id: str = "nc-median-citations"):
    return html.Div(
        [
            dbc.Button(
                [html.I(className="bi bi-info-circle me-2"), "Where do these default numbers come from?"],
                id=f"{panel_id}-toggle",
                color="link",
                size="sm",
                className="p-0 mb-2 text-muted",
                style={"fontSize": "0.85rem", "textDecoration": "none"},
            ),
            dbc.Collapse(
                html.Div(
                    [
                        html.P(
                            "This project ships with several starter scenarios instead of a blank $0 "
                            "template: the Baseline models North Carolina's median personal income, and "
                            "the scenario dropdown at the top of the page has variations (adding a side "
                            "hustle, or swapping in a national software engineer salary). The numbers "
                            "below are their sources. Replace any of them with your own on the Personal "
                            "and Business pages.",
                            className="text-muted mb-3",
                            style={"fontSize": "0.82rem"},
                        ),
                        dbc.Table(
                            [
                                html.Thead(html.Tr([
                                    html.Th("Figure"), html.Th("Default used"), html.Th("Source"), html.Th("Year"),
                                ])),
                                html.Tbody([
                                    html.Tr([
                                        html.Td(label), html.Td(value), html.Td(source), html.Td(year),
                                    ])
                                    for label, value, source, year in NC_MEDIAN_SOURCES
                                ]),
                            ],
                            bordered=False, striped=True, hover=False, size="sm",
                            className="mb-3", style={"fontSize": "0.8rem"},
                        ),
                        html.P("A few numbers aren't from a single cited source:", className="text-muted mb-1", style={"fontSize": "0.8rem", "fontWeight": "600"}),
                        html.Ul(
                            [html.Li(item, style={"fontSize": "0.8rem"}) for item in ESTIMATED_ITEMS],
                            className="text-muted mb-0",
                        ),
                    ],
                    className="glass-card p-3 mb-3",
                ),
                id=f"{panel_id}-collapse",
                is_open=False,
            ),
        ]
    )
