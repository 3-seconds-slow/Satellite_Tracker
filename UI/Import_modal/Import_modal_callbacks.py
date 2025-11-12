from datetime import datetime
from dash import Input, Output, State, no_update
from dash.exceptions import PreventUpdate
from Models.Database import save
import base64, logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename="log.txt", format='%(asctime)s - %(levelname)s:%(message)s', level=logging.INFO)


def register_import_modal_callbacks(app):
    """
    registers the callbacks used in the import modal

    :param app: the dash app where these callback will be run
    """
    @app.callback(
        Output("import-modal", "is_open"),
        [Input("open-import-modal", "n_clicks"),
         Input("close-import-modal", "n_clicks")],
        State("import-modal", "is_open")
    )
    def toggle_import_modal(open_click, close_click, is_open):
        """
        Opens and closes the modal

        :param open_click: registers when the import file button is clicked
        :param close_click: registers when the closed button is clicked
        :param is_open: bool signifying if the import modal is open
        :return: is_open: bool signifying if the import modal is open
        """
        if open_click or close_click:
            return not is_open
        return is_open


    @app.callback(
        Output("import-status-text", "children"),
        Output("import-status-text", "is_open"),
        Output("db-refresh-signal", "data", allow_duplicate=True),
        Input("tle-upload", "contents"),
        State("tle-upload", "filename"),
        background=True,
        running=[
            (Output("cancel-import-btn", "disabled"), False, True),
            (
                    Output("import-progress-bar", "style"),
                    {"visibility": "visible"},
                    {"visibility": "hidden"},
            ),
        ],
        cancel=[Input("cancel-import-btn", "n_clicks")],
        progress=[Output("import-progress-bar", "value"),
                  Output("import-progress-bar", "max")],
        prevent_initial_call=True
    )
    def import_tle(set_progress, contents, filename):
        """
        Processes the contents of a file loaded into the upload component of the import modal, then pass it to the
        database to be saved
        :param set_progress: function for filling the progress bar
        :param contents: contents of the file
        :param filename: name of the file
        :return: HTML element containing the outcome of the import
        """
        logger.info("importing file: %s", filename)
        set_progress((1, 3))
        if not contents:
            raise PreventUpdate

        try:
            # print("contents", contents)
            logger.info("processing file")
            data = contents.split(",")[1]
            # print("data", data)
            text = base64.b64decode(data)
            # print("text", text)
            set_progress((2, 3))
        except Exception as e:
            logger.error(e)
            return f"error reading file {filename}: {e}", True, no_update

        try:
            logger.info("sending file data to database")
            count = save(text)
            set_progress((3, 3))
        except Exception as e:
            logger.error(e)
            return f"error importing file {filename}: {e}", True, no_update

        logger.info("file saved")
        return  f"Imported {count} satellites from {filename}", True, datetime.now()