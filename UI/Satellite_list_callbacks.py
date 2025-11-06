from dash import Input, Output, State, html, no_update, ctx
from skyfield.api import load, wgs84
from Models.Database import get_satellite_list
from Visualisations import Map_Component, Globe_Component

ts = load.timescale()

def register_home_screen_callbacks(app):
    """
    registers the callbacks used from the home screen

    :param app: the dash app where these callback will be run
    """
    @app.callback(
        Output("satellite-table", "data"),
        Input("db-refresh-signal", "data")
    )
    def refresh_table(_):
        """
        reloads the data table when a change in the database has be detected

        :param _: the data within the db-refresh-signal store, which is updated when the database changes
        :return: a list containing the data to be displayed within the table
        """
        # print("refreshing table")
        satellites = get_satellite_list()
        data = satellites_to_table_data(satellites)

        return data

    @app.callback(
        Output("chart-content", "children"),
        [
            Input("chart-tabs", "value"),
            Input("satellite-table", "data"),
            Input("satellite-table", "derived_virtual_data"),
            Input("satellite-table", "active_cell"),
            Input("db-refresh-signal", "data"),
        ],
        prevent_initial_call=False
    )
    def render_chart_content(selected_tab, table_data, filtered_data, active_cell, _):
        """


        """
        selected_sat = None
        filtered_data = filtered_data or table_data or []
        # print("building charts:")
        if active_cell and filtered_data:
            row_index = active_cell.get("row")
            if 0 <= row_index < len(filtered_data):
                selected_sat = filtered_data[row_index]

        if selected_tab == "map-tab":
            # print("Map")
            return Map_Component.create_map_chart(filtered_data, selected_sat)

        elif selected_tab == "globe-tab":
            # print("Globe")
            return Globe_Component.create_globe_chart(filtered_data, selected_sat)

        return html.Div("Select a tab.")

    @app.callback(
        Output("map-graph", "figure"),
        Output("globe-graph", "figure"),
        Input("update-interval", "n_intervals"),
        Input("satellite-table", "active_cell"),
        State("map-graph", "figure"),
        State("globe-graph", "figure"),
        State("satellite-table", "derived_virtual_data"),
        State("chart-tabs", "value"),
    )
    def update_satellite_positions(_, active_cell, map_fig, globe_fig, filtered_data, active_tab):
        """Update only the satellite marker coordinates."""
        selected_sat = None
        if active_cell:
            row_index = active_cell.get("row")
            if 0 <= row_index < len(filtered_data):
                selected_sat = filtered_data[row_index]

        if not filtered_data:
            return no_update, no_update

        if active_tab == "map-tab":
            chart_module = Map_Component
            fig = map_fig
        elif active_tab == "globe-tab":
            chart_module = Globe_Component
            fig = globe_fig
        else:
            return no_update, no_update

        fig["data"][1] = chart_module.update_markers(fig, filtered_data)


        if selected_sat:
            fig["data"][2] = None
            fig["data"][2] = chart_module.update_selected_marker(fig,selected_sat)

        if active_tab == "map-tab":
            return fig, no_update
        else:
            return no_update, fig


    @app.callback(
        Output("satellite-table", "data", allow_duplicate=True),
        [Input("filter-visible-btn", "n_clicks"),
         Input("reset-filter-btn", "n_clicks")],
        State("observer-lat", "value"),
        State("observer-lon", "value"),
        prevent_initial_call=True
    )
    def filter_visible_satellites(n_filter_clicks, n_reset_clicks, lat, lon):
        """Filter satellites visible from a given lat/lon."""

        print("filtering visible satellites")
        if not ctx.triggered or ctx.triggered_id == "reset-filter-btn":
            # no filter applied — show all
            print("No filter")
            satellites = get_satellite_list()
            data = satellites_to_table_data(satellites)
            return data

        observer = wgs84.latlon(lat, lon)
        satellites = get_satellite_list()
        visible_sats = []

        t = ts.now()
        for sat in satellites:
            topocentric = (sat - observer).at(t)
            alt, az, dist = topocentric.altaz()
            if alt.degrees > 0:  # above horizon
                visible_sats.append(sat)

        data = satellites_to_table_data(visible_sats)

        print(f"[Filter] {len(visible_sats)} visible out of {len(satellites)}")
        return data

    @app.callback(
        Output("satellite-table", "active_cell"),
        Input("clear-selection-btn", "n_clicks"),
    )
    def clear_selection(n_clicks):
        return None


def satellites_to_table_data(satellites):
    """Convert a list of EarthSatellite objects into a DataFrame."""
    rows = []
    t = ts.now()
    for sat in satellites:
        lat, lon, alt = calculate_position(sat, t)
        rows.append({
            "OBJECT_ID": sat.model.satnum,
            "OBJECT_NAME": sat.name,
            "LAT": lat,
            "LON": lon,
            "ALT": alt,
        })
    return rows

def calculate_position(sat, t = ts.now()):
    subpoint = wgs84.subpoint(sat.at(t))
    lat = round(subpoint.latitude.degrees, 3)
    lon = round(subpoint.longitude.degrees, 3)
    alt = round(subpoint.elevation.km, 2)
    return lat, lon, alt