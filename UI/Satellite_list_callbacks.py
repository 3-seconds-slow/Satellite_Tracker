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

    """
    TODO: figure out why this callback is being triggered twice during startup. Suspect I don't the filtered data
    """
    @app.callback(
        Output("globe-container", "children"),
        Output("map-container", "children"),
        [
            Input("satellite-table", "data"),
            Input("satellite-table", "derived_virtual_data"),
            Input("satellite-table", "active_cell"),
        ],
        prevent_initial_call=False
    )
    def render_chart_content(table_data, filtered_data, active_cell):
        """
        Sends the table data to the map and globe components when the program opens so the carts can be built

        :param table_data: all the data contained in the unfiltered table
        :param filtered_data: the currently visible data from when the table is filtered
        :param active_cell: the currently selected cell of the table
        :return: two plotly graph objects, 3d globe and 2d map
        """
        selected_sat = None
        filtered_data = filtered_data or table_data or []
        # print("building charts:")
        if active_cell and filtered_data:
            row_index = active_cell.get("row")
            if 0 <= row_index < len(filtered_data):
                selected_sat = filtered_data[row_index]

        globe_chart = Globe_Component.create_globe_chart(filtered_data, selected_sat)
        map_chart = Map_Component.create_map_chart(filtered_data, selected_sat)

        return globe_chart, map_chart

    """
    TODO: Separate the regular marker and selected satellite marker updates into separate callbacks
    """
    @app.callback(
        Output("map-graph", "figure"),
        Output("globe-graph", "figure"),
        Input("satellite-table", "active_cell"),
        State("map-graph", "figure"),
        State("globe-graph", "figure"),
        State("satellite-table", "derived_virtual_data")
    )
    def update_satellite_positions(active_cell, map_fig, globe_fig, filtered_data):
        """
        Update the satellite markers on the charts whenever the table data is changed, either through database updates
        or the table being filtered

        If a satellite is selected from the table, tell the chart component to highlight it
        :param active_cell: the currently selected cell of the table
        :param map_fig: the 2d map component
        :param globe_fig: the 3d map component
        :param filtered_data: the currently visible data from when the table is filtered

        :return: the updated map and globe components
        """
        selected_sat = None
        if active_cell:
            row_index = active_cell.get("row")
            if 0 <= row_index < len(filtered_data):
                selected_sat = filtered_data[row_index]

        if not filtered_data:
            return no_update, no_update

        globe_fig = Globe_Component.update_markers(globe_fig, filtered_data)
        map_fig = Map_Component.update_markers(map_fig, filtered_data)

        if selected_sat:
            globe_fig["data"][2] = None
            globe_fig = Globe_Component.update_selected_marker(globe_fig,selected_sat)

            map_fig["data"][2] = None
            map_fig = Map_Component.update_selected_marker(map_fig, selected_sat)

        return map_fig, globe_fig

    """
    TODO: ensure latitude and longitude input only accept valid data
    """
    @app.callback(
        Output("satellite-table", "data", allow_duplicate=True),
        [Input("filter-visible-btn", "n_clicks"),
         Input("reset-filter-btn", "n_clicks")],
        State("observer-lat", "value"),
        State("observer-lon", "value"),
        prevent_initial_call=True
    )
    def filter_visible_satellites(n_filter_clicks, n_reset_clicks, lat, lon):
        """
        Takes the values of the latitude and longitude inputs and uses them to create a wsg84 object to simulate the
        observer's position. It then calculates the altitude, azimuth and distance relative to the observer's position
        for each satellite in the table. If the altitude angle for a satellite is greater than zero (i.e. is above the
        horizon), this satellite iss added to the list of visible satellites which is used to filter the data table

        Will also clear the visible satellite filter if it detects the clear filter button click

        :param n_filter_clicks: property used to detect the apply filter button has been clicked
        :param n_reset_clicks: property used to detect the reset filter button has been clicked
        :param lat: the value from the latitude input. Should be an int or float
        :param lon: the value from the longitude input. Should be an int or float
        :return: data: a list containing the information of each visible satellite
        """

        # print("filtering visible satellites")
        if not ctx.triggered or ctx.triggered_id == "reset-filter-btn":
            # print("No filter")
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
            if alt.degrees > 0:
                visible_sats.append(sat)

        data = satellites_to_table_data(visible_sats)

        # print(f"[Filter] {len(visible_sats)} visible out of {len(satellites)}")
        return data

    """
    TODO: this isn't working, fix this
    """
    @app.callback(
        Output("satellite-table", "active_cell"),
        Input("clear-selection-btn", "n_clicks"),
    )
    def clear_selection(n_clicks):
        """
        Clears the current satellite selection
        :param n_clicks: property used to detect the clear selection button has been clicked
        :return: None: sets the active cell property of the data table to None
        """
        return None


def satellites_to_table_data(satellites):
    """
    Takes a list of EarthSatellite objects and returns the data to populate the data table
    :param satellites: a list of EarthSatellite objects
    :return: a list of dicts containing the satellite's id, name, latitude, longitude, and altitude
    """
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
"""
TODO: use this in all th other places that perform this operation
"""
def calculate_position(sat, t = ts.now()):
    """
    Calculates the latitude, longitude and altitude of a EarthSatellite object

    :param sat: an EarthSatellite object
    :param t: a skyfield timescale object. default value is timescale.now()
    :return: lat: a float representing the latitude of the EarthSatellite object
    :return: lon: a float representing the longitude of the EarthSatellite object
    :return: alt: a float representing the altitude of the EarthSatellite object
    """
    subpoint = wgs84.subpoint(sat.at(t))
    lat = round(subpoint.latitude.degrees, 3)
    lon = round(subpoint.longitude.degrees, 3)
    alt = round(subpoint.elevation.km, 2)
    return lat, lon, alt