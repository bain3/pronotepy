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


def open_ent_ng(url: str, username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT which has an authentication like https://ent.iledefrance.fr/auth/login

    Parameters
    ----------
    url : str
        url of the ENT
    username : str
        username
    password : str
        password

    Returns
    -------
    cookies : cookies
        returns the ent session cookies
    """
    # ENT Connection
    session = requests.Session()

    payload = {
        'email': username,
        'password': password
    }
    response = session.post(url, headers=HEADERS, data=payload)
    return session.cookies


def ent_essonne(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT Essonne

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
    log.debug(f'[ENT Essonne] Logging in with {username}')
    return open_ent_ng('https://www.moncollege-ent.essonne.fr/auth/login', username, password)


def ile_de_france(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT Ile de France

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
    log.debug(f'[ENT Ile de France] Logging in with {username}')
    return open_ent_ng('https://ent.iledefrance.fr/auth/login', username, password)


def paris_classe_numerique(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT Paris Classe numerique

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
    log.debug(f'[ENT Paris classe numerique] Logging in with {username}')
    return open_ent_ng('https://ent.parisclassenumerique.fr/auth/login', username, password)


def ent77(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT 77

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
    log.debug(f'[ENT 77] Logging in with {username}')
    return open_ent_ng('https://ent77.seine-et-marne.fr/auth/login', username, password)


def ent_mayotte(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT Mayotte

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
    log.debug(f'[ENT Mayotte] Logging in with {username}')
    return open_ent_ng('https://mayotte.opendigitaleducation.com/auth/login', username, password)


def lyceeconnecte_aquitaine(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT Aquitaine

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
    log.debug(f'[ENT Aquitaine] Logging in with {username}')
    return open_ent_ng('https://mon.lyceeconnecte.fr/auth/login#/', username, password)


def neoconnect_guadeloupe(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT Guadeloupe

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
    log.debug(f'[ENT Guadeloupe] Logging in with {username}')
    return open_ent_ng('https://neoconnect.opendigitaleducation.com/auth/login', username, password)
