import requests
from bs4 import BeautifulSoup
import random
from Crypto.Hash import MD5, SHA256
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Util import Padding
from Crypto.PublicKey import RSA
import base64
import logging
import datetime
from math import floor
from . import dataClasses
import threading
from time import time, sleep

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class Client(object):
    """A base PRONOTE client."""
    def __init__(self, pronote_url, ent: bool = False, cookies=None):
        log.info('INIT')
        # start communication session
        self.ent = ent
        self.communication = _Communication(pronote_url, cookies)
        self.attributes, self.func_options = self.communication.initialise()

        # set up encryption
        self.encryption = _Encryption()
        self.encryption.aes_iv = self.communication.encryption.aes_iv

        # some other attribute creation
        self._last_ping = time()

        self.auth_response = self.auth_cookie = None

        self.date = datetime.datetime.now()
        self.start_day = datetime.datetime.strptime(
            self.func_options.json()['donneesSec']['donnees']['General']['PremierLundi']['V'], '%d/%m/%Y')
        self.week = self._get_week(datetime.date.today())

        # get the length of one hour
        hour_start = datetime.datetime.strptime(
            self.func_options.json()['donneesSec']['donnees']['General']['ListeHeures']['V'][0]['L'], '%Hh%M')
        hour_end = datetime.datetime.strptime(
            self.func_options.json()['donneesSec']['donnees']['General']['ListeHeuresFin']['V'][0]['L'], '%Hh%M')
        self.one_hour_duration = hour_end - hour_start

        self.periods_ = self.periods()

    def login(self, username='', password=''):
        """
        Logs in the user.
        :param username:Username
        :param password:Password
        """
        if self.ent is True:
            username = self.attributes['e']
            password = self.attributes['f']
        # identification phase
        ident_json = {
            "genreConnexion": 0,
            "genreEspace": int(self.attributes['a']),
            "identifiant": username,
            "pourENT": self.ent,
            "enConnexionAuto": False,
            "demandeConnexionAuto": False,
            "demandeConnexionAppliMobile": False,
            "demandeConnexionAppliMobileJeton": False,
            "uuidAppliMobile": "",
            "loginTokenSAV": ""}
        idr = self.communication.post("Identification", {'donnees': ident_json})
        log.debug('indentification')

        # creating the authentification data
        idr = idr.json()
        challenge = idr['donneesSec']['donnees']['challenge']
        e = _Encryption()
        e.aes_set_iv(self.communication.encryption.aes_iv)

        # key gen
        if self.ent is True:
            motdepasse = SHA256.new(str(password).encode()).hexdigest().upper()
            e.aes_key = MD5.new(motdepasse.encode()).digest()
        else:
            alea = idr['donneesSec']['donnees']['alea']
            motdepasse = SHA256.new(str(alea + password.lower()).encode()).hexdigest().upper()
            e.aes_key = MD5.new((username.lower() + motdepasse).encode()).digest()
        del password

        # challenge
        dec = e.aes_decrypt(bytes.fromhex(challenge))
        dec_no_alea = _enleverAlea(dec.decode())
        ch = e.aes_encrypt(dec_no_alea.encode()).hex()

        # send
        auth_json = {"connexion": 0, "challenge": ch, "espace": int(self.attributes['a'])}
        self.auth_response = self.communication.post("Authentification", {'donnees': auth_json})
        if 'cle' in self.auth_response.json()['donneesSec']['donnees']:
            self.communication.after_auth(self.auth_response, e.aes_key)
            log.info(f'successfully logged in as {username}')
            return True
        else:
            log.info('login failed')
            return False

    def _get_homepage_info(self):
        """Old function, not used"""
        dta_nav = {"_Signature_": {"onglet": 7}, "donnees": {"onglet": 7, "ongletPrec": 7}}
        self.communication.post('Navigation', dta_nav)
        date_str = self.date.strftime('%d/%m/%Y 0:0:0')
        dta = {"_Signature_": {"onglet": 7},
               "donnees": {
                   "avecConseilDeClasse": True,
                   "dateGrille": {"_T": 7, "V": date_str},
                   "numeroSemaine": self.week,
                   "AppelNonFait": {"date": {"_T": 7, "V": date_str}},
                   "CDTNonSaisi": {"numeroSemaine": self.week},
                   "coursNonAssures": {"numeroSemaine": self.week},
                   "personnelsAbsents": {"numeroSemaine": self.week},
                   "incidents": {"numeroSemaine": self.week},
                   "donneesVS": {"numeroSemaine": self.week},
                   "donneesProfs": {"numeroSemaine": self.week},
                   "EDT": {"date": {"_T": 7, "V": date_str}, "numeroSemaine": self.week},
                   "menuDeLaCantine": {"date": {"_T": 7, "V": date_str}},
                   "partenaireCDI": {"CDI": {}}}}
        p_a_response = self.communication.post('PageAccueil', dta)
        log.info('successfully got data')
        return p_a_response.json()

    def _get_week(self, date: datetime.date):
        return int(1 + floor((date - self.start_day.date()).days / 7))

    def lessons(self, date_from: datetime.date, date_to: datetime.date = None):
        """
        Gets all lessons in a given timespan.
        :param date_from:The first date.
        :param date_to:The second date.
        """
        user = self.auth_response.json()['donneesSec']['donnees']['ressource']
        data = {"_Signature_": {"onglet": 16},
                "donnees": {"ressource": user,
                            "dateDebut": {"_T": 7, 'V': date_from.strftime('%d/%m/%Y 0:0:0')},
                            "DateDebut": {"_T": 7, 'V': date_from.strftime('%d/%m/%Y 0:0:0')},
                            "avecAbsencesEleve": False, "avecConseilDeClasse": True,
                            "estEDTPermanence": False, "avecAbsencesRessource": True,
                            "avecDisponibilites": True, "avecInfosPrefsGrille": True,
                            "Ressource": user}}
        if date_to:
            # noinspection PyTypeChecker
            data['donnees']['dateFin'] = data['donnees']['DateFin'] = {"_T": 7, 'V': date_to.strftime('%d/%m/%Y 0:0:0')}
        output = []
        response = self.communication.post('PageEmploiDuTemps', data)
        l_list = response.json()['donneesSec']['donnees']['ListeCours']
        for lesson in l_list:
            output.append(dataClasses.Lesson(self, lesson))
        return output

    def periods(self):
        """
        Get all of the periods of the year.
        """
        if hasattr(self, 'periods_'):
            return self.periods_
        json = self.func_options.json()['donneesSec']['donnees']['General']['ListePeriodes']
        return [dataClasses.Period(self, j) for j in json]

    def current_periods(self):
        """Get the current period(s)."""
        output = []
        for p in self.periods_:
            if p.start < self.date < p.end:
                output.append(p)
        return output

    def homework(self, date_from: datetime.date, date_to: datetime.date = None):
        """
        Get homework between two given points.
        :param date_from:The first date.
        :param date_to:The second date.
        """
        if not date_to:
            date_to = datetime.datetime.strptime(
                self.func_options.json()['donneesSec']['donnees']['General']['DerniereDate']['V'], '%d/%m/%Y').date()
        json_data = {'donnees': {
            'domaine': {'_T': 8, 'V': f"[{self._get_week(date_from)}..{self._get_week(date_to)}]"}},
            '_Signature_': {'onglet': 88}}
        response = self.communication.post('PageCahierDeTexte', json_data)
        h_list = response.json()['donneesSec']['donnees']['ListeTravauxAFaire']['V']
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


