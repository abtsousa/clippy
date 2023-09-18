from bs4 import BeautifulSoup as bs
import re
import logging as log
from .get_URL import get_URL_YearList, get_URL_CourseList, get_URL_FileList, get_URL_Index
from .get_html import get_html
from modules.CatCount import CatCount
from modules.CourseList import CourseList
from modules.FilesList import FilesList

#Config
import clippy.config as cfg

def parse_years(user: int):
    """
    Parse the user page to look for academic years the user was enrolled in.
    """

    url = get_URL_YearList(user)
    soup = bs(get_html(url), 'html.parser')
    links = soup.find_all("a", {"href": re.compile(r"ano_lectivo.+&ano_lectivo=(\d+)")})
    log.debug(links)
    #years = {match.group(1) for link in links if (match := re.search(r"ano_lectivo.+&ano_lectivo=(\d+)", link))}
    years = { link.text : int(re.search(r"ano_lectivo.+&ano_lectivo=(\d+)",link['href']).group(1)) for link in links }

    log.debug(years)
    return years

def parse_index(year: int, semester_type: str, semester: int, course: int):
    """
    Parse the index of documents for a specific course in a semester and return it as a CatCount dictionary.

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

def parse_docs(year: int, semester_type: str, semester: int, course: int, category: str):
    """
    Parse a list of documents for a specific course and document category in a semester.
    Returns an array of ClipFile objects, one for each document.

    Parameters:
        year (int): The academic year.
        semester_type (str): Specify whether it's a semester ("s") or a trimester ("t").
        semester (int): The semester number.
        course (int): The course ID.
        category (str): The category of document.

    Returns:
        FilesList: An array of ClipFile objects.
    """
    url = get_URL_FileList(year,semester_type,semester,course,category)
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