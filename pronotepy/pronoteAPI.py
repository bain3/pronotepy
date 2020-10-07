import base64
import datetime
import json as jsn
import logging
import secrets
import threading
import zlib
from time import time, sleep
from typing import List, Callable, Optional

import requests
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Hash import MD5, SHA256
from Crypto.PublicKey import RSA
from Crypto.Util import Padding
from bs4 import BeautifulSoup

from . import dataClasses

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

error_messages = {
    22: '[ERROR 22] The object was from a previous session. Please read the "Long Term Usage" section in README on github.',
    10: '[ERROR 10] Session has expired and pronotepy was not able to reinitialise the connection.'
}


class Client(object):
    """
    A PRONOTE client.

    Parameters
    ----------
    pronote_url : str
        URL of the server
    username : str
    password : str
    ent : Callable
        Cookies for ENT connections

    Attributes
    ----------
    start_day : datetime.datetime
        The first day of the school year
    week : int
        The current week of the school year
    logged_in : bool
        If the user is successfully logged in

    """

    def __init__(self, pronote_url, username: str = '', password: str = '', ent: Optional[Callable] = None):
        log.info('INIT')
        # start communication session
        if not password == '' and username == '':
            raise PronoteAPIError(
                'Please provide login credentials. Cookies are None, and username and password are empty.')

        self.ent = ent
        if ent:
            cookies = ent(username, password)
        else:
            cookies = None

        self.username = username
        self.password = password
        self.pronote_url = pronote_url
        self.communication = _Communication(pronote_url, cookies, self)
        self.attributes, self.func_options = self.communication.initialise()

        # set up encryption
        self.encryption = _Encryption()
        self.encryption.aes_iv = self.communication.encryption.aes_iv

        # some other attribute creation
        self._last_ping = time()

        self.parametres_utilisateur = self.auth_cookie = None

        self.date = datetime.datetime.now()
        self.start_day = datetime.datetime.strptime(
            self.func_options['donneesSec']['donnees']['General']['PremierLundi']['V'], '%d/%m/%Y')
        self.week = self.get_week(datetime.date.today())

        # get the length of one hour
        hour_start = datetime.datetime.strptime(
            self.func_options['donneesSec']['donnees']['General']['ListeHeures']['V'][0]['L'], '%Hh%M')
        hour_end = datetime.datetime.strptime(
            self.func_options['donneesSec']['donnees']['General']['ListeHeuresFin']['V'][0]['L'], '%Hh%M')
        self.one_hour_duration = hour_end - hour_start

        self.periods_ = self.periods
        self.logged_in = self._login()
        self._expired = False

    def _login(self) -> bool:
        """
        Logs in the user.

        Returns
        -------
        bool
            True if logged in, False if not
        """
        if self.ent:
            self.username = self.attributes['e']
            self.password = self.attributes['f']
        # identification phase
        ident_json = {
            "genreConnexion": 0,
            "genreEspace": int(self.attributes['a']),
            "identifiant": self.username,
            "pourENT": True if self.ent else False,
            "enConnexionAuto": False,
            "demandeConnexionAuto": False,
            "demandeConnexionAppliMobile": False,
            "demandeConnexionAppliMobileJeton": False,
            "uuidAppliMobile": "",
            "loginTokenSAV": ""}
        idr = self.communication.post("Identification", {'donnees': ident_json})
        log.debug('indentification')

        # creating the authentification data
        log.debug(str(idr))
        challenge = idr['donneesSec']['donnees']['challenge']
        e = _Encryption()
        e.aes_set_iv(self.communication.encryption.aes_iv)

        # key gen
        if self.ent:
            motdepasse = SHA256.new(str(self.password).encode()).hexdigest().upper()
            e.aes_key = MD5.new(motdepasse.encode()).digest()
        else:
            u = self.username
            p = self.password
            if idr['donneesSec']['donnees']['modeCompLog']:
                u = u.lower()
            if idr['donneesSec']['donnees']['modeCompMdp']:
                p = p.lower()
            alea = idr['donneesSec']['donnees']['alea']
            motdepasse = SHA256.new((alea + p).encode()).hexdigest().upper()
            e.aes_key = MD5.new((u + motdepasse).encode()).digest()

        # challenge
        dec = e.aes_decrypt(bytes.fromhex(challenge))
        dec_no_alea = _enleverAlea(dec.decode())
        ch = e.aes_encrypt(dec_no_alea.encode()).hex()

        # send
        auth_json = {"connexion": 0, "challenge": ch, "espace": int(self.attributes['a'])}
        auth_response = self.communication.post("Authentification", {'donnees': auth_json})
        if 'cle' in auth_response['donneesSec']['donnees']:
            self.communication.after_auth(self.communication.last_response, auth_response, e.aes_key)
            self.encryption.aes_key = e.aes_key
            log.info(f'successfully logged in as {self.username}')

            # getting listeOnglets separately because of pronote API change
            self.parametres_utilisateur = self.communication.post('ParametresUtilisateur', {})
            self.communication.authorized_onglets = _prepare_onglets(self.parametres_utilisateur['donneesSec']['donnees']['listeOnglets'])
            log.info("got onglets data.")
            return True
        else:
            log.info('login failed')
            return False

    def get_week(self, date: datetime.date):
        return 1 + int((date - self.start_day.date()).days / 7)

    def lessons(self, date_from: datetime.date, date_to: datetime.date = None) -> List[dataClasses.Lesson]:
        """
        Gets all lessons in a given timespan.

        :rtype: List[dataClasses.Lesson]
        :returns: List of lessons

        :param date_from: first date
        :param date_to: second date
        """
        user = self.parametres_utilisateur['donneesSec']['donnees']['ressource']
        data = {"_Signature_": {"onglet": 16},
                "donnees": {"ressource": user,
                            "avecAbsencesEleve": False, "avecConseilDeClasse": True,
                            "estEDTPermanence": False, "avecAbsencesRessource": True,
                            "avecDisponibilites": True, "avecInfosPrefsGrille": True,
                            "Ressource": user}}
        output = []

        first_week = self.get_week(date_from)
        if not date_to:
            date_to = date_from
        last_week = self.get_week(date_to)

        # getting lessons for all the weeks.
        for week in range(first_week, last_week+1):
            data['donnees']['NumeroSemaine'] = data['donnees']['numeroSemaine'] = week
            response = self.communication.post('PageEmploiDuTemps', data)
            l_list = response['donneesSec']['donnees']['ListeCours']
            for lesson in l_list:
                output.append(dataClasses.Lesson(self, lesson))

        # since we only have week precision, we need to make it more precise on our own
        return [lesson for lesson in output if date_from <= lesson.start.date() <= date_to]

    @property
    def periods(self) -> List[dataClasses.Period]:
        """
        Get all of the periods of the year.

        Returns
        -------
        List[Period]
            All the periods of the year
        """
        if hasattr(self, 'periods_') and self.periods_:
            return self.periods_
        json = self.func_options['donneesSec']['donnees']['General']['ListePeriodes']
        return [dataClasses.Period(self, j) for j in json]

    @property
    def current_period(self) -> dataClasses.Period:
        """Get the current period."""
        id_period = self.parametres_utilisateur['donneesSec']['donnees']['ressource']['listeOngletsPourPeriodes']['V'][0][
            'periodeParDefaut']['V']['N']
        return dataClasses.Util.get(self.periods_, id=id_period)[0]

    def homework(self, date_from: datetime.date, date_to: datetime.date = None) -> List[dataClasses.Homework]:
        """
        Get homework between two given points.

        date_from : datetime
            The first date
        date_to : datetime
            The second date

        Returns
        -------
        List[Homework]
            Homework between two given points
        """
        if not date_to:
            date_to = datetime.datetime.strptime(
                self.func_options['donneesSec']['donnees']['General']['DerniereDate']['V'], '%d/%m/%Y').date()
        json_data = {'donnees': {
            'domaine': {'_T': 8, 'V': f"[{self.get_week(date_from)}..{self.get_week(date_to)}]"}},
            '_Signature_': {'onglet': 88}}
        response = self.communication.post('PageCahierDeTexte', json_data)
        h_list = response['donneesSec']['donnees']['ListeTravauxAFaire']['V']
        out = []
        for h in h_list:
            hw = dataClasses.Homework(self, h)
            if date_from <= hw.date <= date_to:
                out.append(hw)
        return out

    def keep_alive(self):
        """
        Returns a context manager to keep the connection alive. When inside the context manager,
        it sends a "Presence" packet to the server after 5 minutes of inactivity from another thread.
        """
        return _KeepAlive(self)

    def messages(self) -> List[dataClasses.Message]:
        """
        Gets all the discussions in the discussions tab

        Returns
        -------
        List[Messages]
            Messages
        """
        messages = self.communication.post('ListeMessagerie', {'donnees': {'avecMessage': True, 'avecLu': True},
                                                               '_Signature_': {'onglet': 131}})
        return [dataClasses.Message(self, m) for m in messages['donneesSec']['donnees']['listeMessagerie']['V']
                if not m.get('estUneDiscussion')]

    def refresh(self):
        """
        Now this is the true jank part of this program. It refreshes the connection if something went wrong.
        This is the classical procedure if something is broken.
        """
        logging.debug('Reinitialisation')
        self.communication.session.close()

        if self.ent:
            cookies = self.ent(self.username, self.password)
        else:
            cookies = None

        self.communication = _Communication(self.pronote_url, cookies, self)
        self.attributes, self.func_options = self.communication.initialise()

        # set up encryption

        self.encryption = _Encryption()
        self.encryption.aes_iv = self.communication.encryption.aes_iv
        self._login()
        self.periods_ = None
        self.periods_ = self.periods
        self.week = self.get_week(datetime.date.today())
        self._expired = True

    def session_check(self) -> bool:
        """Checks if the session has expired and refreshes it if it had (returns bool signifying if it was expired)"""
        self.communication.post('Presence', {'_Signature_': {'onglet': 7}})
        if self._expired:
            self._expired = False
            return True
        return False


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
        initial_response = self.post('FonctionParametres', {'donnees': json_post}, decryption_change={'iv': MD5.new(self.encryption.aes_iv_temp).digest()})
        return self.attributes, initial_response

    def post(self, function_name: str, data: dict, recursive: bool = False, decryption_change=None):
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
            if recursive:
                raise PronoteAPIError(error_messages.get(r_json["Erreur"]["G"],
                                                         f'Unknown error from pronote: {r_json["Erreur"]["G"]} | {r_json["Erreur"]["Titre"]}'))

            log.info(
                f'Have you tried turning it off and on again? ERROR: {r_json["Erreur"]["G"]} | {r_json["Erreur"]["Titre"]}')
            self.client.refresh()
            return self.client.communication.post(function_name, data, True)

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

    def after_auth(self, auth_response, data, auth_key):
        """
        Key change after the authentification was successful.

        Parameters
        ----------
        auth_response
            The authentification response from the server
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
        self._connection = client.communication
        self.keep_alive = True

    def alive(self):
        while self.keep_alive:
            if time() - self._connection.last_ping >= 300:
                self._connection.post('Presence', {'_Signature_': {'onglet': 7}})
            sleep(1)

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.keep_alive = False
        self.join()


class PronoteAPIError(Exception):
    """
    Base exception for any pronote api errors
    """
    pass


class CryptoError(PronoteAPIError):
    """Exception for known errors in the cryptography."""
    pass


class ExpiredObject(PronoteAPIError):
    """Raised when pronote returns error 22. (unknown object reference)"""
    pass
