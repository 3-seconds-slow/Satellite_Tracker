import numpy as np
from PIL import Image
import plotly.graph_objects as go
from dash import dcc
from functools import lru_cache
from skyfield.api import load, wgs84
from Models.Database import get_satellite_lookup, satellite_lookup

texture_path = "assets/Earth.jpg"
EARTH_RADIUS_KM = 6371.0
ts = load.timescale()
# fig =None

def create_globe_chart(satellites, selected_sat=None):
    """Render a 3D globe with cached Earth mesh and dynamic satellite markers."""
    # global fig
    fig = create_base_chart()

    # placeholder trace for satellites in table
    fig.add_trace(go.Scatter3d(
        x=[], y=[], z=[],
        mode="markers",
        text=[],
        textposition="top center",
        marker=dict(size=4, color="red", line=dict(width=0)),
        hovertemplate="%{text}<br>x=%{x:.0f} km<br>y=%{y:.0f} km<br>z=%{z:.0f} km<extra></extra>",
        name="Satellites"
    ))

    # placeholder trace for selected satellite
    fig.add_trace(go.Scatter3d(
        x=[], y=[], z=[],
        mode="markers+text",
        text=[],
        textposition="top center",
        marker=dict(size=8, color="yellow", line=dict(width=0)),
        hovertemplate="%{text}<br>x=%{x:.0f} km<br>y=%{y:.0f} km<br>z=%{z:.0f} km<extra></extra>",
        name="Selected Satellite"
    ))

    # placeholder trace for predicted position
    fig.add_trace(go.Scatter3d(
        x=[], y=[], z=[],
        mode="markers+text",
        text=[],
        textposition="top center",
        marker=dict(size=8, color="blue", line=dict(width=0)),
        hovertemplate="%{text}<br>x=%{x:.0f} km<br>y=%{y:.0f} km<br>z=%{z:.0f} km<extra></extra>",
        name="Predicted Position"
    ))

    # placeholder trace for satellite path
    fig.add_trace(go.Scatter3d(
        x=[], y=[], z=[],
        mode="markers",
        marker=dict(size=4, color="green", line=dict(width=0)),
        name="Satellite Path"
    ))

    if satellites:
        fig = update_markers(fig, satellites)

    if selected_sat:
        fig = update_selected_marker(fig,selected_sat)


    return dcc.Graph(
        id="globe-graph",
        figure=fig,
        config={"displayModeBar": True, "scrollZoom": True},
        style={"height": "600px"}
    )

# @lru_cache(maxsize=1)
# def create_base_chart():
#     """A base Plotly Figure with only the Earth mesh and layout."""
#     mesh = create_earth()
#     fig = go.Figure([mesh])
#     fig.update_layout(
#         showlegend=False,
#         margin=dict(l=0, r=0, t=0, b=0),
#         scene=dict(
#             xaxis=dict(visible=False),
#             yaxis=dict(visible=False),
#             zaxis=dict(visible=False),
#             aspectmode="manual",
#             aspectratio=dict(x=1, y=1, z=1),
#             bgcolor="black",
#             camera=dict(eye=dict(x=2.5, y=1.5, z=1.2))
#         )
#     )
#     return fig

@lru_cache(maxsize=1)
def create_base_chart():
    """Create a reusable base globe with textured Earth mesh."""
    print("[Globe] Building or retrieving cached Earth mesh...")

    earth_mesh = create_earth()
    if not isinstance(earth_mesh, go.Mesh3d):
        print(f"⚠️ Warning: create_earth returned unexpected type: {type(earth_mesh)}")
        return go.Figure()  # fail-safe empty figure

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
    return fig

@lru_cache(maxsize=1)
def create_earth():
    """Build and cache the textured Earth mesh (computed once)."""

    print("[Globe] Generating Earth mesh (cached)...")

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
    return earth_mesh

