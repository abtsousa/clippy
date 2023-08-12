import re
import logging as log
from bs4 import BeautifulSoup as bs

from modules.Course import Course

#Config
import config

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
        try:
            log.debug(str(html))
            table = html.find_all("td", attrs={"width": "100%"})[1].find_all("a", {"href": re.compile(r"&unidade=(\d+)")}) # TODO possivel IndexError out of range
            return table
        except IndexError as error: #TODO DEBUG
            log.error(f"Falha crítica: o servidor devolveu conteúdo HTML inválido. Espere uns segundos e tente novamente.\nO servidor devolveu o seguinte conteúdo HTML:\n {html}")
            exit()