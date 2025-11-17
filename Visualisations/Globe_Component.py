import numpy as np
from PIL import Image
import plotly.graph_objects as go
from functools import lru_cache
from skyfield.api import load, wgs84
from Models.Database import get_satellite_lookup
import logging

texture_path = "assets/Earth.jpg"
EARTH_RADIUS_KM = 6371.0
ts = load.timescale()
logger = logging.getLogger(__name__)
logging.basicConfig(filename="log.txt", format='%(asctime)s - %(levelname)s:%(message)s', level=logging.ERROR)


def create_globe_chart():
    """
    Creates a base chart and globe, and adds placeholder traces for the different kinds of satellite markers.

    :return: a plotly graph_object figure
    """
    logger.info("creating globe chart")
    earth_mesh = create_earth()
    fig = go.Figure([earth_mesh])

    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            aspectmode="manual",
            aspectratio=dict(x=1, y=1, z=1),
            bgcolor="black",
            camera=dict(eye=dict(x=2.5, y=1.5, z=1.2)),
        ),
    )

    logger.info("adding placeholder traces to globe")
    # placeholder trace for satellites in table
    fig.add_trace(go.Scatter3d(
        x=[], y=[], z=[],
        mode="markers",
        text=[],
        textposition="top center",
        marker=dict(size=4, color="red", line=dict(width=0)),
        hovertemplate="%{text}<br>x=%{x:.0f}<br>y=%{y:.0f}<br>z=%{z:.0f}<extra></extra>",
        name="Satellites"
    ))

    # placeholder trace for selected satellite
    fig.add_trace(go.Scatter3d(
        x=[], y=[], z=[],
        mode="markers+text",
        text=[],
        textposition="top center",
        marker=dict(size=8, color="yellow", line=dict(width=0)),
        hovertemplate="%{text}<br>x=%{x:.0f}<br>y=%{y:.0f}<br>z=%{z:.0f}<extra></extra>",
        name="Selected Satellite"
    ))

    # placeholder trace for predicted position
    fig.add_trace(go.Scatter3d(
        x=[], y=[], z=[],
        mode="markers+text",
        text=[],
        textposition="top center",
        marker=dict(size=8, color="blue", line=dict(width=0)),
        hovertemplate="%{text}<br>x=%{x:.0f}<br>y=%{y:.0f}<br>z=%{z:.0f}<extra></extra>",
        name="Predicted Position"
    ))

    # placeholder trace for satellite path
    fig.add_trace(go.Scatter3d(
        x=[], y=[], z=[],
        mode="lines+markers",
        marker=dict(size=4, color="green", line=dict(width=0)),
        name="Satellite Path"
    ))

    logger.info("globe chart created")
    return fig


@lru_cache(maxsize=1)
def create_earth():
    """
    Create a 3d mesh to add to the globe figure
    :return: earth_mesh: a plotly graph object Mesh3d, textured to look like the plannet earth
    """

    logger.info("Generating Earth mesh")

    x, y, z, i, j, k, vertexcolour = load_earth_mesh()
    earth_mesh = go.Mesh3d(
        x=x, y=y, z=z,
        i=i, j=j, k=k,
        vertexcolor=vertexcolour,
        flatshading=True,
        lighting=dict(ambient=1.0, diffuse=0.0, specular=0.00),
        hoverinfo="skip",
        name="Earth",
        showscale=False,
    )
    logger.info("Earth mesh created")
    return earth_mesh

