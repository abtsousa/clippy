from datetime import datetime
import os
import pandas as pd

from modules.Folder import Folder

#Config
import config

class ClipFile:
    """
    Represents a file in CLIP, and its associated information.

    Args:
        row (pd.Series): A pandas Series containing data for the file.

    Attributes:
        name (str): The name of the file.
        link (str): The download link for the file.
        mtime (datetime.datetime): The modification time of the file.
        size (int): The size of the file in bytes.
        teacher (str): The name of the teacher who uploaded the file.

    Methods:
        is_synced(path: Folder) -> bool, None:
            Check if the file is synchronized with a local path.

    Usage:
        row_data = pd.Series(...)  # Contains data for the file
        file = ClipFile(row_data)  # Create an instance of the ClipFile class
        folder = Folder(...)        # Create an instance of the Folder class
        
        synced = file.is_synced(folder)  # Check if clip file is synchronized with the local folder

    """

    def __init__(self, row: pd.Series):
        """
        Initialize a ClipFile instance based on a pandas Series.

        Args:
            row (pd.Series): A pandas Series containing data for the clip file.
        """
        self.name = row.at["Nome"]
        self.link = row.at["Link"]
        self.mtime = datetime.strptime(row.at["Data"], "%Y-%m-%d %H:%M")
        self.size = row.at["Tamanho"]
        self.teacher = row.at["Docente"]
  
    def __str__(self):
        """
        Get a string representation of the ClipFile instance.

        Returns:
            str: A string representation of the ClipFile instance.
        """
        return f"{self.name} {self.link} {self.mtime} {self.size} {self.teacher}"
    
    def is_synced(self, path: Folder):
        """
        Check if the file is synchronized with a local path.

        Args:
            path (Folder): An instance of the Folder class representing the
                          local path where the file is expected to exist.

        Returns:
            True if the file is synchronized (up to date).
            False if the file exists but is outdated.
            None if the file does not exist at the specified path.
        """
        try:
            return (datetime.fromtimestamp(os.path.getmtime(path.get_filepath(self.name))) >= self.mtime)
        except FileNotFoundError:
            return None
