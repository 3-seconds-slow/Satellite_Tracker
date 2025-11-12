import dash_bootstrap_components as dbc
from dash import html, dcc
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename="log.txt", format='%(asctime)s - %(levelname)s:%(message)s', level=logging.INFO)

def create_export_modal():
    logger.info("Building Export Modal layout")
    return dbc.Modal(
        id="export-modal",
        is_open=False,
        size="md",
        children=[
            dbc.ModalHeader(dbc.ModalTitle("Export Satellite Data")),

            dbc.ModalBody([
                html.P("Choose which satellites to export:", style={"marginBottom": "10px"}),

                dcc.RadioItems(
                    id="export-choice",
                    options=[
                        {"label": "Entire Database", "value": "all"},
                        {"label": "Currently Filtered List", "value": "filtered"},
                    ],
                    value="filtered",
                    style={"marginBottom": "15px"}
                ),

                dcc.Download(id="export-download"),
            ]),

            dbc.ModalFooter([
                dbc.Button("Cancel", id="close-export-modal", color="secondary", className="me-2"),
                dbc.Button("Export", id="confirm-export", color="primary")
            ])
        ],
    )