def load_earth_mesh(radius=EARTH_RADIUS_KM, lat_res=200, lon_res=None):
    """
    Generates the co-ordinates for a textured sphere mesh, then loads and image of the earth and maps it to the sphere.

    The texture mapping is achieved by getting each vertex of the sphere and assigning it the colour of the
    corresponding pixel of the texture image.

    :param: radius: the radius of the sphere. By default, this is equal to the radius of the earth in kms
    :param: lat_res: number of latitude rows. By default, this is 200. A higher number results in a higher resolution
    earth texture on the sphere, but takes longer to generate. This number gives an acceptable appearance and
    performance on my 5+ year old laptop.
    :param: lon_res: number of longitude columns. By default, these are equal to double the number of latitude rows
    :return: x,y,z: flattened vertex arrays
    :return: i, j, k: array of triangle indices
    :return: vertexcolor: a list of colours for each indice
    """
    if lon_res is None:
        lon_res = lat_res * 2

    # Load texture (RGB)
    logger.info("loading texture")
    try:
        img = Image.open(texture_path).convert("RGB")
    except Exception as e:
        logger.error(e)
        raise Exception("Could not load texture", e)

    tex = np.asarray(img) / 255.0
    tex_h, tex_w, _ = tex.shape

    # Create regular grid
    logger.info("creating regular grid")
    lats = np.linspace(-np.pi / 2, np.pi / 2, lat_res)
    lons = np.linspace(-np.pi, np.pi, lon_res, endpoint=False)
    lon_grid, lat_grid = np.meshgrid(lons, lats)

    # Cartesian coordinates for sphere
    logger.info("Calculating cartesian coordinates for sphere")
    x = radius * np.cos(lat_grid) * np.cos(lon_grid)
    y = radius * np.cos(lat_grid) * np.sin(lon_grid)
    z = radius * np.sin(lat_grid)

    # Texture mapping: compute nearest pixel indices in the texture
    logger.info("mapping texture")
    u = ((lon_grid + np.pi) / (2 * np.pi) * tex_w).astype(int) % tex_w
    v = ((np.pi / 2 - lat_grid) / np.pi * tex_h).astype(int) % tex_h
    colours = tex[v, u]

    # Flatten vertex arrays
    logger.info("flattening vertex arrays")
    x_flat = x.flatten()
    y_flat = y.flatten()
    z_flat = z.flatten()
    colours_flat = (colours * 255).astype(np.uint8).reshape(-1, 3)

    # Convert to 'rgb(r,g,b)' strings for Mesh3d
    vertexcolour = [f"rgb({r},{g},{b})" for r, g, b in colours_flat]

    # Build triangles with consistent winding, wrap longitude
    logger.info("building triangles")
    i = []
    j = []
    k = []

    n_lon = lon_res
    n_lat = lat_res

    for lat_i in range(n_lat - 1):
        for lon_i in range(n_lon):
            lon_next = (lon_i + 1) % n_lon

            idx = lat_i * n_lon + lon_i
            idx_next = lat_i * n_lon + lon_next
            idx_down = (lat_i + 1) * n_lon + lon_i
            idx_down_next = (lat_i + 1) * n_lon + lon_next

            # triangle 1: top-left, bottom-left, bottom-right
            i.append(idx)
            j.append(idx_down)
            k.append(idx_down_next)

            # triangle 2: top-left, bottom-right, top-right
            i.append(idx)
            j.append(idx_down_next)
            k.append(idx_next)

    logger.info("texture mapping complete")
    return x_flat, y_flat, z_flat, i, j, k, vertexcolour

"""
TODO: make a separate function for the position calculations
"""
def update_markers (fig, satellites):
    """
    Updates the satellite markers on the globe
    :param fig: plotly graph object to be updates
    :param satellites: a list of IDs for the satellites to be added to the globe
    :return: a plotly graph object
    """
    logger.info("updating globe satellite markers")
    t = ts.now()
    xs, ys, zs, names = [], [], [], []
    satellite_lookup = get_satellite_lookup()
    # print(f"satellite_lookup type: {type(satellite_lookup)}")
    # print("Lookup keys (first 10):", list(satellite_lookup.keys())[:10])
    # print("Sample table IDs:", [sat["OBJECT_ID"] for sat in satellites[:10]])
    for sat in satellites:
        # print(f"getting data: {sat}")
        sat_object = satellite_lookup.get(sat["OBJECT_ID"])
        if not sat_object:
            continue

        x,y,z = calculate_coords(t, sat_object)
        xs.append(x)
        ys.append(y)
        zs.append(z)
        names.append(sat_object.name)

    logger.info("adding satellite markers to globe")
    fig["data"][1].update(x=xs, y=ys, z=zs, text=names)
    # fig.update_traces(selector=dict(name="satellites"), x=xs, y=ys, z=zs, text=names)
    return fig

