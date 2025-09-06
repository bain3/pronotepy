from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Protocol, TypeVar
import logging
import json

from .err import ParsingError

import datetime as dt
import re

log = logging.getLogger(__name__)


class MissingType:
    pass


_missing: MissingType = MissingType()


if TYPE_CHECKING:
    R = TypeVar("R")

    class InnerLocator(Protocol):
        def __call__(
            self, converter: Callable[[Any], R], *path: str, default: MissingType | R = _missing
        ) -> R: ...


def locator(json_dict: dict) -> InnerLocator:
    """
    Resolves an arbitrary value from a json dictionary.
    """

    def inner(
        converter: Callable[[Any], R],
        *path: str,
        default: MissingType | R = _missing,
    ) -> R:
        """
        Resolves an arbitrary value from a json dictionary

        Args:
            converter: the final value will be passed to this converter, it can be any callable with a single argument
            path: arguments describing the path through the dictionary to the value
            default: default value if the actual one cannot be found
        Returns:
            the resolved value
        """
        json_value: Any = json_dict

        try:
            for p in path:  # walk through the json dict according to the path
                json_value = json_value[p]
        except KeyError as e:
            # we have failed to get the correct value, try to return a default
            if default is not _missing:
                json_value = default
            else:
                # in strict mode we do not want to give unpredictable output
                log.debug("Could not follow path in:")
                log.debug(json.dumps(json_dict))
                log.debug(path)
                raise ParsingError("Could not follow path", json_dict, path) from e
        else:
            try:
                json_value = converter(json_value)
            except Exception as e:
                log.debug(
                    "Could not convert value %s(%s) with %s",
                    type(json_value),
                    json_value,
                    converter,
                )
                raise ParsingError(f"Error while converting value: {e}", json_dict, path) from e

        return json_value

    return inner


def datetime(formatted_date: str) -> dt.datetime:
    """convert date to a datetime.datetime object"""
    if re.match(r"\d{2}/\d{2}/\d{4}$", formatted_date):
        return dt.datetime.strptime(formatted_date, "%d/%m/%Y")
    elif re.match(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$", formatted_date):
        return dt.datetime.strptime(formatted_date, "%d/%m/%Y %H:%M:%S")
    elif re.match(r"\d{2}/\d{2}/\d{2} \d{2}h\d{2}$", formatted_date):
        return dt.datetime.strptime(formatted_date, "%d/%m/%y %Hh%M")
    else:
        raise ValueError("Could not parse date", formatted_date)


def date(formatted_date: str) -> dt.date:
    """convert date to a datetime.date object"""

    if re.match(r"\d{2}/\d{2}/\d{4}$", formatted_date):
        return dt.datetime.strptime(formatted_date, "%d/%m/%Y").date()
    elif re.match(r"\d{2}/\d{2}/\d{2}$", formatted_date):
        return dt.datetime.strptime(formatted_date, "%d/%m/%y").date()
    elif re.match(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$", formatted_date):
        return dt.datetime.strptime(formatted_date, "%d/%m/%Y %H:%M:%S").date()
    elif re.match(r"\d{2}/\d{2}/\d{2} \d{2}h\d{2}$", formatted_date):
        return dt.datetime.strptime(formatted_date, "%d/%m/%y %Hh%M").date()
    elif re.match(r"\d{2}/\d{2}", formatted_date):
        formatted_date += f"/{dt.date.today().year}"
        return dt.datetime.strptime(formatted_date, "%d/%m/%Y").date()
    elif re.match(r"\d{2}\d{2}$", formatted_date):
        date = dt.date.today()
        hours = int(formatted_date[:2])
        minutes = int(formatted_date[2:])
        formatted_date = f"{date:%d}/{date:%m}/{date.year} {hours}h{minutes}"
        return dt.datetime.strptime(formatted_date, "%d/%m/%Y %Hh%M").date()
    else:
        raise ValueError("Could not parse date", formatted_date)


class SpecialGradeValue(Enum):
    ABSENT = 1
    DISPENSE = 2
    NONNOTE = 3
    INAPTE = 4
    NONRENDU = 5
    ABSENTZERO = 6
    NONRENDUZERO = 7
    FELICITATIONS = 8

    def __str__(self) -> str:
        return [
            "Absent",
            "Dispense",
            "NonNote",
            "Inapte",
            "NonRendu",
            "AbsentZero",
            "NonRenduZero",
            "Felicitations",
        ][self.value]


GradeValue = str | SpecialGradeValue


def grade(string: str) -> GradeValue:
    if "|" in string:
        return SpecialGradeValue(int(string[1]))
    else:
        return string


def many(f: Callable[[Any], R]) -> Callable[[Any], list[R]]:
    def inner(vals: list[Any]) -> list[R]:
        return [f(v) for v in vals]

    return inner


data_path = ("dataSec", "data")
