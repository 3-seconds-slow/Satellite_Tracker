# import requests
# from Models import Database
# from PySide6.QtWidgets import QDialog, QLineEdit, QPushButton, QGridLayout, QDialogButtonBox, QComboBox, \
#     QLabel, QMessageBox

import dash_bootstrap_components as dbc
from dash import dcc, html

def create_download_modal():
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Download Data")),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col(html.Label("Category:"), width=3),
                dbc.Col(
                    dbc.Select(
                        id="search-field",
                        options=[
                            {"label": "Catalog Number", "value": "CATNR"},
                            {"label": "International Designator", "value": "INTDES"},
                            {"label": "Group", "value": "GROUP"},
                            {"label": "Name", "value": "NAME"}
                        ],
                        value="CATNR"
                    ), width=9)
            ]),
            dbc.Row([
                dbc.Col(dbc.InputGroup([
                    dbc.Input(
                        id="search-term",
                        placeholder="Enter search term...",
                        type="text",
                        valid=False,
                        invalid=False,
                    ),
                    dbc.FormFeedback("Please enter a search term.", type="invalid"),
                ]), width=12)
            ]),
            dbc.Row([
                dbc.Col(dcc.Loading(
                    id="download-loading",
                    type="circle",
                    children=html.Div(id="download-status", className="mt-2")
                ), width=12)
            ]),
            dbc.Row([
                dbc.Col(
                    dbc.Alert(
                        id="download-error",
                        color="danger",
                        dismissable=True,
                        is_open=False,
                        style={"marginTop": "10px"}
                    ), width=12
                )
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Download", id="download-btn", color="primary"),
            dbc.Button("Cancel", id="cancel-btn", color="secondary", className="ms-2"),
        ])
    ], id="download-modal", is_open=False)



# class DownloadData(QDialog):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("Download Data")
#
#         fieldLabel = QLabel("Category:")
#         self.searchField = QComboBox()
#         self.searchField.addItems(["Catalog Number", "International Designator", "Group", "Name"])
#
#         self.searchTerm = QLineEdit()
#         self.searchTerm.setPlaceholderText("Enter search term...")
#
#         downloadBtn = QPushButton("Download")
#         buttonBox = QDialogButtonBox()
#         buttonBox.addButton(downloadBtn, QDialogButtonBox.ButtonRole.AcceptRole)
#         downloadBtn.clicked.connect(self.handleDownload)
#
#
#         layout = QGridLayout()
#         layout.addWidget(fieldLabel, 0, 0)
#         layout.addWidget(self.searchField, 0, 1)
#         layout.addWidget(self.searchTerm, 1, 0, 1, 2)
#         layout.addWidget(buttonBox, 2, 0, 2, 2)
#         self.setLayout(layout)
#
#     def handleDownload(self):
#         field_index = self.searchField.currentIndex()
#         term = self.searchTerm.text().strip()
#
#         if not term:
#             QMessageBox.warning(self, "Input Error", "Please enter a search term.")
#             return
#
#         try:
#             response = self.getData(field_index, term)
#         except Exception as e:
#             QMessageBox.critical(self, "Download Failed", f"Error: {e}")
#
#         try:
#             Database.save(response.json())
#         except Exception as e:
#             QMessageBox.critical(self, "Database Error", f"Error saving data: {e}")
#             return
#
#         # ✅ Show success message and close dialog after user clicks OK
#         QMessageBox.information(self, "Success", "Data downloaded and saved!")
#         self.accept()  # closes the dialog with QDialog.Accepted
#
#
#     def getData(self, searchField, searchTerm):
#         Query = ["CATNR", "INTDES", "GROUP", "NAME"]
#
#         base = 'https://celestrak.org/NORAD/elements/gp.php'
#         url = base + f'?{Query[searchField]}={searchTerm}&FORMAT=json'
#
#         print("downloading from " + url)
#         response = requests.get(url)
#         return response
#
#
#
