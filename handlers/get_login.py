import re, requests
import logging as log
from time import sleep
from InquirerPy import inquirer
from modules.LoginError import LoginError
from .print_handler import print_progress
from .get_html import get_html
from handlers.creds_handler import save_credentials, load_username, load_password

#Config
import clippy.config as cfg

count = 0

# Flag if saved credentials don't match entered credentials
saved_creds = ()
update_creds_flag = False

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
        message=f"Palavra-passe para {username}:",
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
        
        # Return user ID
        if response.url != "https://clip.fct.unl.pt/":
            log.warning("Parece ter havido alterações à página inicial do CLIP (possíveis notificações ou avisos?). A tentar contornar...")
            userHTML = get_html("https://clip.fct.unl.pt/utente/eu")
        else:
            userHTML = response.text
        
        try:
            id = re.search(r"\/utente\/eu\/aluno\?aluno=(\d+)",userHTML).group(1)
        
            # Temporarily save entered credentials so they can optionally be saved at the end of the program
            if username != load_username() or password != load_password():
                global update_creds_flag, saved_creds
                update_creds_flag = True
                saved_creds = (username, password)

            return int(id)
        except AttributeError:
            raise RuntimeError("Não foi possível obter o ID do utilizador.")
        

    except requests.exceptions.ReadTimeout:
        count += 1
        if count > 3: raise LoginError("Demasiadas tentativas de conexão. Tente novamente mais tarde.")
        log.warning(f"Ligação ao servidor excedeu o tempo, a tentar novamente... ({count}/3)")
        cfg.session_mount() # Reset session
        sleep(1)
        get_login(username,password)
    except requests.exceptions.RequestException as e:
        raise LoginError(f"Erro de conexão durante o login: {e}")
    
def check_for_save_credentials():
    if update_creds_flag:
        save_credentials(saved_creds[0], saved_creds[1])