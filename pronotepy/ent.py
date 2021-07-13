import logging

import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def atrium_sud(username, password):
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
    # ENT / PRONOTE required URLs
    ent_login = 'https://www.atrium-sud.fr/connexion/login?service=https:%2F%2F0060013G.index-education.net%2Fpronote%2F'

    # Required Headers
    headers = {
        'connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0'}

    # ENT Connection
    session = requests.Session()
    response = session.get(ent_login, headers=headers)

    log.debug('[ENT Atrium] Logging in with ' + username)

    # Login payload
    soup = BeautifulSoup(response.text, 'html.parser')
    input_ = soup.find('input', {'type': 'hidden', 'name': 'lt'})
    lt = input_.get('value')

    input_ = soup.find('input', {'type': 'hidden', 'name': 'execution'})
    execution = input_.get('value')

    payload = {
        'execution': execution,
        '_eventId': 'submit',
        'submit': '',
        'lt': lt,
        'username': username,
        'password': password}

    # Send user:pass to the ENT
    cookies = requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))
    response = session.post(ent_login, headers=headers, data=payload, cookies=cookies)
    return requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))


def ac_reims(username, password):
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

    # Required Headers
    headers = {
        'connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0'}
    # Login payload
    payload = {
        'auth_mode': 'BASIC',
        'orig_url': '/sso/SSO?SPEntityID=SP-MonBureauNumerique-Production',
        'user': username,
        'password': password}
    # ENT / PRONOTE required URLs
    ent_login = 'https://services-familles.ac-reims.fr/login/ct_logon_vk.jsp?CT_ORIG_URL=%2Fsso%2FSSO%3FSPEntityID%3DSP-MonBureauNumerique-Production&ct_orig_uri=%2Fsso%2FSSO%3FSPEntityID%3DSP-MonBureauNumerique-Production'
    ent_verif = 'https://services-familles.ac-reims.fr/aten-web/connexion/controlesConnexion?CT_ORIG_URL=%2Fsso%2FSSO%3FSPEntityID%3DSP-MonBureauNumerique-Production&ct_orig_uri=%2Fsso%2FSSO%3FSPEntityID%3DSP-MonBureauNumerique-Production'
    pronote_verif = 'https://cas.monbureaunumerique.fr/saml/SAMLAssertionConsumer'
    # ENT Connection
    session = requests.Session()
    response = session.get(ent_login, headers=headers)
    log.debug('[ENT AC Reims] Logging in with ' + username)
    # Send user:pass to the ENT
    cookies = requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))
    response = session.post(ent_login, headers=headers, data=payload, cookies=cookies)
    # Get the CAS verification shit
    cookies = requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))
    response = session.get(ent_verif, headers=headers, cookies=cookies)
    # Get the actual values
    soup = BeautifulSoup(response.text, 'html.parser')
    cas_infos = dict()
    inputs = soup.findAll('input', {'type': 'hidden'})
    for input_ in inputs:
        cas_infos[input_.get('name')] = input_.get('value')
    cookies = requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))
    session.cookies.update({'SERVERID': 'gdest-prod-web14', 'preselection': 'REIMS-ATS_parent_eleve'})
    response = session.post(pronote_verif, headers=headers, data=cas_infos, cookies=cookies)
    # Get Pronote
    cookies = requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))
    return cookies


