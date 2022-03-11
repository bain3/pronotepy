from __future__ import annotations

import base64
import json as jsn
from logging import getLogger, DEBUG
import secrets
import threading
import zlib
from time import time, sleep
from typing import Union, Optional, TYPE_CHECKING, Any, List

import requests
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Hash import MD5
from Crypto.PublicKey import RSA
from Crypto.Util import Padding
from bs4 import BeautifulSoup

from .exceptions import *

if TYPE_CHECKING:
    from requests import Response
    from requests.cookies import RequestsCookieJar
    from .clients import _ClientBase

log = getLogger(__name__)
log.setLevel(DEBUG)

error_messages = {
    22: '[ERROR 22] The object was from a previous session. Please read the "Long Term Usage" section in README on '
        'github.',
    10: '[ERROR 10] Session has expired and pronotepy was not able to reinitialise the connection.',
    25: '[ERROR 25] Exceeded max authorization requests. Please wait before retrying...'
}


class _Communication(object):
    def __init__(self, site: str, cookies: RequestsCookieJar, client: _ClientBase) -> None:
        """Handles all communication with the PRONOTE servers"""
        self.root_site, self.html_page = self.get_root_address(site)
        self.session = requests.Session()
        self.encryption = _Encryption()
        self.attributes: dict = {}
        self.request_number = 1
        self.cookies = cookies
        self.last_ping = 0
        self.authorized_onglets: List[int] = []
        self.client = client
        self.compress_requests = False
        self.encrypt_requests = False
        self.last_response: Response

    def initialise(self) -> Tuple[Any, Any]:
        """
        Initialisation of the communication. Sets up the encryption and sends the IV for AES to PRONOTE.
        From this point, everything is encrypted with the communicated IV.
        """
        # some headers to be real
        headers = {
            'connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0'}

        # get rsa keys and session id
        log.debug(f'Requesing html: {self.root_site}/{self.html_page}')
        get_response = self.session.request('GET', f'{self.root_site}/{self.html_page}', headers=headers,
                                            cookies=self.cookies)
        self.attributes = self._parse_html(get_response.content)
        # uuid
        self.encryption.rsa_keys = {'MR': self.attributes['MR'], 'ER': self.attributes['ER']}
        uuid = base64.b64encode(self.encryption.rsa_encrypt(self.encryption.aes_iv_temp)).decode()
        # post
        json_post = {'Uuid': uuid, 'identifiantNav': None}
        self.encrypt_requests = not self.attributes.get('sCrA', False)
        self.compress_requests = not self.attributes.get('sCoA', False)

        # we need to catch this exception. the iv was not yet set and we need to decrypt it with the correct iv.
        initial_response = self.post('FonctionParametres', {'donnees': json_post},
                                     decryption_change={'iv': MD5.new(self.encryption.aes_iv_temp).digest()})
        return self.attributes, initial_response

    def post(self, function_name: str, data: dict, decryption_change: Optional[dict] = None) -> dict:
        """
        Handler for all POST requests by the api to PRONOTE servers. Automatically provides all needed data for the
        verification of posts. Session id and order numbers are preserved.

        Parameters
        ----------
        function_name : str
            The name of the function (eg. Authentification)
        data : dict
            The date that will be sent in the donneesSec dictionary
        decryption_change
            If the decryption key or iv is changing in the middle of the request, you can set it here
        """
        if '_Signature_' in data and data['_Signature_'].get('onglet') not in self.authorized_onglets:
            raise PronoteAPIError('Action not permitted. (onglet is not normally accessible)')

        post_data: Union[dict, str] = data

        if self.compress_requests:
            # takes care of compression. it is done with zlib, with compression level set to 6. the headers
            # are stripped, and the output is converted to hex
            log.debug('[_Communication.post] compressing data')
            post_data = jsn.dumps(data).encode().hex()
            log.debug(post_data)
            post_data = zlib.compress(post_data.encode(), level=6)[2:-4].hex().upper()
        if self.encrypt_requests:
            # encryption is done with the communicated key, the output is converted to hex (the client makes the output
            # all CAPS, so we're doing the same)
            log.debug('[_Communication.post] encrypt data')
            if type(post_data) == dict:
                # get the data in json form, then proceed to encrypt
                post_data = self.encryption.aes_encrypt(jsn.dumps(post_data).encode()).hex().upper()
            elif type(post_data) == str:
                # we can assume the post_data is from compression, we need to get back the raw bytes
                post_data = self.encryption.aes_encrypt(bytes.fromhex(post_data)).hex().upper()

        # creating the full json dict
        r_number = self.encryption.aes_encrypt(str(self.request_number).encode()).hex()
        json = {'session': int(self.attributes['h']), 'numeroOrdre': r_number, 'nom': function_name,
                'donneesSec': post_data}

        p_site = f'{self.root_site}/appelfonction/{self.attributes["a"]}/{self.attributes["h"]}/{r_number}'

        response: Response = self.session.request('POST', p_site, json=json, cookies=self.cookies)

        self.request_number += 2
        self.last_ping = int(time())
        self.last_response = response

        # error protection
        if not response.ok:
            raise requests.HTTPError(f'Status code: {response.status_code}')
        if 'Erreur' in response.json():
            r_json = response.json()
            if r_json['Erreur']['G'] == 22:
                raise ExpiredObject(error_messages.get(22))
            raise PronoteAPIError(
                error_messages.get(r_json['Erreur']['G'], f'Unknown error from pronote: {r_json["Erreur"]["G"]} '
                                                          f'| {r_json["Erreur"]["Titre"]}'),
                pronote_error_code=r_json['Erreur']['G'],
                pronote_error_msg=r_json['Erreur']['Titre'])

        # TODO: check returned request_number

        # checking for decryption change
        if decryption_change is not None:
            log.debug('[_Communication.post] decryption change')
            if 'iv' in decryption_change:
                self.encryption.aes_iv = decryption_change['iv']
            if 'key' in decryption_change:
                self.encryption.aes_key = decryption_change['key']

        response_data = response.json()

        if self.encrypt_requests:
            # decrypt the received message, the output will either be a hex string, or the json dictionary
            log.debug('[_Communication.post] decrypting')
            decrypted: bytes = self.encryption.aes_decrypt(bytes.fromhex(response_data['donneesSec']))
            if not self.compress_requests:
                response_data['donneesSec'] = jsn.loads(decrypted.decode())
            else:
                response_data['donneesSec'] = decrypted
        if self.compress_requests:
            log.debug('[_Communication.post] decompressing')
            d: Union[bytes, str] = response_data['donneesSec']
            try:
                response_data['donneesSec'] = jsn.loads(
                    zlib.decompress(bytes.fromhex(d) if type(d) == str else d, wbits=-15).decode())  # type: ignore
            except jsn.JSONDecodeError:
                raise PronoteAPIError('JSONDecodeError while requesting from pronote.')

        return response_data

    def after_auth(self, data: dict, auth_key: bytes) -> None:
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
        self.encryption.aes_key = key.digest()

    @staticmethod
    def _parse_html(html: bytes) -> dict:
        """Parses the html for the RSA keys

        Returns
        -------
        dict
            HTML attributes
        """
        parsed = BeautifulSoup(html, 'html.parser')

        onload = parsed.find(id='id_body')
        if onload:
            onload_c = onload['onload'][14:-37]  # type: ignore
        elif b'IP' in html:
            raise PronoteAPIError('Your IP address is suspended.')
        else:
            raise PronoteAPIError(
                'Page html is different than expected. Be sure that pronote_url is the direct url to your pronote page.')
        attributes = {}
        for attr in onload_c.split(','):  # type: ignore
            key, value = attr.split(':')
            attributes[key] = value.replace("'", '')
        return attributes

    @staticmethod
    def get_root_address(addr: str) -> tuple[str, str]:
        return '/'.join(addr.split('/')[:-1]), '/'.join(addr.split('/')[-1:])


