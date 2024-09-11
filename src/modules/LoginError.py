import logging as log
from handlers.creds_handler import reset_login

class LoginError(Exception):
    """
    Raised when the login fails.

    Args:
        message (str): A custom error message (optional).
    """
    def __init__(self, message="Erro de login"):
        reset_login()
        log.error(message)