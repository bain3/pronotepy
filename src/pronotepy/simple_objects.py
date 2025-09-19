from __future__ import annotations

import datetime
from dataclasses import dataclass, field

from . import parse
from .parse import GradeValue, locator


@dataclass(init=False, slots=True)
class Grade:
    """A grade in a school year term"""

    id: str = field(compare=False)
    """Session-specific ID of the object"""
    grade: GradeValue
    """Student's actual grade"""
    out_of: str
    """Maximum amount of points"""
    default_out_of: str | None
    """Default maximum amount of points"""
    date: datetime.date
    """Date on which the grade was given"""
    subject: Subject
    """Subject in which the grade was given"""
    average: GradeValue | None
    """Average of the class"""
    max: GradeValue
    """Highest awarded grade from the class"""
    min: GradeValue
    """Lowest awarded grade from the class"""
    coefficient: str
    """Coefficient of the grade"""
    comment: str
    """Comment on the grade description"""
    is_bonus: bool
    """Is the grade a bonus"""
    is_optional: bool
    """Is the grade optional"""
    is_out_of_20: bool
    """Was the grade recalculated to 20 maximum points"""

    def __init__(self, json_dict: dict) -> None:
        get = locator(json_dict)

        self.id = get(str, "N")
        self.grade = get(parse.grade, "note", "V")
        # TODO: Verify that the property cannot contain SpecialGradeValue
        self.out_of = get(str, "bareme", "V")
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
    """Session-specific ID of the object"""
    name: str
    """Name of the subject"""
    groups: bool
    """Is the subject in groups"""

    def __init__(self, json_dict: dict) -> None:
        get = locator(json_dict)

        self.id = get(str, "N")
        self.name = get(str, "L")
        self.groups = get(bool, "estServiceGroupe", default=False)


@dataclass(init=False, slots=True)
class Average:
    """A subject Average"""

    student_average: GradeValue
    """Student's average in the subject"""
    class_average: GradeValue
    """Class' average in the subject"""
    out_of: str
    """Maximum amount of points"""
    default_out_of: str | None
    """The default maximum amount of points"""
    min: GradeValue
    """Lowest average in the class"""
    max: GradeValue
    """Highest average in the class"""
    subject: Subject
    """Subject the average is from"""
    background_color: str | None
    """Background color of the subject"""

    def __init__(self, json_dict: dict) -> None:
        get = locator(json_dict)

        self.student_average = get(parse.grade, "moyEleve", "V")
        self.class_average = get(parse.grade, "moyClasse", "V")
        # TODO: Verify that the property cannot contain SpecialGradeValue
        self.out_of = get(str, "baremeMoyEleve", "V")
        self.default_out_of = get(str, "baremeMoyEleveParDefault", "V", default=None)
        self.min = get(parse.grade, "moyMin", "V")
        self.max = get(parse.grade, "moyMax", "V")
        self.subject = Subject(json_dict)
        self.background_color = get(str, "couleur", default=None)


@dataclass(init=False, slots=True)
class Absence:
    """A student's absence in class"""

    id: str = field(compare=False)
    """Session-specific ID of the object"""
    from_date: datetime.datetime
    """Start of the absence"""
    to_date: datetime.datetime
    """End of the absence"""
    justified: bool
    """Is the absence justified"""
    hours: str | None
    """The number of hours missed"""
    days: int
    """The number of days missed"""
    reasons: list[str]
    """The reason(s) for the absence"""

    def __init__(self, json_dict: dict) -> None:
        get = locator(json_dict)

        self.id = get(str, "N")
        self.from_date = get(parse.datetime, "dateDebut", "V")
        self.to_date = get(parse.datetime, "dateFin", "V")
        self.justified = get(bool, "justifie", default=False)
        self.hours = get(str, "NbrHeures", default=None)
        self.days = get(int, "NbrJours", default=0)
        self.reasons = get(lambda motifs: [i["L"] for i in motifs], "listeMotifs", "V", default=[])


@dataclass(init=False, slots=True)
class Delay:
    """A student's delay to class"""

    id: str = field(compare=False)
    """Session-specific ID of the object"""
    date: datetime.datetime
    """Date of the delay"""
    minutes: int
    """The number of minutes missed"""
    justified: bool
    """Is the delay justified"""
    justification: str | None
    """The justification for the delay"""
    reasons: list[str]
    """The reason(s) for the delay"""

    def __init__(self, json_dict: dict) -> None:
        get = locator(json_dict)

        self.id = get(str, "N")
        self.date = get(parse.datetime, "date", "V")
        self.minutes = get(int, "duree", default=0)
        self.justified = get(bool, "justifie", default=False)
        self.justification = get(str, "justification", default=None)
        self.reasons = get(lambda motifs: [i["L"] for i in motifs], "listeMotifs", "V", default=[])


# class Punishment:
#     Attributes:
#         id (str)
#         given (Union[datetime.datetime, datetime.date]): Date and time when the punishment was given
#         exclusion (bool): If the punishment is an exclusion from class
#         during_lesson (bool): If the punishment was given during a lesson.
#             `self.during_lesson is True => self.given is datetime.datetime`
#         homework (Optional[str]): Text description of the homework that was given as the punishment
#         homework_documents (List[Attachment]): Attached documents for homework
#         circumstances (str)
#         circumstance_documents (List[Attachment])
#         nature (str): Text description of the nature of the punishment (ex. "Retenue")
#         reasons (List[str]): Text descriptions of the reasons for the punishment
#         giver (str): Name of the person that gave the punishment
#         schedule (List[ScheduledPunishment]): List of scheduled date-times with durations
#         schedulable (bool)
#         duration (Optional[datetime.timedelta])
#     class ScheduledPunishment(Object):
#         Attributes:
#             id (str)
#             start (Union[datetime.datetime, datetime.date])
#             duration (Optional[datetime.timedelta])


