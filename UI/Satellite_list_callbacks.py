from dash import Input, Output, State, no_update, ctx
from skyfield.api import load, wgs84
from Models.Database import get_satellite_list
from Visualisations import Map_Component, Globe_Component
import logging

ts = load.timescale()
logger = logging.getLogger(__name__)
logging.basicConfig(filename="log.txt", format='%(asctime)s - %(levelname)s:%(message)s', level=logging.INFO)

def register_home_screen_callbacks(app):
    """
    registers the callbacks used from the home screen

    :param app: the dash app where these callback will be run
    """
    @app.callback(
        Output("satellite-table", "data"),
        Output("satellite-table", "derived_virtual_data"),
        Input("db-refresh-signal", "data"),
        prevent_initial_call=True

    )
    def refresh_table(db_refresh_signal):
        """
        reloads the data table when a change in the database has be detected

        :param db_refresh_signal: the data within the db-refresh-signal store, which is updated when the database changes
        :return: a list containing the data to be displayed within the table
        """
        logger.info("refreshing table")
        satellites = get_satellite_list()
        # print(satellites)
        data = satellites_to_table_data(satellites)

        return data, None


    """
    TODO: Separate the regular marker and selected satellite marker updates into separate callbacks
    """
    @app.callback(
        Output("map-graph", "figure"),
        Output("globe-graph", "figure"),
        Input("satellite-table", "active_cell"),
        Input("satellite-table", "derived_virtual_data"),
        State("map-graph", "figure"),
        State("globe-graph", "figure"),
        State("satellite-table", "data"),

    )
    def update_satellite_positions(active_cell, filtered_data, map_fig, globe_fig, data):
        """
        Update the satellite markers on the charts whenever the table data is changed, either through database updates
        or the table being filtered

        If a satellite is selected from the table, tell the chart component to highlight it
        :param active_cell: the currently selected cell of the table
        :param map_fig: the 2d map component
        :param globe_fig: the 3d map component
        :param filtered_data: the currently visible data from when the table is filtered
        :param data: the complete table data

        :return: the updated map and globe components
        """
        logger.info("updating satellite markers")
        selected_sat = None
        # print("update_satellite_positions")
        # print(data)
        # print(filtered_data)
        # print(active_cell)
        data = filtered_data if filtered_data is not None else data
        if active_cell:
            row_index = active_cell.get("row")
            if 0 <= row_index < len(filtered_data):
                selected_sat = filtered_data[row_index]
                print(selected_sat)

        globe_fig = Globe_Component.update_markers(globe_fig, data)
        map_fig = Map_Component.update_markers(map_fig, data)

        if selected_sat:
            logger.info("updating selected satellite markers")
            globe_fig = Globe_Component.update_selected_marker(globe_fig,selected_sat)
            map_fig = Map_Component.update_selected_marker(map_fig, selected_sat)

        return map_fig, globe_fig

    """
    TODO: ensure latitude and longitude input only accept valid data
    """
    @app.callback(
        Output("satellite-table", "derived_virtual_data", allow_duplicate=True),
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

        logger.info("filtering visible satellites")
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

        logger.info("returning visible satellites")
        # print(f"[Filter] {len(visible_sats)} visible out of {len(satellites)}")
        return data


    @app.callback(
        Output("satellite-table", "active_cell", allow_duplicate=True),
        Output("map-graph", "figure", allow_duplicate=True),
        Output("globe-graph", "figure",allow_duplicate=True),
        Input("clear-selection-btn", "n_clicks"),
        State("map-graph", "figure"),
        State("globe-graph", "figure"),
        prevent_initial_call=True
    )
    def clear_selection(n_clicks, map_fig, globe_fig):
        """
        Clears the current satellite selection
        :param n_clicks: property used to detect the clear selection button has been clicked
        :param map_fig: the 2d map component
        :param globe_fig: the 3d map component
        :return: None: sets the active cell property of the data table to None
        """
        logger.info("clearing selection")
        globe_fig = Globe_Component.clear_selected_marker(globe_fig)
        map_fig = Map_Component.clear_suggested_marker(map_fig)

        return None, map_fig, globe_fig


def satellites_to_table_data(satellites):
    """
    Takes a list of EarthSatellite objects and returns the data to populate the data table.
    Also flags data that is more than two weeks old, indicating that it should be updated to ensure accuracy
    :param satellites: a list of EarthSatellite objects
    :return: a list of dicts containing the satellite's id, name, latitude, longitude, and altitude
    """
    logger.info("extracting table data from EarthSatellite objects")
    rows = []
    t = ts.now()

    for sat in satellites:
        lat, lon, alt = calculate_position(sat, t)
        epoch = sat.epoch.utc_datetime()
        stale = abs(sat.epoch - t) > 14
        rows.append({
            "OBJECT_ID": sat.model.satnum,
            "OBJECT_NAME": sat.name,
            "LAT": lat,
            "LON": lon,
            "ALT": alt,
            "EPOCH": epoch,
            "STALE": "true" if stale else "false"
        })
    return rows


"""
TODO: use this in all the other places that perform this operation
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