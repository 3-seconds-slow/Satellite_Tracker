import dash_bootstrap_components as dbc
from dash import html, dcc
import dash_daq as daq
import pytz, logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename="log.txt", format='%(asctime)s - %(levelname)s:%(message)s', level=logging.INFO)

def create_details_modal():
    """
    Creates the layout for the details modal
    :return: HTML describing the details modal
    """
    logger.info("building details modal layout")
    return dbc.Modal(
        id="satellite-details-modal",
        is_open=False,
        size="xl",
        fullscreen=True,
        children=[
            dcc.Store(id="details-auto-calc", data=False),
            dcc.Store(id="prediction-datetime", data=None),
            dbc.ModalHeader(dbc.ModalTitle(id="details-title")),
            dbc.ModalBody([

                html.Div(id="satellite-details-body"),

                html.Hr(),

                html.Div(
                    className="d-flex justify-content-center align-items-center gap-2 mb-3",
                    children=[
                        html.Span("Visible from:", style={"fontWeight": "600"}),
                        dbc.Input(id="details-lat-input", type="number", style={"width": "90px"}),
                        dbc.Input(id="details-lon-input", type="number", style={"width": "90px"}),
                        dbc.Button("Check", id="details-calc-btn", color="primary", size="sm"),
                        html.Div(id="details-visible-result", style={"marginLeft": "10px", "fontWeight": "bold"}),
                    ],
                ),
                dbc.Row([
                    dbc.Col([
                        html.Label("Predict Visibility for Next (Days):"),
                        dcc.Slider(
                            id="predict-days-slider",
                            min=1, max=14, value=1, step=1,
                            marks={i: f"{i}" for i in range(1, 15)},
                        ),
                    ], width=8),
                ]),

                html.Div(id="visibility-pass-list", style={"marginTop": "15px"}),
                dcc.Store(id="event-store"),
                dcc.Download(id="events-export"),
                dbc.Button(
                    "Export to CSV",
                    id="export-events-btn",
                    color="primary",
                    className="mt-3 w-100",
                    style={"visibility": "hidden"}
                ),

                html.Hr(),

                dbc.Row(
                    align="center",
                    className="g-2 mb-3",
                    children=[
                        dbc.Col(
                            html.Span("Position at:", style={"fontWeight": "600", "whiteSpace": "nowrap"}),
                            width="auto"
                        ),

                        dbc.Col(
                            dcc.DatePickerSingle(
                                id="predict-date",
                                display_format="YYYY-MM-DD",
                                style={"width": "100%"}
                            ),
                            width="auto"
                        ),

                        dbc.Col(
                            dbc.Input(
                                id="predict-time",
                                type="text",
                                placeholder="HH:MM",
                                style={"width": "100%"}
                            ),
                            width=2
                        ),

                        dbc.Col(
                            dcc.Dropdown(
                                id="predict-timezone",
                                options=[{"label": tz, "value": tz} for tz in pytz.common_timezones],
                                value="UTC",
                                clearable=False,
                                searchable=True,
                                placeholder="Timezone",
                                style={"minWidth": "160px"}
                            ),
                            width=3
                        ),

                        dbc.Col(
                            dbc.Button("Predict", id="predict-btn", color="primary"),
                            width="auto"
                        ),

                        dbc.Col(
                            daq.BooleanSwitch(
                                id="path-switch",
                                on=False,
                                label="Show satellite path",
                                labelPosition="bottom"
                            ),
                            width="auto",
                            style={"marginLeft": "15px"}
                        ),
                    ],
                ),
                html.Div(id="predicted-position", className="mt-3", style={"textAlign": "center"}),

                html.Hr(),

                dcc.Tabs(
                    id="details-chart-tabs",
                    value="globe-tab",
                    children=[
                        dcc.Tab(
                            label="Globe",
                            value="globe-tab",
                            children=[
                                dcc.Loading(
                                    type="circle",
                                    children=dcc.Graph(
                                        id="details-globe-graph",
                                        figure=None,
                                        config={"displayModeBar": True, "scrollZoom": True},
                                        style={"height": "600px"}
                                    )
                                ), ],
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
                                        id="details-map-graph",
                                        figure=None,
                                        config={"displayModeBar": True, "scrollZoom": True},
                                        style={"height": "600px"}
                                    )
                                ), ],
                            className="chart-tab",
                            selected_className="chart-tab--selected"
                        ),
                    ],
                    style={"marginBottom": "10px"}
                ),
            ]),
            dbc.ModalFooter([
                dbc.Button("Close", id="close-details-modal", color="secondary")
            ]),
        ],
    )
