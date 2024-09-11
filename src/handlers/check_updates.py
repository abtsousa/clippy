import requests
import logging as log

# Get the latest release from GitHub
def get_latest_release():
    """Checks github for the latest release."""
    url = "https://api.github.com/repos/abtsousa/clippy/releases/latest"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("tag_name")
    except requests.exceptions.HTTPError as errh: 
        log.warning("Não foi possível verificar a existência de actualizações. Verifica a tua ligação à internet.")
        log.warning(f"Erro HTTP {errh.args[0]}") 
    except requests.exceptions.ReadTimeout: 
        log.warning("Não foi possível verificar a existência de actualizações. Verifica a tua ligação à internet.")
        log.warning("Erro de Time out") 
    except requests.exceptions.ConnectionError: 
        log.warning("Não foi possível verificar a existência de actualizações. Verifica a tua ligação à internet.")
        log.warning("Erro de conexão")
    except requests.exceptions.RequestException: 
        log.warning("Não foi possível verificar a existência de actualizações. Verifica a tua ligação à internet.")
        log.warning("Erro de excepção") 