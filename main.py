#Import
import requests, getpass, os, re
import logging as log
import pandas as pd
import concurrent.futures
from requests.adapters import HTTPAdapter
from datetime import datetime
from bs4 import BeautifulSoup as bs
from tqdm import tqdm
from urllib3.util import Retry

"""
Clipper
A simple web scraper and downloader for FCT-NOVA's internal e-learning platform, CLIP.
The program scrapes a user's courses for available downloads and syncs them with a local folder.

CLIP's files are organized in subcategories for each academic course like this:
Academic year >> Course documents >> Document subcategory >> Files list

Clipper successfully navigates the site in order to scrape it, and compares it with a local folder
with a similar structure, syncing it to the server.
"""

# Dev comment:
# The code mimics the site's structure, as follows:
#       CLIP: Academic year   >> Course >> Document subcategory >> Files list >>   File
#    Clipper:  CourseList     >> Course >>      CatCount        >>  FilesList >> ClipFile
# Local copy:      Year       /  Course /       Category        /     Files

__author__ = "Afonso Bras Sousa (LEI-65263)"
__maintainer__ = "Afonso Bras Sousa"
__email__ = "ab.sousa@campus.fct.unl.pt"
__version__ = "0.9b"

#Implement auto retry
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

# Logging
log.basicConfig(format="[%(levelname)s] %(message)s", level=log.WARNING)

class LoginError(Exception):
    """
    Raised when the login fails.

    Attributes:
        message (str): A custom error message (optional).
    """
    def __init__(self, message="Erro de login"):
        log.error(message)

class Folder(str):
    """
    Represents a local folder.

    This class inherits from the built-in str class and provides additional
    functionality for working with file paths and creating directories.

    Args:
        path (str): The file path for the folder.

    Attributes:
        path (str): The file path for the folder.

    Methods:
        join(path2: str) -> Folder:
            Append a path to the current folder path and return a new Folder instance.
        get_filepath(filename: str) -> str:
            Get the full path to a file inside the folder.

    Usage:
        folder = Folder("path/to/folder")
        new_folder = folder.join("subfolder")
        file_path = folder.get_filepath("file.txt")
    """

    def __new__(cls, path):
        """
        Create a Folder instance and create the folder if it doesn't exist.

        Args:
            path (str): The file path for the folder.
        """
        if not os.path.isdir(path):
            print(f"A criar a directoria '{path}'...")
            os.makedirs(path)
        return super().__new__(cls, path)
    
    def join(self, path2: str) -> 'Folder':
        """
        Append a path to the current folder path and return it as a new Folder instance.

        Args:
            path2 (str): The path to append to the current folder path.

        Returns:
            Folder: A new Folder instance representing the combined path.
        """
        return Folder(os.path.join(self, path2))

    def get_filepath(self, filename: str) -> str:
        """
        Get the full path to a file inside the folder.

        Args:
            filename (str): The name of the file inside the folder.

        Returns:
            str: The full file path.
        
        Raises:
            FileNotFoundError: If the specified file does not exist in the folder.
        """
        fullpath = os.path.join(self, filename)
        if not os.path.isfile(fullpath):
            raise FileNotFoundError(f"O ficheiro {filename} não foi encontrado na pasta {self}.")
        return fullpath

class ClipFile:
    """
    Represents a file in CLIP, and its associated information.

    Args:
        row (pd.Series): A pandas Series containing data for the file.

    Attributes:
        name (str): The name of the file.
        link (str): The download link for the file.
        mtime (datetime.datetime): The modification time of the file.
        size (int): The size of the file in bytes.
        teacher (str): The name of the teacher who uploaded the file.

    Methods:
        is_synced(path: Folder) -> bool, None:
            Check if the file is synchronized with a local path.

    Usage:
        row_data = pd.Series(...)  # Contains data for the file
        file = ClipFile(row_data)  # Create an instance of the ClipFile class
        folder = Folder(...)        # Create an instance of the Folder class
        
        synced = file.is_synced(folder)  # Check if clip file is synchronized with the local folder

    """

    def __init__(self, row: pd.Series):
        """
        Initialize a ClipFile instance based on a pandas Series.

        Args:
            row (pd.Series): A pandas Series containing data for the clip file.
        """
        self.name = row.at["Nome"]
        self.link = row.at["Link"]
        self.mtime = datetime.strptime(row.at["Data"], "%Y-%m-%d %H:%M")
        self.size = row.at["Tamanho"]
        self.teacher = row.at["Docente"]
  
    def __str__(self):
        """
        Get a string representation of the ClipFile instance.

        Returns:
            str: A string representation of the ClipFile instance.
        """
        return f"{self.name} {self.link} {self.mtime} {self.size} {self.teacher}"
    
    def is_synced(self, path: Folder):
        """
        Check if the file is synchronized with a local path.

        Args:
            path (Folder): An instance of the Folder class representing the
                          local path where the file is expected to exist.

        Returns:
            True if the file is synchronized (up to date).
            False if the file exists but is outdated.
            None if the file does not exist at the specified path.
        """
        try:
            return (datetime.fromtimestamp(os.path.getmtime(path.get_filepath(self.name))) >= self.mtime)
        except FileNotFoundError:
            return None