def _enleverAlea(text: str) -> str:
    """Gets rid of the stupid thing that they did, idk what it really is for, but i guess it adds security"""
    sansalea = [b for i, b in enumerate(text) if i % 2 == 0]
    return ''.join(sansalea)


def _enBytes(string: str) -> bytes:
    list_string = string.split(',')
    return bytes(int(i) for i in list_string)


def _prepare_onglets(list_of_onglets):  # type: ignore
    output = []

    if type(list_of_onglets) != list:
        return [list_of_onglets]

    for item in list_of_onglets:
        if type(item) == dict:
            item = list(item.values())
        output.extend(_prepare_onglets(item))
    return output


class _Encryption(object):
    def __init__(self) -> None:
        """The encryption part of the API. You shouldn't have to use this normally."""
        # aes
        self.aes_iv = bytes(16)
        self.aes_iv_temp = secrets.token_bytes(16)
        self.aes_key = MD5.new().digest()
        # rsa
        self.rsa_keys: dict[str, str] = {}

    def aes_encrypt(self, data: bytes) -> bytes:
        cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_iv)
        padded = Padding.pad(data, 16)
        return cipher.encrypt(padded)

    def aes_decrypt(self, data: bytes) -> bytes:
        cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_iv)
        try:
            return Padding.unpad(cipher.decrypt(data), 16)
        except ValueError:
            raise CryptoError('Decryption failed while trying to un pad. (probably bad decryption key/iv)')

    def aes_set_iv(self, iv: bytes = None) -> None:
        self.aes_iv = iv or MD5.new(self.aes_iv_temp).digest()

    def rsa_encrypt(self, data: bytes) -> bytes:
        key = RSA.construct((int(self.rsa_keys['MR'], 16), int(self.rsa_keys['ER'], 16)))
        # noinspection PyTypeChecker
        pkcs = PKCS1_v1_5.new(key)
        return pkcs.encrypt(data)


class _KeepAlive(threading.Thread):
    def __init__(self, client: _ClientBase) -> None:
        super().__init__(target=self.alive)
        self._client = client
        self.keep_alive = True

    def alive(self) -> None:
        while self.keep_alive:
            if time() - self._client.communication.last_ping >= 300:
                self._client.post('Presence', 7)
            sleep(1)

    def __enter__(self) -> None:
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        self.keep_alive = False
        self.join()
        