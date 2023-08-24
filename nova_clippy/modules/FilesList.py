from bs4 import BeautifulSoup as bs
from .ClipFile import ClipFile
import pandas as pd

#Config
import nova_clippy.config as cfg

class FilesList:
    """
    Represents a subcategory of documents, that are displayed in CLIP as a table of downloadable files.
    Returns an array of ClipFile objects, one for each file in the table.

    Args:
        html (bs): Beautiful Soup object containing the HTML content of the table.

    Methods:
        convert_str_to_byte(size: str) -> int:
            Convert a human-readable size string to bytes.
        get_files_table(html: bs) -> pd.DataFrame:
            Internal method that extracts the downloads table from the HTML content.

    Usage:
        html_content = ...
        dtable = FilesList(html_content)
    """

    def __new__(cls, html: bs) -> [ClipFile]:
        """
        Create an array of ClipFile instances based on a subcategory's table.

        Args:
            html (bs): Beautiful Soup object containing the HTML content of the table.

        Returns:
            [ClipFile]: An array of ClipFile instances.
        """
        files = []
        table = cls.get_files_table(cls,html)
        for row in table.index:
            file = ClipFile(table.iloc[row])
            files.append(file)

        return files
    
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
        factor = 1024 ** idx               # ** is the "exponent" operator - you can use it instead of math.pow()
        num += 1 # Hack to get the right size since the size in the html table actually rounds it wrong
        return num * factor

    def get_files_table(self, html: bs) -> pd.DataFrame:
        """
        Extract the table from the HTML content.

        Args:
            html (bs): Beautiful Soup object containing the HTML content of the table.

        Returns:
            pd.DataFrame: A DataFrame containing data for the downloads table.
        """
        df = pd.DataFrame(columns=['Nome', 'Link', 'Data', 'Tamanho', 'Docente'])
        table = html.find_all("form")[1].find("table") # get downloads table TODO parse file size
        for row in table.find_all("tr", {'bgcolor': True}):
            columns = row.find_all("td")

            if columns != []:
                nome = columns[0].text.strip()
                link = cfg.domain + columns[1].find("a").get("href")
                data = columns[2].text.strip()
                tamanho = self.convert_str_to_byte(columns[3].text.strip())
                docente = columns[4].text.strip()

                row = pd.DataFrame({"Nome": [nome], "Link": [link], "Data": [data], "Tamanho": [tamanho], "Docente": [docente]})

                df = pd.concat([df, row], ignore_index=True)
        
        return df
