import enum
from dataclasses import dataclass

import aiohttp


class Spaces(enum.Enum):
    STUDENT = "eleve.html"
    PARENT = "parent.html"
    VIESCOLAIRE = "viescolaire.html"


@dataclass
class UserPass:
    base_url: str
    space: Spaces
    username: str
    password: str


@dataclass
class QRCode:
    code_contents: dict[str, str]
    pin: str
    app_uuid: str


@dataclass
class Token:
    base_url: str
    space: str
    username: str
    token: str
    app_uuid: str


@dataclass
class CasCookies:
    base_url: str
    space: Spaces
    cookies: aiohttp.CookieJar


Credentials = UserPass | QRCode | Token | CasCookies


@dataclass
class MFACredentials:
    """Credentials for (2/M)FA authentication"""

    account_pin: str | None
    device_name: str | None
    client_identifier: str | None

    def __post_init__(self) -> None:
        if self.account_pin is None and self.device_name is None and self.client_identifier is None:
            raise ValueError("MFA credentials are empty, thus invalid")
