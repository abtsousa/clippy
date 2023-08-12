from tqdm import tqdm
import logging as log
import os

from modules.ClipFile import ClipFile
from modules.Folder import Folder

#Config
import config

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
        r = config.session.get(url, stream=True)
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
            log.info(f"Encontrado {file.name} na pasta '{path}', a saltar...")
        case False:
            print(f"O ficheiro '{file_path}' está desactualizado, a transferir...")
            download_to_file(os.path.join(path,file.name),file.link,file.size,file.mtime)
        case None:
            print(f"A transferir '{file_path}'...")
            download_to_file(os.path.join(path,file.name),file.link,file.size,file.mtime)
