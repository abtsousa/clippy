import requests
import logging as log

# Get the latest release from GitHub
def get_latest_release():
    url = "https://api.github.com/repos/abtsousa/clippy/releases/latest"
    response = requests.get(url)
    data = response.json()
    return data.get("tag_name")