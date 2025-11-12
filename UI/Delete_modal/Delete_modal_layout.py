import dash_bootstrap_components as dbc
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename="log.txt", format='%(asctime)s - %(levelname)s:%(message)s', level=logging.INFO)

def create_delete_modal():
    """
    creates a pop-up asking the user for confirmation when they click the delete all satellites button
    :return:
    """
    logger.info("building delete modal layout")
    return dbc.Modal(
        id="delete-modal",
        is_open=False,
        centered=True,
        children=[
            dbc.ModalHeader(dbc.ModalTitle("Confirm Deletion")),
            dbc.ModalBody(
                "Are you sure you want to permanently delete ALL satellite records? "
                "This action cannot be undone."
            ),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="cancel-delete", className="btn-secondary"),
                dbc.Button("Delete", id="confirm-delete", className="btn-danger")
            ])
        ],
    )