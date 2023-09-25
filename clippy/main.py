#Import
from datetime import datetime
from pathlib import Path
import logging as log
import concurrent.futures as cf
import typer
import time
import sys
from typing_extensions import Annotated
from typing import Optional
from InquirerPy import inquirer
from rich import print

#Config
import clippy.config as cfg

# Local modules
from modules.LoginError import LoginError
from modules.CourseList import CourseList
from modules.Course import Course

# Local functions
from handlers.check_updates import get_latest_release
from handlers.get_login import get_login, check_for_save_credentials
from handlers.HTML_parser import parse_courses, parse_docs, parse_index, parse_years
from handlers.file_handler import get_file, download_file, count_files_in_subfolders
from handlers.cache_handler import commit_cache, parse_cache, stash_cache
from handlers.print_handler import print_progress, human_readable_size
from handlers.creds_handler import load_username, load_password

"""
NOVA Clippy
A simple web scraper and downloader for FCT-NOVA's internal e-learning platform, CLIP.
The program scrapes a user's courses for available downloads and syncs them with a local folder.

CLIP's files are organized in subcategories for each academic course like this:
Academic year >> Course documents >> Document subcategory >> Files list

Clippy successfully navigates the site in order to scrape it, and compares it to a local folder
with a similar structure, keeping it in sync with the server.
"""

"""
 __                 
/  \        _______________________ 
|  |       /                       \
@  @       | It looks like you     |
|| ||      | are downloading files |
|| ||   <--| from CLIP. Do you     |
|\_/|      | need assistance?      |
\___/      \_______________________/
"""

# The code mimics the site's structure, as follows:
#       CLIP: Academic year   >> Course >> Document subcategory >> Files list >>   File
#     Clippy:  CourseList     >> Course >>      CatCount        >>  FilesList >> ClipFile
# Local copy:      Year       /  Course /       Category        /     Files

__author__ = "Afonso Bras Sousa (LEI-65263)"
__maintainer__ = "Afonso Bras Sousa"
__email__ = "ab.sousa@campus.fct.unl.pt"
__version__ = "0.9.9"

app = typer.Typer(add_completion=False)

def version_callback(value: bool):
    if value:
        print(f"Clippy version {__version__}")
        raise typer.Exit()

@app.command()
def single(
        id: Annotated[int, typer.Argument(help="O ID da cadeira a transferir.", show_default=False)],
        year: Annotated[int, typer.Argument(help="O ano lectivo a transferir.", show_default=False)],
        semester: Annotated[int, typer.Argument(help="O semestre a transferir.", show_default=False)],
        path: Annotated[Path, typer.Option("-p", "--path", help="A pasta onde os ficheiros do CLIP serão guardados.", show_default=False)] = None,
        is_trimester: Annotated[bool, typer.Option("--is-trimester/--is-semester", "-t/-s", help="Se a cadeira é trimestral ou semestral", show_default=True)] = False,
        username: Annotated[str, typer.Option("-u","--username",help="O nome de utilizador no CLIP.", show_default=False)] = None,
        relogin: Annotated[bool, typer.Option("--relogin", help="Ignora as credenciais guardadas em sistema.")] = False,
        debug: Annotated[bool, typer.Option("-d","--debug",help="Cria um ficheiro log.log para efeitos de debug.", hidden = True)] = False,
    ):
    """Transfere uma cadeira em específico."""

    start_routine(debug)

    name = str(id)

    # Check valid path
    if path is None:
        path = Path.cwd()
        if path.name != "CLIP": path = path / "CLIP"
    print(f"A iniciar o Clippy na directoria {path}...")
    path = check_path(path)

    #0) Start login
    userID = start_login(username, relogin)

    semester_type = "t" if is_trimester else "s"
    course = Course(name, id, year, semester, semester_type)

    # 2) Load the unit's index and compare it to cached file if it exists
    print_progress(2, "A verificar se há ficheiros novos...")
    subcats = search_cats_in_course(path, course)

    # Rename destination path to unit's name
    print(f"Encontrada cadeira {name}: {course.name}")
    name = course.name

    log.debug(f"Lista de subcategorias a procurar: {subcats}")

    # 3) (Multithreaded) Load each subcategory's table and compare it to the local folder
    print_progress(3, "A obter URLs dos ficheiros a transferir...")
    files = threadpool_execute(search_files_in_category, subcats)
    log.debug(f"Lista de ficheiros a transferir: {files}")
    
    # 4) (Multithreaded) Download missing files
    if len(files) != 0:
        download_time, download_size = download_files(files, path)
    else:
        print_progress(4, "Não há ficheiros a transferir.")

    # 5) Update cache after successful download
    print_progress(5, "A actualizar cache...")
    commit_cache()

    # 6) Exit with success
    print_progress(6, "Concluído :)")
    if len(files) != 0:
        unique_folders = sorted({str(file[0].parent) for file in files})
        print(f"Transferidos {len(files)} ficheiros ({human_readable_size(download_size)} em [dim cyan bold]{download_time}[/dim cyan bold]s = {human_readable_size(download_size/download_time)}/s) para as pastas:",flush=True)
        print("\n".join(f"'{folder}'" for folder in unique_folders))
    else:
        print("Não foram encontrados ficheiros novos.")
    
    check_for_save_credentials()

    raise typer.Exit()

