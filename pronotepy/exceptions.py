class PronoteAPIError(Exception):
    """
    Base exception for any pronote api errors
    """

    def __init__(self, *args: object, pronote_error_code: int = None, pronote_error_msg: str = None) -> None:
        super().__init__(*args)
        self.pronote_error_code = pronote_error_code
        self.pronote_error_msg = pronote_error_msg


class CryptoError(PronoteAPIError):
    """Exception for known errors in the cryptography."""
    pass


class ExpiredObject(PronoteAPIError):
    """Raised when pronote returns error 22. (unknown object reference)"""
    pass


class ChildNotFound(PronoteAPIError):
    """Child with this name was not found."""


class DataError(Exception):
    """
    Base exception for any errors made by creating or manipulating data classes.
    """
    pass


class IncorrectJson(DataError):
    """Bad json"""
    pass
