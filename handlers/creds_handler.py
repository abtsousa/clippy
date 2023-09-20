import keyring
from InquirerPy import inquirer
import logging as log
import configparser
from pathlib import Path
import clippy.config as cfg

service_name="clippy"
reset_flag=False

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
    """Save a basic user config."""
    config = configparser.ConfigParser()
    
    config['Credenciais'] = {"username": username}
    Path.mkdir(cfg.cfgpath.parent, parents=True, exist_ok=True)
    with open(cfg.cfgpath, 'w+') as configfile:
        config.write(configfile)
        print(f"Ficheiro de configuração guardado em: '{cfg.cfgpath}'")
def delete_password(username):
    keyring.delete_password(service_name, username)

def load_username():
    if reset_flag:
        return None
    else:
        cred = keyring.get_credential(service_name, None) # does not work in all keychain managers e.g. macOS
        if cred is not None:
            log.debug(f"Found saved username: {cred.username}")
            return cred.username
        else:
            username = load_username_alt() # macOS workaround
            if username is None:
                log.debug("No saved username found.")
            return username

def load_password(username=load_username()):
    if not reset_flag:
        return keyring.get_password(service_name,username)
    else:
        return None

def save_credentials(username, password):
    if inquirer.confirm(
        message="Guardar credenciais em sistema para a próxima vez?",
        default=True,
        confirm_letter="s",
        reject_letter="n",
        transformer=lambda result: "Sim" if result else "Não",
    ).execute():
        keyring.set_password(service_name, username, password)
        print("Credenciais guardadas no sistema.")

        # Check if username is unaccessible and:
        if keyring.get_credential(service_name, None) is None:
            save_username_alt(username)

def reset_login():
    '''Ignores saved credentials if they are wrong.'''
    global reset_flag
    reset_flag = True