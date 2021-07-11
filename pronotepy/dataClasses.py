import datetime
import json
import logging
import re
from html import unescape
from typing import Union, List
from urllib.parse import quote

from Crypto.Util import Padding

from .exceptions import IncorrectJson

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def _get_l(d): return d['L']


class Util:
    """Utilities for the API wrapper"""
    grade_translate = ['Absent', 'Dispense', 'NonNote', 'Inapte', 'NonRendu', 'AbsentZero', 'NonRenduZero',
                       'Felicitations']

    @classmethod
    def get(cls, iterable, **kwargs) -> list:
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
    def prepare_json(cls, data_class, json_dict):
        """Prepares json for the data class."""
        attribute_dict = data_class.attribute_guide
        output = {}
        for key in attribute_dict:
            actual_dict = key.split(',')
            try:
                out = json_dict
                for level in actual_dict:
                    out = out[level]
            except KeyError:
                if len(attribute_dict[key]) == 3:
                    output[attribute_dict[key][0]] = attribute_dict[key][2]
                else:
                    try:
                        output[attribute_dict[key][0]] = attribute_dict[key][1](None)
                    except Exception as e:
                        log.debug("Exception while parsing json (" + str(actual_dict) + "), setting to None: " + str(e))
                        output[attribute_dict[key][0]] = None
            else:
                output[attribute_dict[key][0]] = attribute_dict[key][1](out)
        return output

    @classmethod
    def grade_parse(cls, string):
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
            log.warning("date parsing not possible for value '" + formatted_date + "' set to None")

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
            log.warning("date parsing not possible for value '" + formatted_date + "' set to None")

    @staticmethod
    def html_parse(html_text: str) -> str:
        """remove tags from html text"""
        return unescape(re.sub(re.compile('<.*?>'), '', html_text))


class Subject:
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

    attribute_guide = {
        'N': ('id', str),
        'L': ('name', str),
        'estServiceEnGroupe': ('groups', bool)
    }

    def __init__(self, parsed_json):
        prepared_json = Util.prepare_json(self.__class__, parsed_json)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])


class Period:
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

    id: str
    name: str
    start: datetime.datetime
    end: datetime.datetime

    __slots__ = ['_client', 'id', 'name', 'start', 'end']
    instances = set()

    def __init__(self, client, parsed_json):
        self.__class__.instances.add(self)
        self._client = client
        self.id = parsed_json['N']
        self.name = parsed_json['L']
        self.start = Util.datetime_parse(parsed_json['dateDebut']['V'])
        self.end = Util.datetime_parse(parsed_json['dateFin']['V'])

    @property
    def grades(self):
        """Get grades from the period."""
        json_data = {'periode': {'N': self.id, 'L': self.name}}
        response = self._client.post('DernieresNotes', 198, json_data)
        log.debug(response)
        grades = response['donneesSec']['donnees']['listeDevoirs']['V']
        return [Grade(g) for g in grades]

    @property
    def averages(self):
        """Get averages from the period."""

        json_data = {'periode': {'N': self.id, 'L': self.name}}
        response = self._client.post('DernieresNotes', 198, json_data)
        crs = response['donneesSec']['donnees']['listeServices']['V']
        return [Average(c) for c in crs]

    @property
    def overall_average(self):
        """Get overall average from the period. If the period average is not provided by pronote, then it's calculated.
        Calculation may not be the same as the actual average. (max difference 0.01)"""
        json_data = {'periode': {'N': self.id, 'L': self.name}}
        response = self._client.post('DernieresNotes', 198, json_data)
        average = response['donneesSec']['donnees'].get('moyGenerale')
        if average:
            average = average['V']
        elif response['donneesSec']['donnees']['listeServices']['V']:
            a = 0
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
    def evaluations(self):
        json_data = {'periode': {'N': self.id, 'L': self.name, 'G': 2}}
        response = self._client.post('DernieresEvaluations', 201, json_data)
        evaluations = response['donneesSec']['donnees']['listeEvaluations']['V']
        return [Evaluation(e) for e in evaluations]


