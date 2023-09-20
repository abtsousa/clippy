from datetime import datetime
from tqdm import tqdm
from pathlib import Path
from rich import print
import logging as log
import os
import requests

from modules.ClipFile import ClipFile

#Config
import clippy.config as cfg

def download_file(filepath: Path, url: str, file_size=0, file_mtime=None):
    """
    Download a file from a given URL to a specified filepath.

    Parameters:
        filepath (Path): The path where the downloaded file will be saved.
        url (str): The URL of the file to download.
        file_size (int, optional): The expected size of the file in bytes. Defaults to 0.
        file_mtime (datetime.datetime, optional): The desired modification time for the downloaded file. Defaults to None.
    """
    try:
        r = cfg.session.get(url, stream=True)
        if file_size==0: file_size=r.headers['Content-Length']
        chunk_size = 1024
        downloaded_size = 0

        if r.status_code == 200:
            Path.mkdir(filepath.parent,parents=True, exist_ok=True)
            with open(filepath, 'wb+') as f:
                pbar = tqdm(total=file_size, unit="B", unit_scale=True, unit_divisor=1024, desc=f"A transferir {fixed_string_length(filepath.name,30)}")
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        downloaded_size += len(chunk)
                        pbar.update(len(chunk))
                        f.write(chunk)
                pbar.total=downloaded_size #force show 100% if file size overestimated or downloaded too fast
                pbar.refresh()
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

def get_file(file: ClipFile, path: Path) -> (Path, str, int, datetime):
    """
    Search for a local file.
    Calls download_to_file() to (re)download it if it's older or not found.

    Parameters:
        file (ClipFile): The file to download.
        path (Path): The path where the file should be saved.
    """
    log.debug(f"{file} {file.is_synced(path)}")
    file_path = path / file.name
    
    sync_status = file.is_synced(path)

    if sync_status is None:
        return (path / file.name,file.link,file.size,file.mtime)
    elif sync_status: #True
        log.info(f"Encontrado {file.name} na pasta '{path}', a saltar...")
        return None
    else: #False
        log.warning(f"O ficheiro '{file_path}' está desactualizado e vai ser transferido.")
        #download_to_file(path / file.name,file.link,file.size,file.mtime)
        return (path / file.name,file.link,file.size,file.mtime)

def count_files_in_subfolders(path: Path) -> dict:
    result = {}
    for folder in path.iterdir():
        if folder.is_dir():
            file_count = sum(1 for _ in folder.glob('*') if _.is_file() and not _.name.startswith('.'))
            result[folder.name] = file_count
    return result

def fixed_string_length(input_string, target_length=30):
    if len(input_string) <= target_length:
        padding_length = target_length - len(input_string)
        padded_string = input_string + ' ' * padding_length
        return padded_string
    else:
        truncation_length = target_length - 3  # Account for the '...' part
        truncated_string = input_string[:truncation_length//2+1] + '...' + input_string[-(truncation_length//2):]
        return truncated_string