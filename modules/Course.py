import re

#Config
import clippy.config as cfg

class Course:
    """
    Represents an academic course with associated information.
    The program automatically extracts the relevant attributes from the associated link.

    Args:
        name (str): The name of the course.
        link (str): The link to the course's details page.

    Attributes:
        name (str): The name of the course.
        year (int): The academic year associated with the course.
        ID (int): The identifier for the course.
        semester_type (str): Specify whether it's a semester ("s") or a trimester ("t").
        semester (str): The semester number.

    Usage:
        course = Course(name, link)
    """

    def __init__(self, name: str, link: str):
        """
        Initialize a Course instance.

        Args:
            name (str): The name of the course.
            link (str): The link to the course's details page.
        """
        self.name = name
        self.year = int(re.search(r"ano_lectivo=(\d+)", link).group(1))
        self.ID = int(re.search(r"unidade=(\d+)", link).group(1))
        self.semester_type = re.search(r"tipo_de_per%EDodo_lectivo=(\w)", link).group(1)
        self.semester = re.search(r"per%EDodo_lectivo=(\d)", link).group(1)
    
    def __str__(self):
        """
        Get a string representation of the Course instance.

        Returns:
            str: A string representation of the Course instance.
        """
        return self.name