class Average:
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

    student: str
    class_average: str
    max: str
    min: str
    out_of: str
    default_out_of: str
    subject: Subject

    attribute_guide = {
        'moyEleve,V': ('student', Util.grade_parse),
        'baremeMoyEleve,V': ('out_of', Util.grade_parse),
        'baremeMoyEleveParDefault,V': ('default_out_of', Util.grade_parse, ""),
        'moyClasse,V': ('class_average', Util.grade_parse),
        'moyMin,V': ('min', Util.grade_parse),
        'moyMax,V': ('max', Util.grade_parse)
    }
    __slots__ = ['student', 'out_of', 'default_out_of', 'class_average', 'min', 'max', 'subject']

    def __init__(self, parsed_json):
        prepared_json = Util.prepare_json(self.__class__, parsed_json)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])
        self.subject = Subject(parsed_json)


# noinspection PyTypeChecker
class Grade:
    """Represents a grade. You shouldn't have to create this class manually.

    Attributes
    ----------
    id : str
        the id of the grade (used internally)
    grade : str
        the actual grade
    out_of : str
        the maximum amount of points
    default_out_of : str
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

    id: str
    grade: str
    out_of: str
    default_out_of: str
    date: datetime.date
    subject: Subject
    period: Period
    average: str
    max: str
    min: str
    coefficient: str
    comment: str

    attribute_guide = {
        "N": ("id", str),
        "note,V": ("grade", Util.grade_parse),
        "bareme,V": ("out_of", Util.grade_parse),
        "baremeParDefault,V": ("default_out_of", Util.grade_parse, ""),
        "date,V": ("date", Util.date_parse),
        "service,V": ("subject", Subject),
        "periode,V,N": ("period", lambda p: Util.get(Period.instances, id=p)),
        "moyenne,V": ("average", Util.grade_parse),
        "noteMax,V": ("max", Util.grade_parse),
        "noteMin,V": ("min", Util.grade_parse),
        "coefficient": ("coefficient", str),
        "commentaire": ("comment", str)
    }

    instances = set()

    __slots__ = ['id', 'grade', 'out_of', 'default_out_of', 'date', 'subject',
                 'period', 'average', 'max', 'min', 'coefficient', 'comment']

    def __init__(self, parsed_json):
        if parsed_json['G'] != 60:
            raise IncorrectJson('The json received was not the same as expected.')
        prepared_json = Util.prepare_json(self.__class__, parsed_json)
        self.coefficient = 1
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])


class Lesson:
    """
    Represents a lesson with a given time. You shouldn't have to create this class manually.

    !!If a lesson is a pedagogical outing, it will only have the "outing" and "start" attributes!!

    Attributes
    ----------
    id : str
        the id of the lesson (used internally)
    subject : pronotepy.dataClasses.Subject
        the subject that the lesson is from
    teacher_name : str
        name of the teacher
    classroom : str
        name of the classroom
    canceled : bool
        if the lesson is canceled
    status : str
        status of the lesson
    background_color : str
        background color of the lesson
    outing : bool
        if it is a pedagogical outing
    start : datetime.datetime
        starting time of the lesson
    end : datetime.datetime
        end of the lesson
    group_name : str
        Name of the group.
    exempted : bool
        Specifies if the student's presence is exempt.
    virtual_classrooms : List[str]
        List of urls for virtual classrooms
    num: int
        For the same lesson time, the biggest num is the one shown on pronote.
    """

    id: str
    subject: Union[Subject, None]
    teacher_name: str
    classroom: str
    canceled: bool
    status: str
    background_color: str
    outing: bool
    start: datetime.datetime
    group_name: str
    exempted: bool
    virtual_classrooms: List[str]
    end: datetime.datetime
    num: int

    __slots__ = ['id', 'subject', 'teacher_name', 'classroom', 'start',
                 'canceled', 'status', 'background_color', 'detention',
                 'end', 'outing', 'group_name', 'student_class', 'exempted',
                 '_client', '_content', 'virtual_classrooms', 'num']
    attribute_guide = {
        'DateDuCours,V': ('start', Util.datetime_parse),
        'N': ('id', str),
        'estAnnule': ('canceled', bool),
        'Statut': ('status', str),
        'CouleurFond': ('background_color', str),
        'estRetenue': ('detention', bool, False),
        'estSortiePedagogique': ('outing', bool, False),
        'dispenseEleve': ('exempted', bool, False),
        'listeVisios,V': ('virtual_classrooms', lambda l: [i["url"] for i in l], []),
        'P': ('num', int)
    }
    transformers = {
        16: ('subject', Subject),
        3: ('teacher_name', _get_l),
        17: ('classroom', _get_l),
        2: ('group_name', _get_l)
    }

    def __init__(self, client, parsed_json):
        self._client = client
        self._content = None
        prepared_json = Util.prepare_json(self.__class__, parsed_json)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])

        # get correct ending time
        # Pronote gives us the place where the hour should be in a week, when we modulo that with the amount of
        # hours in a day we can get the "place" when the hour starts. Then we just add the duration (and substract 1)
        end_place = parsed_json['place'] % (len(
            client.func_options['donneesSec']['donnees']['General']['ListeHeuresFin']['V']) - 1) + parsed_json[
                        'duree'] - 1

        # With the end "place" now known we can look up the ending time in func_options
        self.end = None
        end_time = next(filter(
            lambda x: x['G'] == end_place,
            client.func_options['donneesSec']['donnees']['General']['ListeHeuresFin']['V']
        ))
        end_time = datetime.datetime.strptime(end_time['L'], "%Hh%M").time()
        self.end = self.start.replace(hour=end_time.hour, minute=end_time.minute)

        self.teacher_name = self.classroom = self.group_name = self.student_class = ''
        self.subject = None
        if 'ListeContenus' in parsed_json:
            for d in parsed_json['ListeContenus']['V']:
                try:
                    self.__setattr__(self.__class__.transformers[d['G']][0], self.__class__.transformers[d['G']][1](d))
                except KeyError:
                    pass

    @property
    def normal(self):
        if self.detention is None and self.outing is None:
            return True
        return False

    @property
    def content(self):
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


class LessonContent:
    """
    Represents the content of a lesson. You shouldn't have to create this class manually.

    Attributes
    ----------
    title : str
        title of the lesson content
    description : str
        description of the lesson content
    """

    title: str
    description: str

    attribute_guide = {
        'L': ('title', str),
        'descriptif,V': ('description', Util.html_parse),
        'ListePieceJointe,V': ('_files', tuple)
    }

    __slots__ = ['title', 'description', '_files', '_client']

    def __init__(self, client, parsed_json):
        prepared_json = Util.prepare_json(self.__class__, parsed_json)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])
        self._client = client

    @property
    def files(self):
        """Get all the attached files from the lesson"""
        return [File(self._client, jsn) for jsn in self._files]


class File:
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

    name: str
    id: str
    url: str

    attribute_guide = {
        'L': ('name', str),
        'N': ('id', str)
    }

    __slots__ = ['name', 'id', '_client', 'url', '_data']

    def __init__(self, client, parsed_json):
        prepared_json = Util.prepare_json(self.__class__, parsed_json)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])
        self._client = client
        padd = Padding.pad(json.dumps({'N': self.id, 'G': 1}).replace(' ', '').encode(), 16)
        magic_stuff = client.communication.encryption.aes_encrypt(padd).hex()
        self.url = client.communication.root_site \
                   + '/FichiersExternes/' \
                   + magic_stuff + '/' + quote(self.name, safe='~()*!.\'') \
                   + '?Session=' + client.attributes['h']
        self._data = None

    def save(self, file_name=None):
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
    def data(self):
        """Gets the raw file data."""
        if self._data:
            return self._data
        response = self._client.communication.session.get(self.url)
        return response.content


class Homework:
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

    id: str
    subject: Subject
    description: str
    background_color: str
    done: bool
    date: datetime.date

    __slots__ = ['id', 'subject', 'description', 'done', 'background_color', '_client', 'date', '_files']
    attribute_guide = {
        'N': ('id', str),
        'descriptif,V': ('description', Util.html_parse),
        'TAFFait': ('done', bool),
        'Matiere,V': ('subject', Subject),
        'CouleurFond': ('background_color', str),
        'PourLe,V': ('date', Util.date_parse),
        'ListePieceJointe,V': ('_files', tuple)
    }

    def __init__(self, client, parsed_json):
        self.done = False
        self._client = client
        prepared_json = Util.prepare_json(self.__class__, parsed_json)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])

    def set_done(self, status: bool):
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
    def files(self):
        """Get all the files attached to the homework"""
        return [File(self._client, jsn) for jsn in self._files]


class Information:
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
    content: str
        content of the information
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

    id: str
    title: str
    author: str
    content: str
    read: bool
    creation_date: datetime.datetime
    start_date: datetime.datetime
    end_date: datetime.datetime
    category: str
    survey: bool
    anonymous_response: bool

    __slots__ = ['id', 'title', 'author', 'read', 'creation_date', 'start_date', 'end_date', 'category',
                 'survey', 'anonymous_response', '_raw_content', '_client']

    attribute_guide = {
        'N': ('id', str),
        'L': ('title', str),
        'auteur': ('author', str),
        'listeQuestions,V': ('_raw_content', list),
        'lue': ('read', bool),
        'dateCreation,V': ('creation_date', Util.date_parse),
        'dateDebut,V': ('start_date', Util.date_parse),
        'dateFin,V': ('end_date', Util.date_parse),
        'categorie,V,L': ('category', str),
        'estSondage': ('survey', bool),
        'reponseAnonyme': ('anonymous_response', bool)
    }

    def __init__(self, client, json_):
        self._client = client
        prepared_json = Util.prepare_json(self.__class__, json_)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])

    @property
    def content(self):
        return Util.html_parse(self._raw_content[0]['texte']['V'])

    def mark_as_read(self, status: bool):
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


class Message:
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

    id: str
    author: str
    recipients: list
    seen: bool
    date: datetime.datetime

    __slots__ = ['id', 'author', 'recipients', 'seen', 'date', '_client', '_listePM']
    attribute_guide = {
        'N': ('id', str),
        'public_gauche': ('author', str),
        'listePublic': ('recipients', list),
        'lu': ('seen', bool),
        'libelleDate': ('date', lambda d: Util.datetime_parse(' '.join(d.split()[1:])))
    }

    def __init__(self, client, json_):
        self._client = client
        self._listePM = json_['listePossessionsMessages']['V']
        prepared_json = Util.prepare_json(self.__class__, json_)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])

    @property
    def content(self):
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
    id: str
      id of the client (used internally)
    name: str
      name of the client
    delegue: List[str]
      list of classes of which the user is a delegue of
    class_name: str
      name of the student's class
    raw_resource: dict
      Raw json defining the resource
    """

    id: str

    __slots__ = ['id', 'raw_resource']

    def __init__(self, json_):
        self.id = json_['N']
        self.raw_resource = json_

    @property
    def name(self):
        return self.raw_resource['L']

    @property
    def delegue(self):
        if self.raw_resource['estDelegue']:
            return [class_['L'] for class_ in self.raw_resource['listeClassesDelegue']['V']]
        else:
            return []

    @property
    def class_name(self):
        return self.raw_resource.get('classeDEleve', {}).get('L', '')

    @property
    def establishment(self):
        return self.raw_resource.get('Etablissement', {'V': {'L': ""}})['V']['L']


