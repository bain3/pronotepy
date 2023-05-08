from logging import getLogger, DEBUG
import typing

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

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
def pronote_hubeduconnect(
    pronote_url: str,
) -> typing.Callable[[str, str], requests.cookies.RequestsCookieJar]:
    """
    Pronote EduConnect connection (with HubEduConnect.index-education.net)

    .. DANGER:: Unlike the other ENT functions, this one needs to be
        called. e.g. ``pronotepy.Client(url, username, password, pronote_hubeduconnect(url))``

    Parameters
    ----------
    pronote_url: str
        the same pronote_url as passed to the client

    Returns
    -------
    cookies : cookies
        returns the ent session cookies
    """
    # URLs required for the connection
    hubeduconnect_base = (
        "https://hubeduconnect.index-education.net/EduConnect/cas/login"
    )

    def inner(username: str, password: str) -> requests.cookies.RequestsCookieJar:
        with requests.Session() as session:
            response = session.get(
                f"{hubeduconnect_base}?service={pronote_url}", headers=HEADERS
            )

            soup = BeautifulSoup(response.text, "html.parser")
            input_SAMLRequest = soup.find("input", {"name": "SAMLRequest"})
            if input_SAMLRequest:
                payload = {
                    "SAMLRequest": input_SAMLRequest["value"],
                }

                input_relayState = soup.find("input", {"name": "RelayState"})
                if input_relayState:
                    payload["RelayState"] = input_relayState["value"]

                response = session.post(
                    soup.find("form")["action"], data=payload, headers=HEADERS
                )

            if response.content.__contains__(
                b'<label id="zone_msgDetail">L&#x27;url de service est vide</label>'
            ):
                raise ENTLoginError(
                    "Fail to connect with HubEduConnect : Service URL not provided."
                )
            elif response.content.__contains__(b"n&#x27;est pas une url de confiance."):
                raise ENTLoginError(
                    "Fail to connect with HubEduConnect : Service URL not trusted. Is Pronote instance supported?"
                )

            _educonnect(session, username, password, response.url)

        return session.cookies

    return inner
