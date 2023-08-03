"""
Clipper
A simple python web scrapper for FCT-NOVA's own e-learning platform, Clip.
"""

__author__ = "Afonso Bras Sousa"
__maintainer__ = "Afonso Bras Sousa"
__email__ = "ab.sousa@campus.fct.unl.pt"
__version__ = 0.1

import requests
from bs4 import BeautifulSoup as bs
import re

def get_html(user, password, url):
  form_data = {'identificador': user, 'senha': password}
  response = requests.post("https://clip.fct.unl.pt/utente/eu/aluno/ano_lectivo/unidades/unidade_curricular/actividade/documentos?tipo_de_per%EDodo_lectivo=s&tipo_de_documento_de_unidade=t&ano_lectivo=2023&per%EDodo_lectivo=1&unidade_curricular=11504", data=form_data)
  soup = bs(response.text, 'html.parser')

links = []
for link in soup.find_all('a', href=re.compile("^/objecto*")):
  links.append(link.get('href'))
print(links)