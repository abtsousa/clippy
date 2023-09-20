import keyring
from InquirerPy import inquirer

service_name="clippy"
reset_flag=False

def load_username():
    cred = keyring.get_credential(service_name, None)
    if cred is not None and not reset_flag:
        return cred.username
    else:
        return None

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

def delete_password(username):
    keyring.delete_password(service_name, username)

def reset_login():
    '''Ignores saved credentials if they are wrong.'''
    global reset_flag
    reset_flag = True