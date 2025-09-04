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
from typing import Optional, Tuple, Union

import aiohttp
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Hash import MD5
from Crypto.PublicKey import RSA
from Crypto.Util import Padding

log = logging.getLogger(__name__)


class PronoteError(Exception):
    """An unknown error occured (see cause)"""

    def __init__(self, msg: Optional[str] = None) -> None:
        if msg is None and self.__doc__ is not None:
            super().__init__(self.__doc__.strip())
        else:
            super().__init__(msg)


class CredentialsError(PronoteError):
    """Invalid login credentials"""


class ExpiredObject(PronoteError):
    """An object used in the request was from a different session"""


class SuspendedError(PronoteError):
    """Your IP address has been temporairly suspended"""


class BadHtmlError(PronoteError):
    """Page html is different than expected (hint: is the address of your PRONOTE instance correct?)"""


class PronoteAPIError(PronoteError):
    """Unknown PRONOTE API error"""

    def __init__(self, status: int, error: Optional[dict]) -> None:
        super().__init__()
        self.status = status
        self.api_error = error


@dataclass
class UserPass:
    username: str
    password: str


@dataclass
class QRCode:
    code_contents: dict
    pin: str
    uuid: str


@dataclass
class Token:
    username: str
    token: str
    uuid: str


Credentials = Union[UserPass, Token, QRCode]


@dataclass
class MFACredentials:
    """Credentials for (2/M)FA authentication"""

    account_pin: Optional[str]
    device_name: Optional[str]
    client_identifier: Optional[str]

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
    """
    PRONOTE session management. Handles the session's whole lifecycle, from creation,
    through authentication, to deletion. Adds additional information to the
    requests to make them valid.
    """

    USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0  PRONOTE Mobile APP"

    def __init__(
        self,
        base_url: str,
        session: aiohttp.ClientSession,
        encrypt_requests: bool,
        compress_requests: bool,
        session_id: int,
        space_id: str,
    ) -> None:
        self.base_url = base_url

        self.session_lock = Lock()
        self.session = session

        self.encrypt_requests = encrypt_requests
        self.compress_requests = compress_requests
        self.session_id = session_id
        self.space_id = space_id

        self.aes_iv = bytes(16)
        self.aes_key = MD5.new().digest()

        self.request_number = 1

    @classmethod
    async def create(
        cls, base_url: str, space: Spaces, client_identifier: Optional[str] = None
    ) -> Tuple[PronoteSession, dict]:
        """Creates an unauthenticated PRONOTE session"""

        http_session = aiohttp.ClientSession()
        http_session.headers.add("User-Agent", cls.USER_AGENT)

        # get rsa keys and session id, retry 3 times
        for _ in range(3):
            try:
                log.debug(f"requesting html: {base_url}/{space.value}")
                # TODO: cookies
                get_response = await http_session.get(f"{base_url}/{space.value}")
                attributes = cls._parse_html(await get_response.text())
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
            attributes.get("CrA", False),
            attributes.get("CoA", False),
            int(attributes["h"]),
            attributes["a"],
        )

        # we need to catch this exception. the iv was not yet set and we need to decrypt it with the correct iv.
        initial_response = await session.post(
            "FonctionParametres",
            {"data": {"Uuid": uuid, "identifiantNav": client_identifier}},
            new_aes_iv=MD5.new(new_iv).digest(),
        )

        return session, initial_response

    @staticmethod
    def _parse_html(html: str) -> dict:
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

    @classmethod
    async def userpass_login(
        cls, url: str, creds: UserPass, mfa: Optional[MFACredentials] = None
    ) -> PronoteSession:
        """Creates a PRONOTE session authenticated with username and password"""
        ...

    @classmethod
    async def token_login(
        cls, url: str, creds: Token, mfa: Optional[MFACredentials] = None
    ) -> PronoteSession:
        """Creates a PRONOTE session authenticated with a token"""
        ...

    @classmethod
    async def qrcode_login(
        cls,
        url: str,
        creds: QRCode,
        mfa: Optional[MFACredentials] = None,
    ) -> PronoteSession:
        """Creates a PRONOTE session authenticated with a QR code"""
        ...

    async def _login(
        self,
    ) -> None:
        pass

    async def post(
        self,
        function_name: str,
        data: dict,
        new_aes_iv: Optional[bytes] = None,
        new_aes_key: Optional[bytes] = None,
    ) -> dict:

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

            self.request_number += 2

            json = {
                "session": int(self.session_id),
                "no": req_number,
                "id": function_name,
                "dataSec": post_data,
            }
            log.debug("[_Communication.post] sending post request: %s", json)

            p_site = f"{self.base_url}/appelfonction/{self.space_id}/{self.session_id}/{req_number}"

            # TODO: cookies
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

        # TODO: check returned request_number

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

    async def authenticated(self) -> None:
        pass

    async def close(self) -> None:
        await self.session.close()


def _aes_encrypt(key, iv, plaintext: bytes):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(Padding.pad(plaintext, 16))


def _aes_decrypt(key, iv, ciphertext: bytes):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return Padding.unpad(cipher.decrypt(ciphertext), 16)


def _rsa_encrypt(data: bytes) -> bytes:
    # taken from eleve.js
    RSA_1024_MODULO = 130337874517286041778445012253514395801341480334668979416920989365464528904618150245388048105865059387076357492684573172203245221386376405947824377827224846860699130638566643129067735803555082190977267155957271492183684665050351182476506458843580431717209261903043895605014125081521285387341454154194253026277
    RSA_1024_EXPONENT = 65537

    key = RSA.construct((RSA_1024_MODULO, RSA_1024_EXPONENT))
    pkcs = PKCS1_v1_5.new(key)

    return pkcs.encrypt(data)
