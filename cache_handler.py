import json
import logging as log
from pathlib import Path

from modules.CatCount import CatCount

#Config
import config # noqa: F401

cache_stack = []

def stash_cache(dict: CatCount, folder: Path):
    """
    Stores JSON dump operations in an array for later execution with commit_cache().
    
    Args:
        dict (CatCount): A CatCount dictionary that stores a file count.
        folder (Path): The folder where cache is to be stored
    """
    global cache_stack
    cache_stack.append((folder / ".cache.json", dict))

def commit_cache():
    """
    Creates a cache JSON file that stores a CatCount dictionary that was previously stashed with stash_cache().
    
    Args:
        count (dict): A CatCount dictionary that stores a file count.
    """
    global cache_stack
    for file, dict in cache_stack:
        with open(file, 'w+') as json_file:
            json.dump(dict, json_file)

def parse_cache(full_path: Path, index: CatCount, coursename: str):
    """
    Loads a cached file with the CatCount data from the previous scrape.

    Parameters:
        full_path (Path): The path to the folder where cache is stored.
        index (CatCount): The fresh scraped data.
        coursename (str): The course's name.
    """
    try:
        cache_path = full_path / ".cache.json"
        with open(cache_path, 'r') as json_file:
            cache = json.load(json_file)
    except FileNotFoundError:
        log.info(f"Não foi encontrada contagem em cache para {coursename}.")
        return None

    log.debug(f"Contagem em cache para {coursename}: {cache}")
    return cache