def occitanie_montpellier(username, password):
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
    # Required Headers
    headers = {
        'connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0'}
    # Login payload
    payload = {
        'auth_mode': 'BASIC',
        'orig_url': '%2Ffim42%2Fsso%2FSSO%3FSPEntityID%3Dsp-ent-entmip-prod',
        'user': username,
        'password': password}
    # ENT / PRONOTE required URLs
    ent_login = 'https://famille.ac-montpellier.fr/login/ct_logon_vk.jsp?CT_ORIG_URL=/fim42/sso/SSO?SPEntityID=sp-ent-entmip-prod&ct_orig_uri=/fim42/sso/SSO?SPEntityID=sp-ent-entmip-prod'
    ent_verif = 'https://famille.ac-montpellier.fr/aten-web/connexion/controlesConnexion?CT_ORIG_URL=%2Ffim42%2Fsso%2FSSO%3FSPEntityID%3Dsp-ent-entmip-prod&amp;ct_orig_uri=%2Ffim42%2Fsso%2FSSO%3FSPEntityID%3Dsp-ent-entmip-prod'
    pronote_verif = 'https://cas.mon-ent-occitanie.fr/saml/SAMLAssertionConsumer'
    # ENT Connection
    session = requests.Session()
    response = session.get(ent_login, headers=headers)
    log.debug('[ENT Occitanie] Logging in with ' + username)
    # Send user:pass to the ENT
    cookies = requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))
    response = session.post(ent_login, headers=headers, data=payload, cookies=cookies)
    # Get the CAS verification shit
    cookies = requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))
    response = session.get(ent_verif, headers=headers, cookies=cookies)
    # Get the actual values
    soup = BeautifulSoup(response.text, 'html.parser')
    cas_infos = dict()
    inputs = soup.findAll('input', {'type': 'hidden'})
    for input_ in inputs:
        cas_infos[input_.get('name')] = input_.get('value')
    cookies = requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))
    session.cookies.update({'SERVERID': 'entmip-prod-web4', 'preselection': 'MONTP-ATS_parent_eleve'})
    response = session.post(pronote_verif, headers=headers, data=cas_infos, cookies=cookies)
    # Get Pronote
    cookies = requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))
    return cookies


def ac_reunion(username, password):
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

    # Required Headers
    headers = {
        'connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0'}

    # ENT Connection
    session = requests.Session()
    response = session.get(ent_login, headers=headers)

    log.debug('[ENT Reunion] Logging in with ' + username)

    # Login payload
    soup = BeautifulSoup(response.text, 'html.parser')
    input_ = soup.find('input', {'type': 'hidden', 'name': 'lt'})
    lt = input_.get('value')

    payload = {
        'service': 'https://portail.college-jeandesme.re/pronote/eleve.html',
        'lt': lt,
        'previous_user': username + '@default',
        'username': username,
        'password': password}

    # Send user:pass to the ENT
    cookies = requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))
    response = session.post(ent_login, headers=headers, data=payload, cookies=cookies)

    new_url = response.url

    cookies = requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))
    response = session.get(new_url, headers=headers, cookies=cookies)

    pronote_url = response.url

    cookies = requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))
    response = session.get(pronote_url, headers=headers, cookies=cookies)

    return requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))

def ile_de_france(username, password):
    """
    ENT for Ile de France

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
    ent_login = "https://ent.iledefrance.fr/auth/login?callback=https%3A%2F%2Fent.iledefrance.fr%2F"
    # Required Headers
    headers = {
        'connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0'}

    payload = {
        'email' : username,
        'password' : password,
    }
    # ENT Connection
    session = requests.Session()

    cookies = requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))
    response = session.post(ent_login, headers=headers, data=payload, cookies=cookies)
    return requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))

def paris_classe_numerique(username, password):
    """
    ENT for PCN

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
    ent_login = "https://ent.parisclassenumerique.fr/auth/login"
    # Required Headers
    headers = {
        'connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0'}

    payload = {
        'email' : username,
        'password' : password,
    }
    # ENT Connection
    session = requests.Session()

    cookies = requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))
    response = session.post(ent_login, headers=headers, data=payload, cookies=cookies)
    return requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))


