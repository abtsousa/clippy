import requests
import re
import getpass
import sys
from bs4 import BeautifulSoup as bs
from tqdm import tqdm

class LoginError(Exception):
    "Raised when the login fails"
    def __init__(self, message="Login error"):
        print(message)

session = requests.Session()

def getLogin():
    username = input("Username: ")
    password = getpass.getpass()

    login_data = {
        'identificador': username,
        'senha': password
    }

    try:
        response = session.post('https://clip.fct.unl.pt/', data=login_data)
        response.raise_for_status()  # Raise an exception for HTTP errors
        if "Autenticação inválida" in response.text:
            raise LoginError("Autenticação falhou.")
    except requests.exceptions.RequestException as e:
        raise LoginError("Erro de conexão durante o login.")


def get_html(url):
    response = session.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.text

"""
def download(url, size):
    response = session.get(url, stream=True)
    chunk_size = 1024 #1MB
    with open("/tmp/1", "wb") as file:
        for data in tqdm(response.iter_content(chunk_size=chunk_size), total=size/chunk_size, unit="bytes", unit_scale=True, unit_divisor=1024):
            file.write(data)
"""

def download_to_file(filepath: str, url: str, file_length=0):
    try:
        r = session.get(url, stream=True)
        if file_length==0: file_length=r.headers['Content-Length']
        chunk_size = 1024

        if r.status_code == 200:
            with open(filepath, 'wb+') as f:
                pbar = tqdm(total=file_length, unit="B", unit_scale=True, unit_divisor=1024)
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        pbar.update(len(chunk))
                        f.write(chunk)
        else:
            raise requests.HTTPError(f'Status code is {r.status_code}')
    except Exception as ex:
        print(f'[-] Failed to download \'{url}\'! {str(ex)}')
        pass

def main():
    valid_login = False
    while not valid_login:
        try:
            getLogin()
            valid_login = True
        except LoginError:
            continue

    # Create url link for the class
    ano_lectivo=2023
    semestre=1
    unidade_curricular=11504
    tipo_documento='t'
    domain='https://clip.fct.unl.pt'

    url = f'{domain}/utente/eu/aluno/ano_lectivo/unidades/unidade_curricular/actividade/documentos?tipo_de_per%EDodo_lectivo=s&tipo_de_documento_de_unidade={tipo_documento}&ano_lectivo={ano_lectivo}&per%EDodo_lectivo={semestre}&unidade_curricular={unidade_curricular}'
    soup = bs(get_html(url), 'html.parser')

    # Get all download links
    links = []
    for link in soup.find_all('a', href=re.compile("^/objecto*")):
        links.append(domain+link.get('href'))

    # print(soup.find_all("form")[1].find("table")) # get downloads table TODO parse file size
    print(soup.find("td", attrs={"class":"barra_de_escolhas"})) # get left sidebar TODO parse number of downloads
    print(links)
    #download_to_file("/tmp/","1","http://speedtest.ftp.otenet.gr/files/test10Mb.db")
    download_to_file("/tmp/1",links[1], (718+1)*1024) # need to add 1

if __name__ == "__main__":
    main()
