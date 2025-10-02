from Models.Table_model import SkyfieldSatelliteModel
from PySide6.QtCore import QSortFilterProxyModel, Qt, Signal, QTimer
from skyfield.api import wgs84, load

ts = load.timescale()

class ProxyModel(QSortFilterProxyModel):
    satellites_changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.observer = None

    def setFilterFixedString(self, pattern: str):
        super().setFilterFixedString(pattern)
        print("Emitting signal 3")
        QTimer.singleShot(2000, self.satellites_changed.emit)

    def setObserver(self, lat=None, lon=None):
        """Enable/disable location filter."""
        if lat is not None and lon is not None:
            self.observer = wgs84.latlon(lat, lon)
            print("Obeserver set")
        else:
            self.observer = None
        self.invalidateFilter()
        QTimer.singleShot(2000, self.satellites_changed.emit)

    # def filterAcceptsRow(self, source_row, source_parent):
    #     super().filterAcceptsRow(source_row, source_parent)
    #     # print("filtering")
    #     self.observer = wgs84.latlon(lat, lon)
    #     sat = model.satellites[source_row]  # your model stores EarthSatellite objects
    #     difference = sat - self.observer
    #     topocentric = difference.at(ts.now())
    #     alt, az, dist = topocentric.altaz()
    #     if alt.degrees <= 0:
    #         return False
    #
    #     return True