import os
import tempfile
import folium
import webview
from skyfield.api import wgs84, load
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtGui import QWindow
from PySide6.QtWidgets import QWidget

ts = load.timescale()


class FoliumMapWidget(QWidget):
    def __init__(self, satellites=None, parent=None):
        super().__init__(parent)
        self.satellites = satellites or []
        self.highlighted = None
        self.prediction = None

        # Create layout
        layout = QVBoxLayout(self)

        # Initial map HTML file
        self._tmpfile = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
        self._tmpfile.close()

        # Create a pywebview window
        self.view = webview.create_window(
            "Folium Map",
            f"file:///{os.path.abspath(self._tmpfile.name)}",
            frameless=True,
            easy_drag=False,
        )

        # Wrap pywebview window into a QWidget container
        self.container = QWidget.createWindowContainer(QWindow.fromWinId(self.view.gui.Window.window.handle))
        layout.addWidget(self.container)

        # Render initial map
        self.update_map()

    def update_map(self):
        """Regenerate the Folium map and reload it in the view"""
        fmap = folium.Map(location=[0, 0], zoom_start=2)
        now = ts.now()

        # --- Plot all satellites ---
        for sat in self.satellites:
            sp = wgs84.subpoint(sat.at(now))
            folium.CircleMarker(
                location=[sp.latitude.degrees, sp.longitude.degrees],
                radius=4,
                color="blue",
                fill=True,
                fill_opacity=0.8,
                popup=sat.name,
            ).add_to(fmap)

        # --- Highlight selected satellite ---
        if self.highlighted:
            sp = wgs84.subpoint(self.highlighted.at(now))
            folium.CircleMarker(
                location=[sp.latitude.degrees, sp.longitude.degrees],
                radius=8,
                color="yellow",
                fill=True,
                fill_opacity=1.0,
                popup=f"Selected: {self.highlighted.name}",
            ).add_to(fmap)

        # --- Prediction marker + path ---
        if self.prediction:
            sat, t2 = self.prediction
            sp2 = wgs84.subpoint(sat.at(t2))
            folium.Marker(
                [sp2.latitude.degrees, sp2.longitude.degrees],
                popup=f"Prediction: {sat.name}",
                icon=folium.Icon(color="red"),
            ).add_to(fmap)

            # Path between now and prediction
            times = ts.linspace(now, t2, 200)
            path = [wgs84.subpoint(sat.at(t)) for t in times]
            lats = [p.latitude.degrees for p in path]
            lons = [p.longitude.degrees for p in path]
            coords = list(zip(lats, lons))
            folium.PolyLine(coords, color="cyan", weight=2.5, opacity=0.8).add_to(fmap)

        # Save updated map
        fmap.save(self._tmpfile.name)

        # Reload in webview
        self.view.load_url(f"file:///{os.path.abspath(self._tmpfile.name)}")

    # --- Public API ---
    def set_satellites(self, satellites):
        self.satellites = satellites
        self.update_map()

    def highlight_satellite(self, sat):
        self.highlighted = sat
        self.update_map()

    def show_prediction(self, sat, t2):
        self.prediction = (sat, t2)
        self.update_map()

