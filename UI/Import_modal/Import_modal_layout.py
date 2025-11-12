import dash_bootstrap_components as dbc
from dash import html, dcc
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename="log.txt", format='%(asctime)s - %(levelname)s:%(message)s', level=logging.INFO)

def create_import_modal():
    """
    Describes the layout of the import file modal
    """
    logger.info("building import modal layout")
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

                html.Progress(id="import-progress-bar", value="0", style={"visibility": "hidden", "justify": "center"}),
                dbc.Alert(id="import-status-text", color="info", is_open=False),

                dbc.Button("Cancel", id="cancel-import-btn", className="w-100 mb-3"),
            ]),
            dbc.ModalFooter([
                dbc.Button("Close", id="close-import-modal", color="secondary")
            ])
        ]
    )
