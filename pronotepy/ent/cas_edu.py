# type: ignore
from logging import getLogger, DEBUG
import typing

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

from ..exceptions import *
from .educonnect import educonnect

log = getLogger(__name__)
log.setLevel(DEBUG)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0'
}


def cas_edu(url: str, username: str, password: str) -> requests.cookies.RequestsCookieJar:
    # ENT Connection
    session = requests.Session()

    response = session.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    payload = {
        "RelayState": soup.find("input", {"name": "RelayState"})["value"],
        "SAMLRequest": soup.find("input", {"name": "SAMLRequest"})["value"]
        }

    response = session.post(soup.find("form")['action'], data=payload, headers=HEADERS)
    log.debug(f'[ENT Occitanie] Logging in with {username}')

    educonnect(response.url, session, username, password)

    return session.cookies


def occitanie_montpellier_educonnect(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for Occitanie Montpellier

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
    log.debug(f'[ENT Occitanie] Logging in with {username}')

    return cas_edu('https://cas.mon-ent-occitanie.fr/login?selection=MONT-EDU_parent_eleve', username, password)


def ent_auvergnerhonealpe(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for Auvergne Rhone Alpes with Educonnect

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
    log.debug(f'[ENT Auvergne Rhone Alpes] Logging in with {username}')

    return cas_edu('https://cas.ent.auvergnerhonealpes.fr/login?selection=EDU', username, password)


def ac_orleans_tours(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for AC Orleans-Tours

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
    log.debug(f'[ENT ac Orleans Tours] Logging in with {username}')

    return cas_edu('https://ent.netocentre.fr/cas/login?&idpId=parentEleveEN-IdP', username, password)


def monbureaunumerique(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for MonBureauNumerique (Grand Est)

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
    log.debug(f'[ENT Mon bureau numérique] Logging in with {username}')

    return cas_edu('https://cas.monbureaunumerique.fr/login?selection=EDU', username, password)


def ac_reims(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for AC Reims

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
    return monbureaunumerique(username, password)


def eclat_bfc(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for Eclat BFC

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
    log.debug(f'[ENT Eclat BFC] Logging in with {username}')

    return cas_edu('https://cas.eclat-bfc.fr/login?selection=EDU', username, password)


def cas_agora06_educonnect(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for Agora06 with Educonnect

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

    return cas_edu('https://cas.agora06.fr/login?selection=EDU', username, password)