# @dataclass(init=False)
# class Punishment:
#     """A student's punishment
#
#     Attributes:
#         id (str)
#         given (Union[datetime.datetime, datetime.date]): Date and time when the punishment was given
#         exclusion (bool): If the punishment is an exclusion from class
#         during_lesson (bool): If the punishment was given during a lesson.
#             `self.during_lesson is True => self.given is datetime.datetime`
#         homework (Optional[str]): Text description of the work that was given as the punishment
#         homework_documents (List[Attachment]): Attached documents for work
#         circumstances (str)
#         circumstance_documents (List[Attachment])
#         nature (str): Text description of the nature of the punishment (ex. "Retenue")
#         reasons (List[str]): Text descriptions of the reasons for the punishment
#         giver (str): Name of the person that gave the punishment
#         schedule (List[ScheduledPunishment]): List of scheduled date-times with durations
#         duration (Optional[datetime.timedelta])
#     """
#
#     id: str = field(compare=False)
#     """Session-specific ID of the object"""
#     date: datetime.date
#     """Date on which the punishment was given"""
#     time_slot: int | None
#     """Time slot of the lesson the punishment was given in"""
#     during_lesson: bool
#     """If the punishment was given during a lesson"""
#     exclusion: bool
#     """If the punishment is an exclusion from class"""
#     homework: str | None
#     """Text description of the assigned work"""
#     circumstances: str
#     """Description of the event that the punishment is for"""
#     nature: str
#     """Kind of the punishment"""
#     requires_parent: str | None
#     """Is the parent required to fulfill the punishment"""
#     reasons: list[str]
#     """Text descriptions of the reasons for the punishment"""
#     given_by: str
#     """Name of the person that gave the punishment"""
#     schedulable: bool
#     """If the punishment administration can be scheduled"""
#     schedule: list[Punishment.ScheduledPunishment]
#     """Scheduled administrations of the punishment"""
#     duration: datetime.timedelta | None
#     """The full duration of the punishment"""
#
#     @dataclass(init=False)
#     class ScheduledPunishment:
#         """A sheduled administration of the punishment
#
#         Attributes:
#             id (str)
#             start (Union[datetime.datetime, datetime.date])
#             duration (Optional[datetime.timedelta])
#         """
#
#         id: str = field(compare=False)
#         """Session-specific ID of the object"""
#         date: datetime.date
#         """Date to which the punishment was scheduled"""
#         time_slot: int | None
#         """School time slot the punishment was scheduled to"""
#         duration: datetime.timedelta | None
#         """Duration of the scheduled punishment"""
#
#         def __init__(self, client: Client, json_dict: dict) -> None:
#             get = locator(json_dict)
#
#             self.id = get(str, "N")
#             self.date = get(parse.date, "date", "V")
#             self.time_slot = get(int, "placeExecution", default=None)
#             self.duration = get(parse.timedelta, "duree", default=None)
#
#             self._lesson_start_times = client._lesson_start_times
#
#         @property
#         def start(self) -> datetime.datetime:
#             return datetime.datetime.combine(
#                 self.date,
#                 place2time(self._lesson_start_times, self.time_slot)
#                 if self.time_slot is not None
#                 else datetime.datetime.min.time(),
#             )
#
#     def __init__(self, client: Client, json_dict: dict) -> None:
#         get = locator(json_dict)
#         self.id = get(str, "N")
#
#         self.date = get(parse.date, "dateDemande", "V")
#         self.time_slot = get(int, "placeDemande", default=None)
#         self.during_lesson = get(lambda v: not bool(v), "horsCours")
#         self.exclusion = get(bool, "estUneExclusion")
#         self.homework = get(str, "travailAFaire", default=None)
#         # TODO: change to an enum
#         self.nature = get(str, "nature", "V", "L")
#         self.requires_parent = get(str, "nature", "V", "estAvecARParent", default=None)
#         self.reasons = get(lambda x: [i["L"] for i in x], "listeMotifs", "V")
#         self.given_by = get(str, "demandeur", "V", "L")
#         self.duration = get(parse.timedelta, "duree", default=None)
#         self.circumstances = get(str, "circonstances")
#         self.schedule = get(
#             lambda x: [Punishment.ScheduledPunishment(client, i) for i in x],
#             "programmation",
#             "V",
#             default=[],
#         )
#         # self.circumstance_documents: list[Attachment] = get(
#         #     lambda x: [Attachment(client, a) for a in x], "documentsCirconstances", "V"
#         # )
#         # self.homework_documents: list[Attachment] = get(
#         #     lambda x: [Attachment(client, a) for a in x],
#         #     "documentsTAF",
#         #     "V",
#         #     default=[],
#         # )
#
#         self._lesson_start_times = client._lesson_start_times
#
#     @property
#     def given_at(self) -> datetime.datetime:
#         """Date and time when the punishment was given"""
#
#         return datetime.datetime.combine(
#             self.date,
#             place2time(self._lesson_start_times, self.time_slot)
#             if self.time_slot is not None
#             else datetime.datetime.min.time(),
#         )
