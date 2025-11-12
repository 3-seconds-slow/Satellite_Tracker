from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from dash_extensions import EventListener
from UI.Satellite_list_callbacks import satellites_to_table_data
from UI.Download_modal.Download_modal_layout import create_download_modal
from UI.Details_modal.Details_modal_layout import create_details_modal
from UI.Import_modal.Import_modal_layout import create_import_modal
from UI.Export_modal.Export_modal_layout import create_export_modal
from UI.Delete_modal.Delete_modal_layout import create_delete_modal
from Visualisations.Map_Component import create_map_chart
from Visualisations.Globe_Component import create_globe_chart
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename="log.txt", format='%(asctime)s - %(levelname)s:%(message)s', level=logging.INFO)

def create_home_screen(satellites):
    """
    creates home page of the app.

    main components are a dash_table for displaying satellites stored in the database, a globe component showing the
    position of each satellite in 3d, and a map component showing the position of each satellite on a 2d map

    :param satellites: a list of EarthSatellite objects loaded from the database
    :return: the html describing the appearance of the program's home screen
    """

    logging.info("populating table")
    data = satellites_to_table_data(satellites)
    logger.info("generating charts")
    globe = create_globe_chart()
    map = create_map_chart()
    logging.info("building home screen layout")
    return html.Div([
        dcc.Store(id="db-refresh-signal", data=0),
        dcc.Store(id="selected-sat-id", data=None),
        dcc.Store(id="export-data"),
        dcc.Store(id="last-clicked-row", data={"index": None, "timestamp": 0}),
        dcc.Store(id="open-details-trigger", data=0),

        dbc.Row([
            dbc.Col([
                html.H1("Satellite Tracker", style={"textAlign": "center"}),
                html.Div(
                    className="d-flex gap-2 align-items-end mb-3",
                    children=[
                    html.Button(
                        "Clear Selected",
                        id="clear-selection-btn",
                        className="btn btn-secondary"),
                    # html.Button(
                    #     "Update Records",
                    #     id="update-records-btn",
                    #     className="btn btn-secondary"),
                    dbc.Button(
                        "Delete all Satellites",
                        id="open-delete-modal",
                        className="btn btn-secondary",
                    ),
                    create_delete_modal()
                ]),

                dcc.Loading(
                    id="table-loading",
                    type="circle",
                    color="#0d6efd",
                    children=[
                        # this eventListener is designed to detect when a cell in the table has been double-clicked so
                        # the details modal can be opened
                        EventListener(
                            id="table_listener",
                            events=[{"event": "dblclick", "props": ["target.textContent", "target.parentElement.rowIndex"]}],
                            logging=True,
                            children = dash_table.DataTable(
                                id="satellite-table",
                                columns=[{"name": "ID", "id": "OBJECT_ID"},
                                         {"name": "Name", "id": "OBJECT_NAME"},
                                         {"name": "Latitude", "id": "LAT"},
                                         {"name": "Longitude", "id": "LON"},
                                         {"name": "Altitude", "id": "ALT"},
                                         {"name": "epoch", "id": "EPOCH"},
                                         ],
                                data=data,
                                filter_action="native",
                                sort_action="native",
                                page_action="native",
                                page_size=20,
                                cell_selectable=True,
                                active_cell=None,
                                style_table={"overflowX": "auto", "borderRadius": "8px"},
                                style_header={
                                    "backgroundColor": "#1f2630",
                                    "fontWeight": "bold",
                                    "color": "white",
                                    "border": "1px solid #444",
                                },
                                style_cell={
                                    "backgroundColor": "#111111",
                                    "color": "#dddddd",
                                    "border": "1px solid #333",
                                    "textAlign": "center",
                                    "padding": "6px",
                                    "fontFamily": "Segoe UI, sans-serif",
                                    "fontSize": "14px",
                                },
                                style_data_conditional=[
                                    {
                                        "if": {"filter_query": "{STALE} = 'true'"},
                                        "backgroundColor": "#7c0000",
                                        "color": "white",
                                        "border": "1px solid #aa0000"
                                    },
                                    {
                                        "if": {"state": "active"},
                                        "backgroundColor": "#2a9df4",
                                        "color": "white",
                                        "border": "1px solid #2a9df4",
                                    },
                                    {
                                        "if": {"state": "selected"},
                                        "backgroundColor": "#2a9df4",
                                        "color": "white",
                                    }
                                ],
                            ),
                        ),
                        create_details_modal(),

                    ],
                ),
            ], width=6, style={"paddingRight": "10px"}),
            dbc.Col([
                html.Div(
                    className="d-flex gap-2 align-items-end mb-3",
                    children=[
                        dbc.Button("Download New Data", id="open-download-modal", color="success", className="mt-2"),
                        dbc.Button("Import From File", id="open-import-modal", color="success", className="mt-2"),
                        dbc.Button("Export Data", id="open-export-modal", color="success", className="mt-2"),
                        create_download_modal(),
                        create_import_modal(),
                        create_export_modal(),
                    ]),
                html.Div(
                    className="d-flex gap-2 align-items-end mb-3",
                    children=[
                        html.Div([
                            dbc.Label("Latitude:"),
                            dbc.Input(
                                id="observer-lat",
                                type="number",
                                placeholder="e.g. -33.87",
                                debounce=True,
                                step=0.001,
                                style={"width": "120px"},
                            ),
                        ]),
                        html.Div([
                            dbc.Label("Longitude:"),
                            dbc.Input(
                                id="observer-lon",
                                type="number",
                                placeholder="e.g. 151.20",
                                debounce=True,
                                step=0.001,
                                style={"width": "120px"},
                            ),
                        ]),
                        html.Button(
                            "Filter Visible Satellites",
                            id="filter-visible-btn",
                            n_clicks=0,
                            className="btn btn-primary"
                        ),
                        html.Button(
                            "Show All",
                            id="reset-filter-btn",
                            className="btn btn-secondary")
                    ]
                ),
                html.Div([
                    dcc.Tabs(
                        id="chart-tabs",
                        value="globe-tab",
                        children=[
                            dcc.Tab(
                                label="Globe",
                                value="globe-tab",
                                children=[
                                    dcc.Loading(
                                        type="circle",
                                        children=dcc.Graph(
                                            id="globe-graph",
                                            figure=globe,
                                            config={"displayModeBar": True, "scrollZoom": True},
                                            style={"height": "600px"}
                                        )
                                    ),],
                                className="chart-tab",
                                selected_className="chart-tab--selected"
                            ),
                            dcc.Tab(
                                label="Map",
                                value="map-tab",
                                children=[
                                    dcc.Loading(
                                        type="circle",
                                        children=dcc.Graph(
                                            id="map-graph",
                                            figure=map,
                                            config={"displayModeBar": True, "scrollZoom": True},
                                            style={"height": "600px"}
                                        )
                                    ),],
                                className="chart-tab",
                                selected_className="chart-tab--selected"
                            ),
                        ],
                        style={"marginBottom": "10px"}
                    ),

                ])
            ], width=6, style={"paddingLeft": "10px"})
        ], className="gx-2 gy-3"),
    ]),







