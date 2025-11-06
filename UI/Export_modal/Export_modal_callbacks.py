import webview
from dash import Input, Output, State, dcc
from dash.exceptions import PreventUpdate
from Models.Database import get_satellite_data
import json


def register_export_modal_callbacks(app):
    @app.callback(
        Output("export-modal", "is_open"),
        [Input("open-export-modal", "n_clicks"),
         Input("close-export-modal", "n_clicks"),
         Input("confirm-export", "n_clicks")],
        State("export-modal", "is_open"),
    )
    def toggle_export_modal(open_click, close_click, confirm_click, is_open):
        if open_click or close_click:
            return not is_open
        return is_open

    @app.callback(
        Output("export-data", "data"),
        Input("confirm-export", "n_clicks"),
        State("export-choice", "value"),
        State("satellite-table", "derived_virtual_data"),
        prevent_initial_call=True
    )
    def export_tle(n_clicks, choice, filtered_data):

        if not n_clicks:
            raise PreventUpdate

        if choice == "all":
            print("export all")
            satellite_data = get_satellite_data()
        else:
            print("export selected")
            id_list = [row["OBJECT_ID"] for row in filtered_data]
            satellite_data = get_satellite_data(id_list)

        print(satellite_data)
        # Build TLE text string
        lines = []
        for name, line1, line2 in satellite_data:
            lines.append(f"{name}\n{line1}\n{line2}\n")

        content = "".join(lines)
        return content

    '''
    The clientside_callback is used to execute a javascript function in the user's browser. In this case, the browser is 
    the PyWebview that the dash app is running in, and the function passes the contents of the file to be saved to the
    save_file api located in the main file.  
    '''
    app.clientside_callback(
        """
        function(content) {
            if (!content) return;

            window.pywebview.api.save_file(content);
            return null;
        }
        """,
        Output("export-data", "clear"),
        Input("export-data", "data")
    )