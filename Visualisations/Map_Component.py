import numpy as np
import plotly.graph_objects as go
from dash import dcc
from functools import lru_cache
from skyfield.api import load, wgs84
from Models.Database import get_satellite_lookup

ts = load.timescale()
# fig = None

def create_map_chart(satellites, selected_sat=None):
    # global fig
    fig = get_base_map_figure()

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

    fig.add_trace(go.Scattergeo(
        lon=[], lat=[],
        mode="markers",
        textposition="top center",
        marker=dict(size=4, color="green"),
        hovertemplate="%{text}<br>lat=%{lat:.4f} <br>lon=%{lon:.4f} <extra></extra>",
        name="Satellite Path",
    ))

    if satellites:
        fig = update_markers(fig, satellites)

    if selected_sat:
        fig = update_selected_marker(fig, selected_sat)

    return dcc.Graph(
        id="map-graph",
        figure=fig,
        config={"displayModeBar": True, "scrollZoom": True},
        style={"height": "600px"}
    )

@lru_cache(maxsize=1)
def get_base_map_figure():
    """Return a base 2D Earth map with fixed coastlines and layout."""
    fig = go.Figure()

    # Add Earth base map (you can add coastlines or mapbox if you prefer)
    fig.update_geos(
        projection_type="equirectangular",  # or "natural earth", "equirectangular"
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

    return fig

def update_markers (fig, satellites):
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

    fig["data"][0].update(lat=lats, lon=lons, text=names)
    return fig

def update_selected_marker (fig, selected_sat):
    print(selected_sat)
    lat = selected_sat["LAT"]
    lon = selected_sat["LON"]
    name = selected_sat["OBJECT_NAME"]

    fig["data"][1].update(lat=[lat], lon=[lon], text=[name])
    return fig

def clear_suggested_marker(fig):
    fig["data"][1].update(lat=[], lon=[], text=[])
    return fig

def update_prediction_marker (fig, selected_sat, datetime):
    t=ts.utc(datetime)
    print(selected_sat)
    satellite_lookup = get_satellite_lookup()
    sat_object = satellite_lookup[selected_sat]
    if not sat_object:
        return fig

    geocentric = sat_object.at(t)
    subpoint = wgs84.subpoint(geocentric)

    lat = subpoint.latitude.degrees
    lon = subpoint.longitude.degrees

    fig["data"][2].update(lat=[lat], lon=[lon], text=[sat_object.name])
    return fig

def show_path (fig, selected_sat, minutes_diff):
    t = ts.now()
    print(selected_sat)
    satellite_lookup = get_satellite_lookup()
    sat_object = satellite_lookup[selected_sat]

    times = ts.utc(
        t.utc_datetime().year,
        t.utc_datetime().month,
        t.utc_datetime().day,
        t.utc_datetime().hour,
        t.utc_datetime().minute + np.arange(minutes_diff)
    )

    # 2. Vector-propagate orbit points
    positions = sat_object.at(times)

    subpoints = wgs84.subpoint(positions)
    lats = subpoints.latitude.degrees
    lons = subpoints.longitude.degrees

    fig["data"][3].update(lat=lats, lon=lons)
    return fig

def clear_path(fig):
    fig["data"][3].update(lat=[], lon=[], text=[])
    return fig