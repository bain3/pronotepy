from __future__ import annotations

import base64
import enum
import json as jsn
import logging
import re
import secrets
import zlib
from asyncio import Lock
from dataclasses import dataclass
from typing import Any, Final

import aiohttp
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Hash import MD5, SHA256
from Crypto.PublicKey import RSA
from Crypto.Util import Padding

from .err import *

log = logging.getLogger(__name__)

ResponseJson = dict[str, Any]


@dataclass
class UserPass:
    username: str
    password: str
    using_cas: bool = False


@dataclass
class QRCode:
    code_contents: dict[str, str]
    pin: str
    app_uuid: str


@dataclass
class Token:
    username: str
    token: str
    app_uuid: str


Credentials = UserPass | QRCode | Token


@dataclass
class MFACredentials:
    """Credentials for (2/M)FA authentication"""

    account_pin: str | None
    device_name: str | None
    client_identifier: str | None

    def __post_init__(self):
        if (
            self.account_pin is None
            and self.device_name is None
            and self.client_identifier is None
        ):
            raise ValueError("MFA credentials are empty, thus invalid")


class Spaces(enum.Enum):
    STUDENT = "eleve.html"
    PARENT = "parent.html"
    VIESCOLAIRE = "viescolaire.html"


class PronoteSession:
    """Low level PRONOTE session.

    Handles the session's whole lifecycle, from creation, through
    authentication, to deletion. Adds additional information to the requests to
    make them valid.

    TODO: example how to use
    """

    USER_AGENT: Final = (
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0  PRONOTE Mobile APP"
    )

    def __init__(
        self,
        base_url: str,
        session: aiohttp.ClientSession,
        encrypt_requests: bool,
        compress_requests: bool,
        session_id: int,
        space_id: int,
    ) -> None:
        self.base_url: str = base_url

        self.session_lock: Lock = Lock()
        self.session: aiohttp.ClientSession = session

        self.encrypt_requests: bool = encrypt_requests
        self.compress_requests: bool = compress_requests
        self.session_id: int = session_id
        self.space_id: int = space_id

        self.cas_credentials: UserPass | None = None

        self.aes_iv: bytes = bytes(16)
        self.aes_key: bytes = MD5.new().digest()

        self.request_number: int = 1

    @classmethod
    async def create(
        cls,
        base_url: str,
        space: str,
        client_identifier: str | None = None,
        cookie_jar: aiohttp.CookieJar | None = None,
    ) -> tuple[PronoteSession, ResponseJson]:
        """Creates an unauthenticated PRONOTE session"""

        http_session = aiohttp.ClientSession(cookie_jar=cookie_jar)
        http_session.headers.add("User-Agent", cls.USER_AGENT)

        # get rsa keys and session id, retry 3 times
        for _ in range(3):
            try:
                log.debug(f"requesting html: {base_url}/{space}")
                get_response = await http_session.get(f"{base_url}/{space}")
                attributes = _parse_html(await get_response.text())
            except ValueError:
                log.warning(
                    "[_Communication.initialise] Failed to parse html, retrying..."
                )
                continue  # retry
            else:
                break
        else:
            raise PronoteError("Unable to connect to pronote, please try again later")

        new_iv = secrets.token_bytes(16)

        uuid = base64.b64encode(
            _rsa_encrypt(new_iv) if attributes.get("http", False) else new_iv
        ).decode()

        session = PronoteSession(
            base_url,
            http_session,
            bool(attributes.get("CrA", False)),
            bool(attributes.get("CoA", False)),
            int(attributes["h"]),
            int(attributes["a"]),
        )

        if "e" in attributes:
            session.cas_credentials = UserPass(
                attributes["e"], attributes["f"], using_cas=True
            )

        initial_response = await session.post(
            "FonctionParametres",
            {"data": {"Uuid": uuid, "identifiantNav": client_identifier}},
            new_aes_iv=MD5.new(new_iv).digest(),
        )

        return session, initial_response

    @classmethod
    async def userpass_login(
        cls,
        base_url: str,
        space: Spaces,
        creds: UserPass,
        mfa: MFACredentials | None = None,
    ) -> tuple[PronoteSession, ResponseJson, ResponseJson]:
        """Creates a PRONOTE session authenticated with username and password"""
        session, options = await cls.create(
            base_url, space.value, mfa and mfa.client_identifier
        )

        auth_response = await session._login(
            creds.username, creds.password, cls.LoginMode.LOCAL, mfa=mfa
        )

        return session, options, auth_response

    @classmethod
    async def token_login(
        cls,
        base_url: str,
        space: Spaces,
        creds: Token,
        mfa: MFACredentials | None = None,
    ) -> tuple[PronoteSession, ResponseJson, ResponseJson]:
        """Creates a PRONOTE session authenticated with a token"""
        session, options = await cls.create(
            base_url, "mobile." + space.value, mfa and mfa.client_identifier
        )

        auth_response = await session._login(
            creds.username, creds.token, cls.LoginMode.TOKEN, creds.app_uuid, mfa
        )

        return session, options, auth_response

    @classmethod
    async def qrcode_login(
        cls,
        creds: QRCode,
        mfa: MFACredentials | None = None,
    ) -> tuple[PronoteSession, ResponseJson, ResponseJson]:
        """Creates a PRONOTE session authenticated with a QR code

        The created client instance will have its username and password
        attributes set to the credentials for the next login using
        :meth:`.token_login`.

        Args:
            qr_code (dict): JSON contained in the QR code. Must have ``login``, ``jeton`` and ``url`` keys.
            pin (str): 4-digit confirmation code created during QR code setup
            uuid (str): Unique ID for your application. Must not change between logins.
            account_pin (str | None): 2FA PIN to the account
            client_identifier (str | None): Identificator of this client provided by PRONOTE
            device_name (str | None): A name for registering this client as a device.
            skip_2fa (bool): Skip 2FA. PRONOTE will require it when connecting using the generated token (:meth:`.token_login`).
        """

        aes_key = MD5.new(creds.pin.encode()).digest()

        short_token = bytes.fromhex(creds.code_contents["login"])
        long_token = bytes.fromhex(creds.code_contents["jeton"])

        try:
            login = _aes_decrypt(aes_key, bytes(16), short_token).decode()
            jeton = _aes_decrypt(aes_key, bytes(16), long_token).decode()
        except ValueError:
            raise CredentialsError("Invalid QR code pin")

        # The app would query the server for all the available spaces and find
        # a space by checking if the last part of the URL matches one of the
        # space URLs. eg. "/pronote/parent.html" would match "mobile.parent.html"
        # (info url: <pronote root>/InfoMobileApp.json?id=0D264427-EEFC-4810-A9E9-346942A862A4)

        # We're gonna try the shorter route of just prepending "mobile." if it
        # isn't there already
        try:
            *parts, last = creds.code_contents["url"].split("/")
        except ValueError:
            raise CredentialsError("QR code URL is invalid")

        if not last.startswith("mobile."):
            last = "mobile." + last

        # create custom space, add the magic query params
        space = last + "?fd=1&bydlg=A6ABB224-12DD-4E31-AD3E-8A39A1C2C335&login=true"

        base_url = "/".join(parts)

        session, options = await cls.create(
            base_url, space, mfa and mfa.client_identifier
        )

        auth_response = await session._login(
            login, jeton, cls.LoginMode.QRCODE, creds.app_uuid, mfa
        )

        return session, options, auth_response

    @classmethod
    async def cas_login(
        cls,
        base_url: str,
        space: Spaces,
        cas_cookies: aiohttp.CookieJar,
        mfa: MFACredentials | None = None,
    ) -> tuple[PronoteSession, ResponseJson, ResponseJson]:
        session, options = await cls.create(
            base_url, space.value, mfa and mfa.client_identifier, cas_cookies
        )

        auth_response = await session._login(
            session.cas_credentials.username,  # type: ignore
            session.cas_credentials.password,  # type: ignore
            cls.LoginMode.CAS,
            mfa=mfa,
        )

        return session, options, auth_response

    class LoginMode(enum.Enum):
        LOCAL = 1
        CAS = 2
        QRCODE = 3
        TOKEN = 4

    async def _login(
        self,
        username: str,
        password: str,
        login_mode: LoginMode,
        uuid: str = "",
        mfa: MFACredentials | None = None,
    ) -> ResponseJson:
        """Logs in the user"""

        # identification phase
        ident_json = {
            "data": {
                "genreConnexion": 0,
                "genreEspace": self.space_id,
                "identifiant": username,
                "pourENT": login_mode == self.LoginMode.CAS,
                "enConnexionAuto": False,
                "demandeConnexionAuto": False,
                "demandeConnexionAppliMobile": login_mode == self.LoginMode.QRCODE,
                "demandeConnexionAppliMobileJeton": login_mode == self.LoginMode.QRCODE,
                "enConnexionAppliMobile": login_mode == self.LoginMode.TOKEN,
                "uuidAppliMobile": uuid,
                "loginTokenSAV": "",
            }
        }

        idr = await self.post("Identification", data=ident_json)

        # creating the authentification data
        challenge = idr["dataSec"]["data"]["challenge"]

        if login_mode == self.LoginMode.CAS:
            motdepasse = SHA256.new(password.encode()).hexdigest().upper()
            aes_key = MD5.new(motdepasse.encode()).digest()
        else:
            if idr["dataSec"]["data"]["modeCompLog"]:
                username = username.lower()
            if idr["dataSec"]["data"]["modeCompMdp"]:
                password = password.lower()

            alea = idr["dataSec"]["data"].get("alea", "")

            motdepasse = SHA256.new((alea + password).encode()).hexdigest().upper()
            aes_key = MD5.new((username + motdepasse).encode()).digest()

        try:
            # Solve challenge by removing every other character from the string
            # and encrypting it back.
            dec = _aes_decrypt(aes_key, self.aes_iv, bytes.fromhex(challenge)).decode()
            solved_challenge = _aes_encrypt(
                aes_key, self.aes_iv, dec[::2].encode()
            ).hex()
        except ValueError as ex:
            raise CredentialsError() from ex

        auth_json = {
            "data": {
                "connexion": 0,
                "challenge": solved_challenge,
                "espace": self.space_id,
            }
        }

        auth_response = await self.post("Authentification", data=auth_json)

        if "cle" not in auth_response["dataSec"]["data"]:
            log.error("Failed to log in. Server did not respond with key.")
            raise CredentialsError()

        # Switch to final aes key
        # Damn, it's hard to create variable names for stupid things
        key = _aes_decrypt(
            aes_key, self.aes_iv, bytes.fromhex(auth_response["dataSec"]["data"]["cle"])
        )
        self.aes_key = MD5.new(bytes(map(int, key.decode().split(",")))).digest()

        mfa_actions = auth_response["dataSec"]["data"].get("actionsDoubleAuth")
        if mfa_actions:
            if mfa is None:
                raise MFAError("Account requires MFA/2FA")

            actions = jsn.loads(mfa_actions["V"])

            doRegisterDevice = 5 in actions or 3 in actions
            doVerifyPin = 3 in actions

            await self._do_2fa(
                mfa,
                doVerifyPin,
                doRegisterDevice,
            )

        log.info(f"successfully logged in as {username}")

        return auth_response

    async def _do_2fa(
        self,
        mfa: MFACredentials,
        doVerifyPin: bool = False,
        doRegisterDevice: bool = False,
    ) -> None:
        log.debug(
            "doing 2fa doPin=%s, doRegister=%s, pin=%s (redacted), identifier=%s",
            doVerifyPin,
            doRegisterDevice,
            bool(mfa.account_pin),
            mfa.device_name,
        )

        encryptedPin = None

        if doVerifyPin:
            log.debug("verifying pin")

            if mfa.account_pin is None:
                raise MFAError("PIN is required for this account")

            encryptedPin = _aes_encrypt(
                self.aes_key, self.aes_iv, mfa.account_pin.encode()
            ).hex()

            resp = await self.post(
                "SecurisationCompteDoubleAuth",
                data={
                    "data": {
                        "action": 0,
                        "codePin": encryptedPin,
                    }
                },
            )

            if not resp["dataSec"]["data"].get("result", False):
                raise MFAError("Invalid PIN")

        if doRegisterDevice:
            log.debug("registering device")

            if mfa.device_name is None:
                raise MFAError("A device identifier is required for this account")

            data = {
                "data": {
                    "action": 3,
                    "avecIdentification": True,
                    "strIdentification": mfa.device_name,
                }
            }
            if encryptedPin:
                data["data"]["codePin"] = encryptedPin

            _ = await self.post("SecurisationCompteDoubleAuth", data=data)

    async def post(
        self,
        function_name: str,
        data: dict,  # pyright: ignore[reportMissingTypeArgument]
        new_aes_iv: bytes | None = None,
        new_aes_key: bytes | None = None,
    ) -> ResponseJson:

        post_data = data  # remove type

        if self.encrypt_requests:
            post_data = jsn.dumps(post_data).encode()

            # yes, PRONOTE can only compress the request if it is also encrypting it
            if self.compress_requests:
                post_data = zlib.compress(post_data.hex().encode(), level=6)[2:-4]

            post_data = _aes_encrypt(self.aes_key, self.aes_iv, post_data).hex().upper()

        # Requests cannot run in parallel because PRONOTE requires sequential request numbers
        async with self.session_lock:
            req_number = _aes_encrypt(
                self.aes_key, self.aes_iv, str(self.request_number).encode()
            ).hex()

            response_req_number = self.request_number + 1
            self.request_number += 2

            json = {
                "session": int(self.session_id),
                "no": req_number,
                "id": function_name,
                "dataSec": post_data,
            }

            p_site = f"{self.base_url}/appelfonction/{self.space_id}/{self.session_id}/{req_number}"

            log.debug("Calling %s with %s", function_name, data)
            response = await self.session.post(p_site, json=json)

            res_data = await response.json()

            self.aes_key = new_aes_key or self.aes_key
            self.aes_iv = new_aes_iv or self.aes_iv

        # error protection
        if not response.ok:
            raise PronoteAPIError(response.status, None)

        if "Erreur" in res_data:
            if res_data["Erreur"]["G"] == 22:
                raise ExpiredObject()

            raise PronoteAPIError(response.status, res_data)

        received_req_number = _aes_decrypt(
            self.aes_key, self.aes_iv, bytes.fromhex(res_data["no"])
        ).decode()
        if received_req_number != str(response_req_number):
            log.warning(
                "Request number mismatch! wanted: %s, got: %s",
                response_req_number,
                received_req_number,
            )

        try:
            if self.encrypt_requests:
                decrypted: bytes = _aes_decrypt(
                    self.aes_key, self.aes_iv, bytes.fromhex(res_data["dataSec"])
                )

                if self.compress_requests:
                    decrypted = zlib.decompress(decrypted, wbits=-15)

                res_data["dataSec"] = jsn.loads(decrypted.decode())
        except (ValueError, jsn.JSONDecodeError) as e:
            log.error("failed to decode response %s", res_data)
            raise PronoteError("Failed to decode response") from e

        return res_data

    async def close(self) -> None:
        await self.session.close()


