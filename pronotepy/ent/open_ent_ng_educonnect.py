# type: ignore
from logging import getLogger, DEBUG
import typing

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

from ..exceptions import *
from .open_ent_ng import open_ent_ng
from .educonnect import educonnect

log = getLogger(__name__)
log.setLevel(DEBUG)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0'
}


def open_ent_ng_educonnect(domain: str, username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT which has an authentication like https://connexion.l-educdenormandie.fr/

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
    # URL required
    ent_login_page = 'https://educonnect.education.gouv.fr/idp/profile/SAML2/Unsolicited/SSO'

    session = requests.Session()

    params = {
        'providerId': f'{domain}/auth/saml/metadata/idp.xml'
    }

    response = session.get(ent_login_page, params=params, headers=HEADERS)
    response = educonnect(response.url, session, username, password)

    if not response:
        return open_ent_ng(response.url, username, password)
    else:
        soup = BeautifulSoup(response.text, 'html.parser')
        if soup.find('title').get_text() == 'Authentification':
            return open_ent_ng(response.url, username, password)

    return session.cookies


def l_normandie(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT l'educ de Normandie

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
    log.debug(f'[ENT Educ de Normandie] Logging in with {username}')

    return open_ent_ng_educonnect('https://ent.l-educdenormandie.fr', username, password)


def ent_hdf(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT Haut de France

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
    log.debug(f'[ENT HDF] Logging in with {username}')

    return open_ent_ng_educonnect('https://enthdf.fr', username, password)


def ent_somme(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT Somme

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
    log.debug(f'[ENT Somme] Logging in with {username}')

    return ent_hdf(username, password)
