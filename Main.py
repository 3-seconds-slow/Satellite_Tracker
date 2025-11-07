import sys
import threading, webview
import dash
from Models import Database
from Models.Database import get_satellite_list
from UI.Satellite_list_layout import create_home_screen
from UI.Satellite_list_callbacks import register_home_screen_callbacks
from UI.Download_modal.Download_modal_callbacks import register_download_modal_callbacks
from UI.Details_modal.Details_modal_callbacks import register_details_modal_callbacks
from UI.Import_modal.Import_modal_callbacks import register_import_modal_callbacks
from UI.Export_modal.Export_modal_callbacks import register_export_modal_callbacks


testing = False #True: use an in memory database for testing.   False: use a file based DB
db_filename = "Satellite_data"



class API:
    def save_file(self, content):
        """
        This function is used to access the save file dialog for exporting files. PyWebView doesn't expose the apis
        used for downloading files, so to transfer files from the dash app to the local storage I use the clientside_callback
        in the export_modal_callbacks file to pass a string the contains the data to be saved in a file to this api, which opens
        the file dialog and writes the data to a file.

        :return: filepath or ""
        """
        window = webview.windows[0]

        result = window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename="satellites.tle",
            file_types=("TLE Files (*.tle)", "Text Files (*.txt)")
        )

        if result and len(result) > 0:
            filepath = result[0]
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return filepath

        return ""

def run_dash():
    """
    Initiates the dash app

    Loads satellites from the database into memory, creates the home screen of the program and registers all the
    callback functions so they can be accessed from their respective screens or modals.

    """
    satellites = get_satellite_list()
    app = dash.Dash(__name__)
    app.layout = create_home_screen(satellites)

    register_home_screen_callbacks(app)
    register_download_modal_callbacks(app)
    register_details_modal_callbacks(app)
    register_import_modal_callbacks(app)
    register_export_modal_callbacks(app)

    app.run(debug=False, port=8050)

if __name__ == "__main__":
    """
    Program entry point
    
    The satellite tracking app is a locally run dash web app, being displayed using PyWebview so that it functions like 
    a regular desktop app. 
    
    The database is created here, a thread to run the dash app is started, and the program window is opened
    """
    Database.create_database(db_filename, testing)
    t = threading.Thread(target=run_dash, daemon=True)
    t.start()

    api = API()
    webview.create_window(
        "Satellite Tracker",
        "http://127.0.0.1:8050",
        js_api=api
    )
    webview.start()
    sys.exit()