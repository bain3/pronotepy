from __future__ import annotations

import datetime
from typing import Any

from .term import Term

from .session import Credentials, MFACredentials, PronoteSession, ResponseJson

from . import parse


class Client:
    def __init__(
        self,
        session: PronoteSession,
        server_options: ResponseJson,
        auth_response: ResponseJson,
        user_options: ResponseJson,
    ) -> None:
        self.session = session

        # raw responses from session initialisation
        self.server_options = server_options
        self.auth_response = auth_response
        self.user_options = user_options

        so_get = parse.locator(server_options)

        self.start_day: datetime.date = so_get(
            parse.date, *parse.data_path, "General", "PremierLundi", "V"
        )

        def make_term(t: Any) -> Term:
            return Term(self, t)

        self.periods: list[Term] = so_get(
            parse.many(make_term), *parse.data_path, "General", "ListePeriodes"
        )

    @classmethod
    async def login(cls, credentials: Credentials, mfa: MFACredentials | None = None) -> Client:
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

    async def close(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> Client:
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.close()
