import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from skyfield.api import wgs84, load

ts = load.timescale()

class MapWidget(FigureCanvasQTAgg):
    def __init__(self, satellites=None, parent=None):
        fig = plt.Figure(figsize=(8, 4))
        self.ax = fig.add_subplot(111, projection=ccrs.PlateCarree())
        super().__init__(fig)
        self.setParent(parent)

        self.satellites = satellites or []
        self.highlighted = None
        self.prediction = None

        self._setup_map()
        self.update_map()

    def _setup_map(self):
        self.ax.set_global()
        self.ax.coastlines()
        self.ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        self.ax.gridlines(draw_labels=True)

    def update_map(self):
        self.ax.clear()
        self._setup_map()

        # plot all satellites
        now = ts.now()
        lats, lons = [], []
        for sat in self.satellites:
            sp = wgs84.subpoint(sat.at(now))
            lats.append(sp.latitude.degrees)
            lons.append(sp.longitude.degrees)
        self.ax.scatter(lons, lats, s=20, c="blue", transform=ccrs.PlateCarree())

        # highlight selected
        if self.highlighted:
            sp = wgs84.subpoint(self.highlighted.at(now))
            self.ax.scatter(sp.longitude.degrees, sp.latitude.degrees,
                            s=60, c="yellow", edgecolor="black",
                            transform=ccrs.PlateCarree(), zorder=5)

        # show prediction
        if self.prediction:
            sat, t2 = self.prediction
            now = ts.now()
            sp2 = wgs84.subpoint(sat.at(t2))
            self.ax.scatter(sp2.longitude.degrees, sp2.latitude.degrees,
                            s=60, c="red", edgecolor="black",
                            transform=ccrs.PlateCarree(), zorder=5)

            # path
            times = ts.linspace(now, t2, 200)
            path = [wgs84.subpoint(sat.at(t)) for t in times]
            lats = [p.latitude.degrees for p in path]
            lons = [p.longitude.degrees for p in path]
            self.ax.plot(lons, lats, c="cyan", linewidth=2,
                         transform=ccrs.PlateCarree())

        self.draw()

    def set_satellites(self, satellites):
        self.satellites = satellites
        self.update_map()

    def highlight_satellite(self, sat):
        self.highlighted = sat
        self.update_map()

    def show_prediction(self, sat, t2):
        self.prediction = (sat, t2)
        self.update_map()
