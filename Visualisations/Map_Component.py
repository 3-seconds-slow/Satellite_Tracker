import numpy as np
import plotly.graph_objects as go
from functools import lru_cache
from skyfield.api import load, wgs84
from Models.Database import get_satellite_lookup
import logging

ts = load.timescale()
logger = logging.getLogger(__name__)
logging.basicConfig(filename="log.txt", format='%(asctime)s - %(levelname)s:%(message)s', level=logging.INFO)

def create_map_chart():
    """
        Creates a base chart and map, and adds placeholder traces for the different kinds of satellite markers.

        Adds markers for any satellites in the table, and a highlighted marker for any selected satellite.
        :return: a plotly graph_object figure
        """
    logger.info("creating map chart")
    fig = get_base_map_figure()

    logger.info("adding placeholder traces to map")
    # placeholder trace for satellites in table
    fig.add_trace(go.Scattergeo(
        lon=[], lat=[], text=[],
        mode="markers",
        textposition="top center",
        marker=dict(size=4, color="red"),
        hovertemplate="%{text}<br>lat=%{lat:.4f} <br>lon=%{lon:.4f} <extra></extra>",
        name="Satellites",
    ))

    # placeholder trace for selected satellite
    fig.add_trace(go.Scattergeo(
        lon=[], lat=[], text=[],
        mode="markers",
        textposition="top center",
        marker=dict(size=8, color="yellow"),
        hovertemplate="%{text}<br>lat=%{lat:.4f} <br>lon=%{lon:.4f} <extra></extra>",
        name="Selected",
    ))

    # placeholder trace for predicted position
    fig.add_trace(go.Scattergeo(
        lon=[], lat=[], text=[],
        mode="markers",
        textposition="top center",
        marker=dict(size=8, color="blue"),
        hovertemplate="%{text}<br>lat=%{lat:.4f} <br>lon=%{lon:.4f} <extra></extra>",
        name="Predicted Position",
    ))

    # Placeholder trace for satellite path
    fig.add_trace(go.Scattergeo(
        lon=[], lat=[],
        mode="markers",
        textposition="top center",
        marker=dict(size=4, color="green"),
        hovertemplate="%{text}<br>lat=%{lat:.4f} <br>lon=%{lon:.4f} <extra></extra>",
        name="Satellite Path",
    ))

    logger.info("map chart created")
    return fig

@lru_cache(maxsize=1)
def get_base_map_figure():
    """
    Creates a base plotly graph_object figure and adds a map of the earth.
    This figure is cached to that the chart does not have to be rebuilt every time
    :return: a plotly graph_object figure
    """
    logger.info("creating base map")
    fig = go.Figure()

    fig.update_geos(
        projection_type="equirectangular",
        showcoastlines=True,
        showcountries=True,
        showland=True,
        landcolor="rgb(230, 230, 230)",
        oceancolor="rgb(0, 0, 50)",
        showocean=True,
    )

    fig.update_layout(
        geo=dict(projection_scale=1),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="black",
        plot_bgcolor="black",
    )

    logger.info("base map created")
    return fig

def update_markers (fig, satellites):
    """
    Updates the satellite markers on the map
    :param fig: plotly graph object to be updates
    :param satellites: a list of IDs for the satellites to be added to the map
    :return: a plotly graph object
    """
    logger.info("updating map satellite markers")
    lats = []
    lons = []
    names = []
    # print(f"satellite_lookup type: {type(satellite_lookup)}")
    # print("Lookup keys (first 10):", list(satellite_lookup.keys())[:10])
    # print("Sample table IDs:", [sat["OBJECT_ID"] for sat in satellites[:10]])
    for sat in satellites:
        # print(f"getting data: {sat}")
        lats.append(sat["LAT"])
        lons.append(sat["LON"])
        names.append(sat["OBJECT_NAME"])

    logger.info("adding satellite markers to map")
    fig["data"][0].update(lat=lats, lon=lons, text=names)
    return fig


def update_selected_marker (fig, selected_sat):
    """
    Updates the highlighted marker for a selected satellite on the map
    :param fig: plotly graph object to be updated
    :param selected_sat: the id number of the selected satellite
    :return: a plotly graph object
    """
    logger.info("updating highlighted map marker for selected satellite")
    lat = selected_sat["LAT"]
    lon = selected_sat["LON"]
    name = selected_sat["OBJECT_NAME"]

    logger.info("adding highlighted marker to map")
    fig["data"][1].update(lat=[lat], lon=[lon], text=[name])
    return fig

def clear_suggested_marker(fig):
    """
    removes the highlighted selected satellite marker
    :param fig: the plotly graph object to be updated
    :return: the plotly graph object
    """
    logger.info("clearing highlighted map marker")
    fig["data"][1].update(lat=[], lon=[], text=[])
    return fig

def update_prediction_marker (fig, selected_sat, datetime):
    """
    Adds a marker representing the predicted position of a satellite on the map
    :param fig: the plotly graph object to be updated
    :param selected_sat: the id number of the selected satellite
    :param datetime: the date and time to predict the satellite position
    :return: a plotly graph object
    """
    logger.info("updating predicted position map marker")
    t=ts.utc(datetime)
    # print(selected_sat)
    satellite_lookup = get_satellite_lookup()
    sat_object = satellite_lookup[selected_sat]
    if not sat_object:
        return fig

    geocentric = sat_object.at(t)
    subpoint = wgs84.subpoint(geocentric)

    lat = subpoint.latitude.degrees
    lon = subpoint.longitude.degrees

    logger.info("adding prediction marker to map")
    fig["data"][2].update(lat=[lat], lon=[lon], text=[sat_object.name])
    return fig

def show_path (fig, selected_sat, minutes_diff):
    """
    Add a series of markers to the map representing the path the satellite will take to a predicted position.
    The selected satellites position is calculated every minute between now and the selected time, and that position
    plotted on the map.
    :param fig: the plotly graph object to be updated
    :param selected_sat: the id number of the selected satellite
    :param minutes_diff: the number of minutes between now and the prediction time
    :return: a plotly graph object
    """
    logger.info("generating map satellite path")
    t = ts.now()
    # print(selected_sat)
    satellite_lookup = get_satellite_lookup()
    sat_object = satellite_lookup[selected_sat]

    times = ts.utc(
        t.utc_datetime().year,
        t.utc_datetime().month,
        t.utc_datetime().day,
        t.utc_datetime().hour,
        t.utc_datetime().minute + np.arange(minutes_diff)
    )

    positions = sat_object.at(times)

    subpoints = wgs84.subpoint(positions)
    lats = subpoints.latitude.degrees
    lons = subpoints.longitude.degrees

    logger.info("adding path to map")
    fig["data"][3].update(lat=lats, lon=lons)
    return fig

def clear_path(fig):
    """
    Remove the satellite path
    :param fig: the plotly graph object to be updated
    :return: a plotly graph object
    """
    logger.info("removing path from map")
    fig["data"][3].update(lat=[], lon=[], text=[])
    return fig