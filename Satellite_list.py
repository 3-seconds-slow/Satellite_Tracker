import Download_data
import Database
from Satellite_details import SatelliteDetailsDialog
from Models.Table_model import SkyfieldSatelliteModel
from Models.Proxy_model import ProxyModel
from Visualisations.GlobeWidget import GlobeWidget
from Visualisations.MapWidget import MapWidget
from Visualisations.MapWidget2 import FoliumMapWidget
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTableView, QDialog, QLabel, QStackedWidget
)
from skyfield.api import load, wgs84

ts = load.timescale()

'''
This is the main interface for the satellite tracker.
It has 3 main sections: the list of satellites in the database that can be filtered and searched, 
a visualisation of the satellites in the list in orbit, and a collection of import and export function buttons
'''

class App(QWidget):
    def __init__(self):
        super().__init__()
        df = [["OBJECT_ID", "OBJECT_NAME", "updated"]]
        satellites = Database.get_satellite_list()
        self.model = SkyfieldSatelliteModel(satellites)

        self.setWindowTitle("Satellite Tracker")
        # self.setGeometry(100, 100, 800, 400)

        # main_layout contains the top level elements in the main window: content_layout and bottom_layout
        main_layout = QHBoxLayout(self)
        # content_layout contains the table_layout and visualisation_layout
        # content_layout = QHBoxLayout()
        # bottom_layout contains the buttons at the bottom of the window
        bottom_layout = QHBoxLayout()

        # the table_layout contains a table for
        table_layout = QVBoxLayout()
        # Search box

        self.table = QTableView()
        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()

        # selection_model = self.table.selectionModel()
        # selection_model.selectionChanged.connect(self.on_table_selection_changed)

        # Proxy model (adds sorting & filtering)
        self.proxy_model = ProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(0)  # search all columns

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search satellites...")
        self.search_box.textChanged.connect(self.proxy_model.setFilterFixedString)

        self.table.setSortingEnabled(True)
        self.table.setModel(self.proxy_model)

        # disconnect old selection model if needed
        if hasattr(self, "_selection_connection"):
            try:
                self._selection_connection.disconnect()
            except Exception:
                pass

        # connect new one
        sel_model = self.table.selectionModel()
        self._selection_connection = sel_model.selectionChanged.connect(
            self.on_table_selection_changed
        )


        table_layout.addWidget(self.search_box)
        table_layout.addWidget(self.table)

        # --- Controls ---
        controls_layout = QHBoxLayout()
        # main_layout.addLayout(controls_layout)

        controls_layout.addWidget(QLabel("Latitude:"))
        self.lat_input = QLineEdit("-33.883948")
        controls_layout.addWidget(self.lat_input)

        controls_layout.addWidget(QLabel("Longitude:"))
        self.lon_input = QLineEdit("151.199652")
        controls_layout.addWidget(self.lon_input)

        filter_btn = QPushButton("Filter by Location")
        controls_layout.addWidget(filter_btn)
        filter_btn.clicked.connect(self.filter_by_location)

        clear_btn = QPushButton("Clear Filter")
        controls_layout.addWidget(clear_btn)
        clear_btn.clicked.connect(self.clear_filter)



        # left_widget = QWidget()
        # left_layout = QVBoxLayout(left_widget)
        # self.search_bar = QLineEdit()
        # self.search_bar.setPlaceholderText("Search...")
        # self.search_bar.textChanged.connect(self.update_table)
        #
        # self.table = QTableWidget(0, 3)
        # self.table.setHorizontalHeaderLabels(["ID Number", "Name", "Group"])
        # self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        #
        # left_layout.addWidget(self.search_bar)
        # left_layout.addWidget(self.table)

        self.view_toggle = QPushButton("Toggle View")
        self.view_toggle.clicked.connect(self.toggle_view)

        # Right side: Chart

        self.stack = QStackedWidget()
        self.globe = GlobeWidget(satellites)
        self.map = MapWidget(satellites)
        self.map_container = QWidget()
        self.map_layout = QVBoxLayout(self.map_container)
        self.map_toolbar = NavigationToolbar2QT(self.map, self)
        self.map_layout.addWidget(self.map_toolbar)
        self.map_layout.addWidget(self.map)
        self.map2 = FoliumMapWidget(satellites)
        self.stack.addWidget(self.globe)
        # self.stack.addWidget(self.map_container)
        self.stack.addWidget(self.map2)
        self.stack.setCurrentWidget(self.map2)

        right_layout = QVBoxLayout()
        right_layout.addLayout(controls_layout)
        right_layout.addWidget(self.view_toggle)
        right_layout.addWidget(self.stack)


        # Bottom buttons
        web_import_btn = QPushButton("Download data")
        web_import_btn.clicked.connect(self.download_data)
        bottom_layout.addWidget(web_import_btn)
        file_import_btn = QPushButton("Import from file")
        bottom_layout.addWidget(file_import_btn)
        export_btn = QPushButton("Export to file")
        bottom_layout.addWidget(export_btn)

        right_layout.addLayout(bottom_layout)
        main_layout.addLayout(table_layout, 1)
        main_layout.addLayout(right_layout, 1)


        self.proxy_model.layoutChanged.connect(self.update_globe_from_table)
        self.proxy_model.modelReset.connect(self.update_globe_from_table)
        self.proxy_model.satellites_changed.connect(self.update_globe_from_table)
        self.table.doubleClicked.connect(self.open_satellite_details)

        # self.update_table()
        # self.update_chart()


    def refresh_table(self):
        print("Refreshing table")
        satellites = Database.get_satellite_list()
        self.model.updateData(satellites)
        print("adding: ", satellites)

    def filter_by_location(self):
        try:
            lat = float(self.lat_input.text())
            lon = float(self.lon_input.text())
        except ValueError:
            print("Invalid coordinates")
            return
        print("set observer ", lat, lon)
        self.proxy_model.setObserver(lat, lon)

    def clear_filter(self):
        self.proxy_model.setObserver(None, None)

    def update_globe_from_table(self):
        filtered_sats = []
        for r in range(self.proxy_model.rowCount()):
            src_row = self.proxy_model.mapToSource(self.proxy_model.index(r, 0)).row()
            sat = self.model.satellites[src_row]  # grab the actual EarthSatellite object
            filtered_sats.append(sat)

        self.stack.currentWidget().set_satellites(filtered_sats)

    # def update_table(self):
    #     filter_text = self.search_bar.text().lower()
    #     self.table.setRowCount(0)
    #     for constellation, visible in data:
    #         if filter_text in constellation.lower():
    #             row_position = self.table.rowCount()
    #             self.table.insertRow(row_position)
    #             self.table.setItem(row_position, 0, QTableWidgetItem(constellation))
    #             self.table.setItem(row_position, 1, QTableWidgetItem(str(visible)))
    #
    # def update_chart(self):
    #     items = [row[0] for row in data]
    #     values = [row[1] for row in data]
    #     fig = go.Figure(data=[go.Bar(x=items, y=values)])
    #     fig.update_layout(title="Inventory Chart")
    #
    #     html = pio.to_html(fig, full_html=False)
    #     self.webview.setHtml(html)

    def on_table_selection_changed(self, selected, deselected):
        if not selected.indexes():
            return

        # get first selected row (proxy -> source)
        proxy_index = selected.indexes()[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        row = source_index.row()

        sat = self.model.satellites[row]
        print(f"Selected satellite: {sat.name}")

        # tell globe to highlight this sat
        self.stack.currentWidget().highlight_satellite(sat)

    def open_satellite_details(self, index):
        # Map from proxy → source
        source_index = self.proxy_model.mapToSource(index)
        row = source_index.row()
        sat = self.model.satellites[row]

        dlg = SatelliteDetailsDialog(sat, parent=self)
        dlg.exec()

    ##@Slot()
    def download_data(self):
        dlg = Download_data.DownloadData(self)
        if dlg.exec():
            self.refresh_table()
            print("Success!")
        else:
            print("Cancel!")

    def toggle_view(self):
        if self.stack.currentWidget() is self.globe:
            self.stack.setCurrentWidget(self.map2)
        else:
            self.stack.setCurrentWidget(self.globe)

