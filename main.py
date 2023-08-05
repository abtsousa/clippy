import requests, getpass, os, re
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup as bs
from tqdm import tqdm

#Logging
import logging as log
log.basicConfig(format="[%(levelname)s] %(message)s", level=log.WARNING)

#Threading
import concurrent.futures

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

class Folder(str): #subclass of String
    def __new__(cls, path):
        if not os.path.isdir(path):
            print(f"A criar a directoria '{path}'...")
            os.makedirs(path)
        return super().__new__(cls, path)
    
    def join(self, path2: str):
        return Folder(os.path.join(self,path2))

    def get_filepath(self, filename: str) -> str:
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
            return (datetime.fromtimestamp(os.path.getmtime(path.get_filepath(self.name))) >= self.mtime)
        except FileNotFoundError:
            return None
    
class DTable: # Documents table
    
    def __new__(cls, html: bs) -> [ClipFile]:
        files = []
        table = cls.get_downloads_table(cls,html)
        for row in table.index:
            file = ClipFile(table.iloc[row])
            files.append(file)

        return files
    
    def convert_str_to_byte(size: str):
        size_name = ("B", "Kb", "Mb", "Gb", "Tb")
        # divide '1 GB' into ['1', 'GB']
        num, unit = int(size[:-2]), size[-2:]
        idx = size_name.index(unit)        # index in list of sizes determines power to raise it to
        factor = 1024 ** idx               # ** is the "exponent" operator - you can use it instead of math.pow()
        num += 1 # Hack to get the right size since the size in the html table actually rounds it wrong
        return num * factor

    def get_downloads_table(self, html):
        df = pd.DataFrame(columns=['Nome','Link','Data','Tamanho','Docente'])
        table=html.find_all("form")[1].find("table") # get downloads table TODO parse file size
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

class IndexCount(dict): # Documents count

    def __init__(self, html:bs):
        super().__init__
        links = self.get_links(html)
        counter = [re.search(r"^(\D+) \((\d+)\)",match.text.strip()).group(1,2) for match in links]
        for key, value in counter:
            if int(value) != 0: #ignore links with zero files
                self[key] = int(value)
    
    def get_links(self, html):
        table = html.find_all("td", attrs={"width":"100%"})[1].find_all("a")
        return table

    def get_type(self, key):
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
        return type_dict[key]

class Unit:
    def __init__(self, name: str, link: str):
        self.name = name
        self.year = re.search(r"ano_lectivo=(\d+)",link).group(1)
        self.unit = re.search(r"unidade=(\d+)",link).group(1)
        self.semester_type = re.search(r"tipo_de_per%EDodo_lectivo=(\w)",link).group(1)
        self.semester = re.search(r"per%EDodo_lectivo=(\d)",link).group(1)
    
    def __str__(self):
        return f"{self.name} {self.unit} {self.year} {self.semester}{self.semester_type.upper()}"
    
class UnitsList(list): # List of units and their links

    def __init__(self, html:bs):
        super().__init__()
        links = self.get_links(html)
        units = [Unit(link.text,link['href']) for link in links]
        self.extend(units)
    
    def __str__(self):
        return '\n'.join(str(unit) for unit in self)
    
    def get_links(self, html):
        table = html.find_all("td", attrs={"width":"100%"})[1].find_all("a", {"href": re.compile(r"&unidade=(\d+)")}) # TODO possivel IndexError out of range
        return table


def get_login(username=None,password=None,count=0) -> int:
    if username is None: username= input("Nome de utilizador: ")
    if password is None: password = getpass.getpass()

    login_data = {
        'identificador': username,
        'senha': password
    }

    try:
        response = session.post('https://clip.fct.unl.pt/', data=login_data, timeout=5)
        response.raise_for_status()  # Raise an exception for HTTP errors
        if "Autenticação inválida" in response.text:
            raise LoginError("Autenticação falhou.")
        
        # Return user ID
        id = re.search(r"\/utente\/eu\/aluno\?aluno=(\d+)",response.text).group(1)
        return int(id)


    except requests.exceptions.ReadTimeout:
        count += 1
        if count > 3: raise LoginError("Demasiadas tentativas de conexão. Tente novamente mais tarde.")
        log.warning(f"Ligação ao servidor excedeu o tempo, a tentar novamente... ({count}/3)")
        get_login(username,password, count)
    except requests.exceptions.RequestException as e:
        raise LoginError(f"Erro de conexão durante o login: {e}")

