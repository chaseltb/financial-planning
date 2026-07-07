import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/settings", title="Settings & Backup")

def layout():
    return dbc.Container(
        [
            dbc.Row(
                [
                    # Rule Settings
                    dbc.Col(
                        html.Div(
                            [
                                html.H4("Tax Rules & Display Defaults", className="mb-4"),
                                html.Div(
                                    [
                                        html.Label("Filing/Planning Tax Year"),
                                        dcc.Dropdown(
                                            id="settings-tax-year",
                                            options=[{"label": "2026 Rules", "value": 2026}],
                                            value=2026,
                                            clearable=False,
                                            className="mb-3",
                                            style={"color": "#0f172a"}
                                        ),
                                        
                                        html.Label("Planning State"),
                                        dcc.Dropdown(
                                            id="settings-state",
                                            options=[{"label": "North Carolina (NC)", "value": "NC"}],
                                            value="NC",
                                            clearable=False,
                                            className="mb-3",
                                            style={"color": "#0f172a"}
                                        ),
                                        
                                        html.Label("Theme Selection"),
                                        dcc.Dropdown(
                                            id="settings-theme",
                                            options=[
                                                {"label": "Dark Mode (Slate)", "value": "dark"},
                                                {"label": "Light Mode (Flatly)", "value": "light"}
                                            ],
                                            value="dark",
                                            clearable=False,
                                            className="mb-3",
                                            style={"color": "#0f172a"}
                                        ),
                                        
                                        dbc.Checklist(
                                            options=[
                                                {"label": "Enable Autosave", "value": "autosave"}
                                            ],
                                            value=["autosave"],
                                            id="settings-autosave-toggle",
                                            switch=True,
                                            className="mb-3"
                                        )
                                    ]
                                )
                            ],
                            className="glass-card mb-4"
                        ),
                        lg=4
                    ),
                    
                    # Backups, Imports, Exports
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H4("Export Model Configuration", className="mb-3"),
                                    html.P(
                                        "Download your entire profile, business settings, assets, liabilities, and quarterly forecast as a backup JSON file or an Excel workbook.",
                                        className="text-muted",
                                        style={"fontSize": "0.9rem"}
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button("Download Full JSON Backup", id="settings-export-json-btn", color="primary", className="me-2 mb-2"),
                                            dbc.Button("Download Excel Sheet", id="settings-export-excel-btn", color="success", className="me-2 mb-2"),
                                            dcc.Download(id="settings-download-component")
                                        ],
                                        className="d-flex flex-wrap"
                                    )
                                ],
                                className="glass-card mb-4"
                            ),
                            
                            html.Div(
                                [
                                    html.H4("Import Backup Data", className="mb-3"),
                                    html.P(
                                        "Drag and drop a previously exported JSON backup file here to restore your planning workspace.",
                                        className="text-muted",
                                        style={"fontSize": "0.9rem"}
                                    ),
                                    dcc.Upload(
                                        id="settings-import-upload",
                                        children=html.Div(
                                            [
                                                "Drag and Drop or ",
                                                html.A("Select Files", style={"color": "var(--accent-blue)"})
                                            ]
                                        ),
                                        style={
                                            "width": "100%",
                                            "height": "100px",
                                            "lineHeight": "100px",
                                            "borderWidth": "2px",
                                            "borderStyle": "dashed",
                                            "borderRadius": "12px",
                                            "textAlign": "center",
                                            "borderColor": "var(--border-glass)",
                                            "backgroundColor": "rgba(0,0,0,0.15)",
                                            "cursor": "pointer"
                                        },
                                        multiple=False
                                    ),
                                    html.Div(id="settings-import-status", className="mt-3", style={"fontSize": "0.9rem"})
                                ],
                                className="glass-card mb-4"
                            )
                        ],
                        lg=8
                    )
                ]
            )
        ],
        fluid=True
    )
