import base64
import json as jsn
import logging
import secrets
import threading
import zlib
from time import time, sleep

import requests
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Hash import MD5
from Crypto.PublicKey import RSA
from Crypto.Util import Padding
from bs4 import BeautifulSoup

from .exceptions import *

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

error_messages = {
    22: '[ERROR 22] The object was from a previous session. Please read the "Long Term Usage" section in README on '
        'github.',
    10: '[ERROR 10] Session has expired and pronotepy was not able to reinitialise the connection.'
}


class _Communication(object):
    def __init__(self, site, cookies, client):
        """Handles all communication with the PRONOTE servers"""
        self.root_site, self.html_page = self.get_root_address(site)
        self.session = requests.Session()
        self.encryption = _Encryption()
        self.attributes = {}
        self.request_number = 1
        self.cookies = cookies
        self.last_ping = 0
        self.authorized_onglets = []
        self.client = client
        self.compress_requests = False
        self.encrypt_requests = False
        self.last_response = None

    def initialise(self):
        """
        Initialisation of the communication. Sets up the encryption and sends the IV for AES to PRONOTE.
        From this point, everything is encrypted with the communicated IV.
        """
        # some headers to be real
        headers = {
            'connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0'}

        # get rsa keys and session id
        log.debug(f"Requesing html: {self.root_site}/{self.html_page}")
        get_response = self.session.request('GET', f'{self.root_site}/{self.html_page}', headers=headers,
                                            cookies=self.cookies)
        self.attributes = self._parse_html(get_response.content)
        # uuid
        self.encryption.rsa_keys = {'MR': self.attributes['MR'], 'ER': self.attributes['ER']}
        uuid = base64.b64encode(self.encryption.rsa_encrypt(self.encryption.aes_iv_temp)).decode()
        # post
        json_post = {'Uuid': uuid, 'identifiantNav': None}
        self.encrypt_requests = not self.attributes.get("sCrA", False)
        self.compress_requests = not self.attributes.get("sCoA", False)

        # we need to catch this exception. the iv was not yet set and we need to decrypt it with the correct iv.
        initial_response = self.post('FonctionParametres', {'donnees': json_post},
                                     decryption_change={'iv': MD5.new(self.encryption.aes_iv_temp).digest()})
        return self.attributes, initial_response

    def post(self, function_name: str, data: dict, decryption_change=None):
        """
        Handler for all POST requests by the api to PRONOTE servers. Automatically provides all needed data for the
        verification of posts. Session id and order numbers are preserved.

        Parameters
        ----------
        function_name : str
            The name of the function (eg. Authentification)
        data: dict
            The date that will be sent in the donneesSec dictionary
        recursive: bool
            Cursed recursion
        decryption_change
            If the decryption key or iv is changing in the middle of the request, you can set it here
        """
        if '_Signature_' in data and data['_Signature_'].get('onglet') not in self.authorized_onglets:
            raise PronoteAPIError('Action not permitted. (onglet is not normally accessible)')

        # this part is for some pronotes who need to have good encryption even if they're communicating over https
        if self.compress_requests:
            log.debug(f"[_Communication.post] compressing data")
            data = jsn.dumps(data).encode()  # get bytes in utf8
            data = data.hex()  # get hex of data
            log.debug(data)
            data = zlib.compress(data.encode(), level=6)[2:-4]  # actual compression
            log.debug(f"[_Communication.post] data compressed")
        if self.encrypt_requests:
            log.debug("[_Communication.post] encrypt data")
            if type(data) == dict:
                data = str(data).encode()
            data = self.encryption.aes_encrypt(data).hex().upper()

        # sending the actual request. adding some headers
        r_number = self.encryption.aes_encrypt(str(self.request_number).encode()).hex()
        json = {'session': int(self.attributes['h']), 'numeroOrdre': r_number, 'nom': function_name,
                'donneesSec': data}
        p_site = self.root_site + '/appelfonction/' + self.attributes['a'] + '/' + self.attributes['h'] + '/' + r_number
        response = self.session.request('POST', p_site, json=json, cookies=self.cookies)
        self.request_number += 2
        self.last_ping = time()

        self.last_response = response

        # error protection
        if not response.ok:
            raise requests.HTTPError(f'Status code: {response.status_code}')
        if 'Erreur' in response.json():
            r_json = response.json()
            if r_json["Erreur"]["G"] == 22:
                raise ExpiredObject(error_messages.get(22))
            raise PronoteAPIError(error_messages.get(r_json["Erreur"]["G"],
                                                     f'Unknown error from pronote: {r_json["Erreur"]["G"]} | {r_json["Erreur"]["Titre"]}'),
                                  pronote_error_code=r_json['Erreur']['G'],
                                  pronote_error_msg=r_json['Erreur']['Titre'])

        # checking for decryption change
        if decryption_change:
            log.debug("decryption change")
            if 'iv' in decryption_change:
                self.encryption.aes_iv = decryption_change['iv']
            if 'key' in decryption_change:
                self.encryption.aes_key = decryption_change['key']

        response_data = response.json()
        # decryption part of their "super strong" bullshit
        if self.encrypt_requests:
            log.debug("[_Communication.post] decrypting")
            response_data['donneesSec'] = self.encryption.aes_decrypt(bytes.fromhex(response_data['donneesSec']))
            log.debug(f"decrypted: {response_data['donneesSec'].hex()}")
        if self.compress_requests:
            log.debug("[_Communication.post] decompressing")
            response_data['donneesSec'] = zlib.decompress(response_data['donneesSec'], wbits=-15).decode()
        if type(response_data['donneesSec']) == str:
            try:
                response_data['donneesSec'] = jsn.loads(response_data['donneesSec'])
            except jsn.JSONDecodeError:
                raise PronoteAPIError("JSONDecodeError while requesting from pronote.")

        return response_data

    def after_auth(self, data, auth_key):
        """
        Key change after the authentification was successful.

        Parameters
        ----------
        auth_key
            AES authentification key used to calculate the challenge (From password of the user)
        data
            Data from the request
        """
        self.encryption.aes_key = auth_key
        if not self.cookies:
            self.cookies = self.last_response.cookies
        work = self.encryption.aes_decrypt(bytes.fromhex(data['donneesSec']['donnees']['cle']))
        key = MD5.new(_enBytes(work.decode()))
        key = key.digest()
        self.encryption.aes_key = key

    @staticmethod
    def _parse_html(html):
        """Parses the html for the RSA keys

        Returns
        -------
        dict
            HTML attributes
        """
        parsed = BeautifulSoup(html, "html.parser")
        onload = parsed.find(id='id_body')
        if onload:
            onload_c = onload['onload'][14:-37]
        else:
            if b'IP' in html:
                raise PronoteAPIError('Your IP address is suspended.')
            raise PronoteAPIError(
                "Page html is different than expected. Be sure that pronote_url is the direct url to your pronote page.")
        attributes = {}
        for attr in onload_c.split(','):
            key, value = attr.split(':')
            attributes[key] = value.replace("'", '')
        return attributes

    @staticmethod
    def get_root_address(addr):
        return '/'.join(addr.split('/')[:-1]), '/'.join(addr.split('/')[-1:])


