class PronoteError(Exception):
    """An unknown error occured (see cause)"""

    def __init__(self, msg: str | None = None) -> None:
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

    def __init__(self, status: int, error: dict | None) -> None:
        super().__init__(f"Unknown PRONOTE API error: {error}")
        self.status = status
        self.api_error = error


class MFAError(PronoteError):
    pass
