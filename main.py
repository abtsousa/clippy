import requests, sys, getpass, pandas


class LoginError(Exception):
    "Raised when the login fails"
    print("Autenticação falhou.")
    pass


def getLogin():
    print('Username:')
    username = input()
    password = getpass.getpass()

    # Fill in your details here to be posted to the login form.
    payload = {
        'identificador': username,
        'senha': password
    }

    return payload


# Use 'with' to ensure the session context is closed after use.
with requests.Session() as s:
    while True:
        try:
            p = s.post('https://clip.fct.unl.pt/', data=getLogin())
            if "Autenticação inválida" in p.text:
                raise LoginError("Autenticação falhou.")
            break
        except LoginError:
            pass

    #TODO https://clip.fct.unl.pt/utente/eu -> aluno -> ano lectivo -> unidades curriculares por semestre

    # An authorised request.
    r = s.get('https://clip.fct.unl.pt/utente/eu/aluno/ano_lectivo/unidades?tipo_de_per%EDodo_lectivo=s&ano_lectivo=2023&per%EDodo_lectivo=1&aluno=118029&institui%E7%E3o=97747&unidade_curricular=11505')
    r.raise_for_status()

    tb_list = pandas.read_html(r.text)
    files = tb_list[9]
    print(files.loc[0])
    print("Finished.")
    
