import keyring
from InquirerPy import inquirer
import logging as log
import configparser
from pathlib import Path
import clippy.config as cfg
import os

service_name="clippy"
reset_flag=False
keyring_disable=False

# macOS workaround
def load_username_alt():
    """Load a basic user config."""
    if Path.is_file(cfg.cfgpath):
        log.info(f"Ficheiro de configuração encontrado: {cfg.cfgpath}")
        try:
            config = configparser.ConfigParser()
            config.read(cfg.cfgpath)
            try: username = config.get("Credenciais","username")
            except configparser.NoOptionError: username = None
            #try: password = config.get("Credenciais","password")
            #except configparser.NoOptionError: password = None
            return username
        except (configparser.MissingSectionHeaderError, configparser.NoSectionError):
            return None
    else:
        log.info("Nenhum ficheiro de configuração encontrado.")
        return None

# macOS workaround
def save_username_alt(username):
    """
    Save a basic user config.
    
    Args:
        username(str): the user's username.
    """
    config = configparser.ConfigParser()
    
    config['Credenciais'] = {"username": username}
    Path.mkdir(cfg.cfgpath.parent, parents=True, exist_ok=True)
    with open(cfg.cfgpath, 'w+') as configfile:
        config.write(configfile)
        print(f"Ficheiro de configuração guardado em: '{cfg.cfgpath}'")
def delete_password(username):
    keyring.delete_password(service_name, username)

def load_username():
    """Loads a saved username, if found."""
    if reset_flag:
        return None

    username = os.getenv('CLIP_USERNAME')
    if username:
        log.debug(f"Found saved username: {username}")
        return username

    cred = keyring.get_credential(service_name, None)  # does not work in all keychain managers e.g. macOS
    if cred is not None:
        log.debug(f"Found saved username: {cred.username}")
        return cred.username

    username = load_username_alt()  # macOS workaround
    if username is None:
        log.debug("No saved username found.")
    return username


def load_password(username=load_username()):
    """Loads a saved password, if found."""
    global keyring_disable

    if reset_flag:
        return None

    password = os.getenv('CLIP_PASSWORD')
    if password:
        log.debug("Found saved password in environment variable.")
        return password

    try:
        return keyring.get_password(service_name, username)
    except (keyring.errors.NoKeyringError, keyring.errors.KeyringError):  # keyring not found, not installed or error loading
        log.info("Não foi encontrado nenhum serviço para guardar credenciais no sistema.")
        keyring_disable = True
        return None

def save_credentials(username, password):
    """Saves the provided credentials, after asking for the user's permission.
    
    Args:
        username (str): The user's username.
        password (str): The user's password.
    """
    if not keyring_disable and inquirer.confirm(
        message="Guardar credenciais em sistema para a próxima vez?",
        default=True,
        confirm_letter="s",
        reject_letter="n",
        transformer=lambda result: "Sim" if result else "Não",
    ).execute():
        try:
            keyring.set_password(service_name, username, password)
            print("Credenciais guardadas no sistema.")

            # Check if username is unaccessible and save it as a config file if so (workaround)
            if keyring.get_credential(service_name, None) is None:
                save_username_alt(username)

        except (keyring.errors.NoKeyringError, keyring.errors.KeyringError): #keyring not found, not installed or error loading
            log.info("Não foi encontrado nenhum serviço para guardar credenciais no sistema.")


def reset_login():
    '''Ignores saved credentials if they are wrong.'''
    global reset_flag
    reset_flag = True
