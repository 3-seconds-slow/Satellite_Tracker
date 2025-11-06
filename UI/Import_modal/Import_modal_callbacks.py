from datetime import datetime

from dash import Input, Output, State
from dash.exceptions import PreventUpdate
from Models.Database import save
import base64


def register_import_modal_callbacks(app):
    @app.callback(
        Output("import-modal", "is_open"),
        [Input("open-import-modal", "n_clicks"),
         Input("close-import-modal", "n_clicks")],
        State("import-modal", "is_open")
    )
    def toggle_import_modal(open_click, close_click, is_open):
        if open_click or close_click:
            return not is_open
        return is_open


    @app.callback(
        Output("import-status", "children"),
        Output("db-refresh-signal", "data", allow_duplicate=True),
        Input("tle-upload", "contents"),
        State("tle-upload", "filename"),
        prevent_initial_call=True
    )
    def import_tle(contents, filename):
        if not contents:
            raise PreventUpdate

        try:
            print("contents", contents)
            data = contents.split(",")[1]
            print("data", data)
            text = base64.b64decode(data) #.decode("utf-8", errors="replace")
            print("text", text)
        except Exception as e:
            return f"error reading file {filename}: {e}"

        try:
            count = save(text)
        except Exception as e:
            return f"error importing file {filename}: {e}"

        return  f"Imported {count} satellites from {filename}", datetime.now()