class _Communication(object):
    def __init__(self, site, cookies=None):
        """Handles all communication with the PRONOTE servers"""
        self.root_site, self.html_page = self.get_root_address(site)
        self.session = requests.Session()
        self.encryption = _Encryption()
        self.attributes = {}
        self.request_number = 1
        self.cookies = cookies
        self.last_ping = 0
        self.authorized_onglets = []

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
        get_response = self.session.request('GET', f'{self.root_site}/{self.html_page}', headers=headers, cookies=self.cookies)
        self.attributes = self._parse_html(get_response.content)
        # uuid
        self.encryption.rsa_keys = {'MR': self.attributes['MR'], 'ER': self.attributes['ER']}
        uuid = base64.b64encode(self.encryption.rsa_encrypt(self.encryption.aes_iv_temp)).decode()
        # post
        json_post = {'Uuid': uuid}
        initial_response = self.post('FonctionParametres', {'donnees': json_post})
        self.encryption.aes_set_iv()
        return self.attributes, initial_response

    def post(self, function_name: str, data: dict):
        """
        Handler for all POST requests by the api to PRONOTE servers. Automatically provides all needed data for the
        verification of posts. Session id and order numbers are preserved.

        :param function_name:the name of the function (ex.: Authentification)
        :param data:the data that will be sent in the donneesSec dictionary.
        """
        if type(data) != dict:
            raise PronoteAPIError('POST error: donnees not dict')
        elif '_Signature_' in data and data['_Signature_'].get('onglet') not in self.authorized_onglets:
            raise PronoteAPIError('Action not permitted. (onglet is not normally accessible)')

        r_number = self.encryption.aes_encrypt(str(self.request_number).encode()).hex()
        json = {'session': int(self.attributes['h']), 'numeroOrdre': r_number, 'nom': function_name,
                'donneesSec': data}
        p_site = self.root_site + '/appelfonction/' + self.attributes['a'] + '/' + self.attributes['h'] + '/' + r_number
        response = self.session.request('POST', p_site, json=json, cookies=self.cookies)
        self.request_number += 2
        self.last_ping = time()

        # error protection
        if not response.ok:
            raise requests.HTTPError(f'Status code: {response.status_code}')
        if 'Erreur' in response.json():
            raise PronoteAPIError(f'PRONOTE server returned error code: {response.json()["Erreur"]["G"]} | {response.json()["Erreur"]["Titre"]}')

        return response

    def after_auth(self, auth_response, auth_key):
        """
        Key change after the authentification was successful.
        :param auth_response:the authentification response from the server
        :param auth_key:authentification key used to calculate the challenge. (from password of the user)
        """
        self.encryption.aes_key = auth_key
        if not self.cookies:
            self.cookies = auth_response.cookies
        self.authorized_onglets = _prepare_onglets(auth_response.json()['donneesSec']['donnees']['listeOnglets'])
        work = self.encryption.aes_decrypt(bytes.fromhex(auth_response.json()['donneesSec']['donnees']['cle']))
        # ok
        key = MD5.new(_enBytes(work.decode()))
        key = key.digest()
        self.encryption.aes_key = key

    @staticmethod
    def _parse_html(html):
        """Parses the html for the RSA keys"""
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
        return '/'.join(addr.split('/')[:-1]), '/'.join(addr.split('/')[-1:])


def _create_random_string(length):
    output = ''
    for _ in range(length):
        j = random.choice('ABCDEFGHIJKLMNOPQRSTUVabcdefghijklmnopqrstuv123456789')
        output += j
    return output


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
        self.aes_iv_temp = _create_random_string(16).encode()
        self.aes_key = MD5.new().digest()
        # rsa
        self.rsa_keys = {}

    def aes_encrypt(self, data: bytes):
        cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_iv)
        padded = Padding.pad(data, 16)
        return cipher.encrypt(padded)

    def aes_decrypt(self, data: bytes):
        cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_iv)
        return Padding.unpad(cipher.decrypt(data), 16)

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
            if time()-self._connection.last_ping >= 300:
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
