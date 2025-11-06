from dash import Input, Output, State, ctx, no_update
import requests
from Models import Database

def register_download_modal_callbacks(app):
    @app.callback(
        [Output("search-term", "valid"),
         Output("search-term", "invalid")],
        Input("search-term", "value")
    )
    def validate_search_term(value):
        if value and value.strip():
            return True, False
        return False, True

    @app.callback(
        [Output("download-modal", "is_open"),
         Output("db-refresh-signal", "data"),
         Output("download-error", "is_open"),
         Output("download-error", "children")
         ],
        [Input("open-download-modal", "n_clicks"),
         Input("cancel-btn", "n_clicks"),
         Input("download-btn", "n_clicks")],
        [State("search-field", "value"),
         State("search-term", "value"),
         State("download-modal", "is_open"),
         State("db-refresh-signal", "data")]
    )
    def toggle_modal(open_click, cancel_click, download_click, field, term, is_open, refresh_count):
        button_id = ctx.triggered_id
        if button_id == "open-download-modal":
            return True, refresh_count, False, no_update
        elif button_id == "cancel-btn":
            return False, refresh_count, False, no_update
        elif button_id == "download-btn":
            try:
                success = download_data(field, term)
                return False, refresh_count + 1, False, no_update
            except ConnectionError:
                return is_open, refresh_count, True, "Unable to connect to Celestrak. Check your internet connection."
            except ValueError as e:
                return is_open, refresh_count, True, f"Invalid search term: {e}"
            except Exception as e:
                print("Download failed:", e)
                return is_open, refresh_count, True, f"Error saving to database: {e}"
        return is_open, refresh_count, False, no_update



def download_data(field, term):
    base = "https://celestrak.org/NORAD/elements/gp.php"
    url = f"{base}?{field}={term}&FORMAT=tle"
    print("dowloading using: ", field, term)

    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.RequestException:
        raise ConnectionError("Failed to reach Celestrak server.")

    if response.status_code != 200:
        raise ConnectionError(f"Celestrak returned HTTP {response.status_code}.")

    try:
        Database.save(response.content)
    except Exception as e:
        raise Exception(f"Database save failed: {e}")
    return True