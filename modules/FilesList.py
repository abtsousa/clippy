from bs4 import BeautifulSoup as bs
from .ClipFile import ClipFile

#Config
import clippy.config as cfg

class FilesList:
    """
    Represents a subcategory of documents, that are displayed in CLIP as a table of downloadable files.
    Returns an array of ClipFile objects, one for each file in the table.

    Args:
        html (bs): Beautiful Soup object containing the HTML content of the table.

    Methods:
        convert_str_to_byte(size: str) -> int:
            Convert a human-readable size string to bytes.

    """

    def __new__(cls, html: bs) -> [ClipFile]:
        """
        Create an array of ClipFile instances based on a subcategory's table.

        Args:
            html (bs): Beautiful Soup object containing the HTML content of the table.

        Returns:
            [ClipFile]: An array of ClipFile instances.
        """
        flist = []
        table = html.find('th', string='Documentos').find_parent('table')
        for row in table.find_all("tr", {'bgcolor': True}):
            columns = row.find_all("td")

            if columns != []:
                name = columns[0].text.strip()
                link = cfg.domain + columns[1].find("a").get("href")
                date = columns[2].text.strip()
                size = cls.convert_str_to_byte(columns[3].text.strip())
                teacher = columns[4].text.strip()

                file = ClipFile(name,link,date,size,teacher)

                flist.append(file)
        
        return flist
    
    def convert_str_to_byte(size: str) -> int:
        """
        Convert a human-readable size string to bytes.

        Args:
            size (str): The size string, e.g., "1.2 MB".

        Returns:
            int: The size in bytes.
        """
        size_name = ("B", "Kb", "Mb", "Gb", "Tb")
        # divide '1 GB' into ['1', 'GB']
        num, unit = int(size[:-2]), size[-2:]
        idx = size_name.index(unit)        # index in list of sizes determines power to raise it to
        factor = 1024 ** idx
        num += 1 # Hack to get the right size since the size in the html table actually rounds it wrong
        return num * factor