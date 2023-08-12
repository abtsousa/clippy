import json
import logging as log
from pathlib import Path

from modules.CatCount import CatCount

#Config
import config # noqa: F401

def store_cache(dict: CatCount, folder: Path):
    """
    Creates a cache JSON file that stores a CatCount dictionary.
    
    Args:
        count (dict): A CatCount dictionary that stores a file count.
    """
    cache = folder / ".cache.json"
    if not cache.exists(): Path.touch(cache)
    with open(cache, 'w') as json_file:
        json.dump(dict, json_file)

def load_cache(folder: Path) -> dict:
    try:
        cache = folder / ".cache.json"
        with open(cache, 'r') as json_file:
            dict = json.load(json_file)
        return dict
    except FileNotFoundError:
        return None

def parse_cache(full_path: Path, index: CatCount, coursename: str):
    """
    Loads a cached file with the CatCount data from the previous scrape and updates it.
    Compares it to the current CatCount dict (index).
    Returns the differences.

    Parameters:
        full_path (Path): The path to the folder where cache is stored.
        index (CatCount): The fresh scraped data.
        coursename (str): The course's name.
    """
    cache = load_cache(full_path)  # loads cache
    cachediff = {}

    if cache is None:  # check difference between cached count and scraped count
        log.info(f"Não foi encontrada contagem em cache para {coursename}. A criar...")
        cachediff = index
    else:
        log.debug(f"Contagem em cache para {coursename}: {cache}")
        cachediff = {key: index[key] for key in index.keys() if key not in cache or index[key] != cache[key]}

    if not cachediff:
        log.debug(f"Sem diferenças para {coursename} em relação à contagem em cache.")
    else:
        log.debug(f"Categorias de {coursename} com contagem diferente desde a última atualização: {cachediff}")
        # Update cache only if there are differences
        store_cache(index,full_path)

    return cachediff