def update_selected_marker (fig, selected_sat):
    """
    Updates the highlighted marker for a selected satellite on the globe
    :param fig: plotly graph object to be updated
    :param selected_sat: the id number of the selected satellite
    :return: a plotly graph object
    """
    logger.info("updating highlighted globe marker for selected satellite")
    t = ts.now()
    satellite_lookup = get_satellite_lookup()
    sat_object = satellite_lookup.get(selected_sat["OBJECT_ID"])
    # print(selected_sat)
    if not sat_object:
        return fig

    x,y,z = calculate_coords(t, sat_object)

    logger.info("adding highlighted marker to globe")
    fig["data"][2].update(x=[x], y=[y], z=[z], text=[sat_object.name])
    # fig.update_traces(selector=dict(name="satellites"), x=[x], y=[y], z=[z], text=[sat_object.name])
    return fig

def clear_selected_marker(fig):
    """
    removes the highlighted selected satellite marker
    :param fig: the plotly graph object to be updated
    :return: the plotly graph object
    """
    # print("clear marker")
    logger.info("clearing highlighted globe marker")
    fig["data"][2].update(x=[], y=[], z=[], text=[])
    return fig

def update_prediction_marker (fig, selected_sat, datetime):
    """
    Adds a marker representing the predicted position of a satellite on the globe
    :param fig: the plotly graph object to be updated
    :param selected_sat: the id number of the selected satellite
    :param datetime: the date and time to predict the satellite position
    :return: a plotly graph object
    """
    logger.info("updating predicted position globe marker")
    # print(selected_sat)
    t = ts.utc(datetime)
    satellite_lookup = get_satellite_lookup()
    sat_object = satellite_lookup[selected_sat]
    if not sat_object:
        return fig

    x,y,z = calculate_coords(t,sat_object)
    logger.info("adding prediction marker to globe")
    fig["data"][3].update(x=[x], y=[y], z=[z], text=[sat_object.name])
    return fig

def show_path (fig, selected_sat, minutes_diff):
    """
    Add a series of markers to the globe representing the path the satellite will take to a predicted position.
    The selected satellites position is calculated every minute between now and the selected time, and that position
    plotted on the globe.
    :param fig: the plotly graph object to be updated
    :param selected_sat: the id number of the selected satellite
    :param minutes_diff: the number of minutes between now and the prediction time
    :return: a plotly graph object
    """
    logger.info("generating globe satellite path")
    xs, ys, zs = [], [], []
    t = ts.now()
    satellite_lookup = get_satellite_lookup()
    sat_object = satellite_lookup[selected_sat]


    times = ts.utc(
        t.utc_datetime().year,
        t.utc_datetime().month,
        t.utc_datetime().day,
        t.utc_datetime().hour,
        t.utc_datetime().minute + np.arange(minutes_diff)
    )
    # print(times)

    position = sat_object.at(times)
    subpoint = wgs84.subpoint(position)
    lat = subpoint.latitude.radians
    lon = subpoint.longitude.radians
    alt = subpoint.elevation.km

    r = EARTH_RADIUS_KM + alt
    x = r * np.cos(lat) * np.cos(lon)
    y = r * np.cos(lat) * np.sin(lon)
    z = r * np.sin(lat)

    # print(xs)
    logger.info("adding path to globe")
    fig["data"][4].update(x=x, y=y, z=z)
    # print(fig["data"][4])
    return fig

def clear_path(fig):
    """
    Remove the satellite path
    :param fig: the plotly graph object to be updated
    :return: a plotly graph object
    """
    logger.info("removing path from globe")
    fig["data"][4].update(x=[], y=[], z=[])
    return fig

def calculate_coords(t, sat_object):
    """
    calculates the cartesian coordinates of a satellite
    :param: t: skyfield timescale object
    :param: sat_object: an EarthSatellite object
    :return: the x, y, z coordinates of the satellite
    """

    # using the xyz co-ordinates provided by EarthSatellite.at() leads to the markers appearing on the wrong side of
    # the globe. getting the latitude and longitude then converting it into cartesian co-ordinates fixes the issue
    position = sat_object.at(t)
    subpoint = wgs84.subpoint(position)
    lat = subpoint.latitude.radians
    lon = subpoint.longitude.radians
    alt = subpoint.elevation.km

    r = EARTH_RADIUS_KM + alt
    x = r * np.cos(lat) * np.cos(lon)
    y = r * np.cos(lat) * np.sin(lon)
    z = r * np.sin(lat)

    return x, y, z