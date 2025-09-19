from __future__ import annotations

import base64
import enum
import json as jsn
import logging
import re
import secrets
import zlib
from asyncio import Lock
from typing import Any, Final

import aiohttp
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Hash import MD5, SHA256
from Crypto.PublicKey import RSA
from Crypto.Util import Padding

from .err import *
from .credentials import *

log = logging.getLogger(__name__)

ResponseJson = dict[str, Any]


class PronoteSession:
    """Low level PRONOTE session.

    Handles the session's whole lifecycle, from creation, through
    authentication, to deletion. Adds additional information to the requests to
    make them valid.

    An example:

    .. code-block:: python

        credentials = UserPass("https://host.invalid/pronote/", Spaces.STUDENT, "user", "pass")
        session, *_ = await PronoteSession.login(credentials)

        # now we have a valid and authenticated session

        # Send the following post request
        # {
        #     "id": "PageInfosPerso",
        #     "session": ...,
        #     "no": ...,
        #     "dataSec": data
        # }
        response = await session.post("PageInfosPerso", data)
    """

    USER_AGENT: Final = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0  PRONOTE Mobile APP"

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
        """Saved base URL of the PRONOTE instance"""

        self._session_lock: Lock = Lock()
        self._http_session: aiohttp.ClientSession = session

        self.encrypt_requests: bool = encrypt_requests
        """Is the session encrypting requests"""
        self.compress_requests: bool = compress_requests
        """Is the session compressing requests"""
        self.session_id: int = session_id
        """PRONOTE session ID ("h" attribute)"""
        self.space_id: int = space_id
        """Space number ("a" attribute)"""

        self.cas_username: str | None = None
        """If authenticating with CAS cookies, the username we received"""
        self.cas_password: str | None = None
        """If authenticating with CAS cookies, the password we received"""

        self.aes_iv: bytes = bytes(16)
        """Current AES IV"""
        self.aes_key: bytes = MD5.new().digest()
        """Current AES key"""

        self.request_number: int = 1
        """Request number (for "no" attribute in requests)"""

        self.client_identifier: str
        """Received client identifier for MFA"""

        self.next_token: Token | None = None
        """The next credentials to use if authenticating as mobile app (from QRCode / Token)"""

    @classmethod
    async def create(
        cls,
        base_url: str,
        space: str,
        client_identifier: str | None = None,
        cookie_jar: aiohttp.CookieJar | None = None,
    ) -> tuple[PronoteSession, ResponseJson]:
        """Creates an unauthenticated PRONOTE session"""

        base_url = base_url.rstrip("/")

        http_session = aiohttp.ClientSession(cookie_jar=cookie_jar)
        http_session.headers.add("User-Agent", cls.USER_AGENT)

        try:
            # get initialisation attributes from page html
            for _ in range(3):
                try:
                    log.debug(f"requesting html: {base_url}/{space}")
                    get_response = await http_session.get(f"{base_url}/{space}")
                    attributes = _parse_html(await get_response.text())
                except ValueError:
                    log.warning("failed to parse html, retrying...")
                    continue
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
                session.cas_username = attributes["e"]
                session.cas_password = attributes["f"]

            initial_response = await session.post(
                "FonctionParametres",
                {"data": {"Uuid": uuid, "identifiantNav": client_identifier}},
                new_aes_iv=MD5.new(new_iv).digest(),
            )

            session.client_identifier = (
                client_identifier or initial_response["dataSec"]["data"]["identifiantNav"]
            )
        except Exception:
            await http_session.close()
            raise

        return session, initial_response

    @classmethod
    async def login(
        cls,
        creds: Credentials,
        mfa: MFACredentials | None = None,
    ) -> tuple[PronoteSession, ResponseJson, ResponseJson]:
        """Creates an authenticated PRONOTE session

        Args:
            creds: Credentials for authentication
            mfa: Additional credentials for multi-factor authentication
                (code/device name/identifier from earlier session)

        Returns:
            Tuple of the session, and the FonctionsParametres and Authentification
            raw responses.
        """

        match creds:
            case UserPass():
                return await PronoteSession._userpass_login(creds, mfa)
            case QRCode():
                return await PronoteSession._qrcode_login(creds, mfa)
            case Token():
                return await PronoteSession._token_login(creds, mfa)
            case CasCookies():
                return await PronoteSession._cas_login(creds, mfa)

    @classmethod
    async def _userpass_login(
        cls,
        creds: UserPass,
        mfa: MFACredentials | None = None,
    ) -> tuple[PronoteSession, ResponseJson, ResponseJson]:
        """Creates a PRONOTE session authenticated with username and password"""

        session, options = await cls.create(
            creds.base_url, creds.space.value, mfa.client_identifier if mfa else None
        )

        try:
            auth_response = await session._login(
                creds.username, creds.password, cls.LoginMode.LOCAL, mfa=mfa
            )
        except Exception:
            await session.close()
            raise

        return session, options, auth_response

    @classmethod
    async def _token_login(
        cls,
        creds: Token,
        mfa: MFACredentials | None = None,
    ) -> tuple[PronoteSession, ResponseJson, ResponseJson]:
        """Creates a PRONOTE session authenticated with a token"""

        session, options = await cls.create(
            creds.base_url,
            "mobile." + creds.space,
            mfa.client_identifier if mfa else None,
        )

        try:
            auth_response = await session._login(
                creds.username, creds.token, cls.LoginMode.TOKEN, creds.app_uuid, mfa
            )
        except Exception:
            await session.close()
            raise

        session.next_token = Token(
            base_url=session.base_url,
            space=creds.space,
            username=creds.username,
            token=auth_response["dataSec"]["data"]["jetonConnexionAppliMobile"],
            app_uuid=creds.app_uuid,
        )

        return session, options, auth_response

    @classmethod
    async def _qrcode_login(
        cls,
        creds: QRCode,
        mfa: MFACredentials | None = None,
    ) -> tuple[PronoteSession, ResponseJson, ResponseJson]:
        """Creates a PRONOTE session authenticated with a QR code"""

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

        session, options = await cls.create(base_url, space, mfa.client_identifier if mfa else None)

        try:
            auth_response = await session._login(
                login, jeton, cls.LoginMode.QRCODE, creds.app_uuid, mfa
            )
        except Exception:
            await session.close()
            raise

        session.next_token = Token(
            base_url=session.base_url,
            space=space,
            username=login,
            token=auth_response["dataSec"]["data"]["jetonConnexionAppliMobile"],
            app_uuid=creds.app_uuid,
        )

        return session, options, auth_response

    @classmethod
    async def _cas_login(
        cls,
        creds: CasCookies,
        mfa: MFACredentials | None = None,
    ) -> tuple[PronoteSession, ResponseJson, ResponseJson]:
        """Creates a PRONOTE session authenticated with cookies from CAS"""

        session, options = await cls.create(
            creds.base_url,
            creds.space.value,
            mfa.client_identifier if mfa else None,
            creds.cookies,
        )

        try:
            auth_response = await session._login(
                session.cas_credentials.username,  # type: ignore
                session.cas_credentials.password,  # type: ignore
                cls.LoginMode.CAS,
                mfa=mfa,
            )
        except Exception:
            await session.close()
            raise

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

        idr = await self.post("Identification", dataSec=ident_json)

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
            solved_challenge = _aes_encrypt(aes_key, self.aes_iv, dec[::2].encode()).hex()
        except ValueError as ex:
            raise CredentialsError() from ex

        auth_json = {
            "data": {
                "connexion": 0,
                "challenge": solved_challenge,
                "espace": self.space_id,
            }
        }

        auth_response = await self.post("Authentification", dataSec=auth_json)

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

            encryptedPin = _aes_encrypt(self.aes_key, self.aes_iv, mfa.account_pin.encode()).hex()

            resp = await self.post(
                "SecurisationCompteDoubleAuth",
                dataSec={
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

            _ = await self.post("SecurisationCompteDoubleAuth", dataSec=data)

    async def post(
        self,
        function_name: str,
        dataSec: dict,
        new_aes_iv: bytes | None = None,
        new_aes_key: bytes | None = None,
    ) -> ResponseJson:
        """Call the PRONOTE API

        Formats, authenticates, and sends ``dataSec`` as a POST request (puts ``function_name``
        as the "id" of the function that is being called) to the PRONOTE API.

        Even though this method is async, requests are sent in series. PRONOTE expects
        a serial number attached to them, which would break if we sent more requests at
        the same time.

        .. code-block:: python

            # Send the following post request
            # {
            #     "id": "PageInfosPerso",
            #     "session": ...,
            #     "no": ...,
            #     "dataSec": data
            # }
            response = await session.post("PageInfosPerso", data)
        """

        post_data: Any = dataSec  # remove type

        if self.encrypt_requests:
            post_data = jsn.dumps(post_data).encode()

            # yes, PRONOTE can only compress the request if it is also encrypting it
            if self.compress_requests:
                post_data = zlib.compress(post_data.hex().encode(), level=6)[2:-4]

            post_data = _aes_encrypt(self.aes_key, self.aes_iv, post_data).hex().upper()

        # Requests cannot run in parallel because PRONOTE requires sequential request numbers
        async with self._session_lock:
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

            log.debug("Calling %s with %s", function_name, dataSec)
            response = await self._http_session.post(p_site, json=json)

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
        if not self._http_session.closed:
            await self._http_session.close()

    async def __aenter__(self) -> PronoteSession:
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.close()


def _aes_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(Padding.pad(plaintext, 16))


def _aes_decrypt(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
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
