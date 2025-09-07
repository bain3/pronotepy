from __future__ import annotations

from dataclasses import dataclass, field

from . import parse
from .parse import locator, GradeValue

import datetime


@dataclass(init=False, slots=True)
class Grade:
    """A grade in a school year term"""

    id: str = field(compare=False)
    """Session-specific ID of the object"""
    grade: GradeValue
    """Student's actual grade"""
    out_of: GradeValue
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


# @dataclass(init=False, slots=True)
# class Punishment:
#     """
#     Represents a punishment.
#
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
#     """
#
#     class ScheduledPunishment(Object):
#         """
#         Represents a sheduled punishment.
#
#         Attributes:
#             id (str)
#             start (Union[datetime.datetime, datetime.date])
#             duration (Optional[datetime.timedelta])
#         """
#
#         def __init__(self, client: ClientBase, json_dict: dict) -> None:
#             super().__init__(json_dict)
#             self.id: str = self._resolver(str, "N")
#
#             # construct a full datetime from "date" and "placeExecution" fields
#             date = self._resolver(Util.date_parse, "date", "V")
#             place = self._resolver(int, "placeExecution", strict=False)
#
#             self.start: Union[datetime.datetime, datetime.date]
#             if place is not None:
#                 liste_heures = client.func_options["dataSec"]["data"]["General"][
#                     "ListeHeures"
#                 ]["V"]
#                 try:
#                     self.start = datetime.datetime.combine(
#                         date, Util.place2time(liste_heures, place)
#                     )
#                 except ValueError as e:
#                     raise DataError(str(e))
#             else:
#                 self.start = date
#
#             self.duration: Optional[datetime.timedelta] = self._resolver(
#                 lambda v: datetime.timedelta(minutes=int(v)), "duree", strict=False
#             )
#
#             del self._resolver
#
#     def __init__(self, client: ClientBase, json_dict: dict) -> None:
#         super().__init__(json_dict)
#         self.id: str = self._resolver(str, "N")
#
#         date = self._resolver(Util.date_parse, "dateDemande", "V")
#         self.during_lesson: bool = self._resolver(lambda v: not bool(v), "horsCours")
#
#         # construct a full datetime from "dateDemande" and "placeDemande" fields
#         self.given: Union[datetime.datetime, datetime.date]
#         if self.during_lesson:
#             time_place = self._resolver(int, "placeDemande")
#             liste_heures = client.func_options["dataSec"]["data"]["General"][
#                 "ListeHeures"
#             ]["V"]
#             try:
#                 self.given = datetime.datetime.combine(
#                     date, Util.place2time(liste_heures, time_place)
#                 )
#             except ValueError as e:
#                 raise DataError(str(e))
#         else:
#             self.given = date
#
#         self.exclusion: bool = self._resolver(bool, "estUneExclusion")
#
#         self.homework: str = self._resolver(str, "travailAFaire", strict=False)
#         self.homework_documents: List[Attachment] = self._resolver(
#             lambda x: [Attachment(client, a) for a in x],
#             "documentsTAF",
#             "V",
#             default=[],
#         )
#
#         self.circumstances: str = self._resolver(str, "circonstances")
#         self.circumstance_documents: List[Attachment] = self._resolver(
#             lambda x: [Attachment(client, a) for a in x], "documentsCirconstances", "V"
#         )
#
#         # TODO: change to an enum (out of scope for this comment: change this kind of string to enums everywhere)
#         self.nature: str = self._resolver(str, "nature", "V", "L")
#         self.requires_parent: Optional[str] = self._resolver(
#             str, "nature", "V", "estAvecARParent", strict=False
#         )
#
#         self.reasons: List[str] = self._resolver(
#             lambda x: [i["L"] for i in x], "listeMotifs", "V"
#         )
#         self.giver: str = self._resolver(str, "demandeur", "V", "L")
#
#         self.schedulable: bool = self._resolver(bool, "estProgrammable")
#
#         self.schedule: List[Punishment.ScheduledPunishment] = []
#         if self.schedulable:
#             self.schedule = self._resolver(
#                 lambda x: [Punishment.ScheduledPunishment(client, i) for i in x],
#                 "programmation",
#                 "V",
#             )
#
#         self.duration: Optional[datetime.timedelta] = self._resolver(
#             lambda v: datetime.timedelta(minutes=int(v)), "duree", strict=False
#         )
