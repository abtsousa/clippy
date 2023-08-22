import logging as log

#Config
import config as cfg

class LoginError(Exception):
    """
    Raised when the login fails.

    Attributes:
        message (str): A custom error message (optional).
    """
    def __init__(self, message="Erro de login"):
        cfg.update_credentials(None,None) # reset wrong credentials
        log.error(message)