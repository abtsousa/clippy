import logging as log

#Config
import config

class LoginError(Exception):
    """
    Raised when the login fails.

    Attributes:
        message (str): A custom error message (optional).
    """
    def __init__(self, message="Erro de login"):
        log.error(message)