class Acquisition:
    """
    Contains acquisition info for an evaluation.

    Attributes
    ----------
    order: int
        Telling the order in which the acquisition is. The list of acquisitions is already sorted by this.
    level: str
        the level achieved for this acquisition
    id: int
        id, used internally
    abbreviation: str
        abbreviation for the level achieved
    coefficient: int
        coefficient
    domain: str
        domain in which the acquisition is
    domain_id: str
    name: str
        name (description) of the acquisition
    name_id: str
    pillar: str
    pillar_id: str
    pillar_prefix: str
    """
    order: int
    level: str
    id: str
    abbreviation: str
    coefficient: int
    domain: str
    domain_id: str
    name: str
    name_id: str
    pillar: str
    pillar_id: str
    pillar_prefix: str

    attribute_guide = {
        'L': ('level', str),
        'N': ('id', str),
        'abbreviation': ('abbreviation', str),
        'coefficient': ('coefficient', int),
        'domaine,V,L': ('domain', str),
        'domaine,V,N': ('domain_id', str),
        'item,V,L': ('name', str),
        'item,V,N': ('name_id', str),
        'ordre': ('order', int),
        'pilier,V,L': ('pillar', str),
        'pilier,V,N': ('pillar_id', str),
        'pilier,V,strPrefixes': ('pillar_prefix', str)
    }

    __slots__ = [
        "order", "level", "id", "abbreviation", "coefficient", "domain", "domain_id", "name", "name_id", "pillar",
        "pillar_id", "pillar_prefix"]

    def __init__(self, json_):
        prepared_json = Util.prepare_json(self.__class__, json_)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])


