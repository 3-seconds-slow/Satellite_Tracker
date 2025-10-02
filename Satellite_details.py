from Visualisations.GlobeWidget import GlobeWidget
from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import QDialog, QVBoxLayout, QGridLayout, QLabel, QScrollArea, QWidget, QHBoxLayout, \
    QDateTimeEdit, QPushButton
from skyfield.api import wgs84, load
from datetime import timezone

ts = load.timescale()

class SatelliteDetailsDialog(QDialog):
    def __init__(self, sat, parent=None):
        super().__init__(parent)
        self.sat = sat
        self.setWindowTitle(f"Satellite Details: {sat.name}")
        self.resize(900, 700)

        layout = QVBoxLayout(self)

        # --- Scroll area for fields ---
        scroll = QScrollArea()
        fields_widget = QWidget()
        fields_layout = QGridLayout(fields_widget)

        fields = self.satellite_fields(sat)

        # Add each field to the grid
        row = 0
        for key, value in fields.items():
            fields_layout.addWidget(QLabel(f"{key}:"), row, 0)
            fields_layout.addWidget(QLabel(str(value)), row, 1)
            row += 1

        scroll.setWidget(fields_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll, stretch=2)

        # --- Prediction controls ---
        controls = QHBoxLayout()

        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        controls.addWidget(QLabel("Prediction Time:"))
        controls.addWidget(self.datetime_edit)

        self.predict_btn = QPushButton("Predict")
        controls.addWidget(self.predict_btn)


        self.lat_label = QLabel("Lat: —")
        self.lon_label = QLabel("Lon: —")
        controls.addWidget(self.lat_label)
        controls.addWidget(self.lon_label)

        layout.addLayout(controls)

        # Connect button click
        self.predict_btn.clicked.connect(self.update_prediction)

        # Connect changes
        # self.datetime_edit.dateTimeChanged.connect(self.update_prediction)

        # --- Globe widget showing only this satellite ---
        self.globe = GlobeWidget([sat])
        layout.addWidget(self.globe, stretch=3)

    def satellite_fields(self, sat):
        """Return dict of sat fields + computed values."""
        fields = {}

        # Standard Skyfield info
        fields["Name"] = sat.name
        fields["NORAD ID"] = sat.model.satnum
        fields["Classification"] = getattr(sat.model, "classification", "?")
        fields["Epoch"] = sat.epoch
        fields["International Designator"] = sat.model.intldesg

        # All fields from the SGP4 model
        # for key, value in vars(sat.model).items():
        #     fields[key] = value

        # Computed values
        now = ts.now()
        geocentric = sat.at(now)
        subpoint = wgs84.subpoint(geocentric)
        fields["Latitude (deg)"] = round(subpoint.latitude.degrees, 4)
        fields["Longitude (deg)"] = round(subpoint.longitude.degrees, 4)
        fields["Altitude (km)"] = round(subpoint.elevation.km, 2)

        # Example observer: lat=0, lon=0
        observer = wgs84.latlon(0, 0)
        topocentric = (sat - observer).at(now)
        alt, az, dist = topocentric.altaz()
        fields["Azimuth (deg)"] = round(az.degrees, 2)
        fields["Elevation (deg)"] = round(alt.degrees, 2)
        fields["Distance (km)"] = round(dist.km, 2)

        return fields

    def update_prediction(self):
        qdt = self.datetime_edit.dateTime()
        print(qdt)
        dt = qdt.toPython().astimezone(timezone.utc)  # gives a Python datetime
        print(dt)
        t2 = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

        # Skyfield needs UTC
        # t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        geocentric = self.sat.at(t2)
        lat, lon = wgs84.latlon_of(geocentric)

        # lat = round(subpoint.latitude.degrees, 4)
        # lon = round(subpoint.longitude.degrees, 4)

        self.lat_label.setText(f"Lat: {lat.degrees}°")
        self.lon_label.setText(f"Lon: {lon.degrees}°")

        now = ts.now()
        self.globe.highlight_prediction(self.sat, now, t2)