def load_earth_mesh(radius=EARTH_RADIUS_KM, lat_res=150, lon_res=None):
    """
    Build a colored mesh for a textured sphere.
    - lat_res: number of latitude rows
    - lon_res: number of longitude columns (if None -> 2*lat_res)
    Returns: x, y, z (flattened), i, j, k (triangle indices), vertexcolor (list of 'rgb(...)')
    """
    if lon_res is None:
        lon_res = lat_res * 2

    # Load texture (RGB)
    img = Image.open(texture_path).convert("RGB")
    tex = np.asarray(img) / 255.0
    tex_h, tex_w, _ = tex.shape

    # Create regular grid — note endpoint=False for longitudes so we can wrap cleanly
    lats = np.linspace(-np.pi / 2, np.pi / 2, lat_res)            # -90 -> +90
    lons = np.linspace(-np.pi, np.pi, lon_res, endpoint=False)    # -180 -> 180 (wrap)
    lon_grid, lat_grid = np.meshgrid(lons, lats)  # shapes (lat_res, lon_res)

    # Cartesian coordinates for sphere
    x = radius * np.cos(lat_grid) * np.cos(lon_grid)
    y = radius * np.cos(lat_grid) * np.sin(lon_grid)
    z = radius * np.sin(lat_grid)

    # Texture mapping: compute nearest pixel indices in the texture
    u = ((lon_grid + np.pi) / (2 * np.pi) * tex_w).astype(int) % tex_w
    v = ((np.pi / 2 - lat_grid) / np.pi * tex_h).astype(int) % tex_h
    colours = tex[v, u]   # shape (lat_res, lon_res, 3)

    # Flatten vertex arrays
    x_flat = x.flatten()
    y_flat = y.flatten()
    z_flat = z.flatten()
    colours_flat = (colours * 255).astype(np.uint8).reshape(-1, 3)

    # Convert to 'rgb(r,g,b)' strings for Mesh3d
    vertexcolour = [f"rgb({r},{g},{b})" for r, g, b in colours_flat]

    # Build triangles with consistent winding, wrap longitude
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

    return x_flat, y_flat, z_flat, i, j, k, vertexcolour

def update_markers (fig, satellites):
    t = ts.now()
    xs, ys, zs, names = [], [], [], []
    satellite_lookup = get_satellite_lookup()
    # print(f"satellite_lookup type: {type(satellite_lookup)}")
    # print("Lookup keys (first 10):", list(satellite_lookup.keys())[:10])
    # print("Sample table IDs:", [sat["OBJECT_ID"] for sat in satellites[:10]])
    for sat in satellites:
        # print(f"getting data: {sat}")
        sat_object = satellite_lookup[sat["OBJECT_ID"]]
        if not sat_object:
            continue

        position = sat_object.at(t)
        subpoint = wgs84.subpoint(position)
        lat = subpoint.latitude.radians
        lon = subpoint.longitude.radians
        alt = subpoint.elevation.km

        # Convert back to 3D Cartesian for the globe
        r = EARTH_RADIUS_KM + alt
        x = r * np.cos(lat) * np.cos(lon)
        y = r * np.cos(lat) * np.sin(lon)
        z = r * np.sin(lat)
        xs.append(x)
        ys.append(y)
        zs.append(z)
        names.append(sat_object.name)

    fig["data"][1].update(x=xs, y=ys, z=zs, text=names)
    return fig

def update_selected_marker (fig, selected_sat):
    t = ts.now()
    satellite_lookup = get_satellite_lookup()
    sat_object = satellite_lookup[selected_sat["OBJECT_ID"]]
    print(selected_sat)
    if not sat_object:
        return fig

    position = sat_object.at(t)
    subpoint = wgs84.subpoint(position)
    lat = subpoint.latitude.radians
    lon = subpoint.longitude.radians
    alt = subpoint.elevation.km

    # Convert back to 3D Cartesian for the globe
    r = EARTH_RADIUS_KM + alt
    x = r * np.cos(lat) * np.cos(lon)
    y = r * np.cos(lat) * np.sin(lon)
    z = r * np.sin(lat)

    fig["data"][2].update(x=[x], y=[y], z=[z], text=[sat_object.name])
    return fig

def clear_suggested_marker(fig):
    print("clear marker")
    fig["data"][2].update(x=[], y=[], z=[], text=[])
    return fig

def update_prediction_marker (fig, selected_sat, datetime):
    t = ts.utc(datetime)
    print(selected_sat)
    satellite_lookup = get_satellite_lookup()
    sat_object = satellite_lookup[selected_sat]
    if not sat_object:
        return fig

    position = sat_object.at(t)
    subpoint = wgs84.subpoint(position)
    lat = subpoint.latitude.radians
    lon = subpoint.longitude.radians
    alt = subpoint.elevation.km

    # Convert back to 3D Cartesian for the globe
    r = EARTH_RADIUS_KM + alt
    x = r * np.cos(lat) * np.cos(lon)
    y = r * np.cos(lat) * np.sin(lon)
    z = r * np.sin(lat)
    fig["data"][3].update(x=[x], y=[y], z=[z], text=[sat_object.name])
    return fig

def show_path (fig, selected_sat, minutes_diff):
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

    # 2. Vector-propagate orbit points
    position = sat_object.at(times)
    subpoint = wgs84.subpoint(position)
    lat = subpoint.latitude.radians
    lon = subpoint.longitude.radians
    alt = subpoint.elevation.km

    # Convert back to 3D Cartesian for the globe
    r = EARTH_RADIUS_KM + alt
    x = r * np.cos(lat) * np.cos(lon)
    y = r * np.cos(lat) * np.sin(lon)
    z = r * np.sin(lat)
    xs.append(x)
    ys.append(y)
    zs.append(z)

    print(xs)
    fig["data"][4].update(x=xs, y=ys, z=zs)
    return fig

def clear_path(fig):
    fig["data"][4].update(x=[], y=[], z=[])
    return fig