class Evaluation:
    """
    Data class for an evaluation.

    Attributes
    ----------
    name: str
    id: str
    domain: str
    teacher: str
        the teacher who issued the evaluation
    coefficient: int
    description: str
    subject: pronotepy.dataClasses.Subject
    paliers: List[str]
    acquisitions: List[pronotepy.dataClasses.Acquisition]
    date: datetime.date
    """
    name: str
    name: str
    id: str
    domain: str
    teacher: str
    coefficient: int
    description: str
    subject: Subject
    paliers: List[str]
    acquisitions: List[Acquisition]
    date: datetime.date

    __slots__ = [
        "name", "name", "id", "domain", "teacher", "coefficient", "description", "subject", "paliers", "acquisitions",
        "date"]

    attribute_guide = {
        'L': ('name', str),
        'N': ('id', str),
        'domaine,V,L': ('domain', str),
        'individu,V,L': ('teacher', str),
        'coefficient': ('coefficient', int),
        'descriptif': ('description', str),
        'matiere,V': ('subject', Subject),
        'listePaliers,V': ('paliers', lambda x: [_get_l(y) for y in x]),
        # Can we just appreciate the readability of this?
        'listeNiveauxDAcquisitions,V': (
            'acquisitions', lambda x: sorted([Acquisition(y) for y in x], key=lambda z: z.order)),
        "date,V": ("date", Util.date_parse),
    }

    def __init__(self, json_):
        prepared_json = Util.prepare_json(self.__class__, json_)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])