class FilesList:
    """
    Represents a subcategory of documents, that are displayed in CLIP as a table of downloadable files.
    Returns an array of ClipFile objects, one for each file in the table.

    Args:
        html (bs): Beautiful Soup object containing the HTML content of the table.

    Methods:
        convert_str_to_byte(size: str) -> int:
            Convert a human-readable size string to bytes.
        get_files_table(html: bs) -> pd.DataFrame:
            Internal method that extracts the downloads table from the HTML content.

    Usage:
        html_content = ...
        dtable = FilesList(html_content)
    """

    def __new__(cls, html: bs) -> [ClipFile]:
        """
        Create an array of ClipFile instances based on a subcategory's table.

        Args:
            html (bs): Beautiful Soup object containing the HTML content of the table.

        Returns:
            [ClipFile]: An array of ClipFile instances.
        """
        files = []
        table = cls.get_files_table(cls,html)
        for row in table.index:
            file = ClipFile(table.iloc[row])
            files.append(file)

        return files
    
    def convert_str_to_byte(size: str) -> int:
        """
        Convert a human-readable size string to bytes.

        Args:
            size (str): The size string, e.g., "1.2 MB".

        Returns:
            int: The size in bytes.
        """
        size_name = ("B", "Kb", "Mb", "Gb", "Tb")
        # divide '1 GB' into ['1', 'GB']
        num, unit = int(size[:-2]), size[-2:]
        idx = size_name.index(unit)        # index in list of sizes determines power to raise it to
        factor = 1024 ** idx               # ** is the "exponent" operator - you can use it instead of math.pow()
        num += 1 # Hack to get the right size since the size in the html table actually rounds it wrong
        return num * factor

    def get_files_table(self, html: bs) -> pd.DataFrame:
        """
        Extract the table from the HTML content.

        Args:
            html (bs): Beautiful Soup object containing the HTML content of the table.

        Returns:
            pd.DataFrame: A DataFrame containing data for the downloads table.
        """
        df = pd.DataFrame(columns=['Nome', 'Link', 'Data', 'Tamanho', 'Docente'])
        table = html.find_all("form")[1].find("table") # get downloads table TODO parse file size
        for row in table.find_all("tr", {'bgcolor': True}):
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

class CatCount(dict):
    """
    Short for CategoryCount - a dictionary representing CLIP's subcategory index (key)
    with respective file count (value).
    This class inherits from the built-in dictionary class.

    Args:
        html (bs): Beautiful Soup object containing the HTML content.

    Methods:
        get_links(html: bs) -> List[bs.Tag]:
            Internal method that extracts links from the HTML content.
        get_catID(key: str) -> str:
            Get the ID for a given category (key).

    Usage:
        html_content = ...
        index_count = CatCount(html_content)
    """

    def __init__(self, html: bs):
        """
        Initialize an CatCount instance based on HTML content.

        Args:
            html (bs): Beautiful Soup object containing the HTML content.
        """
        super().__init__()
        links = self.get_links(html)
        counter = [re.search(r"^(\D+) \((\d+)\)", match.text.strip()).group(1, 2) for match in links]
        for key, value in counter:
            if int(value) != 0: #ignore links with zero files
                self[key] = int(value)
    
    def get_links(self, html: bs):
        """
        Extract all links from the HTML content.

        Args:
            html (bs): Beautiful Soup object containing the HTML content.

        Returns:
            [bs.Tag]: An array of Beautiful Soup Tag objects.
        """
        table = html.find_all("td", attrs={"width": "100%"})[1].find_all("a")
        return table

    def get_catID(self, category: str) -> str:
        """
        Get the URL code / ID for a given category.

        Args:
            category (str): The category for which to retrieve the ID.

        Returns:
            str: The corresponding ID.
        """
        ID_dict = {
            "Material Multimédia": "0ac",
            "Problemas": "1e",
            "Protocolos": "2tr",
            "Seminários": "3sm",
            "Exames": "ex",
            "Testes": "t",
            "Textos de Apoio": "ta",
            "Outros": "xot",
        }
        return ID_dict[category]

