import re
import logging as log

#Config
import clippy.config as cfg

class Course:
    """
    Represents an academic course with associated information.
    The program automatically extracts the relevant attributes from the associated link.

    Args:
        name (str): The name of the course.
        year (int): The academic year associated with the course.
        id (int): The identifier for the course.
        semester_type (str): Specify whether it's a semester ("s") or a trimester ("t").
        semester (str): The semester number.

    Usage:
        course = Course(name, year, ID, semester_type, semester)
        course = Course.from_link(name, link)
    """

    def __init__(self, name: str, id: int, year: int, semester: int, semester_type: str = "s"):
        self.name = name
        self.id = id
        self.year = year
        self.semester = semester
        self.semester_type = semester_type
        log.debug(f"Novo objecto Course: name:{name} id:{id} year:{year} semester:{semester} semester_type:{semester_type}")

    @classmethod
    def from_link(cls, name: str, link: str):
        """
        Initialize a Course instance from its page link.

        Args:
            name (str): The name of the course.
            link (str): The link to the course's details page.

        """
        obj = cls.__new__(cls)
        super(Course, obj).__init__()
        obj.name = name
        obj.year = int(re.search(r"ano_lectivo=(\d+)", link).group(1))
        obj.id = int(re.search(r"unidade=(\d+)", link).group(1))
        obj.semester_type = re.search(r"tipo_de_per%EDodo_lectivo=(\w)", link).group(1)
        obj.semester = re.search(r"per%EDodo_lectivo=(\d)", link).group(1)
        return obj
    
    def __str__(self):
        """
        Get a string representation of the Course instance.

        Returns:
            str: A string representation of the Course instance.
        """
        return self.name
