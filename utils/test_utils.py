import requests as req
from os import path
from pathlib import Path

API_URL = "http://localhost:5000"


def req_with_auth(user=None):
    r = req.Session()
    if user is None:
        r.auth = ('pctest.admin@btmx.fr', 'pctestadmin')
    else:
        json_path = Path(path.dirname(path.realpath(__file__))) / '..' / 'mock'\
                    / 'users_jeunes.json'
        with open(json_path) as json:
            for user_json in json.load(json):
                if user.email == user_json.email:
                    r.auth = (user_json.email, user_json.password)
                    break
                else:
                    raise ValueError("Utilisateur inconnu: "+user)
    return r
