import logging as log
from handlers.creds_handler import reset_login
from handlers.exit_handler import ExitHandler

class EmptyHTMLException(Exception):
    """
    Raised when the retrieved HTML page is empty.

    Attributes:
        message (str): A custom error message (optional).
    """
    def __init__(self, message="A página obtida está vazia. A(s) cadeira(s) solicitada(s) não existe(m) ou o servidor pode estar com problemas técnicos. Verifique se os parâmetros introduzidos estão correctos e tente novamente mais tarde."):
        reset_login()
        log.error(message)
        raise ExitHandler(0)