def _aes_encrypt(key: bytes, iv: bytes, plaintext: bytes):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(Padding.pad(plaintext, 16))


def _aes_decrypt(key: bytes, iv: bytes, ciphertext: bytes):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return Padding.unpad(cipher.decrypt(ciphertext), 16)


def _rsa_encrypt(data: bytes) -> bytes:
    # taken from eleve.js
    RSA_1024_MODULO = 130337874517286041778445012253514395801341480334668979416920989365464528904618150245388048105865059387076357492684573172203245221386376405947824377827224846860699130638566643129067735803555082190977267155957271492183684665050351182476506458843580431717209261903043895605014125081521285387341454154194253026277
    RSA_1024_EXPONENT = 65537

    key = RSA.construct((RSA_1024_MODULO, RSA_1024_EXPONENT))
    pkcs = PKCS1_v1_5.new(key)

    return pkcs.encrypt(data)


def _parse_html(html: str) -> dict[str, str]:
    if "IP" in html:
        raise SuspendedError()

    match = re.search(r"Start ?\({(?P<param>[^}]*)}\)", html)
    if not match:
        raise BadHtmlError()

    onload_c = match.group("param")

    attributes = {}
    for attr in onload_c.split(","):
        key, value = attr.split(":")
        attributes[key] = value.replace("'", "")

    if "h" not in attributes:
        raise ValueError("internal exception to retry -> cannot prase html")

    return attributes
