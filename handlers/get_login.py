import re, requests
import logging as log
from time import sleep
from InquirerPy import inquirer
from modules.LoginError import LoginError
from .print_handler import print_progress
from .get_html import get_html

#Config
import clippy.config as cfg

count = 0
def get_login(username: str = None,password: str = None) -> int:
    """
    Get the login username and password from the user and generate a session.
    
    Args:
        username (str): The user's username (optional).
        password (str): The user's password (optional).
        count (int): Counts the number of retries it has took.
    
    Returns:
        int: The user's internal ID.
    """
    global count #retry count
    if username is None: username = inquirer.text(message="Nome de utilizador:").execute()
    if password is None: password = inquirer.secret(
        message="Palavra-passe:",
        transformer=lambda _: "[ocultada]",
    ).execute()
    
    login_data = {
        'identificador': username,
        'senha': password
    }

    try:
        print_progress(0,"A fazer login...")
        response = cfg.session.post('https://clip.fct.unl.pt/', data=login_data, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        if "Autenticação inválida" in response.text:
            raise LoginError("Autenticação falhou.")
        
        # Save login info to config.py
        cfg.update_credentials(username, password)

        # Return user ID
        userHTML = get_html("https://clip.fct.unl.pt/utente/eu")
        id = re.search(r"\/utente\/eu\/aluno\?aluno=(\d+)",userHTML).group(1)
        return int(id)


    except requests.exceptions.ReadTimeout:
        count += 1
        if count > 3: raise LoginError("Demasiadas tentativas de conexão. Tente novamente mais tarde.")
        log.warning(f"Ligação ao servidor excedeu o tempo, a tentar novamente... ({count}/3)")
        cfg.session_mount() # Reset session
        sleep(1)
        get_login(username,password)
    except requests.exceptions.RequestException as e:
        raise LoginError(f"Erro de conexão durante o login: {e}")