class Course:
    """
    Represents an academic course with associated information.
    The program automatically extracts the relevant attributes from the associated link.

    Args:
        name (str): The name of the course.
        link (str): The link to the course's details page.

    Attributes:
        name (str): The name of the course.
        year (str): The academic year associated with the course.
        ID (str): The identifier for the course.
        semester_type (str): Specify whether it's a semester ("s") or a trimester ("t").
        semester (str): The semester number.

    Usage:
        course = Course(name, link)
    """

    def __init__(self, name: str, link: str):
        """
        Initialize a Course instance.

        Args:
            name (str): The name of the course.
            link (str): The link to the course's details page.
        """
        self.name = name
        self.year = re.search(r"ano_lectivo=(\d+)", link).group(1)
        self.ID = re.search(r"unidade=(\d+)", link).group(1)
        self.semester_type = re.search(r"tipo_de_per%EDodo_lectivo=(\w)", link).group(1)
        self.semester = re.search(r"per%EDodo_lectivo=(\d)", link).group(1)
    
    def __str__(self):
        """
        Get a string representation of the Course instance.

        Returns:
            str: A string representation of the Course instance.
        """
        return f"{self.name} {self.ID} {self.year} {self.semester}{self.semester_type.upper()}"

class CourseList(list):
    """
    Represents a list of academic courses with associated links.

    Args:
        html (bs): Beautiful Soup object containing the HTML content.

    Usage:
        html_content = ...
        courses_list = CourseList(html_content)
    """

    def __init__(self, html: bs):
        """
        Initialize a CourseList instance based on HTML content.

        Args:
            html (bs): Beautiful Soup object containing the HTML content.
        """
        super().__init__()
        links = self.get_links(html)
        courses = [Course(link.text, link['href']) for link in links]
        self.extend(courses)
    
    def __str__(self):
        """
        Get a string representation of the CourseList instance.

        Returns:
            str: A string representation of the CourseList instance.
        """
        return '\n'.join(str(course) for course in self)
    
    def get_links(self, html: bs) -> [str]:
        """
        Extract links from the HTML content.

        Args:
            html (bs): Beautiful Soup object containing the HTML content.

        Returns:
            An array of links.
        """
        table = html.find_all("td", attrs={"width": "100%"})[1].find_all("a", {"href": re.compile(r"&unidade=(\d+)")}) # TODO possivel IndexError out of range
        return table

def get_login(username: str = None,password: str = None,count: int = 0) -> int:
    """
    Get the login username and password from the user and generate a session.
    
    Args:
        username (str): The user's username (optional).
        password (str): The user's password (optional).
        count (int): Counts the number of retries it has took.
    
    Returns:
        int: The user's internal ID.
    """
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

def get_URL_CourseList(year: int, user: int):
    """
    Generate the URL to the list of academic courses in CLIP.

    Parameters:
        year (int): The academic year.
        user (int): The user ID.

    Returns:
        str: The generated URL.
    """
    return f"{domain}/utente/eu/aluno/ano_lectivo/unidades?ano_lectivo={year}&institui%E7%E3o=97747&aluno={user}"

def get_URL_Index(year: int, semester_type: str, semester: int, course: int):
    """
    Generate the URL to the index of download categories for a specific course in a semester.

    Parameters:
        year (int): The academic year.
        semester_type (str): Specify whether it's a semester ("s") or a trimester ("t").
        semester (int): The semester number.
        course (int): The course ID.

    Returns:
        str: The generated URL.
    """
    return f"{domain}/utente/eu/aluno/ano_lectivo/unidades/unidade_curricular/actividade/documentos?edi%E7%E3o_de_unidade_curricular={course},97747,{year},{semester_type},{semester}"

