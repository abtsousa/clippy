import re
from bs4 import BeautifulSoup as bs

#Config
import config as cfg # noqa: F401

class CatCount(dict):
    """
    Short for CategoryCount - a dictionary representing CLIP's subcategory index (key)
    with respective file count (value).
    This class inherits from the built-in dictionary class.

    Args:
        html (bs): Beautiful Soup object containing the HTML content.

    Methods:
        get_links(html: bs) -> List[bs.Tag]:
            Internal method that extracts links from the HTML content.
        get_catID(key: str) -> str:
            Get the ID for a given category (key).

    Usage:
        html_content = ...
        index_count = CatCount(html_content)
    """

    def __init__(self, html: bs):
        """
        Initialize an CatCount instance based on HTML content.

        Args:
            html (bs): Beautiful Soup object containing the HTML content.
        """
        super().__init__()
        links = self.get_links(html)
        counter = [re.search(r"^(\D+) \((\d+)\)", match.text.strip()).group(1, 2) for match in links]
        for key, value in counter:
            if int(value) != 0: #ignore links with zero files
                self[key] = int(value)
    
    def get_links(self, html: bs):
        """
        Extract all links from the HTML content.

        Args:
            html (bs): Beautiful Soup object containing the HTML content.

        Returns:
            [bs.Tag]: An array of Beautiful Soup Tag objects.
        """
        table = html.find_all("td", attrs={"width": "100%"})[1].find_all("a")
        return table

    def get_catID(self, category: str) -> str:
        """
        Get the URL code / ID for a given category.

        Args:
            category (str): The category for which to retrieve the ID.

        Returns:
            str: The corresponding ID.
        """
        ID_dict = {
            "Material Multimédia": "0ac",
            "Problemas": "1e",
            "Protocolos": "2tr",
            "Seminários": "3sm",
            "Exames": "ex",
            "Testes": "t",
            "Textos de Apoio": "ta",
            "Outros": "xot",
        }
        return ID_dict[category]
    