@app.callback(invoke_without_command=True)
@app.command(help="Sincroniza os ficheiros de todas as cadeiras de um ano lectivo. [default]")
def batch(ctx: typer.Context,
        username: Annotated[str, typer.Option("-u", "--username",help="O nome de utilizador no CLIP.", show_default=False)] = None,
        path: Annotated[Path, typer.Option("-p", "--path", help="A pasta onde os ficheiros do CLIP serão guardados.", show_default=False)] = None,
        year: Annotated[int, typer.Option("-y","--year",help="Define o ano lectivo a transferir.", show_default=False)] = 0,
        auto: Annotated[bool, typer.Option(help="Escolhe automaticamente o ano lectivo mais recente.")] = True,
        relogin: Annotated[bool, typer.Option("--relogin", help="Ignora as credenciais guardadas em sistema.")] = False,
        debug: Annotated[bool, typer.Option("-d","--debug",help="Cria um ficheiro log.log para efeitos de debug.", hidden = True)] = False,
        version: Annotated[Optional[bool], typer.Option("-v", "--version", help=__version__, callback=version_callback, is_eager=True)] = None,
    ):
    """\bO Clippy é um simples web scrapper e gestor de downloads para a plataforma interna de e-learning da FCT-NOVA, o CLIP.
    O programa navega o CLIP à procura de ficheiros nas páginas das cadeiras de um utilizador e sincroniza-os com uma pasta local.
     __                 
    /  \\        _______________________ 
    |  |       /                       \\
    @  @       | Parece que estás a    |
    || ||      | tentar descarregar    |
    || ||   <--| ficheiros do CLIP.    |
    |\\_/|      | Posso ajudar-te?      |
    \\___/      \\_______________________/
    """

    if ctx.invoked_subcommand is not None:
        # Execute subcommand
        return
    
    start_routine(debug)

    # Check valid path
    if path is None:
        path = Path.cwd()
        if path.name != "CLIP": path = path / "CLIP"
    print(f"A iniciar o Clippy na directoria {path}...")
    path = check_path(path)

    #0) Start login and look for academic years
    userID = start_login(username, relogin)

    years = parse_years(userID)
    if year != 0 and year not in years.values:
        log.error("O utilizador não tem cadeiras inscritas no ano solicitado.")
        raise typer.Exit()
    elif len(years)<1:
        log.error("Não foram encontrados anos lectivos nos quais o utilizador está inscrito.")
        raise typer.Exit()
    elif len(years)==1:
        year = list(years.values())[0] # get index 0
        log.info(f"Encontrado apenas um ano lectivo ({year}).")
    elif auto:
        year = sorted(list(years.values()))[-1] # get index 0
        log.info("Modo automático activo, a escolher o ano lectivo mais recente...")
    else:
        year = inquirer.rawlist( #TODO multiselect
            message="Qual é o ano lectivo a transferir?",
            choices=[
                {"name": key, "value": value} for key, value in years.items()
            ],
            default=1,
            max_height=len(years)
        ).execute()
    log.debug(f"Ano: {year}")

    # 1) Scrape units list
    print_progress(1,"A procurar unidades curriculares inscritas...")
    courses = parse_courses(year,userID)
    log.info("Encontradas as seguintes unidades: "+" | ".join(course.name for course in courses) )

    # 2) (Multithreaded) Load each unit's index and compare it to cached file if it exists
    print_progress(2, "A verificar se há ficheiros novos...")
    subcats = threadpool_execute(search_cats_in_course, [(path, course) for course in courses])
    log.debug(f"Lista de subcategorias a procurar: {subcats}")

    # 3) (Multithreaded) Load each subcategory's table and compare it to the local folder
    print_progress(3, "A obter URLs dos ficheiros a transferir...")
    files = threadpool_execute(search_files_in_category, subcats)
    log.debug(f"Lista de ficheiros a transferir: {files}")
    
    # 4) (Multithreaded) Download missing files
    if len(files) != 0:
        download_time, download_size = download_files(files, path)
    else:
        print_progress(4, "Não há ficheiros a transferir.")

    # 5) Update cache after successful download
    print_progress(5, "A actualizar cache...")
    commit_cache()

    # 6) Exit with success
    print_progress(6, "Concluído :)")
    if len(files) != 0:
        unique_folders = sorted({str(file[0].parent) for file in files})
        print(f"Transferidos {len(files)} ficheiros ({human_readable_size(download_size)} em [dim cyan bold]{download_time}[/dim cyan bold]s = {human_readable_size(download_size/download_time)}/s) para as pastas:",flush=True)
        print("\n".join(f"'{folder}'" for folder in unique_folders))
    else:
        print("Não foram encontrados ficheiros novos.")
    
    check_for_save_credentials()

    raise typer.Exit()

