from typing import Tuple


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
    pass


class DataError(Exception):
    """
    Base exception for any errors made by creating or manipulating data classes.
    """
    pass


class ParsingError(DataError):
    """Bad json"""
    def __init__(self, message: str, json_dict: dict, path: Tuple[str, ...]):
        super().__init__(message)
        self.json_dict = json_dict
        self.path = path


class ICalExportError(PronoteAPIError):
    """Error while exporting ICal. Pronote did not return token"""
    pass


class DateParsingError(PronoteAPIError):
    """Bad date string"""
    def __init__(self, message: str, date_string: str):
        super().__init__(message)
        self.date_string = date_string
