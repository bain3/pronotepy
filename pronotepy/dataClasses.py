from __future__ import annotations

import datetime
import json
import logging
import re
from html import unescape
from typing import (
    Union,
    List,
    Callable,
    Any,
    TypeVar,
    Optional,
    Tuple,
    Set,
    Iterable,
    TYPE_CHECKING,
)
from urllib.parse import quote
from autoslot import Slots  # type: ignore

from Crypto.Util import Padding

if TYPE_CHECKING:
    from .clients import ClientBase, Client
from .exceptions import (
    DataError,
    DiscussionClosed,
    ParsingError,
    DateParsingError,
    UnsupportedOperation,
)

from itertools import chain

__all__ = (
    "Util",
    "Object",
    "Subject",
    "Absence",
    "Period",
    "Average",
    "Grade",
    "Attachment",
    "LessonContent",
    "Lesson",
    "Homework",
    "Information",
    "Recipient",
    "Message",
    "Discussion",
    "ClientInfo",
    "Acquisition",
    "Evaluation",
    "Identity",
    "Guardian",
    "Student",
    "StudentClass",
    "Menu",
    "Punishment",
    "Delay",
    "TeachingStaff",
    "Report",
)

log = logging.getLogger(__name__)


def _get_l(d: dict) -> str:
    return d["L"]


T = TypeVar("T")


def noop(any: T) -> T:
    return any


class MissingType:
    pass


class Util:
    """Utilities for the API wrapper"""

    grade_translate = [
        "Absent",
        "Dispense",
        "NonNote",
        "Inapte",
        "NonRendu",
        "AbsentZero",
        "NonRenduZero",
        "Felicitations",
