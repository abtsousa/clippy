import requests, getpass, os 
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup as bs
from tqdm import tqdm
import logging as log
log.basicConfig(format="[%(levelname)s] %(message)s", level=log.WARNING)

class LoginError(Exception):
    "Raised when the login fails"
    def __init__(self, message="Erro de login"):
        log.error(message)

retry_strategy = Retry(
    total=3,  # Number of total retries (including the initial request)
    backoff_factor=0.3,  # Factor to apply exponential backoff between retries
    status_forcelist=[500, 502, 503, 504],  # HTTP status codes to retry
)

# Create a custom HTTP adapter with the retry strategy
adapter = HTTPAdapter(max_retries=retry_strategy)

session = requests.Session()
session.mount("https://", adapter)
session.mount("http://", adapter)
domain='https://clip.fct.unl.pt'

type_dict = {
    "Material Multimédia":"0ac",
    "Problemas":"1e",
    "Protocolos":"2tr",
    "Seminários":"3sm",
    "Exames":"ex",
    "Testes":"t",
    "Textos de Apoio":"ta",
    "Outros":"xot",
}

class Folder(str): #subclass of String
    def __new__(cls, path):
        if not os.path.isdir(path):
            raise ValueError(f"'{path}' não é uma directoria válida")
        return super().__new__(cls, path)

    def join(self, filename: str) -> str:
        fullpath = os.path.join(self, filename)
        if not os.path.isfile(fullpath): raise FileNotFoundError
        return fullpath

class ClipFile: # File in clip

    def __init__(self, row: pd.Series):
        self.name = row.at["Nome"]
        self.link = row.at["Link"]
        self.mtime = datetime.strptime(row.at["Data"],"%Y-%m-%d %H:%M")
        self.size = row.at["Tamanho"]
        self.teacher = row.at["Docente"]
  
    def __str__(self):
        return f"{self.name} {self.link} {self.mtime} {self.size} {self.teacher}"
    
    def is_synced(self,path: Folder): #True = file is synced / False = file exists but is outdated / None: file does not exist
        try:
            return (datetime.fromtimestamp(os.path.getmtime(path.join(self.name))) >= self.mtime)
        except FileNotFoundError:
            return None
    
class DTable: # Downloads table
    
    def __new__(self, html: bs) -> [ClipFile]:
        self.html = html
        self.files = []
        table = self.get_downloads_table(self)
        for row in table.index:
            file = ClipFile(table.iloc[row])
            self.files.append(file)

        return self.files
    
    def convert_str_to_byte(size: str):
        size_name = ("B", "Kb", "Mb", "Gb", "Tb")
        # divide '1 GB' into ['1', 'GB']
        num, unit = int(size[:-2]), size[-2:]
        idx = size_name.index(unit)        # index in list of sizes determines power to raise it to
        factor = 1024 ** idx               # ** is the "exponent" operator - you can use it instead of math.pow()
        num += 1 # Hack to get the right size since the size in the html table actually rounds it wrong
        return num * factor

    def get_downloads_table(self):
        df = pd.DataFrame(columns=['Nome','Link','Data','Tamanho','Docente'])
        table=self.html.find_all("form")[1].find("table") # get downloads table TODO parse file size
        for row in table.find_all("tr", {'bgcolor':True}):
            columns = row.find_all("td")

            if columns != []:
                nome = columns[0].text.strip()
                link = domain + columns[1].find("a").get("href")
                data = columns[2].text.strip()
                tamanho = self.convert_str_to_byte(columns[3].text.strip())
                docente = columns[4].text.strip()

                row = pd.DataFrame({"Nome": [nome], "Link": [link], "Data": [data], "Tamanho": [tamanho], "Docente": [docente]})

                df = pd.concat([df, row], ignore_index=True)
        
        return df

def getLogin(username=None,password=None,count=0):
    if username is None: username= input("Nome de utilizador: ")
    if password is None: password = getpass.getpass()

    login_data = {
        'identificador': username,
        'senha': password
    }

    try:
        response = session.post('https://clip.fct.unl.pt/', data=login_data, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        if "Autenticação inválida" in response.text:
            raise LoginError("Autenticação falhou.")
    except requests.exceptions.ReadTimeout:
        count += 1
        if count > 3: raise LoginError("Demasiadas tentativas de conexão. Tente novamente mais tarde.")
        log.warning(f"Ligação ao servidor excedeu o tempo, a tentar novamente... ({count}/3)")
        getLogin(username,password)
    except requests.exceptions.RequestException as e:
        raise LoginError(f"Erro de conexão durante o login: {e}")

def get_URL(year: int, semester: int, unit: int, type: str):
    return f'{domain}/utente/eu/aluno/ano_lectivo/unidades/unidade_curricular/actividade/documentos?tipo_de_per%EDodo_lectivo=s&tipo_de_documento_de_unidade={type}&ano_lectivo={year}&per%EDodo_lectivo={semester}&unidade_curricular={unit}'
    
def get_html(url: str):
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

def download_to_file(filepath: str, url: str, file_size=0, file_mtime=None): #TODO refactor function with ClipFile and change file time
    try:
        r = session.get(url, stream=True)
        if file_size==0: file_size=r.headers['Content-Length']
        chunk_size = 1024

        if r.status_code == 200:
            with open(filepath, 'wb+') as f:
                pbar = tqdm(total=file_size, unit="B", unit_scale=True, unit_divisor=1024)
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        pbar.update(len(chunk))
                        f.write(chunk)
            if file_mtime is not None:
                log.debug("Mod-time do ficheiro:", os.stat(filepath).st_mtime)
                mtime = file_mtime.timestamp()
                log.debug("A actualizar para", mtime)
                os.utime(filepath,times=(mtime,mtime))
                log.debug("Novo mod-time:", os.stat(filepath).st_mtime)

        else:
            raise requests.HTTPError(f'Status code is {r.status_code}')
    except Exception as ex:
        log.error(f'[-] Failed to download \'{url}\'! {str(ex)}')
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
    url = get_URL(2023,1,11504,"t")

    soup = bs(get_html(url), 'html.parser')

    # Get downloads table
    table = DTable(soup)

    path = Folder("/tmp/clipper/")

    for file in table:
        log.debug(f"{file} {file.is_synced(path)}")
        match file.is_synced(path):
            case True:
                print(f"Encontrado {file.name} na pasta, a saltar...")
            case False:
                print(f"O ficheiro {file.name} está desactualizado, a transferir...")
                download_to_file(os.path.join(path,file.name),file.link,file.size,file.mtime)
            case None:
                print(f"A transferir {file.name}...")
                download_to_file(os.path.join(path,file.name),file.link,file.size,file.mtime)
    """
    # Get all download links
    links = []
    for link in soup.find_all('a', href=re.compile("^/objecto*")):
        links.append(domain+link.get('href'))
    """
    
    
    # print(soup.find("td", class_="barra_de_escolhas"})) # get left sidebar TODO parse number of downloads


    #print(links)
    #download_to_file("/tmp/","1","http://speedtest.ftp.otenet.gr/files/test10Mb.db")
    #download_to_file("/tmp/1",links[1], (718+1)*1024) # need to add 1

if __name__ == "__main__":
    main()
