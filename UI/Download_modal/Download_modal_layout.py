import dash_bootstrap_components as dbc
from dash import html
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename="log.txt", format='%(asctime)s - %(levelname)s:%(message)s', level=logging.INFO)

def create_download_modal():
    logger.info("building Download Modal layout")
    return dbc.Modal(
        id="download-modal",
        is_open=False,
        centered=True,
        children=[
            dbc.ModalHeader(dbc.ModalTitle("Download Satellite Data")),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col(dbc.Select(
                        id="search-field",
                        options=[{"label": "Catalog Number", "value": "CATNR"},
                                {"label": "International Designator", "value": "INTDES"},
                                {"label": "Group", "value": "GROUP"},
                                {"label": "Name", "value": "NAME"}],
                        value="CATNR",
                    ), width=6),
                    dbc.Col(dbc.Input(id="search-term", type="text", placeholder="Enter search term"), width=6),
                ], class_name="mb-3"),

                html.Progress(id="progress_bar", value="0", style={"visibility": "hidden", "justify": "center"}),
                dbc.Alert(id="download-status-text", color="info", is_open=False),

                dbc.Button("Download", id="download-btn", color="primary", className="w-100 mb-3"),
                dbc.Button("Cancel", id="cancel-btn", className="w-100 mb-3"),
            ]),
        ]
    )
