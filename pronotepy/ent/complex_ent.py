from logging import getLogger, DEBUG
import typing

import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urljoin

from ..exceptions import *
from .generic_func import _educonnect

log = getLogger(__name__)
log.setLevel(DEBUG)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0"
}


@typing.no_type_check
def ac_rennes(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT ac Rennes Toutatice.fr

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
    # Toutatice required URL
    toutatice_url = "https://www.toutatice.fr/portail/auth/MonEspace"
    toutatice_login = "https://www.toutatice.fr/wayf/Ctrl"
    toutatice_auth = "https://www.toutatice.fr/idp/Authn/RemoteUser"

    with requests.Session() as session:
        response = session.get(toutatice_url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")
        payload = {
            "entityID": soup.find("input", {"name": "entityID"})["value"],
            "return": soup.find("input", {"name": "return"})["value"],
            "_saml_idp": soup.find("input", {"name": "_saml_idp"})["value"],
        }

        log.debug(f"[ENT Toutatice] Logging in with {username}")
        response = session.post(toutatice_login, data=payload, headers=HEADERS)

        _educonnect(session, username, password, response.url)

        params = {
            "conversation": parse_qs(urlparse(response.url).query)["execution"][0],
            "redirectToLoaderRemoteUser": 0,
            "sessionid": session.cookies.get("IDP_JSESSIONID"),
        }

        response = session.get(toutatice_auth, headers=HEADERS, params=params)
        soup = BeautifulSoup(response.text, "xml")

        if soup.find("erreurFonctionnelle"):
            raise ENTLoginError(
                "Toutatice ENT (ac_rennes) : ", soup.find("erreurFonctionnelle").text
            )
        elif soup.find("erreurTechnique"):
            raise ENTLoginError(
                "Toutatice ENT (ac_rennes) : ", soup.find("erreurTechnique").text
            )
        else:
            params = {
                "conversation": soup.find("conversation").text,
                "uidInSession": soup.find("uidInSession").text,
                "sessionid": session.cookies.get("IDP_JSESSIONID"),
            }
            t = session.get(toutatice_auth, headers=HEADERS, params=params)

        return session.cookies

@typing.no_type_check
def ile_de_france(username,
                   password,
                   pronote_url: str = "") -> requests.cookies.RequestsCookieJar:

    """
    ENT Île-de-France

    Parameters
    ----------
    username : str
        username
    password : str
        password
    pronote_url: str
        URL of Pronote instance

    Returns
    -------
    cookies : cookies
        returns the ent session cookies
    """


    s = requests.Session()
    s.headers.update(HEADERS)

    r = s.get(pronote_url, allow_redirects=True)

    m = re.search(r'<form[^>]+action="([^"]+)"', r.text)

    if not m:
        raise Exception("Formulaire de login introuvable → pas sur la page Keycloak ?")
    form_action = urljoin(r.url, m.group(1))

    hidden_inputs = dict(re.findall(r'name="([^"]+)" value="([^"]*)"', r.text))

    payload = {**hidden_inputs, "username": username, "password": password, "credentialId": ""}

    s.post(form_action, data=payload, allow_redirects=True)

    return s.cookies
