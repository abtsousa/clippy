#Config
import config as cfg

def get_URL_YearList(user: int):
    """
    Generate the URL to the user page in CLIP.
    
    Parametes:
        user (int): The user ID.
        
    Returns:
        str: The generated URL.
    """
    return f"{cfg.domain}/utente/eu/aluno?aluno={user}"

def get_URL_CourseList(year: int, user: int):
    """
    Generate the URL to the list of academic courses in CLIP.

    Parameters:
        year (int): The academic year.
        user (int): The user ID.

    Returns:
        str: The generated URL.
    """
    return f"{cfg.domain}/utente/eu/aluno/ano_lectivo/unidades?ano_lectivo={year}&institui%E7%E3o=97747&aluno={user}"

def get_URL_Index(year: int, semester_type: str, semester: int, course: int):
    """
    Generate the URL to the index of download categories for a specific course in a semester.

    Parameters:
        year (int): The academic year.
        semester_type (str): Specify whether it's a semester ("s") or a trimester ("t").
        semester (int): The semester number.
        course (int): The course ID.

    Returns:
        str: The generated URL.
    """
    return f"{cfg.domain}/utente/eu/aluno/ano_lectivo/unidades/unidade_curricular/actividade/documentos?edi%E7%E3o_de_unidade_curricular={course},97747,{year},{semester_type},{semester}"

def get_URL_FileList(year: int, semester_type: str, semester: int, course: int, doc_type: str):
    """
    Generate the URL to retrieve a list of downloads for a specific course and document type in a semester.

    Parameters:
        year (int): The academic year.
        semester_type (str): Specify whether it's a semester ("s") or a trimester ("t").
        semester (int): The semester number.
        course (int): The course ID.
        doc_type (str): The type of document.

    Returns:
        str: The generated URL.
    """
    return f'{cfg.domain}/utente/eu/aluno/ano_lectivo/unidades/unidade_curricular/actividade/documentos?tipo_de_per%EDodo_lectivo={semester_type}&tipo_de_documento_de_unidade={doc_type}&ano_lectivo={year}&per%EDodo_lectivo={semester}&unidade_curricular={course}'
