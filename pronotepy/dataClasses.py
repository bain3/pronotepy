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
    ]

    @classmethod
    def get(cls, iterable: Iterable[T], **kwargs: Any) -> list[T]:
        """Gets items from the list with the attributes specified.

        Args:
            iterable (list): The iterable to loop over
        """
        output = []
        for i in iterable:
            for attr in kwargs:
                if not hasattr(i, attr) or getattr(i, attr) != kwargs[attr]:
                    break
            else:
                output.append(i)
        return output

    @classmethod
    def grade_parse(cls, string: str) -> str:
        if "|" in string:
            return cls.grade_translate[int(string[1]) - 1]
        else:
            return string

    @staticmethod
    def date_parse(formatted_date: str) -> datetime.date:
        """convert date to a datetime.date object"""

        if re.match(r"\d{2}/\d{2}/\d{4}$", formatted_date):
            return datetime.datetime.strptime(formatted_date, "%d/%m/%Y").date()
        elif re.match(r"\d{2}/\d{2}/\d{2}$", formatted_date):
            return datetime.datetime.strptime(formatted_date, "%d/%m/%y").date()
        elif re.match(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$", formatted_date):
            return datetime.datetime.strptime(
                formatted_date, "%d/%m/%Y %H:%M:%S"
            ).date()
        elif re.match(r"\d{2}/\d{2}/\d{2} \d{2}h\d{2}$", formatted_date):
            return datetime.datetime.strptime(formatted_date, "%d/%m/%y %Hh%M").date()
        elif re.match(r"\d{2}/\d{2}", formatted_date):
            formatted_date += f"/{datetime.date.today().year}"
            return datetime.datetime.strptime(formatted_date, "%d/%m/%Y").date()
        elif re.match(r"\d{2}\d{2}$", formatted_date):
            date = datetime.date.today()
            hours = int(formatted_date[:2])
            minutes = int(formatted_date[2:])
            formatted_date = f"{date:%d}/{date:%m}/{date.year} {hours}h{minutes}"
            return datetime.datetime.strptime(formatted_date, "%d/%m/%Y %Hh%M").date()
        else:
            raise DateParsingError("Could not parse date", formatted_date)

    @staticmethod
    def datetime_parse(formatted_date: str) -> datetime.datetime:
        """convert date to a datetime.datetime object"""
        if re.match(r"\d{2}/\d{2}/\d{4}$", formatted_date):
            return datetime.datetime.strptime(formatted_date, "%d/%m/%Y")
        elif re.match(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$", formatted_date):
            return datetime.datetime.strptime(formatted_date, "%d/%m/%Y %H:%M:%S")
        elif re.match(r"\d{2}/\d{2}/\d{2} \d{2}h\d{2}$", formatted_date):
            return datetime.datetime.strptime(formatted_date, "%d/%m/%y %Hh%M")
        else:
            raise DateParsingError("Could not parse date", formatted_date)

    @staticmethod
    def html_parse(html_text: str) -> str:
        """remove tags from html text"""
        return unescape(re.sub(re.compile("<.*?>"), "", html_text))

    @staticmethod
    def place2time(listeHeures: List, place: int) -> datetime.time:
        if place > len(listeHeures):
            # might be wrong... works with demo
            place = place % (len(listeHeures) - 1)
        start_time = next(
            filter(lambda x: x["G"] == place, listeHeures),
            None,
        )
        if start_time is None:
            raise ValueError(f"Could not find starting time for place {place}")
        start_time = datetime.datetime.strptime(start_time["L"], "%Hh%M").time()
        return start_time


class Object(Slots):
    """
    Base object for all pronotepy data classes.
    """

    __slots__ = ("_resolver",)

    class _Resolver:
        """
        Resolves an arbitrary value from a json dictionary.
        """

        R = TypeVar("R")
        _missing: MissingType = MissingType()

        def __init__(self, json_dict: dict):
            self.json_dict = json_dict

        def __call__(
            self,
            converter: Callable[[Any], R],
            *path: str,
            default: Union[MissingType, R] = _missing,
            strict: bool = True,
        ) -> R:
            """
            Resolves an arbitrary value from a json dictionary

            Args:
                converter (Callable[[Any], R]): the final value will be passed to this converter, it can be any callable with a single argument
                path (str): arguments describing the path through the dictionary to the value
                default (Union[MissingType, R]): default value if the actual one cannot be found, works with strict as False
                strict (bool): if False, the resolver will return None when it can't find the correct value
            Returns:
                the resolved value
            """
            json_value: Any = self.json_dict
            try:
                for p in path:  # walk through the json dict according to the path
                    json_value = json_value[p]
            except KeyError as e:
                # we have failed to get the correct value, try to return a default
                if default is not self._missing:
                    log.debug(
                        f"Could not get value for (path: %s), setting to default.",
                        ",".join(path),
                    )
                    json_value = default
                elif strict:
                    # in strict mode we do not want to give unpredictable output
                    log.debug("Could not follow path in:")
                    log.debug(json.dumps(self.json_dict))
                    log.debug(path)
                    raise ParsingError(
                        "Could not follow path", self.json_dict, path
                    ) from e
                else:
                    json_value = None
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
                    raise ParsingError(
                        f"Error while converting value: {e}", self.json_dict, path
                    ) from e

            return json_value

    def __init__(self, json_dict: dict) -> None:
        self._resolver: Object._Resolver = self._Resolver(json_dict)

    def to_dict(
        self, exclude: Set[str] = set(), include_properties: bool = False
    ) -> dict:
        """
        Recursively serializes this object into a dict

        .. note:: Does not check for loops, which are currently handled on a case to case basis.

        Args:
            exclude (Set[str]): items to exclude from serialization
            include_properties (bool): whether to evaluate properties.
                This may be useful for example for a :class:`Period` for which you want to
                serialize its grades too. :attr:`Period.grades` is a property that is evaluated
                only when called.

                .. warning:: Setting this option to `True` can be **extremely** inefficient!

        Returns:
            dict: A dictionary containing all non-private properties
        """

        def serialize_slot(slot: Any) -> Any:
            if isinstance(slot, Object):
                return slot.to_dict()
            else:
                # Assume all other values are primitives
                return slot

        serialized = {}

        # Join __slots__ with a list of all properties if include_properties is True
        # otherwise just iterate overs __slots__
        to_iter = (
            chain(
                self.__slots__,
                [
                    prop
                    for prop in dir(self.__class__)
                    if not prop.startswith("_")
                    and isinstance(getattr(self.__class__, prop), property)
                ],
            )
            if include_properties
            else self.__slots__
        )
        for slot_name in to_iter:
            if slot_name.startswith("_") or slot_name in exclude:
                # Skip private and excluded slots
                continue

            slot = getattr(self, slot_name)

            serialized[slot_name] = (
                [serialize_slot(v) for v in slot]
                if isinstance(slot, list)
                else serialize_slot(slot)
            )
        return serialized


class Subject(Object):
    """
    Represents a subject. You shouldn't have to create this class manually.

    Attributes:
        id (str): the id of the subject (used internally)
        name (str): name of the subject
        groups (bool): if the subject is in groups
    """

    def __init__(self, parsed_json: dict) -> None:
        super().__init__(parsed_json)

        self.id: str = self._resolver(str, "N")
        self.name: str = self._resolver(str, "L")
        self.groups: bool = self._resolver(bool, "estServiceGroupe", default=False)


class Report(Object):
    """Represents a student report. You shouldn't have to create this class manually.

    Attributes:
        subjects (List[ReportSubject]): the subjects that are present in the report
        comments (List[str]): the global report comments
    """

    class ReportSubject(Object):
        """
        Represents a subject found in a report. You shouldn't have to create this class manually.

        Attributes:
            id (str): the id of the subject (used internally)
            name (str): name of the subject
            color (str): the color of the subject
            comments (List[str]): the list of the subject's comments
            class_average (Optional[str]): the average of the class
            student_average (Optional[str]): the average of the student
            min_average (Optional[str]): the lowest average of the class
            max_average (Optional[str]): the highest average of the class
            coefficient (Optional[str]): the coefficient of the subject
            teachers (List[str]): the subject's teachers' names
        """

        def __init__(self, parsed_json: dict) -> None:
            super().__init__(parsed_json)

            self.id: str = self._resolver(str, "N")
            self.name: str = self._resolver(str, "L")

            self.color: str = self._resolver(str, "couleur")
            self.comments: List[str] = self._resolver(
                lambda l: [c["L"] for c in l if "L" in c], "ListeAppreciations", "V"
            )

            def grade_or_none(grade: Any) -> Optional[str]:
                return Util.grade_parse(grade) if grade else None

            self.class_average: Optional[str] = self._resolver(
                grade_or_none, "MoyenneClasse", "V", strict=False
            )
            self.student_average: Optional[str] = self._resolver(
                grade_or_none, "MoyenneEleve", "V", strict=False
            )
            self.min_average: Optional[str] = self._resolver(
                grade_or_none, "MoyenneInf", "V", strict=False
            )
            self.max_average: Optional[str] = self._resolver(
                grade_or_none, "MoyenneSup", "V", strict=False
            )
            self.coefficient: Optional[str] = self._resolver(
                str, "Coefficient", "V", strict=False
            )
            self.teachers: List[str] = self._resolver(
                lambda l: [i["L"] for i in l], "ListeProfesseurs", "V", default=[]
            )

            del self._resolver

    def __init__(self, parsed_json: dict) -> None:
        super().__init__(parsed_json)

        self.subjects: List[Report.ReportSubject] = self._resolver(
            lambda l: [Report.ReportSubject(s) for s in l],
            "ListeServices",
            "V",
            default=[],
        )
        self.comments: List[str] = self._resolver(
            lambda l: [c["L"] for c in l if "L" in c],
            "ObjetListeAppreciations",
            "V",
            "ListeAppreciations",
            "V",
            default=[],
        )


class Absence(Object):
    """
    Represents an absence with a given period. You shouldn't have to create this class manually.

    Attributes:
        id (str): the id of the absence (used internally)
        from_date (datetime.datetime): starting time of the absence
        to_date (datetime.datetime): end of the absence
        justified (bool): is the absence justified
        hours (str): the number of hours missed
        days (int): the number of days missed
        reasons (List[str]): The reason(s) for the absence
    """

    def __init__(self, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.id: str = self._resolver(str, "N")
        self.from_date: datetime.datetime = self._resolver(
            Util.datetime_parse, "dateDebut", "V"
        )
        self.to_date: datetime.datetime = self._resolver(
            Util.datetime_parse, "dateFin", "V"
        )
        self.justified: bool = self._resolver(bool, "justifie", default=False)
        self.hours: Optional[str] = self._resolver(str, "NbrHeures", strict=False)
        self.days: int = self._resolver(int, "NbrJours", default=0)
        self.reasons: List[str] = self._resolver(
            lambda l: [i["L"] for i in l], "listeMotifs", "V", default=[]
        )

        del self._resolver


class Delay(Object):
    """
    Represents a delay with a given period. You shouldn't have to create this class manually.

    Attributes:
        id (str): the id of the delay (used internally)
        date (datetime.datetime): date of the delay
        minutes (str): the number of minutes missed
        justified (bool): is the delay justified
        justification (str): the justification for the delay
        reasons (List[str]): The reason(s) for the delay
    """

    def __init__(self, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.id: str = self._resolver(str, "N")
        self.date: datetime.datetime = self._resolver(Util.datetime_parse, "date", "V")
        self.minutes: int = self._resolver(int, "duree", default=0)
        self.justified: bool = self._resolver(bool, "justifie", default=False)
        self.justification: Optional[str] = self._resolver(
            str, "justification", strict=False
        )
        self.reasons: List[str] = self._resolver(
            lambda l: [i["L"] for i in l], "listeMotifs", "V", default=[]
        )

        del self._resolver


class Period(Object):
    """
    Represents a period of the school year. You shouldn't have to create this class manually.

    Attributes:
        id (str): the id of the period (used internally)
        name (str): name of the period
        start (datetime.datetime): date on which the period starts
        end (datetime.datetime): date on which the period ends
    """

    instances: Set[Any] = set()

    def __init__(self, client: ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.__class__.instances.add(self)
        self._client = client

        self.id: str = self._resolver(str, "N")
        self.name: str = self._resolver(str, "L")
        self.start: datetime.datetime = self._resolver(
            Util.datetime_parse, "dateDebut", "V"
        )
        self.end: datetime.datetime = self._resolver(
            Util.datetime_parse, "dateFin", "V"
        )

        del self._resolver

    @property
    def report(self) -> Optional[Report]:
        """
        Gets a report from a period.

        Returns:
            Optional[Report]:
                When ``None``, then the report is not yet published or is unavailable for any other reason
        """
        json_data = {"periode": {"G": 2, "N": self.id, "L": self.name}}
        data = self._client.post("PageBulletins", 13, json_data)["donneesSec"][
            "donnees"
        ]
        return Report(data) if "Message" not in data else None

    @property
    def grades(self) -> List["Grade"]:
        """Get grades from the period."""
        json_data = {"Periode": {"N": self.id, "L": self.name}}
        response = self._client.post("DernieresNotes", 198, json_data)
        grades = response["donneesSec"]["donnees"]["listeDevoirs"]["V"]
        return [Grade(g) for g in grades]

    @property
    def averages(self) -> List["Average"]:
        """Get averages from the period."""

        json_data = {"Periode": {"N": self.id, "L": self.name}}
        response = self._client.post("DernieresNotes", 198, json_data)
        crs = response["donneesSec"]["donnees"]["listeServices"]["V"]
        try:
            return [Average(c) for c in crs]
        except ParsingError as e:
            if e.path == ["moyEleve", "V"]:
                raise UnsupportedOperation("Could not get averages")
            raise

    @property
    def overall_average(self) -> str:
        """Get overall average from the period. If the period average is not provided by pronote, then it's calculated.
        Calculation may not be the same as the actual average. (max difference 0.01)"""
        json_data = {"Periode": {"N": self.id, "L": self.name}}
        response = self._client.post("DernieresNotes", 198, json_data)
        average = response["donneesSec"]["donnees"].get("moyGenerale")
        if average:
            return average["V"]
        # VVVVVVVV will be removed in v3.0.0
        elif response["donneesSec"]["donnees"]["listeServices"]["V"]:
            a: float = 0
            total = 0
            services = response["donneesSec"]["donnees"]["listeServices"]["V"]
            for s in services:
                try:
                    avrg = s["moyEleve"]["V"].replace(",", ".")
                except KeyError:
                    raise UnsupportedOperation("Could not get averages")
                try:
                    flt = float(avrg)
                except ValueError:
                    flt = False
                if flt:
                    a += flt
                    total += 1
            average = round(a / total, 2) if total else -1
        else:
            average = -1
        return str(average)

    @property
    def class_overall_average(self) -> Optional[str]:
        """Get group average from the period."""
        json_data = {"Periode": {"N": self.id, "L": self.name}}
        response = self._client.post("DernieresNotes", 198, json_data)
        average = response["donneesSec"]["donnees"].get("moyGeneraleClasse")
        if average:
            return average["V"]
        else:
            return None

    @property
    def evaluations(self) -> List["Evaluation"]:
        """
        All evaluations from this period
        """
        json_data = {"periode": {"N": self.id, "L": self.name, "G": 2}}
        response = self._client.post("DernieresEvaluations", 201, json_data)
        evaluations = response["donneesSec"]["donnees"]["listeEvaluations"]["V"]
        return [Evaluation(e) for e in evaluations]

    @property
    def absences(self) -> List[Absence]:
        """
        All absences from this period
        """
        json_data = {
            "periode": {"N": self.id, "L": self.name, "G": 2},
            "DateDebut": {"_T": 7, "V": self.start.strftime("%d/%m/%Y %H:%M:%S")},
            "DateFin": {"_T": 7, "V": self.end.strftime("%d/%m/%Y %H:%M:%S")},
        }

        response = self._client.post("PagePresence", 19, json_data)
        absences = response["donneesSec"]["donnees"]["listeAbsences"]["V"]
        return [Absence(a) for a in absences if a["G"] == 13]

    @property
    def delays(self) -> List[Delay]:
        """
        All delays from this period
        """
        json_data = {
            "periode": {"N": self.id, "L": self.name, "G": 2},
            "DateDebut": {"_T": 7, "V": self.start.strftime("%d/%m/%Y %H:%M:%S")},
            "DateFin": {"_T": 7, "V": self.end.strftime("%d/%m/%Y %H:%M:%S")},
        }

        response = self._client.post("PagePresence", 19, json_data)
        delays = response["donneesSec"]["donnees"]["listeAbsences"]["V"]
        return [Delay(a) for a in delays if a["G"] == 14]

    @property
    def punishments(self) -> List[Punishment]:
        """
        All punishments from a given period
        """
        json_data = {
            "periode": {"N": self.id, "L": self.name, "G": 2},
            "DateDebut": {"_T": 7, "V": self.start.strftime("%d/%m/%Y %H:%M:%S")},
            "DateFin": {"_T": 7, "V": self.end.strftime("%d/%m/%Y %H:%M:%S")},
        }

        response = self._client.post("PagePresence", 19, json_data)
        absences = response["donneesSec"]["donnees"]["listeAbsences"]["V"]
        return [Punishment(self._client, a) for a in absences if a["G"] == 41]


class Average(Object):
    """
    Represents an Average.

    Attributes:
        student (str): students average in the subject
        class_average (str): classes average in the subject
        max (str): highest average in the class
        min (str): lowest average in the class
        out_of (str): maximum amount of points
        default_out_of (str): the default maximum amount of points
        subject (Subject): subject the average is from
        background_color (str): background color of the subject
    """

    def __init__(self, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.student: str = self._resolver(Util.grade_parse, "moyEleve", "V")
        self.out_of: str = self._resolver(Util.grade_parse, "baremeMoyEleve", "V")
        self.default_out_of: str = self._resolver(
            Util.grade_parse, "baremeMoyEleveParDefault", "V", default=""
        )
        self.class_average: str = self._resolver(Util.grade_parse, "moyClasse", "V")
        self.min: str = self._resolver(Util.grade_parse, "moyMin", "V")
        self.max: str = self._resolver(Util.grade_parse, "moyMax", "V")
        self.subject = Subject(json_dict)
        self.background_color: Optional[str] = self._resolver(
            str, "couleur", strict=False
        )

        del self._resolver


class Grade(Object):
    """Represents a grade. You shouldn't have to create this class manually.

    Attributes:
        id (str): the id of the grade (used internally)
        grade (str): the actual grade
        out_of (str): the maximum amount of points
        default_out_of (Optional[str]): the default maximum amount of points
        date (datetime.date): the date on which the grade was given
        subject (Subject): the subject in which the grade was given
        period (Period): the period in which the grade was given
        average (str): the average of the class
        max (str): the highest grade of the test
        min (str): the lowest grade of the test
        coefficient (str): the coefficient of the grade
        comment (str): the comment on the grade description
        is_bonus (bool): is the grade bonus : only points above 10 count
        is_optionnal (bool): is the grade optionnal : the grade only counts if it increases the average
        is_out_of_20 (bool): is the grade out of 20. Example 8/10 -> 16/20
    """

    # TODO: optionnal -> optional

    def __init__(self, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.id: str = self._resolver(str, "N")
        self.grade: str = self._resolver(Util.grade_parse, "note", "V")
        self.out_of: str = self._resolver(Util.grade_parse, "bareme", "V")
        self.default_out_of: str = self._resolver(
            Util.grade_parse, "baremeParDefaut", "V", strict=False
        )
        self.date: datetime.date = self._resolver(Util.date_parse, "date", "V")
        self.subject: Subject = self._resolver(Subject, "service", "V")
        # TODO: remove, because it creates a loop when trying to `to_dict`
        self.period: Period = self._resolver(
            lambda p: Util.get(Period.instances, id=p)[0], "periode", "V", "N"
        )
        self.average: str = self._resolver(
            Util.grade_parse, "moyenne", "V", strict=False
        )
        self.max: str = self._resolver(Util.grade_parse, "noteMax", "V")
        self.min: str = self._resolver(Util.grade_parse, "noteMin", "V")
        self.coefficient: str = self._resolver(str, "coefficient")
        self.comment: str = self._resolver(str, "commentaire")
        self.is_bonus: bool = self._resolver(bool, "estBonus")
        self.is_optionnal: bool = (
            self._resolver(bool, "estFacultatif") and not self.is_bonus
        )
        self.is_out_of_20: bool = self._resolver(bool, "estRamenerSur20")

        del self._resolver

    def to_dict(
        self, exclude: Set[str] = set(), include_properties: bool = False
    ) -> dict:
        # Exclude self.period, because it would otherwise cause a loop
        return super().to_dict(
            exclude={
                "period",
            }.union(exclude),
            include_properties=include_properties,
        )


class Attachment(Object):
    """
    Represents a attachment to homework for example

    Attributes:
        name (str): Name of the file or url of the link.
        id (str): id of the file (used internally and for url)
        url (str): url of the file/link
        type (int): type of the attachment (0 = link, 1 = file)
    """

    def __init__(self, client: ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)

        self._client = client

        self.name: str = self._resolver(str, "L", default="")
        self.id: str = self._resolver(str, "N")
        self.type: int = self._resolver(int, "G")  # 0 link, 1 file

        if self.type == 0:
            self.url = self.name
        else:
            padd = Padding.pad(
                json.dumps({"N": self.id, "Actif": True}).replace(" ", "").encode(), 16
            )
            magic_stuff = client.communication.encryption.aes_encrypt(padd).hex()

            self.url = (
                f"{client.communication.root_site}/FichiersExternes/{magic_stuff}/"
                + quote(self.name, safe="~()*!.'")
                + f"?Session={client.attributes['h']}"
            )

        self._data = None

        del self._resolver

    def save(self, file_name: Optional[str] = None) -> None:
        """
        Saves the file on to local storage.

        Args:
            file_name (str): file name
        """
        if self.type == 1:
            response = self._client.communication.session.get(self.url)
            if not file_name:
                file_name = self.name
            if response.status_code != 200:
                raise FileNotFoundError(
                    "The file was not found on pronote. The url may be badly formed."
                )
            with open(file_name, "wb") as handle:
                for block in response.iter_content(1024):
                    handle.write(block)

    @property
    def data(self) -> bytes:
        """Gets the raw file data."""
        if self._data:
            return self._data
        response = self._client.communication.session.get(self.url)
        return response.content


class LessonContent(Object):
    """
    Represents the content of a lesson. You shouldn't have to create this class manually.

    Attributes:
        title (Optional[str]): title of the lesson content
        description (Optional[str]): description of the lesson content
        category (Optional[str]): category of the lesson content
    """

    def __init__(self, client: ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)

        self._client = client

        self.title: Optional[str] = self._resolver(str, "L", strict=False)
        self.description: Optional[str] = self._resolver(
            Util.html_parse, "descriptif", "V", strict=False
        )
        self.category: Optional[str] = self._resolver(
            str, "categorie", "V", "L", strict=False
        )
        self._files: Tuple[Any, ...] = self._resolver(tuple, "ListePieceJointe", "V")

        del self._resolver

    @property
    def files(self) -> List[Attachment]:
        """Get all the attached files from the lesson"""
        return [Attachment(self._client, jsn) for jsn in self._files]


class Lesson(Object):
    """
    Represents a lesson with a given time. You shouldn't have to create this class manually.

    Attributes:
        id (str): the id of the lesson (used internally)
        subject (Optional[Subject]): the subject that the lesson is from
        teacher_name (Optional[str]): name of the teacher
        teacher_names (Optional[List[str]]): name of the teachers
        classroom (Optional[str]): name of the classroom
        classrooms (Optional[List[str]]): name of the classrooms
        canceled (bool): if the lesson is canceled
        status (Optional[str]): status of the lesson
        background_color (Optional[str]): background color of the lesson
        outing (bool): if it is a pedagogical outing
        start (datetime.datetime): starting time of the lesson
        end (datetime.datetime): end of the lesson
        memo (Optional[str]): memo of the lesson
        group_name (Optional[str]): Name of the group.
        group_names (Optional[List[str]]): Name of the groups.
        exempted (bool): Specifies if the student's presence is exempt.
        virtual_classrooms (List[str]): List of urls for virtual classrooms
        num (int): For the same lesson time, the biggest num is the one shown on pronote.
        detention (bool): is marked as detention
        test (bool): if there will be a test in the lesson
    """

    def __init__(self, client: ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)
        self._client = client
        self._content: Optional[LessonContent] = None

        self.id: str = self._resolver(str, "N")
        self.canceled: bool = self._resolver(bool, "estAnnule", default=False)
        self.status: Optional[str] = self._resolver(str, "Statut", strict=False)
        self.memo: Optional[str] = self._resolver(str, "memo", strict=False)
        self.background_color: Optional[str] = self._resolver(
            str, "CouleurFond", strict=False
        )
        self.outing: bool = self._resolver(bool, "estSortiePedagogique", default=False)
        self.start: datetime.datetime = self._resolver(
            Util.datetime_parse, "DateDuCours", "V"
        )
        self.exempted: bool = self._resolver(bool, "dispenseEleve", default=False)
        self.virtual_classrooms: List[str] = self._resolver(
            lambda l: [i["url"] for i in l], "listeVisios", "V", default=[]
        )
        self.num: int = self._resolver(int, "P", default=0)
        self.detention: bool = self._resolver(bool, "estRetenue", default=False)
        self.test: bool = self._resolver(
            bool, "cahierDeTextes", "V", "estDevoir", default=False
        )

        self.end: datetime.datetime = self._resolver(
            Util.datetime_parse, "DateDuCoursFin", "V", strict=False
        )
        if self.end is None:
            end_times = client.func_options["donneesSec"]["donnees"]["General"][
                "ListeHeuresFin"
            ]["V"]

            # get correct ending time
            # Pronote gives us the place where the hour should be in a week, when
            # we modulo that with the amount of hours in a day we can get the "place" when the
            # hour starts. Then we just add the duration (and substract 1)
            end_place = (
                json_dict["place"] % (len(end_times) - 1) + json_dict["duree"] - 1
            )

            # With the end "place" now known we can look up the ending time in func_options
            end_time = Util.place2time(end_times, end_place)
            self.end = self.start.replace(hour=end_time.hour, minute=end_time.minute)

        # get additional information about the lesson
        self.teacher_names: Optional[List[str]] = []
        self.classrooms: Optional[List[str]] = []
        self.group_names: Optional[List[str]] = []
        self.subject: Optional[Subject] = None

        if "ListeContenus" not in json_dict:
            raise ParsingError(
                "Error while parsing for lesson details",
                json_dict,
                ("ListeContenus", "V"),
            )

        for d in json_dict["ListeContenus"]["V"]:
            if "G" not in d:
                continue
            elif d["G"] == 16:
                self.subject = Subject(d)
            elif d["G"] == 3:
                self.teacher_names.append(d["L"])
            elif d["G"] == 17:
                self.classrooms.append(d["L"])
            elif d["G"] == 2:
                self.group_names.append(d["L"])

        # All values joined together to prevent breaking changes
        self.teacher_name: Optional[str] = (
            ", ".join(self.teacher_names) if self.teacher_names else None
        )
        self.classroom: Optional[str] = (
            ", ".join(self.classrooms) if self.classrooms else None
        )
        self.group_name: Optional[str] = (
            ", ".join(self.group_names) if self.group_names else None
        )

        del self._resolver

    @property
    def normal(self) -> bool:
        """Is the lesson considered normal (is not detention, or an outing)."""
        if self.detention is None and self.outing is None:
            return True
        return False

    @property
    def content(self) -> Optional[LessonContent]:
        """
        Gets content of the lesson. May be None if there is no description.

        .. note:: This property is very inefficient and will send
           a request to pronote, so don't use it often.
        """
        if self._content:
            return self._content
        week = self._client.get_week(self.start.date())
        data = {"domaine": {"_T": 8, "V": f"[{week}..{week}]"}}
        response = self._client.post("PageCahierDeTexte", 89, data)
        contents = {}
        for lesson in response["donneesSec"]["donnees"]["ListeCahierDeTextes"]["V"]:
            if lesson["cours"]["V"]["N"] == self.id and lesson["listeContenus"]["V"]:
                contents = lesson["listeContenus"]["V"][0]
                break
        if not contents:
            return None
        self._content = LessonContent(self._client, contents)
        return self._content


class Homework(Object):
    """
    Represents a homework. You shouldn't have to create this class manually.

    Attributes:
        id (str): the id of the homework (used internally)
        subject (Subject): the subject that the homework is for
        description (str): the description of the homework
        background_color (str): the background color of the homework
        done (bool): if the homework is marked done
        date (datetime.date): deadline
    """

    def __init__(self, client: ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)

        self._client = client

        self.id: str = self._resolver(str, "N")
        self.description: str = self._resolver(Util.html_parse, "descriptif", "V")
        self.done: bool = self._resolver(bool, "TAFFait")
        self.subject: Subject = self._resolver(Subject, "Matiere", "V")
        self.date: datetime.date = self._resolver(Util.date_parse, "PourLe", "V")
        self.background_color: str = self._resolver(str, "CouleurFond")
        self._files = self._resolver(tuple, "ListePieceJointe", "V")

        del self._resolver

    def set_done(self, status: bool) -> None:
        """
        Sets the status of the homework.

        Args:
            status (bool): The status to which to change
        """
        data = {"listeTAF": [{"N": self.id, "TAFFait": status}]}
        self._client.post("SaisieTAFFaitEleve", 88, data)
        self.done = status

    @property
    def files(self) -> List[Attachment]:
        """Get all the files and links attached to the homework"""
        return [Attachment(self._client, jsn) for jsn in self._files]  # type: ignore


class Information(Object):
    """
    Represents a information in a information and surveys tab.

    Attributes:
        id (str): the id of the information
        author (str): author of the information
        title (str): title of the information
        read (bool): if the message has been read
        creation_date (datetime.datetime): the date when the message was created
        start_date (datetime.datetime): the date when the message became visible
        end_date (datetime.datetime): the date on which the message will be withdrawn
        category (str): category of the information
        survey (bool): if the message is a survey
        anonymous_response (bool): if the survey response is anonymous
        attachments (List[Attachment])
        template (bool): if it is a template message
        shared_template (bool): if it is a shared template message
    """

    def __init__(self, client: ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)

        self._client = client

        self.id: str = self._resolver(str, "N")
        self.title: Optional[str] = self._resolver(str, "L", strict=False)
        self.author: str = self._resolver(str, "auteur")
        self._raw_content: list = self._resolver(list, "listeQuestions", "V")
        self.read: bool = self._resolver(bool, "lue")
        self.creation_date: datetime.datetime = self._resolver(
            Util.datetime_parse, "dateCreation", "V"
        )
        self.start_date: Optional[datetime.datetime] = self._resolver(
            Util.datetime_parse, "dateDebut", "V", strict=False
        )
        self.end_date: Optional[datetime.datetime] = self._resolver(
            Util.datetime_parse, "dateFin", "V", strict=False
        )
        self.category: str = self._resolver(str, "categorie", "V", "L")
        self.survey: bool = self._resolver(bool, "estSondage")
        self.template: bool = self._resolver(bool, "estModele", default=False)
        self.shared_template: bool = self._resolver(
            bool, "estModelePartage", default=False
        )
        self.anonymous_response: bool = self._resolver(bool, "reponseAnonyme")

        def make_attachments(questions: dict) -> List[Attachment]:
            attachments = []
            for question in questions:
                for j in question["listePiecesJointes"]["V"]:
                    attachments.append(Attachment(client, j))
            return attachments

        self.attachments: List[Attachment] = self._resolver(
            make_attachments, "listeQuestions", "V"
        )

        del self._resolver

    @property
    def content(self) -> str:
        """Content of the information"""
        return Util.html_parse(self._raw_content[0]["texte"]["V"])

    def mark_as_read(self, status: bool) -> None:
        """Mark this information as read"""
        data = {
            "listeActualites": [
                {
                    "N": self.id,
                    "validationDirecte": True,
                    "genrePublic": 4,
                    "public": {
                        "N": self._client.info.id,
                        "G": 4,
                    },
                    "lue": status,
                }
            ],
            "saisieActualite": False,
        }
        self._client.post("SaisieActualites", 8, data)
        self.read = status


class Recipient(Object):
    """
    Represents a recipient to create a discussion

    Attributes:
        id (str): the id of the recipient (used internally)
        name (str): name of the recipient
        type (str): teacher or staff
        email (Optional[str]): email of the recipient
        functions (List[str]): all function or subject of the recipient
        with_discussion (bool): can be contacted by message
    """

    def __init__(self, client: ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)
        self._client = client
        self._type: int = self._resolver(int, "G")

        self.id: str = self._resolver(str, "N")
        self.name: str = self._resolver(str, "L")
        self.type: str = "teacher" if self._type == 3 else "staff"
        self.email: Optional[str] = self._resolver(str, "email", strict=False)
        self.functions: List[str] = []

        if self.type == "teacher":
            self.functions = self._resolver(
                lambda x: [r.get("L") for r in x], "listeRessources", "V"
            )
        else:
            self.functions = self._resolver(
                lambda f: [f], "fonction", "V", "L", default=[]
            )

        self.with_discussion: bool = self._resolver(
            bool, "avecDiscussion", default=False
        )

        del self._resolver


class Message(Object):
    """
    Represents a message in a discussion.

    Attributes:
        id (str): the id of the message (used internally)
        author (Optional[str]): author of the message, if ``None``, then we are the author
        seen (bool): if the message was seen
        created (datetime.datetime): when the message was created
        content (str): content of the messages
        replying_to (Optional[Message]): the message that this is replying to, if None,
            it is the first message in a discussion
    """

    def __init__(self, client: ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)
        self._client = client
        self._possession = self._resolver(str, "possessionMessage", "V", "N")

        self.id: str = self._resolver(str, "N")
        self.content: str = ""
        self.author: Optional[str] = (
            None
            if self._resolver(bool, "emetteur", default=False)
            else self._resolver(str, "public_gauche")
        )
        self.seen: bool = self._resolver(bool, "lu", default=False)
        self.created: datetime.datetime = self._resolver(
            Util.datetime_parse, "date", "V"
        )

        # TODO: DEPRECATED
        self.date = self.created

        self.replying_to: Optional[Message] = None

        if json_dict.get("estHTML", False):
            self.content = self._resolver(Util.html_parse, "contenu", "V")
        else:
            self.content = self._resolver(str, "contenu")

        del self._resolver

    def recipients(self) -> List[str]:
        """
        Recipients of this message
        """

        resp = self._client.post(
            "SaisiePublicMessage", 131, {"message": {"N": self.id}}
        )

        return [r["L"] for r in resp["donneesSec"]["donnees"]["listeDest"]["V"]]

    def reply(self, message: str) -> None:
        """
        Reply to this message

        Args:
            message (str)

        Raises:
            DiscussionClosed: when the parent discussion is closed and we cannot reply
        """

        resp = self._client.post(
            "ListeMessages",
            131,
            {
                "listePossessionsMessages": [{"N": self._possession}],
                "message": {"N": self.id},
            },
        )

        if len(resp["donneesSec"]["donnees"].get("listeBoutons", {"V": []})["V"]) == 0:
            raise DiscussionClosed("Cannot reply to discussion")

        msg = resp["donneesSec"]["donnees"]["messagePourReponse"]["V"]
        button = resp["donneesSec"]["donnees"]["listeBoutons"]["V"][0]

        self._client.post(
            "SaisieMessage",
            131,
            {
                "messagePourReponse": msg,
                "contenu": message,
                "listeFichiers": [],
                "bouton": button,  # pronote wants the specific button we pressed
            },
        )


class Discussion(Object):
    """
    Represents a discussion.

    A PRONOTE discussion is a channel that, in the web UI, has threads. The internal
    structure, however, looks more linear, with messages replying to other messages.

    You can get messages sent in a discussion using :attr:`.messages`. The messages will be
    in ascending chronological order (ending with the newest). Each message also has a
    :attr:`Message.replying_to` attribute specifying what message it is replying to. In most cases
    this will be just the previous message.

    For example, to get a chat like printout of a discussion:

    .. code-block:: python

        discussion: Discussion = ...

        print(discussion.subject or "(no subject)")
        print("-------------------")

        last_msg = None

        for message in discussion.messages:
            if message.replying_to != last_msg and message.replying_to:
                print(f"  (replying to {message.replying_to.author or 'Me'}: {message.replying_to.content[:20]})")

            print(message.author or "Me", ">", message.content)
            print()

            last_msg = message

    Attributes:
        id (str): the id of the discussion (used internally)
        subject (str): the subject of the discussion, can be an empty string
        creator (Optional[str]): person that created the discussion, if ``None``, then we are the creator
        unread (int): number of unread messages
        closed (bool): if the discussion is closed
        labels (List[str]): labels on the discussion, usually can be ``["Trash"]``, or ``["Drafts"]``
        replyable (bool): because pronotepy does not currently support replying
            to discussions that are inside other discussions, this boolean signifies
            if pronotepy is able to reply

            .. deprecated:: 2.10

               Always ``True``

        close (bool):
            if the discussion is closed

            .. deprecated:: 2.10

               Use :attr:`.closed` instead
    """

    def __init__(self, client: Client, json_dict: dict, labels: dict) -> None:
        super().__init__(json_dict)
        self._client = client
        self._possessions: list = self._resolver(noop, "listePossessionsMessages", "V")
        self._date_cache: Optional[datetime.datetime] = None

        self.replyable: bool = True
        self.subject: str = self._resolver(str, "objet")
        self.creator: Optional[str] = self._resolver(str, "initiateur", strict=False)

        self._participants_message_id = self._resolver(
            str, "messagePourParticipants", "V", "N"
        )

        self.unread: int = self._resolver(int, "nbNonLus", default=0)
        self.closed: bool = self._resolver(bool, "ferme", default=False)

        self.close: bool = self.closed

        labels_str = {4: "Drafts", 5: "Trash"}
        self.labels: List[str] = self._resolver(
            lambda l: [labels_str[labels[i["N"]]] for i in l],
            "listeEtiquettes",
            "V",
            default=[],
        )

        del self._resolver

    def participants(self) -> List[str]:
        """
        Get participants in the discussion. A participant does not have to send
        a message to the discussion to be included.

        The names may be in the format ``NAME - KID'S NAME ...``.
        Ex: ``M. PARENT F. - PARENT Fanny (3A) PARENT Manon (6D)``
        """
        resp = self._client.post(
            "SaisiePublicMessage",
            131,
            {
                "estDestinatairesReponse": False,
                "estPublicParticipant": True,
                "message": {"N": self._participants_message_id},
            },
        )
        # the names are often in the format "NAME - KID'S NAME"
        return [i["L"] for i in resp["donneesSec"]["donnees"]["listeDest"]["V"]]

    @property
    def messages(self) -> List[Message]:
        """
        Messages linked to the discussion

        .. warning:: Makes a request everytime it is accessed

        ..
            TODO: should be a method instead
        """
        resp = self._client.post(
            "ListeMessages",
            131,
            {"listePossessionsMessages": self._possessions},
        )

        messages = {}

        for message_json in resp["donneesSec"]["donnees"]["listeMessages"]["V"]:
            msg = Message(self._client, message_json)
            messages[msg.id] = msg

        for message_json in resp["donneesSec"]["donnees"]["listeMessages"]["V"]:
            messages[message_json["N"]].replying_to = messages.get(
                message_json["messageSource"]["V"]["N"]
            )

        return list(sorted(messages.values(), key=lambda x: x.created))

    @property
    def date(self) -> datetime.datetime:
        """
        Date when the discussion was opened. Alias for ``Discussion.messages[0].date``.
        """
        if not self._date_cache:
            msgs = self.messages
            self._date_cache = msgs[0].date
        return self._date_cache

    def mark_as(self, read: bool) -> None:
        """
        Mark as read/unread the discussion

        Args:
            read (bool): read/unread
        """
        self._client.post(
            "SaisieMessage",
            131,
            {
                "commande": "pourLu",
                "lu": read,
                "listePossessionsMessages": self._possessions,
            },
        )

    def reply(self, message: str) -> None:
        """
        Reply to a discussion, this usually means replying to the last message

        Args:
            message (str)
        """

        if self.closed:
            raise DiscussionClosed("Cannot reply to discussion")

        # get the message we should respond to
        resp = self._client.post(
            "ListeMessages",
            131,
            {"listePossessionsMessages": self._possessions},
        )

        msg = resp["donneesSec"]["donnees"]["messagePourReponse"]["V"]
        button = resp["donneesSec"]["donnees"]["listeBoutons"]["V"][0]

        self._client.post(
            "SaisieMessage",
            131,
            {
                "messagePourReponse": msg,
                "contenu": message,
                "listeFichiers": [],
                "bouton": button,  # pronote wants the specific button we pressed
            },
        )

    def delete(self) -> None:
        """
        Delete the discussion
        """
        self._client.post(
            "SaisieMessage",
            131,
            {
                "commande": "corbeille",
                "listePossessionsMessages": self._possessions,
            },
        )


class ClientInfo(Slots):
    """
    Contains info for a resource (a client).

    Attributes:
        id (str): id of the client (used internally)
        raw_resource (dict): Raw json defining the resource
    """

    def __init__(self, client: ClientBase, json_: dict) -> None:
        self.id: str = json_["N"]
        self.raw_resource: dict = json_
        self._client = client
        self.__cache: Optional[dict] = None

    @property
    def name(self) -> str:
        """
        Name of the client
        """
        return self.raw_resource["L"]

    @property
    def profile_picture(self) -> Optional[Attachment]:
        """
        Profile picture of the client
        """
        if self.raw_resource.get("avecPhoto"):
            return Attachment(
                self._client, {"L": "photo.jpg", "N": self.raw_resource["N"], "G": 1}
            )
        else:
            return None

    @property
    def delegue(self) -> List[str]:
        """
        list of classes of which the user is a delegue of
        """
        if self.raw_resource.get("estDelegue"):
            return [
                class_["L"] for class_ in self.raw_resource["listeClassesDelegue"]["V"]
            ]
        else:
            return []

    @property
    def class_name(self) -> str:
        """
        name of the student's class
        """
        return self.raw_resource.get("classeDEleve", {}).get("L", "")

    @property
    def establishment(self) -> str:
        """
        name of the student's establishment
        """
        return self.raw_resource.get("Etablissement", {"V": {"L": ""}})["V"]["L"]

    def _cache(self) -> dict:
        if self.__cache is None:
            # this does not have all the protection _ClientBase.post provides,
            # but we need to manually add the resource id
            self.__cache = self._client.communication.post(
                "PageInfosPerso",
                {"_Signature_": {"onglet": 49, "ressource": {"N": self.id, "G": 4}}},
            )["donneesSec"]["donnees"]["Informations"]

        return self.__cache

    @property
    def address(self) -> tuple[str, str, str, str, str, str, str, str]:
        """
        Address of the client

        Returns:
            A tuple of 8 elements:
                - 4 lines of address info
                - postal code
                - city
                - province
                - country
        """
        c = self._cache()
        return (
            c["adresse1"],
            c["adresse2"],
            c["adresse3"],
            c["adresse4"],
            c["codePostal"],
            c["ville"],
            c["province"],
            c["pays"],
        )

    @property
    def email(self) -> str:
        """
        Email of the client
        """
        return self._cache()["eMail"]

    @property
    def phone(self) -> str:
        """
        Phone of the client

        Returns:
            str: Phone in the format +[country-code][phone-number]
        """
        c = self._cache()
        return "+" + c["indicatifTel"] + c["telephonePortable"]

    @property
    def ine_number(self) -> str:
        """
        INE number of the client
        """
        return self._cache()["numeroINE"]


class Acquisition(Object):
    """
    Contains acquisition info for an evaluation.

    Attributes:
        order (int): Telling the order in which the acquisition is. The list of acquisitions is already sorted by this.
        level (str): the level achieved for this acquisition
        id (int): id, used internally
        abbreviation (str): abbreviation for the level achieved
        coefficient (int): coefficient
        domain (str): domain in which the acquisition is
        domain_id (str)
        name (str): name (description) of the acquisition
        name_id (str)
        pillar (str)
        pillar_id (str)
        pillar_prefix (str)
    """

    def __init__(self, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.id: str = self._resolver(str, "N")
        self.level: str = self._resolver(str, "L")
        self.abbreviation: str = self._resolver(str, "abbreviation")
        self.coefficient: int = self._resolver(int, "coefficient")
        self.domain: str = self._resolver(str, "domaine", "V", "L")
        self.domain_id: str = self._resolver(str, "domaine", "V", "N")
        self.name: Optional[str] = self._resolver(str, "item", "V", "L", strict=False)
        self.name_id: Optional[str] = self._resolver(
            str, "item", "V", "N", strict=False
        )
        self.order: int = self._resolver(int, "ordre")
        self.pillar: str = self._resolver(str, "pilier", "V", "L")
        self.pillar_id: str = self._resolver(str, "pilier", "V", "N")
        self.pillar_prefix: str = self._resolver(str, "pilier", "V", "strPrefixes")

        del self._resolver


class Evaluation(Object):
    """
    Data class for an evaluation.

    Attributes:
        name (str)
        id (str)
        domain (Optional[str])
        teacher (str): the teacher who issued the evaluation
        coefficient (int)
        description (str)
        subject (Subject)
        paliers (List[str])
        acquisitions (List[Acquisition])
        date (datetime.date)
    """

    def __init__(self, json_dict: dict) -> None:
        super().__init__(json_dict)
        self.name: str = self._resolver(str, "L")
        self.id: str = self._resolver(str, "N")
        self.domain: Optional[str] = self._resolver(
            str, "domaine", "V", "L", strict=False
        )
        self.teacher: str = self._resolver(str, "individu", "V", "L")
        self.coefficient: int = self._resolver(int, "coefficient")
        self.description: str = self._resolver(str, "descriptif")
        self.subject: Subject = self._resolver(Subject, "matiere", "V")
        self.paliers: List[str] = self._resolver(
            lambda x: [_get_l(y) for y in x], "listePaliers", "V"
        )
        self.acquisitions: List[Acquisition] = self._resolver(
            lambda x: sorted([Acquisition(y) for y in x], key=lambda z: z.order),
            "listeNiveauxDAcquisitions",
            "V",
        )
        self.date: datetime.date = self._resolver(Util.date_parse, "date", "V")

        del self._resolver


class Identity(Object):
    """
    Represents an Identity of a person

    Attributes:
        postal_code (str)
        date_of_birth (datetime.date)
        email (Optional[str])
        last_name (str)
        country (str)
        mobile_number (Optional[str])
        landline_number (Optional[str])
        other_phone_number (Optional[str])
        city (str)
        place_of_birth (Optional[str])
        first_names (List[str])
        address (List[str])
        formatted_address (str): concatenated address information into a single string
    """

    def __init__(self, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.postal_code: str = self._resolver(str, "CP")
        self.date_of_birth: Optional[datetime.date] = self._resolver(
            Util.date_parse, "dateNaiss", strict=False
        )
        self.email: Optional[str] = self._resolver(str, "email", strict=False)
        self.last_name: str = self._resolver(str, "nom")
        self.country: str = self._resolver(str, "pays")
        self.mobile_number: Optional[str] = self._resolver(str, "telPort", strict=False)
        self.landline_number: Optional[str] = self._resolver(
            str, "telFixe", strict=False
        )
        self.other_phone_number: Optional[str] = self._resolver(
            str, "telAutre", strict=False
        )
        self.city: str = self._resolver(str, "ville")
        self.place_of_birth: Optional[str] = self._resolver(
            str, "villeNaiss", strict=False
        )

        self.address: List[str] = []
        i = 1
        while True:
            option = json_dict.get("adresse" + str(i))
            if not option:
                break
            self.address.append(option)
            i += 1
        self.formatted_address: str = ",".join(
            [*self.address, self.postal_code, self.city, self.country]
        )
        self.first_names: List[str] = [
            json_dict.get("prenom", ""),
            json_dict.get("prenom2", ""),
            json_dict.get("prenom3", ""),
        ]

        del self._resolver


class Guardian(Object):
    """
    Represents a guardian of a student.

    Attributes:
        identity (Identity)
        accepteInfosProf (bool)
        authorized_email (bool)
        authorized_pick_up_kid (bool)
        urgency_contact (bool)
        preferred_responsible_contact (bool)
        accomodates_kid (bool)
        relatives_link (str)
        responsibility_level (str)
        financially_responsible (bool)
        full_name (str)
        is_legal (bool)
    """

    def __init__(self, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.accepteInfosProf: bool = self._resolver(bool, "accepteInfosProf")
        self.authorized_email: bool = self._resolver(bool, "autoriseEmail")
        self.authorized_pick_up_kid: bool = self._resolver(
            bool, "autoriseRecupererEnfant"
        )
        self.urgency_contact: bool = self._resolver(bool, "contactUrgence")
        self.preferred_responsible_contact: bool = self._resolver(
            bool, "estResponsablePreferentiel"
        )
        self.accomodates_kid: bool = self._resolver(bool, "hebergeEnfant")
        self.relatives_link: str = self._resolver(str, "lienParente")
        self.responsibility_level: str = self._resolver(str, "niveauResponsabilite")
        self.financially_responsible: bool = self._resolver(
            bool, "responsableFinancier"
        )
        self.full_name: str = self._resolver(str, "nom")

        self.identity = Identity(json_dict)
        self.is_legal = self.responsibility_level == "LEGAL"

        del self._resolver


class Student(Object):
    """
    Represents a student

    Attributes:
        full_name (str)
        id (str)
        enrollment_date (datetime.date)
        date_of_birth (datetime.date)
        projects (List[str])
        last_name (str)
        first_names (str)
        sex (str)
        options (List[str]): language options
    """

    def __init__(self, client: ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.full_name: str = self._resolver(str, "L")
        self.id: str = self._resolver(str, "N")
        self.enrollment_date: datetime.date = self._resolver(
            Util.date_parse, "entree", "V"
        )
        self.date_of_birth: datetime.date = self._resolver(Util.date_parse, "neLe", "V")
        self.projects: List[str] = self._resolver(
            lambda p: [
                f"{x.get('typeAmenagement', '')} ({x.get('handicap', '')})" for x in p
            ],
            "listeProjets",
            "V",
        )
        self.last_name: str = self._resolver(str, "nom")
        self.first_names: str = self._resolver(str, "prenoms")
        self.sex: str = self._resolver(str, "sexe")

        self._client = client
        self._cache: Optional[dict] = None

        self.options = []
        i = 1
        while True:
            option = json_dict.get("option" + str(i))
            if not option:
                break
            self.options.append(option)
            i += 1

        del self._resolver

    @property
    def identity(self) -> Identity:
        """
        Identity of this student
        """
        if self._cache is None:
            self._cache = self._client.post(
                "FicheEleve",
                105,
                {"Eleve": {"N": self.id}, "AvecEleve": True, "AvecResponsables": True},
            )
        return Identity(self._cache["donneesSec"]["donnees"]["Identite"])

    @property
    def guardians(self) -> List[Guardian]:
        """
        List of responsible persons (parents).
        """
        if self._cache is None:
            self._cache = self._client.post(
                "FicheEleve",
                105,
                {"Eleve": {"N": self.id}, "AvecEleve": True, "AvecResponsables": True},
            )
        return [
            Guardian(j)
            for j in self._cache["donneesSec"]["donnees"]["Responsables"]["V"]
        ]


class StudentClass(Object):
    """
    Represents a class of students

    Attributes:
        name (str)
        id (str)
        responsible (bool): is the teacher responsible for the class
        grade (str)
    """

    def __init__(self, client: ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.name: str = self._resolver(str, "L")
        self.id: str = self._resolver(str, "N")
        self.responsible: bool = self._resolver(bool, "estResponsable")
        self.grade: str = self._resolver(str, "niveau", "V", "L", default="")

        self._client = client

        del self._resolver

    def students(self, period: Optional[Period] = None) -> List[Student]:
        """
        Get students in the class

        Args:
            period (Optional[Period]): select a particular period (client.periods[0] by default)
        """
        period = period or self._client.periods[0]
        r = self._client.post(
            "ListeRessources",
            105,
            {"classe": {"N": self.id, "G": 1}, "periode": {"N": period.id, "G": 1}},
        )
        return [
            Student(self._client, j)
            for j in r["donneesSec"]["donnees"]["listeRessources"]["V"]
        ]


class Menu(Object):
    """
    Represents the menu of a meal

    Attributes:
        id (str)
        self.name (Optional[str])
        date (datetime.date): the date of the menu
        is_lunch (bool): the menu is a lunch menu
        is_dinner (bool): the menu is a dinner menu
        first_meal (Optional[List[Food]]): food list of first meal
        main_meal (Optional[List[Food]]): food list of main meal
        side_meal (Optional[List[Food]]): food list of side meal
        other_meal (Optional[List[Food]]): food list of other meal
        cheese (Optional[List[Food]]): food list of cheese
        dessert (Optional[List[Food]]): food list of dessert
    """

    class Food(Object):
        """
        Represents food of a menu

        Attributes:
            id (str)
            name (str)
            labels (List[FoodLabel])
        """

        class FoodLabel(Object):
            """
            Represents the label of a food

            Attributes:
                id (str)
                name (str)
                color (Optional[str])
            """

            def __init__(self, client: ClientBase, json_dict: dict) -> None:
                super().__init__(json_dict)

                self.id: str = self._resolver(str, "N")
                self.name: str = self._resolver(str, "L")
                self.color: Optional[str] = self._resolver(str, "couleur", strict=False)

                self._client = client

                del self._resolver

        def __init__(self, client: ClientBase, json_dict: dict) -> None:
            super().__init__(json_dict)

            self.id: str = self._resolver(str, "N")
            self.name: str = self._resolver(str, "L")
            self.labels: List[Menu.Food.FoodLabel] = self._resolver(
                lambda labels: [self.FoodLabel(client, label) for label in labels],
                "listeLabelsAlimentaires",
                "V",
            )

            self._client = client

            del self._resolver

    def __init__(self, client: ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.id: str = self._resolver(str, "N")
        self.name: Optional[str] = self._resolver(str, "L", strict=False)
        self.date: datetime.date = self._resolver(Util.date_parse, "Date", "V")

        self.is_lunch: bool = self._resolver(int, "G") == 0
        self.is_dinner: bool = self._resolver(int, "G") == 1

        def init_food(d: dict) -> List[Menu.Food]:
            return [self.Food(client, x) for x in d["ListeAliments"]["V"]]

        d_dict = {str(meal["G"]): meal for meal in json_dict["ListePlats"]["V"]}
        super().__init__(d_dict)

        self.first_meal: Optional[List[Menu.Food]] = self._resolver(
            init_food, "0", strict=False
        )
        self.main_meal: Optional[List[Menu.Food]] = self._resolver(
            init_food, "1", strict=False
        )
        self.side_meal: Optional[List[Menu.Food]] = self._resolver(
            init_food, "2", strict=False
        )
        self.other_meal: Optional[List[Menu.Food]] = self._resolver(
            init_food, "3", strict=False
        )
        self.cheese: Optional[List[Menu.Food]] = self._resolver(
            init_food, "5", strict=False
        )
        self.dessert: Optional[List[Menu.Food]] = self._resolver(
            init_food, "4", strict=False
        )

        self._client = client

        del self._resolver


class Punishment(Object):
    """
    Represents a punishment.

    Attributes:
        id (str)
        given (Union[datetime.datetime, datetime.date]): Date and time when the punishment was given
        exclusion (bool): If the punishment is an exclusion from class
        during_lesson (bool): If the punishment was given during a lesson.
            `self.during_lesson is True => self.given is datetime.datetime`
        homework (str): Text description of the homework that was given as the punishment
        homework_documents (List[Attachment]): Attached documents for homework
        circumstances (str)
        circumstance_documents (List[Attachment])
        nature (str): Text description of the nature of the punishment (ex. "Retenue")
        reasons (List[str]): Text descriptions of the reasons for the punishment
        giver (str): Name of the person that gave the punishment
        schedule (List[ScheduledPunishment]): List of scheduled date-times with durations
        schedulable (bool)
        duration (Optional[datetime.timedelta])
    """

    class ScheduledPunishment(Object):
        """
        Represents a sheduled punishment.

        Attributes:
            id (str)
            start (Union[datetime.datetime, datetime.date])
            duration (Optional[datetime.timedelta])
        """

        def __init__(self, client: ClientBase, json_dict: dict) -> None:
            super().__init__(json_dict)
            self.id: str = self._resolver(str, "N")

            # construct a full datetime from "date" and "placeExecution" fields
            date = self._resolver(Util.date_parse, "date", "V")
            place = self._resolver(int, "placeExecution", strict=False)

            self.start: Union[datetime.datetime, datetime.date]
            if place is not None:
                liste_heures = client.func_options["donneesSec"]["donnees"]["General"][
                    "ListeHeures"
                ]["V"]
                try:
                    self.start = datetime.datetime.combine(
                        date, Util.place2time(liste_heures, place)
                    )
                except ValueError as e:
                    raise DataError(str(e))
            else:
                self.start = date

            self.duration: Optional[datetime.timedelta] = self._resolver(
                lambda v: datetime.timedelta(minutes=int(v)), "duree", strict=False
            )

            del self._resolver

    def __init__(self, client: ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)
        self.id: str = self._resolver(str, "N")

        date = self._resolver(Util.date_parse, "dateDemande", "V")
        self.during_lesson: bool = self._resolver(lambda v: not bool(v), "horsCours")

        # construct a full datetime from "dateDemande" and "placeDemande" fields
        self.given: Union[datetime.datetime, datetime.date]
        if self.during_lesson:
            time_place = self._resolver(int, "placeDemande")
            liste_heures = client.func_options["donneesSec"]["donnees"]["General"][
                "ListeHeures"
            ]["V"]
            try:
                self.given = datetime.datetime.combine(
                    date, Util.place2time(liste_heures, time_place)
                )
            except ValueError as e:
                raise DataError(str(e))
        else:
            self.given = date

        self.exclusion: bool = self._resolver(bool, "estUneExclusion")

        self.homework: str = self._resolver(str, "travailAFaire")
        self.homework_documents: List[Attachment] = self._resolver(
            lambda x: [Attachment(client, a) for a in x], "documentsTAF", "V"
        )

        self.circumstances: str = self._resolver(str, "circonstances")
        self.circumstance_documents: List[Attachment] = self._resolver(
            lambda x: [Attachment(client, a) for a in x], "documentsCirconstances", "V"
        )

        # TODO: change to an enum (out of scope for this comment: change this kind of string to enums everywhere)
        self.nature: str = self._resolver(str, "nature", "V", "L")
        self.requires_parent: Optional[str] = self._resolver(
            str, "nature", "V", "estAvecARParent", strict=False
        )

        self.reasons: List[str] = self._resolver(
            lambda x: [i["L"] for i in x], "listeMotifs", "V"
        )
        self.giver: str = self._resolver(str, "demandeur", "V", "L")

        self.schedulable: bool = self._resolver(bool, "estProgrammable")

        self.schedule: List[Punishment.ScheduledPunishment] = []
        if self.schedulable:
            self.schedule = self._resolver(
                lambda x: [Punishment.ScheduledPunishment(client, i) for i in x],
                "programmation",
                "V",
            )

        self.duration: Optional[datetime.timedelta] = self._resolver(
            lambda v: datetime.timedelta(minutes=int(v)), "duree", strict=False
        )


class TeachingStaff(Object):
    """
    Represents a teaching staff member. You shouldn't have to create this class manually.

    Attributes:
        id (str): id of the teaching staff (used internally)
        name (str): name of the teaching staff
        type (str): teacher or staff
        num (int): the teaching staff number used for sorting
        subjects (List[TeachingSubject]): list of subject the teacher teaches
    """

    class TeachingSubject(Object):
        """
        Represents a subject taught. You shouldn't have to create this class manually.

        Attributes:
            id (str): id of the subject (used internally)
            name (str): name of the subject
            duration (Optional[datetime.timedelta]): the duration of the subject per week
            parent_subject_name (Optional[str]): name of the parent subject
            parent_subject_id (Optional[str]): id of the parent subject (used internally)
        """

        def __init__(self, json_dict: dict) -> None:
            super().__init__(json_dict)

            self.id: str = self._resolver(str, "N")
            self.name: str = self._resolver(str, "L")
            self._duration: str = self._resolver(str, "volumeHoraire")
            self.parent_subject_name: Optional[str] = self._resolver(
                str, "servicePere", "V", "L", strict=False
            )
            self.parent_subject_id: Optional[str] = self._resolver(
                str, "servicePere", "V", "N", strict=False
            )

            if "h" in self._duration:  # duration can be an empty string
                self.duration: Optional[datetime.timedelta] = datetime.timedelta(
                    hours=int(self._duration.split("h")[0]),
                    minutes=int(self._duration.split("h")[1]),
                )
            else:
                self.duration = None

                del self._resolver

    def __init__(self, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.id: str = self._resolver(str, "N")
        self.name: str = self._resolver(str, "L")
        self.num: int = self._resolver(int, "P")
        self._type: int = self._resolver(int, "G")
        self.type: str = "teacher" if self._type == 3 else "staff"
        self.subjects: List[TeachingStaff.TeachingSubject] = self._resolver(
            lambda x: [TeachingStaff.TeachingSubject(i) for i in x], "matieres", "V"
        )

        del self._resolver