def start_routine(debug) -> int:
    """Sets up the program environment and logs in.
    Returns the user's ID."""
    # Logging
    set_log_level(debug)

    # Disclaimer
    cfg.show_disclaimer()

    # Check for updates
    check_for_updates()

def start_login(username: str, force_relogin: bool = False):
    valid_login = False
    while not valid_login:
        try:
            if force_relogin:
                userID = get_login(username)
            elif username is None:
                userID = get_login(load_username(), load_password())
            else:
                userID = get_login(username, load_password(username))
            valid_login = True
        except LoginError:
            continue
    return userID
    
def set_log_level(debug: bool = False):
    logger = log.getLogger()
    logger.handlers.clear() #clear default logger
    logger.setLevel(log.DEBUG if debug else log.WARNING)

    #Console log
    console_formatter = log.Formatter('[%(levelname)s] %(message)s')
    console_logging = log.StreamHandler()
    console_logging.setLevel(log.DEBUG if debug else log.WARNING)
    console_logging.setFormatter(console_formatter)
    logger.addHandler(console_logging)

    #File log
    if debug:
        formatter = log.Formatter(
            '%(asctime)s.%(msecs)03d [%(levelname)s] %(module)s - %(funcName)s [%(lineno)s]: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )
        file_logging = log.FileHandler('debug.log')
        file_logging.setLevel(log.DEBUG)
        file_logging.setFormatter(formatter)
        logger.addHandler(file_logging)

def threadpool_execute(worker_function, items, max_workers=cfg.MAX_THREADS):
    results = []
    with cf.ThreadPoolExecutor(max_workers=max_workers) as pool: 
        futures = {pool.submit(worker_function, *args): args for args in items}
        
        for future in cf.as_completed(futures):
            args = futures[future]
            try:
                result = future.result()  # Get the result from the future
                if result is not None:
                    results.extend(result)
            except Exception as e:
                log.error(f"Erro a processar {args}: {e}")
    
    return results

def check_path(path: Path):
    if not path.exists():
        if inquirer.confirm(
            message=f"A directoria {path} não existe. Criá-la?",
            default=True,
            confirm_letter="s",
            reject_letter="n",
            transformer=lambda result: "Sim" if result else "Não",
        ).execute():
            path.mkdir(parents=True, exist_ok=True)
            print(f"A criar a directoria {path}.")
        else:
            path = query_path(path)
            check_path(path)
    elif not path.is_dir():
        print("O caminho desejado não é uma directoria válida.")
        path = query_path(path)
        check_path(path)
    return path

def query_path(path: Path = None):
    return Path(inquirer.filepath(
                message="Introduza a directoria onde pretende guardar os ficheiros:",
                default = str(path),
                only_directories=True,
            ).execute()).expanduser()

def dict_compare(dict_a: dict, dict_b: dict):
    if dict_b is None: return dict_a
    elif dict_a is None: return dict_b
    else: return {key: dict_a[key] for key in dict_a.keys() if key not in dict_b or dict_a[key] > dict_b[key]}

def search_cats_in_course(path: Path, course: Course) -> [(str, str, Course, Path)]:
    print(f"A procurar documentos de {course.name}...")
    path = path / str(course.year)

    index, course.name = parse_index(course.year, course.semester_type, course.semester, course.id)

    if not index: #skips creating directory if there are no documents
        log.info(f"Não foram encontrados documentos em {course.name}.")
    else:
        log.debug(f"Contagem para {course.name}: {index}")
        full_semester = str(course.semester)+course.semester_type.upper()
        full_path = path / full_semester / course.name

        full_path.mkdir(parents=True, exist_ok=True) # Create folder if it does not exist

        # Cache management
        cachedict = parse_cache(full_path, index, course.name)
        cachediff = dict_compare(index, cachedict)

        _subcats = []
        
        if not cachediff:
            log.debug(f"Sem diferenças para {course.name} em relação à contagem em cache.")
        else:
            log.debug(f"Em cache: {cachedict}")
            log.debug(f"No servidor: {index}")
            log.info(f"Categorias de {course.name} com novos ficheiros no servidor desde a última actualização: {cachediff}")
            # Update cache only if there are differences
            stash_cache(index,full_path)

            for category,count in cachediff.items():
                _subcats.append((category,index.get_catID(category),course,full_path))
                #search_files_in_category(category,index.get_catID(category),course,full_path)
        
        folderdict = count_files_in_subfolders(full_path)
        folderdiff = dict_compare(cachedict, folderdict)

        if not folderdiff:
            log.debug(f"Sem diferenças para {course.name} em relação à contagem de ficheiros.")
        else:
            log.warning(f"A contagem de ficheiros em {course.name} não coincide com a da última actualização. Quaisquer ficheiros apagados serão transferidos novamente.")
            log.debug(f"Na pasta: {folderdict}")
            log.debug(f"Em cache: {cachedict}")
            log.info(f"Pastas de {course.name} com menos ficheiros que a contagem em cache: {folderdiff}")

            for category,count in folderdiff.items():
                _subcats.append((category,index.get_catID(category),course,full_path))
                #search_files_in_category(category,index.get_catID(category),course,full_path)

        log.debug(f"Subcategorias de {course.name}: {_subcats}")
        return _subcats

def search_files_in_category(category: str, catID: str, course: Course, full_path: Path) -> [(Path, str, int, datetime)]:
    """
    Search for files in a specific category and download them if needed.

    Parameters:
        category (str): The category of files to search for.
        catID (str): The ID of respective category.
        course (Course): The course for which to search documents.
        full_path (Path): The full path to the directory where files should be downloaded.
    """
    try:
        print(f"A procurar {category} de {course.name}...")
        table = parse_docs(course.year,course.semester_type, course.semester, course.id, catID)

        _files = []
        for file in table:
            folder = full_path / category
            log.debug(f"A procurar {file} na pasta {folder}...")
            _file = get_file(file,folder)
            if _file is not None:
                _files.append(_file)
        
        log.debug(f"Ficheiros de {course} > {category}: {_files}")
        return _files

    except Exception as ex:
        log.error(f'Erro a procurar {category} de {course}: {str(ex)}')
        pass

def download_files(files, path) -> (int,int):
    """Download requested files to the specified path.
    
    Parameters:
    files: The array of files to download.
    path (Path): The path to save the files.
    
    Returns (download_time, download_size)
        download_time: How much time the download took.
        download_size: The total size of the downloaded files.
    """
    download_timestart = time.time_ns()
    download_sizestart = sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())
    print_progress(4, "A transferir ficheiros em falta...")
    _ = threadpool_execute(download_file, files, max_workers=4)
    print_progress(4,"Todos os ficheiros foram transferidos.")
    download_time = (time.time_ns() - download_timestart) / 10**9
    download_size = (sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())) - download_sizestart
    return download_time, download_size

def check_for_updates():
    '''Checks Github for updates.'''
    latest_version = get_latest_release()
    log.debug(f"Latest version: {latest_version}")
    log.debug(f"Current version: {__version__}")
    if latest_version != __version__:
        update_text = f"[bold underline red]!!!Actualização disponível!!![/bold underline red] ({__version__} → {latest_version})\nTransfere a versão mais recente em: https://github.com/abtsousa/clippy/releases/latest"
        print("*" * 45)
        print(update_text)
        print("*" * 45)
        print()
    else:
        log.info("Estás a usar a versão mais recente da aplicação.")


if __name__ == "__main__":
    try:
        commands = {'batch', 'single'}
        print(sys.argv)
        sys.argv.insert(1, 'batch') if sys.argv[1] not in commands else None
        app()
    except typer.Exit():
        if getattr(sys, 'frozen', False):
            log.debug("A correr a partir de EXE!")
            input("Pressiona ENTER para terminar o programa.")
        else:
            log.debug("A correr a partir de script, a terminar o programa automaticamente...")
            raise typer.Exit()
    except Exception:
        log.exception("Ocorreu um erro.\n")