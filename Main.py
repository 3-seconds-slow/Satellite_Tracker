import Download_data
from skyfield.api import load, wgs84
from skyfield.iokit import parse_tle_file
import plotly.graph_objects as go
import plotly.io as pio
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QDialog
)
from PySide6.QtWebEngineWidgets import QWebEngineView
import sys

data = []

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Satellite Tracker")
        self.setGeometry(100, 100, 800, 400)

        main_layout = QVBoxLayout(self)
        content_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()

        # Left side: Table and search
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.update_table)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Constellation", "Number Visible"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        left_layout.addWidget(self.search_bar)
        left_layout.addWidget(self.table)

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

        content_layout.addWidget(left_widget, 1)
        content_layout.addWidget(right_widget, 1)
        main_layout.addLayout(content_layout)
        main_layout.addLayout(bottom_layout)

        self.update_table()
        self.update_chart()

    def update_table(self):
        filter_text = self.search_bar.text().lower()
        self.table.setRowCount(0)
        for constellation, visible in data:
            if filter_text in constellation.lower():
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                self.table.setItem(row_position, 0, QTableWidgetItem(constellation))
                self.table.setItem(row_position, 1, QTableWidgetItem(str(visible)))

    def update_chart(self):
        items = [row[0] for row in data]
        values = [row[1] for row in data]
        fig = go.Figure(data=[go.Bar(x=items, y=values)])
        fig.update_layout(title="Inventory Chart")

        html = pio.to_html(fig, full_html=False)
        self.webview.setHtml(html)

    ##@Slot()
    def download_data(self):
        dlg = Download_data.DownloadData(self)
        if dlg.exec():
            print("Success!")
        else:
            print("Cancel!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())