def get_URL_FileList(year: int, semester_type: str, semester: int, course: int, doc_type: str):
    """
    Generate the URL to retrieve a list of downloads for a specific course and document type in a semester.

    Parameters:
        year (int): The academic year.
        semester_type (str): Specify whether it's a semester ("s") or a trimester ("t").
        semester (int): The semester number.
        course (int): The course ID.
        doc_type (str): The type of document.

    Returns:
        str: The generated URL.
    """
    return f'{domain}/utente/eu/aluno/ano_lectivo/unidades/unidade_curricular/actividade/documentos?tipo_de_per%EDodo_lectivo={semester_type}&tipo_de_documento_de_unidade={doc_type}&ano_lectivo={year}&per%EDodo_lectivo={semester}&unidade_curricular={course}'
    
def get_html(url: str):
    """
    Retrieve the HTML content of a given URL.

    Parameters:
        url (str): The URL to fetch.

    Returns:
        str: The HTML content of the URL.
    """
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

def parse_index(year: int, semester_type: str, semester: int, course: int):
    """
    Parse the index of documents for a specific course in a semester and return it as an CatCount dictionary.

    Parameters:
        year (int): The academic year.
        semester_type (str): Specify whether it's a semester ("s") or a trimester ("t").
        semester (int): The semester number.
        course (int): The course ID.

    Returns:
        CatCount: A dictionary containing parsed index information.
    """
    # Get all the links count
    # Create url link for the class
    url = get_URL_Index(year,semester_type, semester,course)
    soup = bs(get_html(url), 'html.parser')  
    return CatCount(soup)

def parse_docs(year: int, semester_type: str, semester: int, course: int, doc_type: str):
    """
    Parse a list of documents for a specific course and document type in a semester.
    Returns an array of ClipFile objects, one for each document.

    Parameters:
        year (int): The academic year.
        semester_type (str): Specify whether it's a semester ("s") or a trimester ("t").
        semester (int): The semester number.
        course (int): The course ID.
        doc_type (str): The type of document.

    Returns:
        FilesList: An array of ClipFile objects.
    """
    url = get_URL_FileList(year,semester_type,semester,course,doc_type)
    soup = bs(get_html(url), 'html.parser')  
    return FilesList(soup)

def parse_courses(year: int, user: int):
    """
    Parse a list of courses for a specific year and user.

    Parameters:
        year (int): The academic year.
        user (int): The user ID.

    Returns:
        CourseList: An object containing parsed course information.
    """
    url = get_URL_CourseList(year, user)
    soup = bs(get_html(url), 'html.parser') #TODO quando o servidor falha a meio dá IndexError out of range
    return CourseList(soup)

def search_files_in_category(category: str, index: CatCount, course: Course, full_path: Folder):
    """
    Search for files in a specific category and download them if needed.

    Parameters:
        category (str): The category of files to search for.
        index (CatCount): The index of document categories.
        course (Course): The course for which to search documents.
        full_path (Folder): The full path to the directory where files should be downloaded.
    """
    try:
        print(f"> A procurar {category}...")
        doc_type = index.get_catID(category)
        table = parse_docs(course.year,course.semester_type, course.semester, course.ID, doc_type)
        for file in table:
            folder = full_path.join(category)
            get_file(file,folder)
    except Exception as ex:
        log.error(f'Erro a procurar {category} de {course}: {str(ex)}')
        pass


def download_to_file(filepath: str, url: str, file_size=0, file_mtime=None): #TODO refactor function with ClipFile and change file time
    """
    Download a file from a given URL to a specified filepath.

    Parameters:
        filepath (str): The path where the downloaded file will be saved.
        url (str): The URL of the file to download.
        file_size (int, optional): The expected size of the file in bytes. Defaults to 0.
        file_mtime (datetime.datetime, optional): The desired modification time for the downloaded file. Defaults to None.
    """
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
    """
    Search for a local file.
    Calls download_to_file() to (re)download it if it's older or not found.

    Parameters:
        file (ClipFile): The file to download.
        path (Folder): The path where the file should be saved.
    """
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

    courses = parse_courses(year,user)
    print("Encontradas as seguintes unidades: "+" | ".join(course.name for course in courses) )

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for course in courses:
            print(f"A procurar documentos de {course.name}...")
            full_path = path.join(course.year)

            index = parse_index(course.year, course.semester_type, course.semester, course.ID)

            if not index: #skips creating directory if there are no documents
                log.info(f"Não foram encontrados documentos em {course.name}")
            else:
                full_semester = course.semester+course.semester_type.upper()
                full_path = full_path.join(full_semester).join(course.name)
            
                for category,count in index.items():
                    pool.submit(search_files_in_category,category,index,course,full_path)

if __name__ == "__main__":
    main()
