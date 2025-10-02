from PySide6.QtCore import QAbstractTableModel, Qt, Signal
from skyfield.api import load, wgs84

ts = load.timescale()

class SkyfieldSatelliteModel(QAbstractTableModel):
    satellites_changed = Signal(list)

    def __init__(self, satellites, parent=None):
        super().__init__(parent)
        self.satellites = satellites
        print(self.satellites)
        self.headers = ["Name", "Catalog ID", "Latitude", "Longitude", "Altitude", "Visible"]


    def rowCount(self, parent=None):
        return len(self.satellites)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None

        now = ts.now()
        sat = self.satellites[index.row()]
        print(sat)
        col = index.column()
        geocentric = sat.at(now)
        lat, lon = wgs84.latlon_of(geocentric)
        alt = wgs84.height_of(geocentric)
        #print("data() called:", index.row(), index.column())
        location = wgs84.latlon(-33.883948, +151.199652)
        difference = sat - location
        topocentric = difference.at(now)
        altitude, azimuth, distance = topocentric.altaz()

        if altitude.degrees > 0:
            visible = "True"
        else:
            visible = "False"

        match col:
            case 0:
                return sat.name
            case 1:
                return sat.model.satnum
            case 2:
                formatLat = "{:4.4f}".format(lat.degrees)
                return formatLat
            case 3:
                formatLon = "{:4.4f}".format(lon.degrees)
                return str(formatLon)
            case 4:
                formatAlt = "{:4.4f}".format(alt.km)
                return str(formatAlt)
            case 5:
                return visible
            case _:
                return None


        # if col == 0:
        #     return sat.name
        # elif col == 1:
        #     return sat.model.satnum
        # elif col in (2, 3, 4):
        #     # Calculate lat/lon/alt
        #     now = ts.now()
        #     geocentric = sat.at(now)
        #     subpoint = wgs84.subpoint(geocentric)
        #     print(subpoint)
        #     if col == 3:
        #         return round(subpoint.latitude.degrees, 2)
        #     elif col == 4:
        #         return round(subpoint.longitude.degrees, 2)
        #     elif col == 5:
        #         return round(subpoint.elevation.km, 2)
        # return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def updateData(self, new_satellites):
        self.beginResetModel()
        self.satellites = new_satellites
        self.endResetModel()
        self.satellites_changed.emit(self.satellites)