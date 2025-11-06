import dash_bootstrap_components as dbc
from dash import html, dcc

def create_import_modal():
    return dbc.Modal(
        id="import-modal",
        is_open=False,
        size="lg",
        children=[
            dbc.ModalHeader(dbc.ModalTitle("Import TLE From File")),
            dbc.ModalBody([
                html.P("Upload a TLE file (.txt or .tle):"),

                dcc.Upload(
                    id="tle-upload",
                    children=html.Div([
                        "Drag and Drop or ",
                        html.A("Select a File", style={"color": "#2a9df4"})
                    ]),
                    style={
                        "width": "100%", "height": "80px", "lineHeight": "80px",
                        "borderWidth": "2px", "borderStyle": "dashed",
                        "borderRadius": "6px", "textAlign": "center"
                    },
                    accept=".txt,.tle",
                    multiple=False
                ),

                html.Div(id="import-status", className="mt-3", style={"color": "#ddd"}),
            ]),
            dbc.ModalFooter([
                dbc.Button("Close", id="close-import-modal", color="secondary")
            ])
        ]
    )
