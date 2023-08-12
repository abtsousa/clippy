import os

#Config
import config

class Folder(str):
    """
    Represents a local folder.

    This class inherits from the built-in str class and provides additional
    functionality for working with file paths and creating directories.

    Args:
        path (str): The file path for the folder.

    Attributes:
        path (str): The file path for the folder.

    Methods:
        join(path2: str) -> Folder:
            Append a path to the current folder path and return a new Folder instance.
        get_filepath(filename: str) -> str:
            Get the full path to a file inside the folder.

    Usage:
        folder = Folder("path/to/folder")
        new_folder = folder.join("subfolder")
        file_path = folder.get_filepath("file.txt")
    """

    def __new__(cls, path):
        """
        Create a Folder instance and create the folder if it doesn't exist.

        Args:
            path (str): The file path for the folder.
        """
        cls.create(path)
        return super().__new__(cls, path)
    
    def create(path):
        if not os.path.isdir(path):
            print(f"A criar a directoria '{path}'...")
            os.makedirs(path)
    
    def join(self, path2: str) -> 'Folder':
        """
        Append a path to the current folder path and return it as a new Folder instance.

        Args:
            path2 (str): The path to append to the current folder path.

        Returns:
            Folder: A new Folder instance representing the combined path.
        """
        return Folder(os.path.join(self, path2))

    def get_filepath(self, filename: str) -> str:
        """
        Get the full path to a file inside the folder.

        Args:
            filename (str): The name of the file inside the folder.

        Returns:
            str: The full file path.
        
        Raises:
            FileNotFoundError: If the specified file does not exist in the folder.
        """
        fullpath = os.path.join(self, filename)
        if not os.path.isfile(fullpath):
            raise FileNotFoundError(f"O ficheiro {filename} não foi encontrado na pasta {self}.")
        return fullpath