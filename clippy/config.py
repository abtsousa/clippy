from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from requests import Session
import logging as log
from pathlib import Path
from InquirerPy import inquirer
from appdirs import user_data_dir

# Multithreading
MAX_THREADS = 8

def session_mount():
    global session
    #Implement auto retry
    retry_strategy = Retry(
        total=3,  # Number of total retries (including the initial request)
        backoff_factor=0.3,  # Factor to apply exponential backoff between retries
        status_forcelist=[500, 502, 503, 504],  # HTTP status codes to retry
    )

    # Create a custom HTTP adapter with the retry strategy
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    log.debug("Sessão montada com sucesso.")

def show_disclaimer():
    """Shows the disclaimer if it's the first time running the program."""
    discpath = cfgpath.parent / "disclaimer_shown"
    if not Path.is_file(discpath):
        print(disclaimer)
        Path.mkdir(discpath.parent, exist_ok=True)
        Path.touch(discpath, exist_ok=True)

# Disclaimer
disclaimer = '''
NOTA: Este programa é fornecido "tal como está" e destina-se estritamente ao uso privado, 
limitado às suas funcionalidades de transferência de arquivos. Ao utilizar este programa, 
o utilizador concorda em isentar o autor de qualquer responsabilidade por danos ou 
consequências decorrentes de uso inadequado ou inesperado, incluindo, mas não se limitando a, 
bugs, erros de servidor ou uso indevido de funcionalidades não previstas inicialmente. Se não 
concordar, desinstale imediatamente o programa. Esta mensagem não aparecerá novamente.
'''

# Domain
domain='https://clip.fct.unl.pt'

cfgpath = Path(user_data_dir("clippy")) / "config.ini"

session_mount()

log.info("Config.py carregado.")