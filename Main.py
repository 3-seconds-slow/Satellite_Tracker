import Satellite_list
import Database
from PySide6.QtWidgets import QApplication
import sys


testing = False
db_filename = "Satellite_data"

if __name__ == "__main__":
    Database.create_database(db_filename, testing)
    app = QApplication(sys.argv)
    window = Satellite_list.App()
    window.show()
    sys.exit(app.exec())

