from datetime import datetime
import pytz
from dash import Input, Output, State, html, dcc, ctx
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from skyfield.api import wgs84, load
from Models.Database import get_satellite_lookup
from Visualisations import Map_Component, Globe_Component

ts = load.timescale()

def register_details_modal_callbacks(app):
    """Attach all callbacks related to the details modal."""

    @app.callback(
        Output("satellite-details-modal", "is_open"),
        Output("selected-sat-id", "data"),
        Output("details-title", "children"),
        Output("satellite-details-body", "children"),
        Output("details-lat-input", "value"),
        Output("details-lon-input", "value"),
        Output("details-auto-calc", "data"),
        Output("details-globe-container", "children"),
        Output("details-map-container", "children"),
        Input("table_listener", "event"),
        State("satellite-table", "derived_virtual_data"),
        State("satellite-table", "active_cell"),
        State("observer-lat", "value"),
        State("observer-lon", "value"),
        State("satellite-details-modal", "is_open"),
    )
    def show_satellite_details(event, table_data, active_cell, lat_from_main_screen, lon_from_main_screen, is_open):
        print(f"double click detected at: {event}")
        if not event:
            raise PreventUpdate

        if not active_cell or not table_data:
            raise PreventUpdate

        row_index = active_cell.get("row")
        if row_index is None or row_index < 0 or row_index >= len(table_data):
            raise PreventUpdate

        selected_sat = table_data[row_index]

        print(f"index: {row_index}, satellite: {selected_sat}")


    # --- Open modal and populate details ---
        lookup = get_satellite_lookup()
        sat_obj = lookup[selected_sat["OBJECT_ID"]]
        t = ts.now()
        geocentric = sat_obj.at(t)
        subpoint = wgs84.subpoint(geocentric)

        lat = round(subpoint.latitude.degrees, 3)
        lon = round(subpoint.longitude.degrees, 3)
        alt = round(subpoint.elevation.km, 2)

        # Compute visibility from a fixed location (e.g. Sydney)
        # observer = wgs84.latlon(-33.8688, 151.2093)
        # difference = sat_obj - observer
        # topocentric = difference.at(t)
        # altitude, azimuth, distance = topocentric.altaz()
        # visibility = "Visible" if altitude.degrees > 0 else "Below Horizon"

        # Generate charts
        map_chart = Map_Component.create_map_chart([selected_sat], selected_sat)
        globe_chart = Globe_Component.create_globe_chart([selected_sat], selected_sat)

        computed = {
            "lat": lat,
            "lon": lon,
            "alt": alt,
            "map_chart": map_chart,
            "globe_chart": globe_chart
        }

        auto_calc = lat_from_main_screen is not None and lon_from_main_screen is not None
        print(f"auto_calc = {auto_calc}")

        details = build_satellite_details_layout(
            sat_obj,
            computed,
        )

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
    def close_details(_):
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
        from skyfield.api import wgs84, load
        ts = load.timescale()

        # Only trigger when modal opens or user clicks "Calculate"
        if not ctx.triggered_id:
            raise PreventUpdate

        # Don’t run on modal close
        if ctx.triggered_id == "satellite-details-modal" and not is_open:
            raise PreventUpdate

        # Validate input
        if lat is None or lon is None:
            return html.Span("Enter coordinates", style={"color": "#aaa"})

        if not sat_id:
            return html.Span("No satellite selected", style={"color": "orange"})

        lookup = get_satellite_lookup()
        sat_obj = lookup[sat_id]
        # Compute visibility
        observer = wgs84.latlon(lat, lon)
        t = ts.now()
        topocentric = (sat_obj - observer).at(t)
        alt, az, dist = topocentric.altaz()

        if alt.degrees > 0:
            return html.Span("Visible")
        else:
            return html.Span("Not Visible")


    @app.callback(
        Output("predicted-position", "children"),
        Output("globe-graph", "figure", allow_duplicate=True),
        Output("map-graph", "figure", allow_duplicate=True),
        Output("prediction-datetime", "data"),
        Input("predict-btn", "n_clicks"),
        State("predict-date", "date"),
        State("predict-time", "value"),
        State("predict-timezone", "value"),
        State("selected-sat-id", "data"),
        State("globe-graph", "figure"),
        State("map-graph", "figure"),
        prevent_initial_call=True
    )
    def predict_future_position(n_clicks, date_str, time_str, timezone, sat_id, globe_fig, map_fig):
        print("callback triggered")
        if not n_clicks or not date_str or not time_str or not sat_id:
            raise PreventUpdate

        # try:
        # --- Combine date and time into datetime ---
        dt_str = f"{date_str}T{time_str}:00Z"
        dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
        print(dt)
        dt = pytz.timezone(timezone).localize(dt)
        print(dt)

        # --- Skyfield time conversion ---
        t = ts.utc(dt)

        # --- Lookup satellite ---
        lookup = get_satellite_lookup()
        sat = lookup.get(sat_id)
        if not sat:
            return html.Span("Satellite not found.", style={"color": "orange"}), globe_fig, map_fig

        # --- Compute predicted position ---
        geocentric = sat.at(t)
        subpoint = wgs84.subpoint(geocentric)

        lat = subpoint.latitude.degrees
        lon = subpoint.longitude.degrees
        alt = subpoint.elevation.km
        print(f"new position: {lat}, {lon}, {alt}")

        # --- Build result text ---
        result_text = html.Div([
            html.H6("Predicted Position:"),
            html.P([
                f"Latitude: {lat:.3f}°",
                html.Br(),
                f"Longitude: {lon:.3f}°",
                html.Br(),
                f"Altitude: {alt:.1f} km"
            ])
        ])

        # --- Update the charts (optional marker) ---
        globe_fig = Globe_Component.update_prediction_marker(globe_fig, sat_id, dt)
        map_fig = Map_Component.update_prediction_marker(map_fig, sat_id, dt)
        # if globe_fig:
        #     globe_fig["data"][2]["x"] = [geocentric.position.km[0]]
        #     globe_fig["data"][2]["y"] = [geocentric.position.km[1]]
        #     globe_fig["data"][2]["z"] = [geocentric.position.km[2]]
        #     globe_fig["data"][2]["text"] = [f"Predicted @ {dt_str}"]
        #
        # if map_fig:
        #     map_fig["data"][2]["lat"] = [lat]
        #     map_fig["data"][2]["lon"] = [lon]
        #     map_fig["data"][2]["text"] = [f"Predicted @ {dt_str}"]

        return result_text, globe_fig, map_fig, dt

        # except Exception as e:
        #     return html.Span(f"Error: {e}", style={"color": "red"}), globe_fig, map_fig

    @app.callback(
        Output("globe-graph", "figure", allow_duplicate=True),
        Output("map-graph", "figure", allow_duplicate=True),
        Input("path-switch", "on"),
        State("globe-graph", "figure"),
        State("map-graph", "figure"),
        State("selected-sat-id", "data"),
        State("prediction-datetime", "data"),
        prevent_initial_call=True
    )
    def show_path(path_switch, globe_fig, map_fig, sat_id, prediction_datetime):
        if path_switch:
            if not prediction_datetime:
                prediction_datetime = datetime.now().astimezone()

            dt = datetime.strptime(prediction_datetime, "%Y-%m-%dT%H:%M:%S%z")
            minutes_diff = (dt - datetime.now().astimezone()).total_seconds() / 60.0

            if minutes_diff < 1:
                minutes_diff = 1

            globe_fig = Globe_Component.show_path(globe_fig, sat_id, minutes_diff)
            map_fig = Map_Component.show_path(map_fig, sat_id, minutes_diff)
        else:
            print("hide path")
            globe_fig = Globe_Component.clear_path(globe_fig)
            map_fig = Map_Component.clear_path(map_fig)

        return globe_fig, map_fig


    def build_satellite_details_layout(sat_obj, computed, auto_calc=False):
        """Return a clean TLE-style layout for satellite details."""
        return html.Div(
            style={
                "padding": "15px",
                "color": "white",
                "backgroundColor": "#111",
                "borderRadius": "8px",
            },
            children=[
                # html.H3(
                #     f"Satellite Details {sat_obj.name}",
                #     style={
                #         "textAlign": "center",
                #         "marginBottom": "20px",
                #         "fontWeight": "bold",
                #         "color": "#2a9df4"
                #     }
                # ),

                dbc.Row([
                    build_field("NORAD catalog number", sat_obj.model.satnum),
                ], justify="center"),
                dbc.Row([
                    dbc.Col([
                        build_field("Classification", sat_obj.model.classification),
                    ], width=1),
                    dbc.Col([
                        build_field("International Designator", sat_obj.model.intldesg),
                    ], width=1),
                    dbc.Col([
                        build_field("Epoch", f"{sat_obj.model.epochyr}{sat_obj.model.epochdays}"),
                    ], width=2),
                    dbc.Col([
                        build_field("1st Derivative of Mean Motion (rev/day)", sat_obj.model.ndot),
                    ], width=2),
                    dbc.Col([
                        build_field("2nd Derivative of Mean Motion (rev^3/day)", sat_obj.model.nddot),
                    ], width=2),
                    dbc.Col([
                        build_field("Ballistic Drag Coefficient", sat_obj.model.bstar),
                    ], width=2),
                    dbc.Col([
                        build_field("Ephemiris Type", sat_obj.model.ephtype),
                    ], width=1),
                    dbc.Col([
                        build_field("Element Set Number", sat_obj.model.elnum),
                    ], width=1),
                ], justify="center"),
                dbc.Row([
                    dbc.Col([
                        build_field("Inclination (°)", sat_obj.model.inclo),
                    ], width=2),
                    dbc.Col([
                        build_field("RAAN (°)", sat_obj.model.nodeo),
                    ], width=2),
                    dbc.Col([
                        build_field("Eccentricity", sat_obj.model.ecco),
                    ], width=1),
                    dbc.Col([
                        build_field("Argument of Perigee (°)", sat_obj.model.argpo),
                    ], width=2),
                    dbc.Col([
                        build_field("Mean Anomaly (°)", sat_obj.model.mo),
                    ], width=2),
                    dbc.Col([
                        build_field("Mean Motion (°/minute)", sat_obj.model.no_kozai),
                    ], width=2),
                    dbc.Col([
                        build_field("Revolutions at Epoch", sat_obj.model.revnum),
                    ], width=1),
                ], justify="center"),

                html.Hr(style={"margin": "20px 0", "borderColor": "#333"}),

                # Computed info (lat/lon/alt/visibility)
                html.Div([
                    html.H5("Current Position", style={"color": "#2a9df4"}),
                    dbc.Row([
                        dbc.Col(build_field("Latitude (°)", computed["lat"]), width=3),
                        dbc.Col(build_field("Longitude (°)", computed["lon"]), width=3),
                        dbc.Col(build_field("Altitude (km)", computed["alt"]), width=3),
                    ])
                ], style={"textAlign": "center"}),
            ]
        )

    def build_field(label, value):
        """Reusable helper for value-over-label display."""
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

