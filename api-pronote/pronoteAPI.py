import requests
from bs4 import BeautifulSoup
import random
from Crypto.Hash import MD5, SHA256
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Util import Padding
from Crypto.PublicKey import RSA
import base64
import json


class API(object):
    def __init__(self, site):
        self.communication = Communication(site)
        self.options = self.communication.initialise()
        self.encryption = Encryption()
        self.encryption.aes_iv = self.communication.encryption.aes_iv

    def login(self, username, password):
        # TODO: PAGe a expire
        ident_json = {"nom": "Identification",
                      "donneesSec":
                          {"donnees":
                               {"genreConnexion": "0",
                                "genreEspace": self.options['a'],
                                "identifiant": username,
                                "pourENT": "false",
                                "enConnexionAuto": "false",
                                "demandeConnexionAuto": "false",
                                "demandeConnexionAppliMobile": "false",
                                "demandeConnexionAppliMobileJeton": "false",
                                "uuidAppliMobile": "",
                                "loginTokenSAV": ""}}}
        idr = self.communication.post(ident_json)
        print("identification pass")
        print(idr.content)
        id_response = json.loads(idr.content)
        alea = id_response['donneesSec']['donnees']['alea']
        challenge = id_response['donneesSec']['donnees']['challenge']
        motdepasse = SHA256.new(alea + password).hexdigest().upper()
        del password
        cle = username + motdepasse
        self.encryption.aes_key = cle
        ch_dec = self.enleverAlea(self.encryption.aes_decrypt(challenge.encode()).decode())
        ch = self.encryption.aes_encrypt(ch_dec.encode()).decode()
        auth_json = {"nom": "Authentification",
                     "donneesSec": {
                         "donnees": {
                             "connexion": 0,
                             "challenge": ch,
                             "espace": self.options['a']}}}
        print(self.communication.post(auth_json).content)

    @staticmethod
    def enleverAlea(text):
        n = len(text)
        sansalea = []
        for i in range(n):
            if i % 2 == 0:
                sansalea.append(text[i])
        return ''.join(sansalea)


class Communication(object):
    def __init__(self, site):
        self.root_site = self.get_root_address(site)
        self.session = requests.Session()
        self.encryption = Encryption()
        self.attributes = {}
        self.initial_response = None
        self.request_number = 1

    def initialise(self):
        headers = {'connection': 'keep-alive',
                   'cache-control': 'max-age=0',
                   'DNT': '1',
                   'Upgrade-Insecure-Requests': '1',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/79.0.3945.117 Safari/537.36',
                   'Sec-Fetch-User': '?1',
                   'Accept': '*/*',
                   'Sec-Fetch-Site': 'same-origin',
                   'Sec-Fetch-Mode': 'cors',
                   'Accept-Encoding': 'gzip, deflate, br',
                   'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,cs;q=0.7'}
        get_response = self.session.request('GET', self.root_site + '/eleve.html', headers=headers)
        self.attributes = self._parse_html(get_response.content)
        request_number = self.encryption.aes_encrypt(str(self.request_number).encode()).hex()
        self.encryption.rsa_keys = {'MR': self.attributes['MR'], 'ER': self.attributes['ER']}
        uuid = base64.b64encode(self.encryption.rsa_encrypt(self.encryption.aes_iv_temp)).decode()
        self.encryption.aes_set_iv()
        p_site = self.root_site + '/appelfonction/' + self.attributes['a'] + '/' + self.attributes[
            'h'] + '/' + request_number
        json_post = {'session': int(self.attributes['h']), 'numeroOrdre': request_number, 'nom': 'FonctionParametres',
                     'donneesSec': {'donnees': {'Uuid': uuid}}}
        self.initial_response = self.session.request('POST', p_site, json=json_post)
        return self.attributes

    def post(self, json: dict):
        # TODO: Secure with numeroOrdre verification
        if type(json) != dict:
            return PronoteAPIError('POST error: json not dict')

        self.request_number += 2
        r_number = self.encryption.aes_encrypt(str(self.request_number).encode()).hex()
        json['session'] = self.attributes['h']
        json['numeroOrdre'] = r_number
        p_site = self.root_site + '/appelfonction/' + self.attributes['a'] + '/' + self.attributes['h'] + '/' + r_number
        return self.session.request('POST', p_site, json=json)

    @staticmethod
    def _parse_html(html):
        parsed = BeautifulSoup(html, "html.parser")
        onload = parsed.find(id='id_body')
        if onload:
            onload_c = onload['onload'][14:-37]
        else:
            raise PronoteAPIError("The html parser couldn't find the json data.")
        attributes = {}
        for attr in onload_c.split(','):
            key, value = attr.split(':')
            attributes[key] = value.replace("'", '')
        return attributes

    @staticmethod
    def get_root_address(addr):
        return '/'.join(addr.split('/')[:-1])


def create_random_string(length):
    output = ''
    for _ in range(length + 1):
        j = random.choice('ABCDEFGHIJKLMNOPQRSTUVabcdefghijklmnopqrstuv123456789')
        output += j
    return output


class Encryption(object):
    def __init__(self):
        # aes
        self.aes_iv = bytes(16)
        self.aes_iv_temp = create_random_string(15).encode()
        self.aes_key = MD5.new().digest()

        # rsa
        self.rsa_keys = {}

    def aes_encrypt(self, data: bytes):
        cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_iv)
        padded = Padding.pad(data, 16)
        return cipher.encrypt(padded)

    def aes_decrypt(self, data: bytes):
        cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_iv)
        return cipher.decrypt(data)

    def aes_set_iv(self):
        self.aes_iv = self.aes_iv_temp

    def rsa_encrypt(self, data):
        if not self.rsa_keys:
            raise PronoteAPIError('Encryption Error: No RSA key.')
        elif type(self.rsa_keys) == dict:
            try:
                self.rsa_keys = RSA.construct((int(self.rsa_keys['MR'], 16), int(self.rsa_keys['ER'], 16)))
            except TypeError:
                raise PronoteAPIError('Encryption Error: Bad RSA key.')
        cipher = PKCS1_v1_5.new(self.rsa_keys)
        return cipher.encrypt(data)


class PronoteAPIError(Exception):
    pass

