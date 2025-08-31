import requests
import Database
from PySide6.QtWidgets import QDialog, QLineEdit, QPushButton, QGridLayout, QDialogButtonBox, QComboBox, \
    QLabel, QMessageBox


class DownloadData(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Data")

        fieldLabel = QLabel("Category:")
        self.searchField = QComboBox()
        self.searchField.addItems(["Catalog Number", "International Designator", "Group", "Name"])

        self.searchTerm = QLineEdit()
        self.searchTerm.setPlaceholderText("Enter search term...")

        downloadBtn = QPushButton("Download")
        buttonBox = QDialogButtonBox()
        buttonBox.addButton(downloadBtn, QDialogButtonBox.ButtonRole.AcceptRole)
        downloadBtn.clicked.connect(self.handleDownload)


        layout = QGridLayout()
        layout.addWidget(fieldLabel, 0, 0)
        layout.addWidget(self.searchField, 0, 1)
        layout.addWidget(self.searchTerm, 1, 0, 1, 2)
        layout.addWidget(buttonBox, 2, 0, 2, 2)
        self.setLayout(layout)

    def handleDownload(self):
        field_index = self.searchField.currentIndex()
        term = self.searchTerm.text().strip()

        if not term:
            QMessageBox.warning(self, "Input Error", "Please enter a search term.")
            return

        try:
            response = self.getData(field_index, term)
        except Exception as e:
            QMessageBox.critical(self, "Download Failed", f"Error: {e}")

        Database.save(response.json())


    def getData(self, searchField, searchTerm):
        Query = ["CATNR", "INTDES", "GROUP", "NAME"]

        base = 'https://celestrak.org/NORAD/elements/gp.php'
        url = base + f'?{Query[searchField]}={searchTerm}&FORMAT=json'

        print("downloading from " + url)
        response = requests.get(url)
        return response


        # if not load.exists(name) or load.days_old(name) >= max_days:
        #     load.download(url, filename=name)
        #     QMessageBox.information(self, "Success", "Data downloaded!")
        #     self.accept()