class Identity:
    """
    Represents an Identity of a person
    
    Attributes
    ----------
    postal_code: str
    date_of_birth: datetime.date
    email: str
    last_name: str
    country: str
    mobile_number: str
    landline_number: str
    other_phone_number: str
    city: str
    place_of_birth: str
    first_names: List[str]
    address: List[str]
    formatted_address: str
        concatenated address information into a single string
    """
    attribute_guide = {
        "CP": ("postal_code", str),
        "dateNaiss": ("date_of_birth", Util.date_parse, None),
        "email": ("email", str),
        "nom": ("last_name", str),
        "pays": ("country", str),
        "telPort": ("mobile_number", str),
        "telFixe": ("landline_number", str),
        "telAutre": ("other_phone_number", str),
        "ville": ("city", str),
        "villeNaiss": ("place_of_birth", str)
    }
    __slots__ = ["postal_code", "date_of_birth", "email", "last_name", "country", "mobile_number", "landline_number",
                 "other_phone_number", "city", "place_of_birth", "first_names", "address", "formatted_address"]

    postal_code: str
    date_of_birth: datetime.date
    email: str
    last_name: str
    country: str
    mobile_number: str
    landline_number: str
    other_phone_number: str
    city: str
    place_of_birth: str
    first_names: List[str]
    address: List[str]
    formatted_address: str

    def __init__(self, json_):
        prepared_json = Util.prepare_json(self.__class__, json_)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])

        self.address = []
        i = 1
        while True:
            option = json_.get("adresse" + str(i))
            if not option: break
            self.address.append(option)
            i += 1
        self.formatted_address = ','.join([*self.address, self.postal_code, self.city, self.country])
        self.first_names = [json_.get("prenom"), json_.get("prenom2"), json_.get("prenom3")]


