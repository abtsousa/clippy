import re
import logging as log
from bs4 import BeautifulSoup as bs

from .Course import Course

#Config
import clippy.config as cfg

class CourseList(list):
    """
    Represents a list of academic courses with associated links.

    Args:
        html (bs): Beautiful Soup object containing the HTML of a Courses page in CLIP.
    """

    def __init__(self, html: bs):
        """
        Initialize a CourseList instance based on HTML content.

        Args:
            html (bs): Beautiful Soup object containing the HTML of a Courses page in CLIP.
        """
        super().__init__()
        links = self.get_links(html)
        courses = [Course.from_link(link.text, link['href']) for link in links]
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
            html (bs): Beautiful Soup object containing the HTML of a Courses page in CLIP.

        Returns:
            An array of links.
        """
        try:
            log.debug(str(html))
            table = html.find_all("td", attrs={"width": "100%"})[1].find_all("a", {"href": re.compile(r"&unidade=(\d+)")}) # TODO possivel IndexError out of range
            return table
        except IndexError:
            log.error(f"Falha crítica: o servidor devolveu conteúdo HTML inválido. Espere uns segundos e tente novamente.\n"
                      f"O servidor devolveu o seguinte conteúdo HTML:\n {html}")
            exit()