def get_URL_UnitsList(year: int, user: int):
    return f"{domain}/utente/eu/aluno/ano_lectivo/unidades?ano_lectivo={year}&institui%E7%E3o=97747&aluno={user}"

def get_URL_Index(year: int, semester_type: str, semester: int, unit: int):
    return f"{domain}/utente/eu/aluno/ano_lectivo/unidades/unidade_curricular/actividade/documentos?edi%E7%E3o_de_unidade_curricular={unit},97747,{year},{semester_type},{semester}"

def get_URL_DList(year: int, semester_type: str, semester: int, unit: int, doc_type: str):
        return f'{domain}/utente/eu/aluno/ano_lectivo/unidades/unidade_curricular/actividade/documentos?tipo_de_per%EDodo_lectivo={semester_type}&tipo_de_documento_de_unidade={doc_type}&ano_lectivo={year}&per%EDodo_lectivo={semester}&unidade_curricular={unit}'
    
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

def parse_index(year: int, semester_type: str, semester: int, unit: int):
    # Get all the links count
    # Create url link for the class
    url = get_URL_Index(year,semester_type, semester,unit)
    soup = bs(get_html(url), 'html.parser')  
    return IndexCount(soup)

def parse_docs(year: int, semester_type: str, semester: int, unit: int, doc_type: str):
    url = get_URL_DList(year,semester_type,semester,unit,doc_type)
    soup = bs(get_html(url), 'html.parser')  
    return DTable(soup)

def parse_units(year: int, user: int):
    url = get_URL_UnitsList(year, user)
    soup = bs(get_html(url), 'html.parser') #TODO quando o servidor falha a meio dá IndexError out of range
    return UnitsList(soup)

def search_files_in_category(category: str, index: IndexCount, unit: Unit, full_path: Folder):
    try:
        print(f"> A procurar {category}...")
        doc_type = index.get_type(category)
        table = parse_docs(unit.year,unit.semester_type, unit.semester, unit.unit, doc_type)
        for file in table:
            folder = full_path.join(category)
            get_file(file,folder)
    except Exception as ex:
        log.error(f'Erro a procurar {category} de {unit}: {str(ex)}')
        pass


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
                log.debug("Mod-time do ficheiro: %d", int(os.stat(filepath).st_mtime))
                mtime = file_mtime.timestamp()
                log.debug("A actualizar para %d", int(mtime))
                os.utime(filepath,times=(mtime,mtime))
                log.debug("Novo mod-time: %d", int(os.stat(filepath).st_mtime))

        else:
            raise requests.HTTPError(f'Código de estado HTTP: {r.status_code}')
    except Exception as ex:
        log.error(f'Falhou o download de \'{url}\': {str(ex)}')
        pass
    # print(soup.find("td", class_="barra_de_escolhas"})) # get left sidebar TODO parse number of downloads

def get_file(file: ClipFile, path: Folder):
    log.debug(f"{file} {file.is_synced(path)}")
    file_path = os.path.join(path,file.name)
    match file.is_synced(path):
        case True:
            log.info(f"Encontrado {file.name} na pasta {path}, a saltar...")
        case False:
            print(f"O ficheiro {file_path} está desactualizado, a transferir...")
            download_to_file(os.path.join(path,file.name),file.link,file.size,file.mtime)
        case None:
            print(f"A transferir {file_path}...")
            download_to_file(os.path.join(path,file.name),file.link,file.size,file.mtime)

def main():
    valid_login = False
    while not valid_login:
        try:
            user = get_login()
            valid_login = True
        except LoginError:
            continue
    
    path = Folder(os.getcwd())
    year = 2023

    units = parse_units(year,user)
    print("Encontradas as seguintes unidades: "+" | ".join(unit.name for unit in units) )

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for unit in units:
            print(f"A procurar documentos de {unit.name}...")
            full_path = path.join(unit.year)

            index = parse_index(unit.year, unit.semester_type, unit.semester, unit.unit)

            if not index: #skips creating directory if there are no documents
                log.info(f"Não foram encontrados documentos em {unit.name}")
            else:
                full_semester = unit.semester+unit.semester_type.upper()
                full_path = full_path.join(full_semester).join(unit.name)
            
                for category,count in index.items():
                    pool.submit(search_files_in_category,category,index,unit,full_path)

if __name__ == "__main__":
    main()