def ac_lyon(username, password):
    """
    ENT for Lyon

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
    ent_login = 'https://cas.ent.auvergnerhonealpes.fr/login?selection=LYON-ATS_parent_eleve&submit=Valider'

    # Required Headers
    headers = {
        'connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0'}

    # ENT Connection
    session = requests.Session()
    response = session.get(ent_login, headers=headers)


    soup = BeautifulSoup(response.text, 'html.parser')
    input_ = soup.find('input', {'type': 'hidden', 'name': 'execution'})
    executions = input_.get('value')

    payload = {
        'username' : username,
        'password' : password,
        'selection' : "LYON-ATS_parent_eleve",
        'codeFournisseurIdentite' : "ATS-LYON",
        '_eventId' :	"submit",
        'submit': "Confirm",
        'geolocation': "",
        'execution': executions
      }


    cookies = requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))
    
    response = session.post(ent_login, headers=headers, data=payload, cookies=cookies)
    

    
    return requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))

def ac_orleans_tours(username, password):
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

    # Required Headers
    headers = {
        'connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0'
    }
    
    # Login payload
    payload = {
        "j_username": username,
        "j_password": password,
        "_eventId_proceed": ""
    }
    
    # ENT / PRONOTE required URLs
    ent_login_page = "https://ent.netocentre.fr/cas/login?service=https://0451462V.index-education.net/pronote/eleve.html&idpId=parentEleveEN-IdP"
    ent_login = "https://educonnect.education.gouv.fr/idp/profile/SAML2/Redirect/SSO?execution=e1s1"
    pronote_verif = "https://ent.netocentre.fr/cas/Shibboleth.sso/SAML2/POST?client_name=EduConnect"
    
    # ENT Connection
    session = requests.Session()

    # Connection URL specifying the pronote service
    session.get(ent_login_page, headers=headers)

    # Send user:pass to the ENT
    response = session.post(ent_login, headers=headers, data=payload)

    # retrieving the "RelayState", "SAMLResponse" tokens in the response
    soup = BeautifulSoup(response.text, 'html.parser')
    cas_infos = dict()
    inputs = soup.findAll('input', {'type': 'hidden'})
    for input_ in inputs:
        cas_infos[input_.get('name')] = input_.get('value')

    # retrieving pronote ticket
    response = session.post(pronote_verif, headers=headers, data=cas_infos)


    cookies = requests.utils.cookiejar_from_dict(
        requests.utils.dict_from_cookiejar(session.cookies))
    return cookies

def monbureaunumerique(username, password):
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

    # Required Headers
    headers = {
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0'
    }

    # Login payload
    payload = {
        "j_username": username,
        "j_password": password,
        "_eventId_proceed": ""
    }

    # ENT / PRONOTE required URLs
    ent_login_page = "https://cas.monbureaunumerique.fr/login?selection=EDU&service=http%3A%2F%2Fpronote.lycee-fabert.com%2Fpronote%2F&submit=Valider"
    ent_load = "https://educonnect.education.gouv.fr/idp/profile/SAML2/POST/SSO"
    ent_login = "https://educonnect.education.gouv.fr/idp/profile/SAML2/POST/SSO?execution=e1s1"
    pronote_verif = "https://cas.monbureaunumerique.fr/saml/SAMLAssertionConsumer"

    # ENT Connection
    session = requests.Session()

    # Connection URL specifying the pronote service
    response = session.get(ent_login_page, headers=headers)

    # retrieving the "RelayState", "SAMLResponse" in the ent response for educonnect
    soup = BeautifulSoup(response.text, 'html.parser')
    cas_info = dict()
    inputs = soup.findAll('input', {'type':'hidden'})
    for input_ in inputs:
        cas_info[input_.get('name')] = input_.get('value')

    session.post(ent_load, headers=headers, data=cas_info)

    # Send user:pass to the ENT
    response = session.post(ent_login, headers=headers, data=payload)

    # retrieving the "RelayState", "SAMLResponse" tokens in the response
    soup = BeautifulSoup(response.text, 'html.parser')
    cas_infos = dict()
    inputs = soup.findAll('input', {'type': 'hidden'})
    for input_ in inputs:
        cas_infos[input_.get('name')] = input_.get('value')

    # retrieving pronote ticket
    response = session.post(pronote_verif, headers=headers, data=cas_infos)

    cookies = requests.utils.cookiejar_from_dict(
        requests.utils.dict_from_cookiejar(session.cookies))
    return cookies
