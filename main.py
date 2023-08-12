#Import
from datetime import datetime
from pathlib import Path
import logging as log
import concurrent.futures
import typer
from rich import print

#Config
import config
from modules.CourseList import CourseList

# Local modules
from modules.LoginError import LoginError
from modules.Course import Course

# Local functions
from get_login import get_login
from parse import parse_courses, parse_docs, parse_index
from file_handler import get_file
from cache import parse_cache

"""
Clipper
A simple web scraper and downloader for FCT-NOVA's internal e-learning platform, CLIP.
The program scrapes a user's courses for available downloads and syncs them with a local folder.

CLIP's files are organized in subcategories for each academic course like this:
Academic year >> Course documents >> Document subcategory >> Files list

Clipper successfully navigates the site in order to scrape it, and compares it with a local folder
with a similar structure, syncing it to the server.
"""

# TODO: Proper multithread management 
# 1) Scrape units list
# 2) Create basic unit folder structure
# 3) (Multithreaded) Load each unit's index and compare it to cached file if it exists
# 4) (Multithreaded) Load each subcategory's table and compare it to the local folder
# 5) (Multithreaded) Download missing files
# Store cache only if it was successful

# TODO: One-line progress bar?

# TODO: Warning if file count in folder is less than cache value

# Dev comment:
# The code mimics the site's structure, as follows:
#       CLIP: Academic year   >> Course >> Document subcategory >> Files list >>   File
#    Clipper:  CourseList     >> Course >>      CatCount        >>  FilesList >> ClipFile
# Local copy:      Year       /  Course /       Category        /     Files

__author__ = "Afonso Bras Sousa (LEI-65263)"
__maintainer__ = "Afonso Bras Sousa"
__email__ = "ab.sousa@campus.fct.unl.pt"
__version__ = "0.9b"

def main(path: Path = Path.cwd()):
    # Check valid path
    check_path(path)

    # 0/5 Start login
    print_progress(0,"A fazer login...")
    valid_login = False
    while not valid_login:
        try:

            user = get_login()
            valid_login = True
        except LoginError:
            continue
    
    year = 2023 #TODO config

    # 1/5 Scrape units list
    courses = parse_courses(year,user)
    print_progress(1,"Encontradas as seguintes unidades: "+" | ".join(course.name for course in courses) )

    # 2/5 Create basic unit folder structure
    print_progress(2,"A verificar/criar a estrutura de pastas...")
    create_folder_structure(path,courses)
    
    # 3/5 (Multithreaded) Load each unit's index and compare it to cached file if it exists
    print_progress(3,"A verificar se há ficheiros novos...")
    subcats = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(search_cats_in_course, path, course): course for course in courses} # set future : course dict
        
        for future in concurrent.futures.as_completed(futures):
            course = futures[future] # value
            try:
                subcat = future.result()  # Get the result from the future
                if subcat is not None:
                    subcats.extend(subcat)
            except Exception as e:
                log.error(f"Erro a processar {course}: {e}")

    log.debug(f"Lista de subcategorias a procurar: {subcats}")

    # 4/5 (Multithreaded) Load each subcategory's table and compare it to the local folder
    print_progress(4,"A obter URLs dos ficheiros a transferir...")
    files = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(search_files_in_category,*subcat) : subcat for subcat in subcats}
        
        for future in concurrent.futures.as_completed(futures):
            subcat = futures[future] # value
            try:
                file = future.result()  # Get the result from the future
                if file is not None:
                    files.extend(subcat)
            except Exception as e:
                log.error(f"Erro a processar {subcat[0]}: {e}")

    log.debug(f"Lista de ficheiros a transferir: {files}")

def print_progress(progress: int, msg: str, max: int = 5):
    bar = progress*"▰"+(max-progress)*"▱"
    print(f"{bar} {msg}")

def check_path(path: Path):
    if not path.exists():
        char = input(f"A directoria {path} não existe. Criá-la? (S/n) ")
        match char:
            case 's' | 'S' | 'y' | 'Y' | '\r':
                path.mkdir(parents=True, exist_ok=True)
                log.info("A criar directoria {path}.")
            case _:
                print("A abortar programa... Adeus!")
                exit()
        #TODO check for config file in directory?
        #TODO default directory input instead of cwd?

def create_folder_structure(path: Path, list: CourseList):
    for course in list:
        full_path = path / course.year / f"{course.semester}S" / course.name
        log.debug(f"A criar a pasta {full_path} se não existir...")
        full_path.mkdir(parents=True, exist_ok=True)

def search_cats_in_course(path: Path, course: Course) -> [(str, str, Course, Path)]:
    print(f"A procurar documentos de {course.name}...")
    full_path = path / course.year

    index = parse_index(course.year, course.semester_type, course.semester, course.ID)

    if not index: #skips creating directory if there are no documents
        log.info(f"Não foram encontrados documentos em {course.name}.")
    else:
        log.debug(f"Contagem para {course.name}: {index}")
        full_semester = course.semester+course.semester_type.upper()
        full_path = full_path / full_semester / course.name

        cachediff = parse_cache(full_path, index, course.name)
        
        _subcats = []
        if cachediff is not None:
            for category,count in cachediff.items():
                _subcats.append((category,index.get_catID(category),course,full_path))
                #search_files_in_category(category,index.get_catID(category),course,full_path)
        
        log.debug(f"Subcategorias de {course.name}: {_subcats}")
        return _subcats

def search_files_in_category(category: str, catID: str, course: Course, full_path: Path) -> [(Path, str, str, datetime)]:
    """
    Search for files in a specific category and download them if needed.

    Parameters:
        category (str): The category of files to search for.
        catID (str): The ID of respective category.
        course (Course): The course for which to search documents.
        full_path (Path): The full path to the directory where files should be downloaded.
    """
    try:
        print(f"> A procurar {category} de {course.name}...")
        table = parse_docs(course.year,course.semester_type, course.semester, course.ID, catID)

        _files = []
        for file in table:
            folder = full_path / category
            log.debug(f"A procurar {file} na pasta {folder}...")
            _file = get_file(file,folder)
            if file is not None:
                _files.append(_file)
        
        log.debug(f"Ficheiros de {course} > {category}: {_files}")
        return _files

    except Exception as ex:
        log.error(f'Erro a procurar {category} de {course}: {str(ex)}')
        pass

if __name__ == "__main__":
    typer.run(main)