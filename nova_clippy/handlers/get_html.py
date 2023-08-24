#Config
import nova_clippy.config as cfg

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
    return response.text
