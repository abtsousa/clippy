import requests
import re
import getpass
from bs4 import BeautifulSoup as bs
from tqdm import tqdm

class LoginError(Exception):
    "Raised when the login fails"
    def __init__(self, message="Login error"):
        print(message)

def getLogin():
    username = input("Username: ")
    password = getpass.getpass()

    login_data = {
        'identificador': username,
        'senha': password
    }

    with requests.Session() as session:
        try:
            response = session.post('https://clip.fct.unl.pt/', data=login_data)
            response.raise_for_status()  # Raise an exception for HTTP errors
            if "Autenticação inválida" in response.text:
                raise LoginError("Autenticação falhou.")
        except requests.exceptions.RequestException as e:
            raise LoginError("Erro de conexão durante o login.")

        return session

def get_html(url, session):
    response = session.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.text

def download(url, session):
    response = session.get(url, stream=True)
    with open("/tmp/1", "wb") as file:
        for data in tqdm(response.iter_content()):
            file.write(data)

def main():
    valid_login = False
    while not valid_login:
        try:
            login = getLogin()
            valid_login = True
        except LoginError:
            continue

    ano_lectivo=2023
    semestre=1
    unidade_curricular=11504
    tipo_documento='t'
    domain='https://clip.fct.unl.pt'

    url = f'{domain}/utente/eu/aluno/ano_lectivo/unidades/unidade_curricular/actividade/documentos?tipo_de_per%EDodo_lectivo=s&tipo_de_documento_de_unidade={tipo_documento}&ano_lectivo={ano_lectivo}&per%EDodo_lectivo={semestre}&unidade_curricular={unidade_curricular}'
    soup = bs(get_html(url, login), 'html.parser')

    links = []
    for link in soup.find_all('a', href=re.compile("^/objecto*")):
        links.append(domain+link.get('href'))

    print(links)
    download(links[1],login)

if __name__ == "__main__":
    main()
