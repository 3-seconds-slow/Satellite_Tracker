import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import QTimer
from pyvista import examples
from skyfield.api import load


# --- Skyfield timescale ---
ts = load.timescale()


def get_satellite_positions(satellites):
    """Return Nx3 array of [x, y, z] in km for given EarthSatellite list."""
    if not satellites:
        return np.empty((0, 3))
    now = ts.now()
    positions = []
    for sat in satellites:
        geocentric = sat.at(now)
        x, y, z = geocentric.position.km
        positions.append([x, y, z])
    return np.array(positions)


def make_earth(radius=6371):
    """Return a textured Earth sphere for PyVista."""
    sphere = pv.Sphere(
        radius=radius,
        theta_resolution=120,
        phi_resolution=120,
        start_theta=270.001,
        end_theta=270,
    )

    # Generate UV coords for texture
    sphere.active_texture_coordinates = np.zeros((sphere.points.shape[0], 2))
    for i in range(sphere.points.shape[0]):
        x, y, z = sphere.points[i] / np.linalg.norm(sphere.points[i])
        u = 0.5 + np.arctan2(-x, y) / (2 * np.pi)
        v = 0.5 + np.arcsin(z) / np.pi
        sphere.active_texture_coordinates[i] = [u, v]

    texture = examples.load_globe_texture()
    return sphere, texture


class GlobeWidget(QWidget):
    def __init__(self, satellites, update_interval=2000, parent=None):
        """
        satellites: list of Skyfield EarthSatellite objects
        update_interval: refresh rate in ms
        """
        super().__init__(parent)
        self.satellites = satellites
        self.highlight_actor = None  # single point actor for selection

        # Layout + PyVista interactor
        layout = QVBoxLayout(self)
        self.plotter = QtInteractor(self)
        layout.addWidget(self.plotter.interactor)

        self.plotter.set_background('black')

        # Build Earth
        sphere, texture = make_earth()
        self.plotter.add_mesh(sphere, texture=texture)

        # Initial satellites
        self.sat_poly = None
        self.sat_actor = None
        # self._add_satellite_points()

        # Add satellites
        # positions = get_satellite_positions(self.satellites)
        # self.sat_poly = pv.PolyData(positions)
        # self.sat_points = self.plotter.add_mesh(
        #     self.sat_poly,
        #     color="red",
        #     point_size=15,
        #     render_points_as_spheres=True,
        # )

        self.plotter.reset_camera()

        # Timer for updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_satellites)
        self.timer.start(update_interval)

    def _add_satellite_points(self):
        """(Re)create the PolyData and actor for current satellites."""
        positions = get_satellite_positions(self.satellites)

        # Remove old actor if it exists
        if self.sat_actor is not None:
            self.plotter.remove_actor(self.sat_actor)

        # Build new PolyData + actor
        self.sat_poly = pv.PolyData(positions) if len(positions) else pv.PolyData()
        self.sat_actor = self.plotter.add_mesh(
            self.sat_poly,
            color="red",
            point_size=5,
            render_points_as_spheres=True,
        )

    def update_satellites(self):
        """Update positions in place, or rebuild if list size changed."""
        if not self.satellites:
            return

        positions = get_satellite_positions(self.satellites)

        # Case 1: same number of satellites → update in place
        if self.sat_poly is not None and positions.shape[0] == self.sat_poly.n_points:
            self.sat_poly.points = positions
        else:
            # Case 2: different number → rebuild
            self._add_satellite_points()

        self.plotter.update()

    def set_satellites(self, new_satellites):
        """Replace the satellite list and refresh display."""
        self.satellites = new_satellites
        self._add_satellite_points()
        self.plotter.update()

    def highlight_satellite(self, sat):
        """Highlight one satellite and centre camera on it."""
        # remove old highlight
        if self.highlight_actor is not None:
            self.plotter.remove_actor(self.highlight_actor)

        # compute position now
        geocentric = sat.at(ts.now())
        x, y, z = geocentric.position.km
        pos = np.array([[x, y, z]])

        # add highlighted point (yellow, larger)
        self.highlight_actor = self.plotter.add_points(
            pos,
            color="green",
            point_size=10,
            render_points_as_spheres=True,
        )

        # centre camera on it
        self.plotter.camera_position = 'yz'  # optional preset
        self.plotter.set_focus([x, y, z])
        self.plotter.reset_camera_clipping_range()

    def highlight_prediction(self, sat, t1, t2, steps=1000):
        """Show current & predicted positions and orbit path (wrapped correctly)."""
        # remove old prediction actors if they exist
        if hasattr(self, "_prediction_actors"):
            for actor in self._prediction_actors:
                try:
                    self.plotter.remove_actor(actor)
                except Exception:
                    pass
        self._prediction_actors = []

        # --- Current position marker ---
        pos1 = sat.at(t1).position.km
        p1 = np.array([pos1])
        act1 = self.plotter.add_points(p1, color="yellow",
                                       point_size=20, render_points_as_spheres=True)
        self._prediction_actors.append(act1)

        # --- Predicted position marker ---
        pos2 = sat.at(t2).position.km
        p2 = np.array([pos2])
        act2 = self.plotter.add_points(p2, color="red",
                                       point_size=20, render_points_as_spheres=True)
        self._prediction_actors.append(act2)

        # --- Orbit trace (sampled positions along the arc) ---
        times = ts.linspace(t1, t2, steps)
        points = np.array([sat.at(t).position.km for t in times])

        # This gives a curved polyline around Earth
        act3 = self.plotter.add_lines(points, color="cyan", width=2)
        self._prediction_actors.append(act3)

        self.plotter.render()


