import Download_data
import Database
import pandas as pd
from Models.Pandas_model import PandasModel
from Models.Proxy_model import ProxyModel
from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTableView, QDialog
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from Models.Proxy_model import ProxyModel

# data = pd.DataFrame([
#     [4, 9, 2],
#     [1, 0, 0],
#     [3, 5, 0],
#     [3, 3, 2],
#     [7, 8, 9],
# ], columns = ['A', 'B', 'C'], index=['Row 1', 'Row 2', 'Row 3', 'Row 4', 'Row 5'])

'''
This is the main interface for the satellite tracker.
It has 3 main sections: the list of satellites in the database that can be filtered and searched, 
a visualisation of the satellites in the list in orbit, and a collection of import and export function buttons
'''

class App(QWidget):
    def __init__(self):
        super().__init__()
        df = [["OBJECT_ID", "OBJECT_NAME", "updated"]]
        satellites_df = Database.get_satellite_list()
        self.model = PandasModel(satellites_df)

        self.setWindowTitle("Satellite Tracker")
        self.setGeometry(100, 100, 800, 400)

        # main_layout contains the top level elements in the main window: content_layout and bottom_layout
        main_layout = QVBoxLayout(self)
        # content_layout contains the table_layout and visualisation_layout
        content_layout = QHBoxLayout()
        # bottom_layout contains the buttons at the bottom of the window
        bottom_layout = QHBoxLayout()

        # the table_layout contains a table for
        table_layout = QVBoxLayout()
        # Search box

        self.table = QTableView()

        # Proxy model (adds sorting & filtering)
        self.proxy_model = ProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(-1)  # search all columns

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search satellites...")
        self.search_box.textChanged.connect(self.proxy_model.setFilterFixedString)

        self.table.setSortingEnabled(True)
        self.table.setModel(self.proxy_model)


        table_layout.addWidget(self.search_box)
        table_layout.addWidget(self.table)


        #
        # # Table view
        # self.table_view = QTableView()
        # self.table_view.setModel(self.proxy_model)
        # self.table_view.setSortingEnabled(True)
        # self.table_view.resizeColumnsToContents()
        #
        # table_layout.addWidget(self.search_box)
        # table_layout.addWidget(self.table_view)
        # self.setLayout(table_layout)





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

        # Right side: Chart
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        self.webview = QWebEngineView()
        right_layout.addWidget(self.webview)


        # Bottom buttons
        web_import_btn = QPushButton("Download data")
        web_import_btn.clicked.connect(self.download_data)
        bottom_layout.addWidget(web_import_btn)
        file_import_btn = QPushButton("Import from file")
        bottom_layout.addWidget(file_import_btn)
        export_btn = QPushButton("Export to file")
        bottom_layout.addWidget(export_btn)

        content_layout.addLayout(table_layout)
        content_layout.addWidget(right_widget, 1)
        main_layout.addLayout(content_layout)
        main_layout.addLayout(bottom_layout)

        # self.update_table()
        # self.update_chart()

    def refresh_table(self):
        print("Refreshing table")
        satellites_df = Database.get_satellite_list()
        self.model.updateData(satellites_df)

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

    ##@Slot()
    def download_data(self):
        dlg = Download_data.DownloadData(self)
        if dlg.exec():
            self.refresh_table()
            print("Success!")
        else:
            print("Cancel!")
