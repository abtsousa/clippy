import logging as log
import typer
import sys

class ExitHandler(Exception):
    """
    Raised when the retrieved HTML page is empty.

    Attributes:
        message (str): A custom error message (optional).
    """
    def __init__(self, code: int):
        if getattr(sys, 'frozen', False):
            log.debug("A correr a partir de EXE!")
            input("Pressiona ENTER para terminar o programa.")
        else:
            log.debug("A correr a partir de script, a terminar o programa automaticamente...")
        raise typer.Exit(code)