class Guardian:
    """
    Represents a guardian of a student.

    Attributes
    ----------
    identity: dataClasses.Identity
    accepteInfosProf: bool
    authorized_email: bool
    authorized_pick_up_kid: bool
    urgency_contact: bool
    preferred_responsible_contact: bool
    accomodates_kid: bool
    relatives_link: str
    responsibility_level: str
    financially_responsible: bool
    full_name: str
    is_legal: bool
    """
    attribute_guide = {
        "accepteInfosProf": ("accepteInfosProf", bool),
        "autoriseEmail": ("authorized_email", bool),
        "autoriseRecupererEnfant": ("authorized_pick_up_kid", bool),
        "contactUrgence": ("urgency_contact", bool),
        "estResponsablePreferentiel": ("preferred_responsible_contact", bool),
        "hebergeEnfant": ("accomodates_kid", bool),
        "lienParente": ("relatives_link", str),
        "niveauResponsabilite": ("responsibility_level", str),
        "responsableFinancier": ("financially_responsible", bool),
        "nom": ("full_name", str)
    }
    __slots__ = ["identity", "accepteInfosProf", "authorized_email", "authorized_pick_up_kid", "urgency_contact",
                 "preferred_responsible_contact", "accomodates_kid", "relatives_link", "responsibility_level",
                 "financially_responsible", "full_name", "is_legal"]

    identity: Identity
    accepteInfosProf: bool
    authorized_email: bool
    authorized_pick_up_kid: bool
    urgency_contact: bool
    preferred_responsible_contact: bool
    accomodates_kid: bool
    relatives_link: str
    responsibility_level: str
    financially_responsible: bool
    full_name: str
    is_legal: bool

    def __init__(self, json_):
        prepared_json = Util.prepare_json(self.__class__, json_)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])

        self.identity = Identity(json_)
        self.is_legal = self.responsibility_level == "LEGAL"


class Student:
    """
    Represents a student

    Attributes
    ----------
    full_name: str
    id: str
    enrollment_date: datetime.date
    date_of_birth: datetime.date
    projects: List[str]
    last_name: str
    first_names: str
    sex: str
    options: List[str]
        language options
    """
    attribute_guide = {
        "L": ("full_name", str),
        "N": ("id", str),
        "entree,V": ("enrollment_date", Util.date_parse),
        "neLe,V": ("date_of_birth", Util.date_parse),
        "listeProjets,V": ("projects", lambda p: [f"{x['typeAmenagement']} ({x['handicap']})" for x in p]),
        "nom": ("last_name", str),
        "prenoms": ("first_names", str),
        "sexe": ("sex", str),
    }
    __slots__ = ["_client", "full_name", "id", "enrollment_date", "date_of_birth", "projects", "last_name",
                 "first_names", "sex", "options", "_cache"]

    full_name: str
    id: str
    enrollment_date: datetime.date
    date_of_birth: datetime.date
    projects: List[str]
    last_name: str
    first_names: str
    sex: str
    options: List[str]

    def __init__(self, client, json_):
        prepared_json = Util.prepare_json(self.__class__, json_)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])

        self._client = client
        self._cache = None

        self.options = []
        i = 1
        while True:
            option = json_.get("option" + str(i))
            if not option:
                break
            self.options.append(option)
            i += 1

    @property
    def identity(self) -> Identity:
        """
        Identity of this student
        """
        if not self._cache:
            self._cache = self._client.post("FicheEleve", 105,
                                            {"Eleve": {"N": self.id}, "AvecEleve": True, "AvecResponsables": True})
        return Identity(self._cache["donneesSec"]["donnees"]["Identite"])

    @property
    def guardians(self) -> List[Guardian]:
        """
        List of responsible persons (parents).
        """
        if not self._cache:
            self._cache = self._client.post("FicheEleve", 105,
                                            {"Eleve": {"N": self.id}, "AvecEleve": True, "AvecResponsables": True})
        return [Guardian(j) for j in self._cache["donneesSec"]["donnees"]["Responsables"]["V"]]


class StudentClass:
    """
    Represents a class of students

    Attributes
    ----------
    name: str
    id: str
    responsible: bool
        is the teacher responsible for the class
    grade: str
    """
    attribute_guide = {
        "L": ("name", str),
        "N": ("id", str),
        "estResponsable": ("responsible", bool),
        "niveau,V,L": ("grade", str, "")
    }
    __slots__ = ["name", "id", "responsible", "grade", "_client"]

    name: str
    id: str
    responsible: bool
    grade: str

    def __init__(self, client, json_):
        prepared_json = Util.prepare_json(self.__class__, json_)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])

        self._client = client

    def students(self, period: Period = None) -> List[Student]:
        period = period or self._client.periods[0]
        r = self._client.post("ListeRessources", 105,
                              {"classe": {"N": self.id, "G": 1}, "periode": {"N": period.id, "G": 1}})
        return [Student(self._client, j) for j in r["donneesSec"]["donnees"]["listeRessources"]["V"]]
