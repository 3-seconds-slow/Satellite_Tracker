from datetime import datetime, timedelta
import pytz, logging
from dash import Input, Output, State, html, ctx, no_update, dcc
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from skyfield.api import wgs84, load
import pandas as pd
from Models.Database import get_satellite_lookup
from Visualisations import Map_Component, Globe_Component


ts = load.timescale()
ephemeris_path = "assets/de421.bsp"

logger = logging.getLogger(__name__)
logging.basicConfig(filename="log.txt", format='%(asctime)s - %(levelname)s:%(message)s', level=logging.ERROR)

def register_details_modal_callbacks(app):
    """
    registers details modal callbacks
    :param app: the dash instance these callback will run in
    """

    @app.callback(
        Output("satellite-details-modal", "is_open"),
        Output("selected-sat-id", "data"),
        Output("details-title", "children"),
        Output("satellite-details-body", "children"),
        Output("details-lat-input", "value"),
        Output("details-lon-input", "value"),
        Output("details-auto-calc", "data"),
        Output("details-globe-graph", "figure"),
        Output("details-map-graph", "figure"),
        Input("table_listener", "event"),
        State("satellite-table", "derived_virtual_data"),
        State("satellite-table", "active_cell"),
        State("observer-lat", "value"),
        State("observer-lon", "value"),
        State("satellite-details-modal", "is_open"),
    )
    def show_satellite_details(event, table_data, active_cell, lat_from_main_screen, lon_from_main_screen, is_open):
        """
        When the details modal is opened, this function builds the details display and the visualisations. It also gets
        any latitude and longitude values from the inputs on the home screen to calculate visibility.

        :param event: the output of the event listener for detecting a double click in the table. this signal triggers
        the modal opening
        :param table_data: the data from the home screen satellite table
        :param active_cell: the currently selected cell of the table
        :param lat_from_main_screen: the latitude value from the input on the home screen
        :param lon_from_main_screen: the longitude value from the input on the home screen
        :return:
        """
        # print(f"double click detected at: {event}")
        if not event:
            raise PreventUpdate

        if not active_cell or not table_data:
            raise PreventUpdate


        row_index = active_cell.get("row")
        if row_index is None or row_index < 0 or row_index >= len(table_data):
            raise PreventUpdate

        selected_sat = table_data[row_index]

        # print(f"index: {row_index}, satellite: {selected_sat}")

        lookup = get_satellite_lookup()
        sat_obj = lookup[selected_sat["OBJECT_ID"]]
        logger.info(f"opening details for {sat_obj}")
        logger.info("building charts")
        map_chart = Map_Component.create_map_chart()
        map_chart = Map_Component.update_selected_marker(map_chart, selected_sat)
        globe_chart = Globe_Component.create_globe_chart()
        globe_chart = Globe_Component.update_selected_marker(globe_chart, selected_sat)

        auto_calc = lat_from_main_screen is not None and lon_from_main_screen is not None
        # print(f"auto_calc = {auto_calc}")

        details = build_satellite_details_layout(sat_obj)

        return (True,
                selected_sat["OBJECT_ID"],
                sat_obj.name,
                details,
                lat_from_main_screen,
                lon_from_main_screen,
                auto_calc,
                globe_chart,
                map_chart)


    # --- Close modal ---
    @app.callback(
        Output("satellite-details-modal", "is_open", allow_duplicate=True),
        Input("close-details-modal", "n_clicks"),
        prevent_initial_call=True
    )
    def close_details(n_close_clicks):
        """
        Closes the details modal
        :param n_close_clicks: n_click property of the close modal button
        """
        logger.info("closing details")
        return False

    @app.callback(
        Output("details-visible-result", "children"),
        [Input("details-calc-btn", "n_clicks"),  # manual trigger
        Input("satellite-details-modal", "is_open"),],
        [State("details-lat-input", "value"),
        State("details-lon-input", "value"),
        State("selected-sat-id", "data")],
        prevent_initial_call=True
    )
    def calculate_visibility(n_clicks, is_open, lat, lon, sat_id):
        """
        Calculates whether a selected satellite is visible from a user defined location.

        :param n_clicks: property used to detect the calculate position button has been clicked
        :param is_open: bool indicating if the modal is open or closed
        :param lat: the value from the latitude input. Should be an int or float
        :param lon: the value from the longitude input. Should be an int or float
        :param sat_id: the id number of the selected satellite
        :return: an HTML component that displays the visibility of the selected satellite
        """
        if not ctx.triggered_id:
            raise PreventUpdate

        if ctx.triggered_id == "satellite-details-modal" and not is_open:
            raise PreventUpdate

        if lat is None or lon is None:
            return html.Span("Enter coordinates", style={"color": "#aaa"})

        if not sat_id:
            return html.Span("No satellite selected", style={"color": "orange"})

        logger.info("calculating visibility")
        lookup = get_satellite_lookup()
        sat_obj = lookup[sat_id]
        observer = wgs84.latlon(lat, lon)
        t = ts.now()
        topocentric = (sat_obj - observer).at(t)
        alt, az, dist = topocentric.altaz()

        if alt.degrees > 0:
            return html.Span("Visible")
        else:
            return html.Span("Not Visible")

    @app.callback(
        Output("visibility-pass-list", "children"),
        Output("event-store", "data"),
        Input("predict-days-slider", "value"),
        State("selected-sat-id", "data"),
        State("details-lat-input", "value"),
        State("details-lon-input", "value"),
    )
    def update_event_list(days, sat_id, lat, lon):
        if not sat_id:
            return no_update

        logger.info("building event list")
        lookup = get_satellite_lookup()
        sat = lookup[sat_id]
        eph = load(ephemeris_path)

        t0 = ts.now()
        t1 = ts.utc((t0.utc_datetime() + timedelta(days=days)))

        if lat is None or lon is None:
            return html.Span("Enter coordinates", style={"color": "#aaa"})

        observer = wgs84.latlon(lat, lon)

        logger.info("calculating event times")
        times, events = sat.find_events(observer, t0, t1, altitude_degrees=0)
        event_names = 'rise above 0°', 'culminate', 'set below 0°'
        sunlit = sat.at(times).is_sunlit(eph)

        rows = []
        logger.info("populating table")
        for t, event, sunlit_flag in zip(times, events, sunlit):
            name = event_names[event]
            # state = ('in shadow', 'in sunlight')[sunlit_flag]

            rows.append({
                "Time (UTC)": t.utc_strftime("%Y-%m-%d %H:%M:%S"),
                "Event": name,
                "Sunlit": "Yes" if sunlit_flag else "No"
            })

        df = pd.DataFrame(rows)
        csv_string = df.to_csv(index=False)
        logger.info("returning events")
        if df.empty:
            return html.Div("No events in this period.", style={"color": "#aaa"}), None

        table = dbc.Table.from_dataframe(df, striped=True, bordered=False, hover=True, size="sm")
        export_btn = dbc.Button(
            "Export to CSV",
            id="export-events-btn",
            color="primary",
            className="mt-3 w-100"
        )
        return html.Div([table, export_btn]), csv_string

    @app.callback(
        Output("events-export", "data"),
        Input("export-events-btn", "n_clicks"),
        State("event-store", "data"),
        prevent_initial_call=True,
    )
    def export_events(n, csv_string):
        if not csv_string:
            return None


        return csv_string


    @app.callback(
        Output("predicted-position", "children"),
        Output("details-globe-graph", "figure", allow_duplicate=True),
        Output("details-map-graph", "figure", allow_duplicate=True),
        Output("prediction-datetime", "data"),
        Input("predict-btn", "n_clicks"),
        State("predict-date", "date"),
        State("predict-time", "value"),
        State("predict-timezone", "value"),
        State("selected-sat-id", "data"),
        State("details-globe-graph", "figure"),
        State("details-map-graph", "figure"),
        prevent_initial_call=True
    )
    def predict_future_position(n_clicks, date_str, time_str, timezone, sat_id, globe_fig, map_fig):
        """
        Calculates the position the selected satellite will be at user entered time in the future.

        The predicted latitude, longitude and altitude will be displayed within the details modal, and a new marker
        will be added to the  map and globe components.

        :param n_clicks: property used to detect the prediction button hs been clicked
        :param date_str: a sting representing a date from the date picker component
        :param time_str: a string representing the time entered into the time input
        :param timezone: the vale from the timezone dropdown
        :param sat_id: the id number of the selected satellite
        :param globe_fig: the 3d globe visualisation component
        :param map_fig: the 2d map visualisation component
        :return: an HTML component that displays the predicted position of the selected satellite, the map component,
        the globe component, and a datetime object containing the date and time entered by the user
        """
        # print("callback triggered")
        if not n_clicks or not date_str or not time_str or not sat_id:
            raise PreventUpdate

        dt_str = f"{date_str}T{time_str}:00Z"
        dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
        # print(dt)
        dt = pytz.timezone(timezone).localize(dt)
        # print(dt)
        t = ts.utc(dt)

        logger.info(f"calculating position of sat (id: {sat_id} at {dt}")
        lookup = get_satellite_lookup()
        sat = lookup.get(sat_id)
        if not sat:
            return html.Span("Satellite not found.", style={"color": "orange"}), globe_fig, map_fig

        geocentric = sat.at(t)
        x, y, z = geocentric.xyz.km
        subpoint = wgs84.subpoint(geocentric)

        lat = subpoint.latitude.degrees
        lon = subpoint.longitude.degrees
        alt = subpoint.elevation.km
        # print(f"new position: {lat}, {lon}, {alt}")

        result_text = html.Div([
            html.H5("Predicted Position:"),
            dbc.Row([
                dbc.Col(build_field("Latitude (°)", lat), width=3),
                dbc.Col(build_field("Longitude (°)", lon), width=3),
                dbc.Col(build_field("Altitude (km)", alt), width=3),
            ]),
            dbc.Row([
                dbc.Col(build_field("X", x), width=3),
                dbc.Col(build_field("Y", y), width=3),
                dbc.Col(build_field("Z", z), width=3)
            ])

        ])

        logger.info("updating charts")
        globe_fig = Globe_Component.update_prediction_marker(globe_fig, sat_id, dt)
        map_fig = Map_Component.update_prediction_marker(map_fig, sat_id, dt)

        return result_text, globe_fig, map_fig, dt


    @app.callback(
        Output("details-globe-graph", "figure", allow_duplicate=True),
        Output("details-map-graph", "figure", allow_duplicate=True),
        Input("path-switch", "on"),
        State("details-globe-graph", "figure"),
        State("details-map-graph", "figure"),
        State("selected-sat-id", "data"),
        State("prediction-datetime", "data"),
        prevent_initial_call=True
    )
    def show_path(path_switch, globe_fig, map_fig, sat_id, prediction_datetime):
        """
        When the show path toggle is clicked, this function will calculate the satellites predicted position for every
        minute between now and the datetime entered by the user and add them to a list. A marker will be placed on the
        globe and map for every position in the list, plotting the satellite's path.

        :param path_switch: the value of the display path the toggle switch
        :param globe_fig: the 3d globe visualisation component
        :param map_fig: the 2d map visualisation component
        :param sat_id: the id number of the selected satellite
        :param prediction_datetime: the datetime entered by the user
        :return: the map component and the globe component
        """
        if path_switch:
            logger.info("showing path")
            if not prediction_datetime:
                prediction_datetime = datetime.now().astimezone()

            dt = datetime.strptime(prediction_datetime, "%Y-%m-%dT%H:%M:%S%z")
            minutes_diff = (dt - datetime.now().astimezone()).total_seconds() / 60.0

            if minutes_diff < 1:
                minutes_diff = 1

            globe_fig = Globe_Component.show_path(globe_fig, sat_id, minutes_diff)
            map_fig = Map_Component.show_path(map_fig, sat_id, minutes_diff)
        else:
            logger.info("hide path")
            globe_fig = Globe_Component.clear_path(globe_fig)
            map_fig = Map_Component.clear_path(map_fig)

        return globe_fig, map_fig


    def build_satellite_details_layout(sat_obj):
        """
        Builds an HTML component which displays the details of the selected satellite, including calculating its current
        position.

        :param sat_obj: the selected EarthSatellite object
        :return: an HTML component
        """
        logger.info("building details fields")
        t = ts.now()
        geocentric = sat_obj.at(t)
        x, y, z = geocentric.xyz.km
        subpoint = wgs84.subpoint(geocentric)

        lat = round(subpoint.latitude.degrees, 3)
        lon = round(subpoint.longitude.degrees, 3)
        alt = round(subpoint.elevation.km, 2)

        return html.Div(
            style={
                "padding": "15px",
                "color": "white",
                "backgroundColor": "#111",
                "borderRadius": "8px",
            },
            children=[
                dbc.Row([
                    build_field("NORAD catalog number", sat_obj.model.satnum),
                    build_field("Epoch datetime(UTC)", sat_obj.epoch.utc_datetime()),
                ], justify="center"),
                dbc.Row([
                    dbc.Col([
                        build_field("Classification", sat_obj.model.classification),
                    ], xs=6, sm=3, md=2, lg=1),
                    dbc.Col([
                        build_field("International Designator", sat_obj.model.intldesg),
                    ], xs=6, sm=3, md=2, lg=1),
                    dbc.Col([
                        build_field("Epoch", f"{sat_obj.model.epochyr}{sat_obj.model.epochdays}"),
                    ], xs=8, sm=4, md=3, lg=2),
                    dbc.Col([
                        build_field("1st Derivative of Mean Motion (rev/day)", sat_obj.model.ndot),
                    ], xs=8, sm=4, md=3, lg=2),
                    dbc.Col([
                        build_field("2nd Derivative of Mean Motion (rev^3/day)", sat_obj.model.nddot),
                    ], xs=8, sm=4, md=3, lg=2),
                    dbc.Col([
                        build_field("Ballistic Drag Coefficient", sat_obj.model.bstar),
                    ], xs=8, sm=4, md=3, lg=2),
                    dbc.Col([
                        build_field("Ephemiris Type", sat_obj.model.ephtype),
                    ], xs=6, sm=3, md=2, lg=1),
                    dbc.Col([
                        build_field("Element Set Number", sat_obj.model.elnum),
                    ], xs=6, sm=3, md=2, lg=1),
                ], justify="center"),
                dbc.Row([
                    dbc.Col([
                        build_field("Inclination (°)", sat_obj.model.inclo),
                    ], xs=8, sm=4, md=3, lg=2),
                    dbc.Col([
                        build_field("RAAN (°)", sat_obj.model.nodeo),
                    ], xs=6, sm=3, md=2, lg=1),
                    dbc.Col([
                        build_field("Eccentricity", sat_obj.model.ecco),
                    ], xs=6, sm=3, md=2, lg=1),
                    dbc.Col([
                        build_field("Argument of Perigee (°)", sat_obj.model.argpo),
                    ], xs=8, sm=4, md=3, lg=2),
                    dbc.Col([
                        build_field("Mean Anomaly (°)", sat_obj.model.mo),
                    ], xs=8, sm=4, md=3, lg=2),
                    dbc.Col([
                        build_field("Mean Motion (°/minute)", sat_obj.model.no_kozai),
                    ], xs=8, sm=4, md=3, lg=2),
                    dbc.Col([
                        build_field("Revolutions at Epoch", sat_obj.model.revnum),
                    ], xs=6, sm=3, md=2, lg=1),
                ], justify="center"),

                html.Hr(style={"margin": "20px 0", "borderColor": "#333"}),

                # Computed info (lat/lon/alt/visibility)
                html.Div([
                    html.H5("Current Position", style={"color": "#2a9df4"}),
                    dbc.Row([
                        dbc.Col(build_field("Latitude (°)", lat), width=3),
                        dbc.Col(build_field("Longitude (°)", lon), width=3),
                        dbc.Col(build_field("Altitude (km)", alt), width=3),
                    ]),
                    dbc.Row([
                        dbc.Col(build_field("X", x), width=3),
                        dbc.Col(build_field("Y", y), width=3),
                        dbc.Col(build_field("Z", z), width=3)
                    ])
                ], style={"textAlign": "center"}),
            ]
        )

    def build_field(label, value):
        """
        Builds and populates a field for the satellite details display component

        :param label: the name of the field being built
        :param value: the value of the field
        :return: an HTML component
        """
        return html.Div(
            style={"marginBottom": "12px", "textAlign": "center"},
            children=[
                html.Div(str(value) if value is not None else "-", style={
                    "fontSize": "16px",
                    "fontWeight": "600",
                    "color": "#e8e8e8",
                    "marginBottom": "4px"
                }),
                html.Div(label, style={
                    "fontSize": "12px",
                    "color": "#aaaaaa",
                    "textTransform": "uppercase"
                })
            ]
        )


    '''
        The clientside_callback is used to execute a javascript function in the user's browser. In this case, the browser is 
        the PyWebview that the dash app is running in, and the function passes the contents of the file to be saved to the
        save_file api located in the main file.  
        '''
    app.clientside_callback(
        """
        function(content) {
            if (!content) return;
            
            filename = "events.csv"
            filetypes = ("CSV Files (#.csv)", "Text Files (*.txt)")
            window.pywebview.api.save_file(content, filename, filetypes);
            return null;
        }
        """,
        Output("events-export", "clear"),
        Input("events-export", "data")
    )

