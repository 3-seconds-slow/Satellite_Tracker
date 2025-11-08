import dash_bootstrap_components as dbc
from dash import html, dcc
import dash_daq as daq
import pytz

def create_details_modal():
    """
    Creates the layout for the details modal
    :return: HTML describing the details modal
    """
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

                # ✅ The dynamic satellite details insert goes here
                html.Div(id="satellite-details-body"),

                html.Hr(),

                # ✅ Visibility calculation UI (always present)
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
                            dbc.Select(
                                id="predict-timezone",
                                options=[{"label": tz, "value": tz} for tz in pytz.common_timezones],
                                value="UTC",
                                style={"width": "100%"}
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

                dcc.Tabs([
                    dcc.Tab(
                        label="Globe",
                        children=[html.Div(id="details-globe-container")],
                        className="chart-tab",
                        selected_className="chart-tab--selected"
                    ),
                    dcc.Tab(
                        label="Map",
                        children=[html.Div(id="details-map-container")],
                        className="chart-tab",
                        selected_className="chart-tab--selected"
                    ),
                ]),
            ]),
            dbc.ModalFooter([
                dbc.Button("Close", id="close-details-modal", color="secondary")
            ]),
        ],
    )
