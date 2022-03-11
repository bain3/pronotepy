# type: ignore
from logging import getLogger, DEBUG
import typing

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

from ..exceptions import *

log = getLogger(__name__)
log.setLevel(DEBUG)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0'
}


def simple_auth(url: str, username: str, password: str, form_attr: dict = {}, params: dict = {}) -> requests.cookies.RequestsCookieJar:
    # ENT Connection
    session = requests.Session()
    response = session.get(url, params=params, headers=HEADERS)

    soup = BeautifulSoup(response.text, 'html.parser')
    form = soup.find('form', form_attr)
    payload = {}
    for input_ in form.findAll('input'):
        payload[input_['name']] = input_.get('value')
    payload['username'] = username
    payload['password'] = password

    session.post(response.url, data=payload, headers=HEADERS)

    return session.cookies


def atrium_sud(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for Atrium Sud

    Parameters
    ----------
    username : str
        username
    password : str
        password

    Returns
    -------
    cookies : cookies
        returns the ent session cookies
    """
    log.debug(f'[ENT Atrium] Logging in with {username}')

    form_attr = {'id': 'fm1'}

    return simple_auth('https://www.atrium-sud.fr/connexion/login', username, password, form_attr=form_attr)


'''CAS with simple_auth'''


def occitanie_toulouse(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for Occitanie Toulouse

    Parameters
    ----------
    username : str
        username
    password : str
        password

    Returns
    -------
    cookies : cookies
        returns the ent session cookies
    """
    log.debug(f'[ENT Occitanie Toulouse] Logging in with {username}')

    form_attr = {'class': 'cas__login-form'}
    params = {
        'selection': 'TOULO-ENT_parent_eleve',
        'submit': 'Valider'}

    return simple_auth('https://cas.mon-ent-occitanie.fr/login', username, password, form_attr=form_attr, params=params)


def occitanie_montpellier(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for Montpellier without Educonnect

    Parameters
    ----------
    username : str
        username
    password : str
        password

    Returns
    -------
    cookies : cookies
        returns the ent session cookies
    """
    log.debug(f'[ENT Montpellier] Logging in with {username}')

    form_attr = {'class': 'cas__login-form'}
    params = {
        'selection': 'CSES-ENT_parent_eleve',
        'submit': 'Valider'}

    return simple_auth('https://cas.mon-ent-occitanie.fr/login', username, password, form_attr=form_attr, params=params)


def ac_lyon(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for AC Lyon without Educonnect

    Parameters
    ----------
    username : str
        username
    password : str
        password

    Returns
    -------
    cookies : cookies
        returns the ent session cookies
    """
    log.debug(f'[ENT AC Lyon] Logging in with {username}')

    form_attr = {'class': 'cas__login-form'}
    params = {
        'selection': 'LYON-ATS_parent_eleve',
        'submit': 'Valider'
    }

    return simple_auth('https://cas.ent.auvergnerhonealpes.fr/login', username, password, form_attr=form_attr, params=params)


def ac_grenoble(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for AC Grenoble without Educonnect

    Parameters
    ----------
    username : str
        username
    password : str
        password

    Returns
    -------
    cookies : cookies
        returns the ent session cookies
    """
    log.debug(f'[ENT AC Grenoble] Logging in with {username}')

    form_attr = {'class': 'cas__login-form'}
    params = {
        'selection': 'GRE-ATS_parent_eleve',
        'submit': 'Valider'
    }

    return simple_auth('https://cas.ent.auvergnerhonealpes.fr/login', username, password, form_attr=form_attr, params=params)


def ac_clermont_ferrand(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for AC Clermont Ferrand without Educonnect

    Parameters
    ----------
    username : str
        username
    password : str
        password

    Returns
    -------
    cookies : cookies
        returns the ent session cookies
    """
    log.debug(f'[ENT AC Clermont Ferrand] Logging in with {username}')

    form_attr = {'class': 'cas__login-form'}
    params = {
        'selection': 'CLERMONT-ATS_parent_eleve',
        'submit': 'Valider'
    }
    return simple_auth('https://cas.ent.auvergnerhonealpes.fr/login', username, password, form_attr=form_attr, params=params)


def cas_agora06(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for Agora06 without Educonnect

    Parameters
    ----------
    username : str
        username
    password : str
        password

    Returns
    -------
    cookies : cookies
        returns the ent session cookies
    """
    log.debug(f'[CAS Agora 06] Logging in with {username}')

    form_attr = {'class': 'cas__login-form'}
    params = {
        'selection': 'ATS-NICE',
        'submit': 'Valider'
    }
    return simple_auth('https://cas.agora06.fr/login', username, password, form_attr=form_attr, params=params)


'''Don t know how to simplify this ENT. It s unlike any other system'''


def ac_reunion(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for AC Reunion

    Parameters
    ----------
    username : str
        username
    password : str
        password

    Returns
    -------
    cookies : cookies
        returns the ent session cookies
    """
    # ENT / PRONOTE required URLs
    ent_login = 'https://portail.college-jeandesme.re:8443/login?service=https:%2F%2Fportail.college-jeandesme.re%2Fpronote%2Feleve.html'

    # ENT Connection
    session = requests.Session()
    response = session.get(ent_login, headers=HEADERS)

    log.debug(f'[ENT Reunion] Logging in with {username}')

    # Login payload
    soup = BeautifulSoup(response.text, 'html.parser')
    payload = {
        'service': 'https://portail.college-jeandesme.re/pronote/eleve.html',
        'lt': soup.find('input', {'type': 'hidden', 'name': 'lt'}).get('value'),
        'previous_user': f'{username}@default',
        'username': username,
        'password': password,
    }
    # Send user:pass to the ENT
    response = session.post(ent_login, headers=HEADERS, data=payload)

    response = session.get(response.url, headers=HEADERS)

    response = session.get(response.url, headers=HEADERS)

    return session.cookies
