from datetime import datetime
from dash import Input, Output, State, ctx, no_update
import requests, logging
from Models import Database

logger = logging.getLogger(__name__)
logging.basicConfig(filename="log.txt", format='%(asctime)s - %(levelname)s:%(message)s', level=logging.INFO)

def register_download_modal_callbacks(app):
    """
    registers the callbacks used in the download modal

    :param app: the dash app where these callback will be run
    """

    @app.callback(
        Output("download-modal", "is_open"),
        [Input("open-download-modal", "n_clicks"),
         Input("cancel-btn", "n_clicks")],
        State("download-modal", "is_open"),
        prevent_initial_call=True
    )
    def toggle_modal(open_click, cancel_click, is_open):
        if ctx.triggered_id == "open-download-modal":
            return True
        return False


    @app.callback(
        [Output("search-term", "valid"),
         Output("search-term", "invalid")],
        Input("search-term", "value")
    )
    def validate_search_term(value):
        """
        Input validation to ensure a search tem in entered into the field
        :param value: the value of the search input field
        :return:
        """
        if value and value.strip():
            return True, False
        return False, True


    @app.callback(
        Output("download-status-text", "children"),
        Output("download-status-text", "is_open"),
        Output("db-refresh-signal", "data"),
        Input("download-btn", "n_clicks"),
        State("search-field", "value"),
        State("search-term", "value"),
        background=True,
        running=[
            (Output("download-btn", "disabled"), True, False),
            (Output("cancel-btn", "disabled"), False, True),
            (
                Output("progress_bar", "style"),
                {"visibility": "visible"},
                {"visibility": "hidden"},
            ),
        ],
        cancel=[Input("cancel-btn", "n_clicks")],
        progress=[Output("progress_bar", "value"),
                  Output("progress_bar", "max")],
        prevent_initial_call=True
    )
    def start_download(set_progress, n_clicks, field, term):
        logger.info("starting download")
        try:
            set_progress((1, 3))
            response = download_data(field, term)
        except ValueError as e:
            logger.error(e)
            return f"Invalid search term: {e}", True, no_update
        except requests.exceptions.RequestException:
            return "Unable to connect to Celestrak. Check your internet connection.", True, no_update
        except Exception as e:
            logger.error(e)
            raise Exception(f"Download failed: {e}")

        if response.status_code != 200:
            logger.error(f"received response code {response.status_code}")
            return f"Celestrak returned HTTP {response.status_code}.", True, no_update

        try:
            set_progress((2, 3))
            logger.info("sending data to database")
            count = Database.save(response.content)
        except Exception as e:
            logger.error(e)
            return f"Error saving to database: {e}", True, no_update
        set_progress((3, 3))

        logger.info(f"Download complete! Downloaded {count} satellites")
        return f"Download complete! Downloaded {count} satellites", True, datetime.now()


def download_data(field, term):
    """
    This function sends a request to the Celestrak API to download the data using the user provide search field and
    term.

    If the download is successful, the data is sent to be saved in the database
    :param field: the search field
    :param term:  the search term
    :return: a bool represent the success of the download
    """
    base = "https://celestrak.org/NORAD/elements/gp.php"
    url = f"{base}?{field}={term}&FORMAT=tle"
    # print("dowloading using: ", field, term)
    logger.info(f"Requesting data from {url}")

    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.RequestException as e:
        logger.error(e)
        raise ConnectionError("Failed to reach Celestrak server.")

    return response