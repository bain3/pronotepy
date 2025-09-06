from __future__ import annotations

from dataclasses import dataclass, field

from . import parse
from .parse import locator, GradeValue

import datetime


@dataclass(init=False, slots=True)
class Grade:
    """A grade in a school year term"""

    id: str = field(compare=False)
    grade: GradeValue
    out_of: GradeValue
    default_out_of: str | None
    date: datetime.date
    subject: Subject
    average: GradeValue | None
    max: GradeValue
    min: GradeValue
    coefficient: str
    comment: str
    is_bonus: bool
    is_optional: bool
    is_out_of_20: bool

    def __init__(self, json_dict: dict) -> None:
        get = locator(json_dict)

        self.id = get(str, "N")
        self.grade = get(parse.grade, "note", "V")
        self.out_of = get(parse.grade, "bareme", "V")
        self.default_out_of = get(str, "baremeParDefaut", "V", default=None)
        self.date = get(parse.date, "date", "V")
        self.subject = get(Subject, "service", "V")
        self.average = get(parse.grade, "moyenne", "V", default=None)
        self.max = get(parse.grade, "noteMax", "V")
        self.min = get(parse.grade, "noteMin", "V")
        self.coefficient = get(str, "coefficient")
        self.comment = get(str, "commentaire")
        self.is_bonus = get(bool, "estBonus")
        self.is_optional = get(bool, "estFacultatif") and not self.is_bonus
        self.is_out_of_20 = get(bool, "estRamenerSur20")


@dataclass(init=False, slots=True)
class Subject:
    """A subject"""

    id: str = field(compare=False)
    name: str
    groups: bool

    def __init__(self, json_dict: dict) -> None:
        get = locator(json_dict)

        self.id = get(str, "N")
        self.name = get(str, "L")
        self.groups = get(bool, "estServiceGroupe", default=False)
