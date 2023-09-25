#Config
import clippy.config as cfg
import logging as log
from modules.EmptyHTMLException import EmptyHTMLException

def get_html(url: str):
    """
    Retrieve the HTML content of a given URL.

    Parameters:
        url (str): The URL to fetch.

    Returns:
        str: The HTML content of the URL.
    """
    response = cfg.session.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    log.debug(f"[HTML] Received HTML for {url}:\n\n{response.text}")
    if len(response.text) == 0: raise EmptyHTMLException
    return response.text
