from dash import Input, Output, State
from dash.exceptions import PreventUpdate
from Models.Database import get_satellite_data
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename="log.txt", format='%(asctime)s - %(levelname)s:%(message)s', level=logging.ERROR)

def register_export_modal_callbacks(app):
    """
    registers the callbacks used in the export modal

    :param app: the dash app where these callback will be run
    """
    @app.callback(
        Output("export-modal", "is_open"),
        [Input("open-export-modal", "n_clicks"),
         Input("close-export-modal", "n_clicks")],
        State("export-modal", "is_open"),
    )
    def toggle_export_modal(open_click, close_click, is_open):
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
        Output("export-data", "data"),
        Input("confirm-export", "n_clicks"),
        State("export-choice", "value"),
        State("satellite-table", "derived_virtual_data"),
        prevent_initial_call=True
    )
    def export_tle(n_clicks, choice, filtered_data):
        """
        Gets the requested satellite data from the database and converts it into a TLE format string to be written to a
        file
        :param n_clicks: property used to track the clicks on confirm export
        :param choice: the input from a pair of radio buttons asking the user if they'd like to export the whole
        database of just the current selection
        :param filtered_data: the currently displayed data
        :return: content: a string containing the TLE formatted data
        """
        logger.info("exporting file")
        if not n_clicks:
            raise PreventUpdate

        if choice == "all":
            # print("export all")
            satellite_data = get_satellite_data()
        else:
            # print("export selected")
            id_list = [row["OBJECT_ID"] for row in filtered_data]
            satellite_data = get_satellite_data(id_list)

        # print(satellite_data)
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
            
            let filename = "satellites.txt";
            window.pywebview.api.save_file(content, filename);
            return null;
        }
        """,
        Output("export-data", "clear"),
        Input("export-data", "data")
    )