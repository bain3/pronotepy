from __future__ import annotations

import datetime
import logging
from typing import Any

from . import parse
from .session import Credentials, MFACredentials, PronoteSession, ResponseJson
from .term import Term
from .credentials import Token

log = logging.getLogger(__name__)


def _get_current_term(user_options: ResponseJson, terms: list[Term]) -> Term:
    onglets = user_options["dataSec"]["data"]["ressource"]["listeOngletsPourPeriodes"]["V"]

    # get onglet with number 198 (mes notes), otherwise fallback to the
    # first one in the list
    onglet = next((x for x in onglets if x.get("G") == 198), None)

    if onglet is None:
        log.warning('Could not find "mes notes" onglet')
        onglet = onglets[0]

    id_term = onglet["periodeParDefaut"]["V"]["N"]

    return next(term for term in terms if term.id == id_term)


class Client:
    def __init__(
        self,
        session: PronoteSession,
        server_options: ResponseJson,
        auth_response: ResponseJson,
        user_options: ResponseJson,
    ) -> None:
        self.session = session
        """Access to the low level PRONOTE session"""

        # raw responses from session initialisation
        self.server_options = server_options
        """Raw FonctionParametres response"""

        self.auth_response = auth_response
        """Raw Authentification response"""

        self.user_options = user_options
        """Raw ParametresUtilisateur response"""

        so_get = parse.locator(server_options)

        self.first_monday: datetime.date = so_get(
            parse.date, *parse.data_path, "General", "PremierLundi", "V"
        )
        """Date of the monday of the starting week of the school year"""

        self.first_day: datetime.date = so_get(
            parse.date, *parse.data_path, "General", "PremiereDate", "V"
        )
        """First day of the school year"""

        self.last_day: datetime.date = so_get(
            parse.date, *parse.data_path, "General", "DerniereDate", "V"
        )
        """Last day of the school year"""

        def make_term(t: Any) -> Term:
            return Term(self, t)

        self.terms: list[Term] = so_get(
            parse.many(make_term), *parse.data_path, "General", "ListePeriodes"
        )
        """School year terms"""

        self.current_term: Term = _get_current_term(user_options, self.terms)
        """Current school year term"""

        self._lesson_start_times = so_get(list, *parse.data_path, "General", "ListeHeures", "V")

    @classmethod
    async def login(cls, credentials: Credentials, mfa: MFACredentials | None = None) -> Client:
        """Create an authenticated client

        See :ref:`logging-in` for documentation on how to construct the credentials.
        """
        session, options, auth_response = await PronoteSession.login(credentials, mfa)

        try:
            user_options = await session.post("ParametresUtilisateur", {})
        except Exception:
            await session.close()
            raise

        return Client(session, options, auth_response, user_options)

    async def post(self, function_name: str, onglet: int, data: dict) -> ResponseJson:
        """Raw call to the PRONOTE API. Adds signature and calls PronoteSession.post."""

        post_data = {}
        if onglet:
            post_data["Signature"] = {"onglet": onglet}
        if data:
            post_data["data"] = data

        return await self.session.post(function_name, dataSec=post_data)

    @property
    async def client_identifier(self) -> str:
        return self.session.client_identifier

    @property
    async def next_token(self) -> Token | None:
        return self.session.next_token

    async def close(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> Client:
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.close()
