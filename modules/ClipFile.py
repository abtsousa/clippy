from datetime import datetime
from pathlib import Path
import os

#Config
import clippy.config as cfg

class ClipFile:
    """
    Represents a file in CLIP, and its associated information.

    Args:
        name (str): The name of the file.
        link (str): The download link for the file.
        mtime (datetime.datetime): The modification time of the file.
        size (int): The size of the file in bytes.
        teacher (str): The name of the teacher who uploaded the file.

    Methods:
        is_synced(path: Path) -> bool, None:
            Check if the file is synchronized with the corresponding local folder.

    Usage:
        file = ClipFile(name, link, mtime size, teacher)  # Create an instance of the ClipFile class
        folder = Path(...)        # Create an instance of the Path class
        
        synced = file.is_synced(folder)  # Check if clip file is synchronized with the local folder

    """

    def __init__(self, name : str, link : str, mtime, size, teacher : str):
        """
        Initialize a ClipFile instance.
        """
        self.name = name
        self.link = link
        self.mtime = datetime.strptime(mtime, "%Y-%m-%d %H:%M")
        self.size = size
        self.teacher = teacher
  
    def __str__(self):
        """
        Get a string representation of the ClipFile instance.

        Returns:
            str: A string representation of the ClipFile instance.
        """
        return f"{self.name} {self.link} {self.mtime} {self.size} {self.teacher}"
    
    def is_synced(self, path: Path):
        """
        Check if the file is synchronized with a local path.

        Args:
            path (Path): local path where the file is expected to exist.

        Returns:
            True if the file is synchronized (up to date).
            False if the file exists but is outdated.
            None if the file does not exist at the specified path.
        """
        try:
            return (datetime.fromtimestamp(os.path.getmtime(path / self.name)) >= self.mtime)
        except FileNotFoundError:
            return None
