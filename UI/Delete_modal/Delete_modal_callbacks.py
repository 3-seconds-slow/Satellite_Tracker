from dash import Input, Output, State, ctx
from Models.Database import delete_all_satellites
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename="log.txt", format='%(asctime)s - %(levelname)s:%(message)s', level=logging.INFO)

def register_delete_modal_callbacks(app):
    @app.callback(
        Output("delete-modal", "is_open"),
        [Input("open-delete-modal", "n_clicks"),
         Input("cancel-delete", "n_clicks"),
         Input("confirm-delete", "n_clicks")],
        State("delete-modal", "is_open"),
        prevent_initial_call=True
    )
    def toggle_delete_all_modal(open_click, cancel_click, confirm_click, is_open):
        """
        Opens and closes the delete modal
        :param open_click: property to detect the open modal button click
        :param cancel_click: property to detect the cancel button click
        :param confirm_click: property to detect the confirm button click
        :param is_open: bool representing if the delete modal is open
        """
        print("opening delete modal")
        if ctx.triggered_id == "open-delete-modal":
            return True
        return False

    @app.callback(
        Output("db-refresh-signal", "data", allow_duplicate=True),
        Input("confirm-delete", "n_clicks"),
        prevent_initial_call=True
    )
    def delete_all_records(confirm_click):
        """
        deletes all records from the database
        :param confirm_click: property to detect the confirm button click
        :return: signal to refresh the database
        """
        logger.info("delete all confirmed")
        delete_all_satellites()
        return {"refresh": True}