def _enleverAlea(text):
    """Gets rid of the stupid thing that they did, idk what it really is for, but i guess it adds security"""
    sansalea = []
    for i, b in enumerate(text):
        if i % 2 == 0:
            sansalea.append(b)
    return ''.join(sansalea)


def _enBytes(string: str):
    list_string = string.split(',')
    return bytes([int(i) for i in list_string])


def _prepare_onglets(list_of_onglets):
    output = []

    if type(list_of_onglets) != list:
        return [list_of_onglets]

    for item in list_of_onglets:
        if type(item) == dict:
            item = list(item.values())
        output.extend(_prepare_onglets(item))
    return output


class _Encryption(object):
    def __init__(self):
        """The encryption part of the API. You shouldn't have to use this normally."""
        # aes
        self.aes_iv = bytes(16)
        self.aes_iv_temp = secrets.token_bytes(16)
        self.aes_key = MD5.new().digest()
        # rsa
        self.rsa_keys = {}

    def aes_encrypt(self, data: bytes):
        cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_iv)
        padded = Padding.pad(data, 16)
        return cipher.encrypt(padded)

    def aes_decrypt(self, data: bytes):
        cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_iv)
        try:
            return Padding.unpad(cipher.decrypt(data), 16)
        except ValueError:
            raise CryptoError('Decryption failed while trying to un pad. (probably bad decryption key/iv)')

    def aes_set_iv(self, iv=None):
        if iv is None:
            self.aes_iv = MD5.new(self.aes_iv_temp).digest()
        else:
            self.aes_iv = iv

    def rsa_encrypt(self, data: bytes):
        key = RSA.construct((int(self.rsa_keys['MR'], 16), int(self.rsa_keys['ER'], 16)))
        # noinspection PyTypeChecker
        pkcs = PKCS1_v1_5.new(key)
        return pkcs.encrypt(data)


class _KeepAlive(threading.Thread):
    def __init__(self, client):
        super().__init__(target=self.alive)
        self._client = client
        self.keep_alive = True

    def alive(self):
        while self.keep_alive:
            if time() - self._client._communication.last_ping >= 300:
                self._client.post('Presence', 7)
            sleep(1)

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.keep_alive = False
        self.join()
