from __future__ import annotations

from .session import Credentials, MFACredentials, PronoteSession, ResponseJson


class Client:
    def __init__(
        self,
        session: PronoteSession,
        server_options: ResponseJson,
        auth_response: ResponseJson,
    ) -> None:
        self.session = session
        self.server_options = server_options
        self.auth_response = auth_response

    @classmethod
    async def login(
        cls, credentials: Credentials, mfa: MFACredentials | None = None
    ) -> Client:
        session, options, auth_response = await PronoteSession.login(credentials, mfa)

        return Client(session, options, auth_response)
