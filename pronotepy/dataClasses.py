from __future__ import annotations

import datetime
import json
import logging
import re
from html import unescape
from typing import Union, List, Callable, Any, TypeVar, Optional, Tuple, Set, Iterable, TYPE_CHECKING
from urllib.parse import quote

from Crypto.Util import Padding

if TYPE_CHECKING:
    from .clients import _ClientBase
from .exceptions import ParsingError, DateParsingError

log = logging.getLogger(__name__)


def _get_l(d: dict) -> str: return d['L']


class MissingType: pass


class Util:
    """Utilities for the API wrapper"""
    grade_translate = ['Absent', 'Dispense', 'NonNote', 'Inapte', 'NonRendu', 'AbsentZero', 'NonRenduZero',
                       'Felicitations']

    @classmethod
    def get(cls, iterable: Iterable, **kwargs: Any) -> list:
        """Gets items from the list with the attributes specified.

        Parameters
        ----------
        iterable : list
            The iterable to loop over
        """
        output = []
        for i in iterable:
            for attr in kwargs:
                if not hasattr(i, attr) or getattr(i, attr) != kwargs[attr]:
                    i = False
                    break
            if i is not False:
                output.append(i)
        return output

    @classmethod
    def grade_parse(cls, string: str) -> str:
        if '|' in string:
            return cls.grade_translate[int(string[1]) - 1]
        else:
            return string

    @staticmethod
    def date_parse(formatted_date: str) -> datetime.date:
        """convert date to a datetime.date object"""
        if re.match(r"\d{2}/\d{2}/\d{4}$", formatted_date):
            return datetime.datetime.strptime(formatted_date, '%d/%m/%Y').date()
        elif re.match(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$", formatted_date):
            return datetime.datetime.strptime(formatted_date, '%d/%m/%Y %H:%M:%S').date()
        elif re.match(r"\d{2}/\d{2}/\d{2} \d{2}h\d{2}$", formatted_date):
            return datetime.datetime.strptime(formatted_date, '%d/%m/%y %Hh%M').date()
        else:
            raise DateParsingError("Could not parse date", formatted_date)

    @staticmethod
    def datetime_parse(formatted_date: str) -> datetime.datetime:
        """convert date to a datetime.datetime object"""
        if re.match(r"\d{2}/\d{2}/\d{4}$", formatted_date):
            return datetime.datetime.strptime(formatted_date, '%d/%m/%Y')
        elif re.match(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$", formatted_date):
            return datetime.datetime.strptime(formatted_date, '%d/%m/%Y %H:%M:%S')
        elif re.match(r"\d{2}/\d{2}/\d{2} \d{2}h\d{2}$", formatted_date):
            return datetime.datetime.strptime(formatted_date, '%d/%m/%y %Hh%M')
        else:
            raise DateParsingError("Could not parse date", formatted_date)

    @staticmethod
    def html_parse(html_text: str) -> str:
        """remove tags from html text"""
        return unescape(re.sub(re.compile('<.*?>'), '', html_text))


class Object:
    """
    Base object for all pronotepy data classes.
    """

    class _Resolver:
        """
        Resolves an arbitrary value from a json dictionary.
        """

        R = TypeVar("R")
        _missing: MissingType = MissingType()

        def __init__(self, json_dict: dict):
            self.json_dict = json_dict

        def __call__(self, converter: Callable[[Any], R], *path: str, default: Union[MissingType, R] = _missing,
                     strict: bool = True) -> R:
            """

            Parameters
            ----------
            converter : Callable[[Any], R]
                the final value will be passed to this converter, it can be any callable with a single argument
            path : str
                arguments describing the path through the dictionary to the value
            default : Union[MissingType, R]
                default value if the actual one cannot be found, works with strict as False
            strict : bool
                if True, the resolver will return None when it can't find the correct value

            Returns
            -------
            the resolved value
            """
            json_value: Any = self.json_dict
            try:
                for p in path:  # walk through the json dict according to the path
                    json_value = json_value[p]
            except KeyError:
                # we have failed to get the correct value, try to return a default
                if default is not self._missing:
                    log.debug(
                        f"Could not get value for (path: {','.join(path)}), setting to default.")
                    json_value = default
                else:
                    if strict:
                        # in strict mode we do not want to give unpredictable output
                        raise ParsingError("Error while parsing received json", self.json_dict, path)

                    json_value = None
            else:
                try:
                    json_value = converter(json_value)
                except Exception as e:
                    raise ParsingError(f"Error while converting value: {e}", self.json_dict, path)

            return json_value

    def __init__(self, json_dict: dict) -> None:
        self._resolver: Object._Resolver = self._Resolver(json_dict)


class Subject(Object):
    """
    Represents a subject. You shouldn't have to create this class manually.

    Attributes
    ----------
    id : str
        the id of the subject (used internally)
    name : str
        name of the subject
    groups : bool
        if the subject is in groups
    """

    __slots__ = ['id', 'name', 'groups']

    def __init__(self, parsed_json: dict) -> None:
        super().__init__(parsed_json)

        self.id: str = self._resolver(str, "N")
        self.name: str = self._resolver(str, "L")
        self.groups: bool = self._resolver(bool, "estServiceGroupe", default=False)

        del self._resolver


class Absence(Object):
    """
    Represents an absence with a given period. You shouldn't have to create this class manually.

    Attributes
    ----------
    id : str
        the id of the absence (used internally)
    from_date : datetime.datetime
        starting time of the absence
    to_date : datetime.datetime
        end of the absence
    justified : bool
        is the absence justified
    hours : str
        the number of hours missed
    days : int
        the number of days missed
    reasons: List[str]
        The reason(s) for the absence
    """

    __slots__ = ['id', 'from_date', 'to_date', 'justified',
                 'hours' 'days', 'reasons']

    def __init__(self, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.id: str = self._resolver(str, "N")
        self.from_date: datetime.datetime = self._resolver(Util.datetime_parse, "dateDebut", "V")
        self.to_date: datetime.datetime = self._resolver(Util.datetime_parse, "dateFin", "V")
        self.justified: bool = self._resolver(bool, "justifie", default=False)
        self.hours: Optional[str] = self._resolver(str, "NbrHeures", strict=False)
        self.days: int = self._resolver(int, "NbrJours", default=0)
        self.reasons: List[str] = self._resolver(lambda l: [i["L"] for i in l], "listeMotifs", "V", default=[])

        del self._resolver


class Period(Object):
    """
    Represents a period of the school year. You shouldn't have to create this class manually.

    Attributes
    ----------
    id : str
        the id of the period (used internally)
    name : str
        name of the period
    start : datetime.datetime
        date on which the period starts
    end : datetime.datetime
        date on which the period ends
    """

    __slots__ = ['_client', 'id', 'name', 'start', 'end']
    instances: Set[Any] = set()

    def __init__(self, client: _ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.__class__.instances.add(self)
        self._client = client

        self.id: str = self._resolver(str, "N")
        self.name: str = self._resolver(str, "L")
        self.start: datetime.datetime = self._resolver(Util.datetime_parse, "dateDebut", "V")
        self.end: datetime.datetime = self._resolver(Util.datetime_parse, "dateFin", "V")

        del self._resolver

    @property
    def grades(self) -> List["Grade"]:
        """Get grades from the period."""
        json_data = {'Periode': {'N': self.id, 'L': self.name}}
        response = self._client.post('DernieresNotes', 198, json_data)
        log.debug(response)
        grades = response['donneesSec']['donnees']['listeDevoirs']['V']
        return [Grade(g) for g in grades]

    @property
    def averages(self) -> List["Average"]:
        """Get averages from the period."""

        json_data = {'Periode': {'N': self.id, 'L': self.name}}
        response = self._client.post('DernieresNotes', 198, json_data)
        crs = response['donneesSec']['donnees']['listeServices']['V']
        return [Average(c) for c in crs]

    @property
    def overall_average(self) -> float:
        """Get overall average from the period. If the period average is not provided by pronote, then it's calculated.
        Calculation may not be the same as the actual average. (max difference 0.01)"""
        json_data = {'Periode': {'N': self.id, 'L': self.name}}
        response = self._client.post('DernieresNotes', 198, json_data)
        average = response['donneesSec']['donnees'].get('moyGenerale')
        if average:
            average = average['V']
        elif response['donneesSec']['donnees']['listeServices']['V']:
            a: float = 0
            total = 0
            services = response['donneesSec']['donnees']['listeServices']['V']
            for s in services:
                avrg = s['moyEleve']['V'].replace(',', '.')
                try:
                    flt = float(avrg)
                except ValueError:
                    flt = False
                if flt:
                    a += flt
                    total += 1
            if total:
                average = round(a / total, 2)
            else:
                average = -1
        else:
            average = -1
        return average

    @property
    def evaluations(self) -> List["Evaluation"]:
        json_data = {'periode': {'N': self.id, 'L': self.name, 'G': 2}}
        response = self._client.post('DernieresEvaluations', 201, json_data)
        evaluations = response['donneesSec']['donnees']['listeEvaluations']['V']
        return [Evaluation(e) for e in evaluations]

    @property
    def absences(self) -> List[Absence]:
        """
        Gets all absences in a given period.

        Returns
        -------
        List[Absence]
            All the absences of the period
        """
        json_data = {
            'periode': {'N': self.id, 'L': self.name, 'G': 2},
            'DateDebut': {'_T': 7, 'V': self.start.strftime("%d/%m/%Y %H:%M:%S")},
            'DateFin': {'_T': 7, 'V': self.end.strftime("%d/%m/%Y %H:%M:%S")}
        }

        response = self._client.post('PagePresence', 19, json_data)
        absences = response['donneesSec']['donnees']['listeAbsences']['V']
        return [Absence(a) for a in absences if a["G"] == 13]


class Average(Object):
    """
    Represents an Average.

    Attributes
    ----------
    student : str
        students average in the subject
    class_average : str
        classes average in the subject
    max : str
        highest average in the class
    min : str
        lowest average in the class
    out_of : str
        maximum amount of points
    default_out_of : str
        the default maximum amount of points
    subject : pronotepy.dataClasses.Subject
        subject the average is from
    """

    __slots__ = ['student', 'out_of', 'default_out_of', 'class_average', 'min', 'max', 'subject']

    def __init__(self, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.student: str = self._resolver(Util.grade_parse, "moyEleve", "V")
        self.out_of: str = self._resolver(Util.grade_parse, "baremeMoyEleve", "V")
        self.default_out_of: str = self._resolver(Util.grade_parse, "baremeMoyEleveParDefault", "V", default="")
        self.class_average: str = self._resolver(Util.grade_parse, "moyClasse", "V")
        self.min: str = self._resolver(Util.grade_parse, "moyMin", "V")
        self.max: str = self._resolver(Util.grade_parse, "moyMax", "V")
        self.subject = Subject(json_dict)

        del self._resolver


class Grade(Object):
    """Represents a grade. You shouldn't have to create this class manually.

    Attributes
    ----------
    id : str
        the id of the grade (used internally)
    grade : str
        the actual grade
    out_of : str
        the maximum amount of points
    default_out_of : Optional[str]
        the default maximum amount of points
    date : datetime.date
        the date on which the grade was given
    subject : pronotepy.dataClasses.Subject
        the subject in which the grade was given
    period : pronotepy.dataClasses.Period
        the period in which the grade was given
    average : str
        the average of the class
    max : str
        the highest grade of the test
    min : str
        the lowest grade of the test
    coefficient : str
        the coefficient of the grade
    comment : str
        the comment on the grade description
    """

    __slots__ = ['id', 'grade', 'out_of', 'default_out_of', 'date', 'subject',
                 'period', 'average', 'max', 'min', 'coefficient', 'comment']

    def __init__(self, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.id: str = self._resolver(str, "N")
        self.grade: str = self._resolver(Util.grade_parse, "note", "V")
        self.out_of: str = self._resolver(Util.grade_parse, "bareme", "V")
        self.default_out_of: str = self._resolver(Util.grade_parse, "baremeParDefault", "V", strict=False)
        self.date: datetime.date = self._resolver(Util.date_parse, "date", "V")
        self.subject: Subject = self._resolver(Subject, "service", "V")
        self.period: Period = self._resolver(lambda p: Util.get(Period.instances, id=p)[0], "periode", "V", "N")
        self.average: str = self._resolver(Util.grade_parse, "moyenne", "V")
        self.max: str = self._resolver(Util.grade_parse, "noteMax", "V")
        self.min: str = self._resolver(Util.grade_parse, "noteMin", "V")
        self.coefficient: str = self._resolver(str, "coefficient")
        self.comment: str = self._resolver(str, "commentaire")

        del self._resolver


class File(Object):
    """
    Represents a file uploaded to pronote.

    Attributes
    ----------
    name : str
        Name of the file.
    id : str
        id of the file (used internally and for url)
    url : str
        url of the file
    """

    __slots__ = ['name', 'id', '_client', 'url', '_data']

    def __init__(self, client: _ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)

        self._client = client

        self.name: str = self._resolver(str, 'L')
        self.id: str = self._resolver(str, 'N')

        padd = Padding.pad(json.dumps({'N': self.id, 'G': 1}).replace(' ', '').encode(), 16)
        magic_stuff = client.communication.encryption.aes_encrypt(padd).hex()

        self.url = f"{client.communication.root_site}/FichiersExternes/{magic_stuff}/" + \
                   quote(self.name, safe='~()*!.\'') + f"?Session={client.attributes['h']}"

        self._data = None

        del self._resolver

    def save(self, file_name: str = None) -> None:
        """
        Saves the file on to local storage.

        Parameters
        ----------
        file_name : str
            file name
        """
        response = self._client.communication.session.get(self.url)
        if not file_name:
            file_name = self.name
        if response.status_code == 200:
            with open(file_name, 'wb') as handle:
                for block in response.iter_content(1024):
                    handle.write(block)
        else:
            raise FileNotFoundError("The file was not found on pronote. The url may be badly formed.")

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

    Attributes
    ----------
    title : Optional[str]
        title of the lesson content
    description : Optional[str]
        description of the lesson content
    category : Optional[str]
        category of the lesson content
    files : tuple
        files attached on lesson content
    """

    __slots__ = ['title', 'description', '_files', '_client']

    def __init__(self, client: _ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)

        self._client = client

        self.title: Optional[str] = self._resolver(str, 'L', strict=False)
        self.description: Optional[str] = self._resolver(Util.html_parse, "descriptif", "V", strict=False)
        self.category: Optional[str] = self._resolver(str, "categorie", "V", "L", strict=False)
        self._files: Tuple[Any, ...] = self._resolver(tuple, "ListePieceJointe", "V")

        del self._resolver

    @property
    def files(self) -> List[File]:
        """Get all the attached files from the lesson"""
        return [File(self._client, jsn) for jsn in self._files]


class Lesson(Object):
    """
    Represents a lesson with a given time. You shouldn't have to create this class manually.

    Attributes
    ----------
    id : str
        the id of the lesson (used internally)
    subject : Optional[pronotepy.Subject]
        the subject that the lesson is from
    teacher_name : Optional[str]
        name of the teacher
    teacher_names : Optional[List[str]]
        name of the teachers
    classroom : Optional[str]
        name of the classroom
    classrooms : Optional[List[str]]
        name of the classrooms
    canceled : bool
        if the lesson is canceled
    status : Optional[str]
        status of the lesson
    background_color : Optional[str]
        background color of the lesson
    outing : bool
        if it is a pedagogical outing
    start : datetime.datetime
        starting time of the lesson
    end : datetime.datetime
        end of the lesson
    group_name : Optional[str]
        Name of the group.
    group_names : Optional[List[str]]
        Name of the groups.
    exempted : bool
        Specifies if the student's presence is exempt.
    virtual_classrooms : List[str]
        List of urls for virtual classrooms
    num : int
        For the same lesson time, the biggest num is the one shown on pronote.
    detention : bool
        is marked as detention
    """

    __slots__ = ['id', 'subject', 'teacher_name', 'teacher_names',
                 'classroom', 'classrooms', 'start', 'canceled',
                 'status', 'background_color', 'detention', 'end',
                 'outing', 'group_name', 'group_names', 'exempted',
                 '_client', '_content', 'virtual_classrooms', 'num']

    def __init__(self, client: _ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)
        self._client = client
        self._content: Optional[LessonContent] = None

        self.id: str = self._resolver(str, "N")
        self.canceled: bool = self._resolver(bool, "estAnnule", default=False)
        self.status: Optional[str] = self._resolver(str, "Statut", strict=False)
        self.background_color: Optional[str] = self._resolver(str, "CouleurFond", strict=False)
        self.outing: bool = self._resolver(bool, "estSortiePedagogique", default=False)
        self.start: datetime.datetime = self._resolver(Util.datetime_parse, "DateDuCours", "V")
        self.exempted: bool = self._resolver(bool, "dispenseEleve", default=False)
        self.virtual_classrooms: List[str] = self._resolver(lambda l: [i["url"] for i in l], "listeVisios", "V",
                                                            default=[])
        self.num: int = self._resolver(int, "P", default=0)
        self.detention: bool = self._resolver(bool, "estRetenue", default=False)
        self.test: bool = self._resolver(bool, "cahierDeTextes", "V", "estDevoir", default=False)

        # get correct ending time
        # Pronote gives us the place where the hour should be in a week, when we modulo that with the amount of
        # hours in a day we can get the "place" when the hour starts. Then we just add the duration (and substract 1)
        end_place = json_dict['place'] % (len(
            client.func_options['donneesSec']['donnees']['General']['ListeHeuresFin']['V']) - 1) + json_dict[
                        'duree'] - 1

        # With the end "place" now known we can look up the ending time in func_options
        end_time = next(filter(
            lambda x: x['G'] == end_place,
            client.func_options['donneesSec']['donnees']['General']['ListeHeuresFin']['V']
        ))
        end_time = datetime.datetime.strptime(end_time['L'], "%Hh%M").time()
        self.end: datetime.datetime = self.start.replace(hour=end_time.hour, minute=end_time.minute)

        # get additional information about the lesson
        self.teacher_names: Optional[List[str]] = []
        self.classrooms: Optional[List[str]] = []
        self.group_names: Optional[List[str]] = []
        self.subject: Optional[Subject] = None

        if 'ListeContenus' not in json_dict:
            raise ParsingError("Error while parsing for lesson details", json_dict, ("ListeContenus", "V"))

        for d in json_dict['ListeContenus']['V']:
            if 'G' not in d:
                continue
            elif d['G'] == 16:
                self.subject = Subject(d)
            elif d['G'] == 3:
                self.teacher_names.append(d['L'])
            elif d['G'] == 17:
                self.classrooms.append(d['L'])
            elif d['G'] == 2:
                self.group_names.append(d['L'])

        # All values joined together to prevent breaking changes
        self.teacher_name: Optional[str] = ', '.join(self.teacher_names) if self.teacher_names else None
        self.classroom: Optional[str] = ', '.join(self.classrooms) if self.classrooms else None
        self.group_name: Optional[str] = ', '.join(self.group_names) if self.group_names else None

        del self._resolver

    @property
    def normal(self) -> bool:
        if self.detention is None and self.outing is None:
            return True
        return False

    @property
    def content(self) -> Optional[LessonContent]:
        """
        Gets content of the lesson. May be None if there is no description.

        Notes
        -----
        This property is very inefficient and will send a request to pronote, so don't use it often.
        """
        if self._content:
            return self._content
        week = self._client.get_week(self.start.date())
        data = {"domaine": {"_T": 8, "V": f"[{week}..{week}]"}}
        response = self._client.post('PageCahierDeTexte', 89, data)
        contents = {}
        for lesson in response['donneesSec']['donnees']['ListeCahierDeTextes']['V']:
            if lesson['cours']['V']['N'] == self.id and lesson['listeContenus']['V']:
                contents = lesson['listeContenus']['V'][0]
                break
        if not contents:
            return None
        self._content = LessonContent(self._client, contents)
        return self._content


class Homework(Object):
    """
    Represents a homework. You shouldn't have to create this class manually.

    Attributes
    ----------
    id : str
        the id of the homework (used internally)
    subject : pronotepy.dataClasses.Subject
        the subject that the homework is for
    description : str
        the description of the homework
    background_color : str
        the background color of the homework
    done : bool
        if the homework is marked done
    date : datetime.date
        deadline
    """

    __slots__ = ['id', 'subject', 'description', 'done', 'background_color', '_client', 'date', '_files']

    def __init__(self, client: _ClientBase, json_dict: dict) -> None:
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

        Parameters
        ----------
        status : bool
            The status to which to change
        """
        data = {'listeTAF': [
            {'N': self.id, 'TAFFait': status}
        ]}
        self._client.post("SaisieTAFFaitEleve", 88, data)
        self.done = status

    @property
    def files(self) -> List[File]:
        """Get all the files attached to the homework"""
        return [File(self._client, jsn) for jsn in self._files]  # type: ignore


class Information(Object):
    """
    Represents a information in a information and surveys tab.

    Attributes
    ----------
    id : str
        the id of the information
    author : str
        author of the information
    title : str
        title of the information
    read : bool
        if the message has been read
    creation_date : datetime.datetime
        the date when the message was created
    start_date : datetime.datetime
        the date when the message became visible
    end_date : datetime.datetime
        the date on which the message will be withdrawn
    category: str
        category of the information
    survey: bool
        if the message is a survey
    anonymous_response : bool
        if the survey response is anonymous
    """

    __slots__ = ['id', 'title', 'author', 'read', 'creation_date', 'start_date', 'end_date', 'category',
                 'survey', 'anonymous_response', '_raw_content', '_client']

    def __init__(self, client: _ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)

        self._client = client

        self.id: str = self._resolver(str, 'N')
        self.title: Optional[str] = self._resolver(str, "L", strict=False)
        self.author: str = self._resolver(str, "auteur")
        self._raw_content: list = self._resolver(list, "listeQuestions", "V")
        self.read: bool = self._resolver(bool, "lue")
        self.creation_date: datetime.datetime = self._resolver(Util.datetime_parse, "dateCreation", "V")
        self.start_date: datetime.datetime = self._resolver(Util.datetime_parse, "dateDebut", "V")
        self.end_date: datetime.datetime = self._resolver(Util.datetime_parse, "dateFin", "V")
        self.category: str = self._resolver(str, "categorie", "V", "L")
        self.survey: bool = self._resolver(bool, "estSondage")
        self.anonymous_response: bool = self._resolver(bool, "reponseAnonyme")

        del self._resolver

    @property
    def content(self) -> str:
        return Util.html_parse(self._raw_content[0]['texte']['V'])

    def mark_as_read(self, status: bool) -> None:
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
            "saisieActualite": False
        }
        self._client.post("SaisieActualites", 8, data)
        self.read = status


class Message(Object):
    """
    Represents a message in a discussion.

    Attributes
    ----------
    id : str
        the id of the message (used internally)
    author : str
        author of the message
    recipients : list
        Recipitents of the message. ! May be just ['# recipients'] !
    seen : bool
        if the message was seen
    date : datetime.datetime
        the date when the message was sent
    """

    __slots__ = ['id', 'author', 'recipients', 'seen', 'date', '_client', '_listePM']

    def __init__(self, client: _ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)
        self._client = client
        self._listePM = json_dict['listePossessionsMessages']['V']

        self.id: str = self._resolver(str, "N")
        self.author: str = self._resolver(str, "public_gauche")
        self.recipients: list = self._resolver(list, "listePublic")
        self.seen: bool = self._resolver(bool, "lu")
        self.date: datetime.datetime = self._resolver(lambda d: Util.datetime_parse(" ".join(d.split()[1:])),
                                                      "libelleDate")

        del self._resolver

    @property
    def content(self) -> Optional[str]:
        """Returns the content of the message"""
        data = {'message': {'N': self.id},
                'marquerCommeLu': False,
                'estNonPossede': False,
                'listePossessionsMessages': self._listePM}
        resp = self._client.post('ListeMessages', 131, data)
        for m in resp['donneesSec']['donnees']['listeMessages']['V']:
            if m['N'] == self.id:
                if type(m['contenu']) == dict:
                    return Util.html_parse(m['contenu']['V'])
                else:
                    return m['contenu']
        return None


class ClientInfo:
    """
    Contains info for a resource (a client).

    Attributes
    ----------
    id : str
      id of the client (used internally)
    raw_resource : dict
      Raw json defining the resource
    """

    __slots__ = ['id', 'raw_resource', '_client', '__cache']

    def __init__(self, client: _ClientBase, json_: dict) -> None:
        self.id: str = json_['N']
        self.raw_resource: dict = json_
        self._client = client
        self.__cache: Optional[dict] = None

    @property
    def name(self) -> str:
        """
        Name of the client
        """
        return self.raw_resource['L']

    @property
    def delegue(self) -> List[str]:
        """
        list of classes of which the user is a delegue of
        """
        if self.raw_resource['estDelegue']:
            return [class_['L'] for class_ in self.raw_resource['listeClassesDelegue']['V']]
        else:
            return []

    @property
    def class_name(self) -> str:
        """
        name of the student's class
        """
        return self.raw_resource.get('classeDEleve', {}).get('L', '')

    @property
    def establishment(self) -> str:
        """
        name of the student's establishment
        """
        return self.raw_resource.get('Etablissement', {'V': {'L': ""}})['V']['L']

    def _cache(self) -> dict:
        if self.__cache is None:
            # this does not have all the protection _ClientBase.post provides,
            # but we need to manually add the resource id
            self.__cache = self._client.communication.post(
                "PageInfosPerso",
                {"_Signature_": {"onglet": 49, "ressource": {"N": self.id, "G": 4}}}
            )["donneesSec"]["donnees"]["Informations"]

        return self.__cache

    @property
    def address(self) -> tuple[str, str, str, str, str, str, str, str]:
        """
        Address of the client

        Returns
        -------
        A tuple of 8 elements:
            - 4 lines of address info
            - postal code
            - city
            - province
            - country
        """
        c = self._cache()
        return c["adresse1"], c["adresse2"], c["adresse3"], c["adresse4"], c["codePostal"], c["ville"], c["province"], \
               c["pays"]

    @property
    def email(self) -> str:
        return self._cache()["eMail"]

    @property
    def phone(self) -> str:
        """
        Phone of the client

        Returns
        -------
        Phone in the format +[country-code][phone-number]
        """
        c = self._cache()
        return "+" + c["indicatifTel"] + c["telephonePortable"]

    @property
    def ine_number(self) -> str:
        return self._cache()["numeroINE"]


class Acquisition(Object):
    """
    Contains acquisition info for an evaluation.

    Attributes
    ----------
    order : int
        Telling the order in which the acquisition is. The list of acquisitions is already sorted by this.
    level : str
        the level achieved for this acquisition
    id : int
        id, used internally
    abbreviation : str
        abbreviation for the level achieved
    coefficient : int
        coefficient
    domain : str
        domain in which the acquisition is
    domain_id : str
    name : str
        name (description) of the acquisition
    name_id : str
    pillar : str
    pillar_id : str
    pillar_prefix : str
    """

    __slots__ = [
        "order", "level", "id", "abbreviation", "coefficient", "domain", "domain_id", "name", "name_id", "pillar",
        "pillar_id", "pillar_prefix"]

    def __init__(self, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.id: str = self._resolver(str, "N")
        self.level: str = self._resolver(str, "L")
        self.abbreviation: str = self._resolver(str, "abbreviation")
        self.coefficient: int = self._resolver(int, "coefficient")
        self.domain: str = self._resolver(str, "domaine", "V", "L")
        self.domain_id: str = self._resolver(str, "domaine", "V", "N")
        self.name: Optional[str] = self._resolver(str, "item", "V", "L", strict=False)
        self.name_id: Optional[str] = self._resolver(str, "item", "V", "N", strict=False)
        self.order: int = self._resolver(int, "ordre")
        self.pillar: str = self._resolver(str, "pilier", "V", "L")
        self.pillar_id: str = self._resolver(str, "pilier", "V", "N")
        self.pillar_prefix: str = self._resolver(str, "pilier", "V", "strPrefixes")

        del self._resolver


class Evaluation(Object):
    """
    Data class for an evaluation.

    Attributes
    ----------
    name : str
    id : str
    domain : Optional[str]
    teacher : str
        the teacher who issued the evaluation
    coefficient : int
    description : str
    subject : pronotepy.dataClasses.Subject
    paliers : List[str]
    acquisitions : List[pronotepy.dataClasses.Acquisition]
    date : datetime.date
    """

    __slots__ = [
        "name", "name", "id", "domain", "teacher", "coefficient", "description", "subject", "paliers", "acquisitions",
        "date"]

    def __init__(self, json_dict: dict) -> None:
        super().__init__(json_dict)
        self.name: str = self._resolver(str, "L")
        self.id: str = self._resolver(str, "N")
        self.domain: Optional[str] = self._resolver(str, "domaine", "V", "L", strict=False)
        self.teacher: str = self._resolver(str, "individu", "V", "L")
        self.coefficient: int = self._resolver(int, "coefficient")
        self.description: str = self._resolver(str, "descriptif")
        self.subject: Subject = self._resolver(Subject, "matiere", "V")
        self.paliers: List[str] = self._resolver(lambda x: [_get_l(y) for y in x], "listePaliers", "V")
        self.acquisitions: List[Acquisition] = self._resolver(
            lambda x: sorted([Acquisition(y) for y in x], key=lambda z: z.order), "listeNiveauxDAcquisitions", "V")
        self.date: datetime.date = self._resolver(Util.date_parse, "date", "V")

        del self._resolver


class Identity(Object):
    """
    Represents an Identity of a person

    Attributes
    ----------
    postal_code : str
    date_of_birth : datetime.date
    email : Optional[str]
    last_name : str
    country : str
    mobile_number : Optional[str]
    landline_number : Optional[str]
    other_phone_number : Optional[str]
    city : str
    place_of_birth : Optional[str]
    first_names : List[str]
    address : List[str]
    formatted_address : str
        concatenated address information into a single string
    """
    __slots__ = ["postal_code", "date_of_birth", "email", "last_name", "country", "mobile_number", "landline_number",
                 "other_phone_number", "city", "place_of_birth", "first_names", "address", "formatted_address"]

    def __init__(self, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.postal_code: str = self._resolver(str, "CP")
        self.date_of_birth: Optional[datetime.date] = self._resolver(Util.date_parse, "dateNaiss", strict=False)
        self.email: Optional[str] = self._resolver(str, "email", strict=False)
        self.last_name: str = self._resolver(str, "nom")
        self.country: str = self._resolver(str, "pays")
        self.mobile_number: Optional[str] = self._resolver(str, "telPort", strict=False)
        self.landline_number: Optional[str] = self._resolver(str, "telFixe", strict=False)
        self.other_phone_number: Optional[str] = self._resolver(str, "telAutre", strict=False)
        self.city: str = self._resolver(str, "ville")
        self.place_of_birth: Optional[str] = self._resolver(str, "villeNaiss", strict=False)

        self.address: List[str] = []
        i = 1
        while True:
            option = json_dict.get("adresse" + str(i))
            if not option: break
            self.address.append(option)
            i += 1
        self.formatted_address: str = ','.join([*self.address, self.postal_code, self.city, self.country])
        self.first_names: List[str] = [json_dict.get("prenom", ""), json_dict.get("prenom2", ""),
                                       json_dict.get("prenom3", "")]

        del self._resolver


class Guardian(Object):
    """
    Represents a guardian of a student.

    Attributes
    ----------
    identity : dataClasses.Identity
    accepteInfosProf : bool
    authorized_email : bool
    authorized_pick_up_kid : bool
    urgency_contact : bool
    preferred_responsible_contact : bool
    accomodates_kid : bool
    relatives_link : str
    responsibility_level : str
    financially_responsible : bool
    full_name : str
    is_legal : bool
    """
    __slots__ = ["identity", "accepteInfosProf", "authorized_email", "authorized_pick_up_kid", "urgency_contact",
                 "preferred_responsible_contact", "accomodates_kid", "relatives_link", "responsibility_level",
                 "financially_responsible", "full_name", "is_legal"]

    def __init__(self, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.accepteInfosProf: bool = self._resolver(bool, "accepteInfosProf")
        self.authorized_email: bool = self._resolver(bool, "autoriseEmail")
        self.authorized_pick_up_kid: bool = self._resolver(bool, "autoriseRecupererEnfant")
        self.urgency_contact: bool = self._resolver(bool, "contactUrgence")
        self.preferred_responsible_contact: bool = self._resolver(bool, "estResponsablePreferentiel")
        self.accomodates_kid: bool = self._resolver(bool, "hebergeEnfant")
        self.relatives_link: str = self._resolver(str, "lienParente")
        self.responsibility_level: str = self._resolver(str, "niveauResponsabilite")
        self.financially_responsible: bool = self._resolver(bool, "responsableFinancier")
        self.full_name: str = self._resolver(str, "nom")

        self.identity = Identity(json_dict)
        self.is_legal = self.responsibility_level == "LEGAL"

        del self._resolver


class Student(Object):
    """
    Represents a student

    Attributes
    ----------
    full_name : str
    id : str
    enrollment_date : datetime.date
    date_of_birth : datetime.date
    projects : List[str]
    last_name : str
    first_names : str
    sex : str
    options : List[str]
        language options
    """
    __slots__ = ["_client", "full_name", "id", "enrollment_date", "date_of_birth", "projects", "last_name",
                 "first_names", "sex", "options", "_cache"]

    def __init__(self, client: _ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.full_name: str = self._resolver(str, "L")
        self.id: str = self._resolver(str, "N")
        self.enrollment_date: datetime.date = self._resolver(Util.date_parse, "entree", "V")
        self.date_of_birth: datetime.date = self._resolver(Util.date_parse, "neLe", "V")
        self.projects: List[str] = self._resolver(
            lambda p: [f"{x.get('typeAmenagement', '')} ({x.get('handicap', '')})" for x in p], "listeProjets", "V")
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
            self._cache = self._client.post("FicheEleve", 105,
                                            {"Eleve": {"N": self.id}, "AvecEleve": True, "AvecResponsables": True})
        return Identity(self._cache["donneesSec"]["donnees"]["Identite"])

    @property
    def guardians(self) -> List[Guardian]:
        """
        List of responsible persons (parents).
        """
        if self._cache is None:
            self._cache = self._client.post("FicheEleve", 105,
                                            {"Eleve": {"N": self.id}, "AvecEleve": True, "AvecResponsables": True})
        return [Guardian(j) for j in self._cache["donneesSec"]["donnees"]["Responsables"]["V"]]


class StudentClass(Object):
    """
    Represents a class of students

    Attributes
    ----------
    name : str
    id : str
    responsible : bool
        is the teacher responsible for the class
    grade : str
    """
    __slots__ = ["name", "id", "responsible", "grade", "_client"]

    def __init__(self, client: _ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.name: str = self._resolver(str, "L")
        self.id: str = self._resolver(str, "N")
        self.responsible: bool = self._resolver(bool, "estResponsable")
        self.grade: str = self._resolver(str, "niveau", "V", "L", default="")

        self._client = client

        del self._resolver

    def students(self, period: Period = None) -> List[Student]:
        period = period or self._client.periods[0]
        r = self._client.post("ListeRessources", 105,
                              {"classe": {"N": self.id, "G": 1}, "periode": {"N": period.id, "G": 1}})
        return [Student(self._client, j) for j in r["donneesSec"]["donnees"]["listeRessources"]["V"]]


class Menu(Object):
    """
    Represents the menu of a meal

    Attributes
    ----------
    id : str
    self.name: Optional[str]
    date : datetime.date
        the date of the menu
    is_lunch : bool
        the menu is a lunch menu
    is_dinner : bool
        the menu is a dinner menu
    first_meal : Optional[List[Food]]
        food list of first meal
    main_meal : Optional[List[Food]]
        food list of main meal
    side_meal : Optional[List[Food]]
        food list of side meal
    other_meal : Optional[List[Food]]
        food list of other meal
    cheese : Optional[List[Food]]
        food list of cheese
    dessert : Optional[List[Food]]
        food list of dessert
    """

    class Food(Object):
        """
        Represents food of a menu

        Attributes
        ----------
        id : str
        name : str
        labels : List[FoodLabel]
        """

        class FoodLabel(Object):
            """
            Represents the label of a food

            Attributes
            ----------
            id : str
            name: str
            color: str
            """

            __slots__ = ["name", "id", "color", "_client"]

            def __init__(self, client: _ClientBase, json_dict: dict) -> None:
                super().__init__(json_dict)

                self.id: str = self._resolver(str, "N")
                self.name: str = self._resolver(str, "L")
                self.color: str = self._resolver(str, 'couleur')

                self._client = client

                del self._resolver

        __slots__ = ["name", "id", "labels", "_client"]

        def __init__(self, client: _ClientBase, json_dict: dict) -> None:
            super().__init__(json_dict)

            self.id: str = self._resolver(str, "N")
            self.name: str = self._resolver(str, "L")
            self.labels: List[Menu.Food.FoodLabel] = self._resolver(
                lambda labels: [self.FoodLabel(client, label) for label in labels],
                "listeLabelsAlimentaires", "V"
            )

            self._client = client

            del self._resolver

    __slots__ = ["name", "id", "date", "is_lunch", "is_dinner", "first_meal",
                 "main_meal", "side_meal", "other_meal", "cheese", "dessert", "_client"]

    def __init__(self, client: _ClientBase, json_dict: dict) -> None:
        super().__init__(json_dict)

        self.id: str = self._resolver(str, "N")
        self.name: Optional[str] = self._resolver(str, "L", strict=False)
        self.date: datetime.date = self._resolver(Util.date_parse, 'Date', 'V')

        self.is_lunch: bool = self._resolver(int, 'G') == 0
        self.is_dinner: bool = self._resolver(int, 'G') == 1

        def init_food(d: dict) -> List[Menu.Food]:
            return [self.Food(client, x) for x in d["ListeAliments"]["V"]]

        d_dict = {str(meal['G']): meal for meal in json_dict["ListePlats"]["V"]}
        super().__init__(d_dict)

        self.first_meal: Optional[List[Menu.Food]] = self._resolver(init_food, "0", strict=False)
        self.main_meal: Optional[List[Menu.Food]] = self._resolver(init_food, "1", strict=False)
        self.side_meal: Optional[List[Menu.Food]] = self._resolver(init_food, "2", strict=False)
        self.other_meal: Optional[List[Menu.Food]] = self._resolver(init_food, "3", strict=False)
        self.cheese: Optional[List[Menu.Food]] = self._resolver(init_food, "5", strict=False)
        self.dessert: Optional[List[Menu.Food]] = self._resolver(init_food, "4", strict=False)

        self._client = client

        del self._resolver
