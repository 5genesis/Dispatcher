import json
from jwcrypto import jwk


def set_key():
    json1_file = open('key.json')
    json1_str = json1_file.read()
    json1_data = json.loads(json1_str)
    return jwk.JWK(**json1_data)


class Settings:

    KEY = None

    def __init__(self):
        self.KEY = set_key()
