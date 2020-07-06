import datetime
import re
import json
from urllib.parse import quote
from Crypto.Util import Padding
from html import unescape
from typing import Union


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
    start : str
        date on which the period starts
    end : str
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
        self.start = datetime.datetime.strptime(parsed_json['dateDebut']['V'], '%d/%m/%Y')
        self.end = datetime.datetime.strptime(parsed_json['dateFin']['V'], '%d/%m/%Y')

    @property
    def grades(self):
        """Get grades from the period."""
        json_data = {'donnees': {'Periode': {'N': self.id, 'L': self.name}}, "_Signature_": {"onglet": 198}}
        response = self._client.communication.post('DernieresNotes', json_data)
        grades = response['donneesSec']['donnees']['listeDevoirs']['V']
        return [Grade(g) for g in grades]

    @property
    def averages(self):
        """Get averages from the period."""
        json_data = {'donnees': {'Periode': {'N': self.id, 'L': self.name}}, "_Signature_": {"onglet": 198}}
        response = self._client.communication.post('DernieresNotes', json_data)
        crs = response['donneesSec']['donnees']['listeServices']['V']
        return [Average(c) for c in crs]

    @property
    def overall_average(self):
        """Get overall average from the period. If the period average is not provided by pronote, then it's calculated.
        Calculation may not be the same as the actual average. (max difference 0.01)"""
        json_data = {'donnees': {'Periode': {'N': self.id, 'L': self.name}}, "_Signature_": {"onglet": 198}}
        response = self._client.communication.post('DernieresNotes', json_data)
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
        'baremeMoyEleveParDefault,V': ('default_out_of', Util.grade_parse),
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
    date : str
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
    """

    id: str
    grade: str
    out_of: str
    default_out_of: str
    date: str
    subject: Subject
    period: Period
    average: str
    max: str
    min: str
    coefficient: str

    attribute_guide = {
        "N": ("id", str),
        "note,V": ("grade", Util.grade_parse),
        "bareme,V": ("out_of", Util.grade_parse),
        "baremeParDefault,V": ("default_out_of", Util.grade_parse),
        "date,V": ("date", lambda d: datetime.datetime.strptime(d, '%d/%m/%Y').date()),
        "service,V": ("subject", Subject),
        "periode,V,N": ("period", lambda p: Util.get(Period.instances, id=p)),
        "moyenne,V": ("average", Util.grade_parse),
        "noteMax,V": ("max", Util.grade_parse),
        "noteMin,V": ("min", Util.grade_parse),
        "coefficient": ("coefficient", int),
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
    start : str
        starting time of the lesson
    group_name : str
        Name of the group."""

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

    __slots__ = ['id', 'subject', 'teacher_name', 'classroom', 'start',
                 'canceled', 'status', 'background_color', 'detention', 'end', 'outing', 'group_name', 'student_class',
                 '_client', '_content']
    attribute_guide = {
        'DateDuCours,V': ('start', lambda d: datetime.datetime.strptime(d, '%d/%m/%Y %H:%M:%S')),
        'N': ('id', str),
        'estAnnule': ('canceled', bool),
        'Statut': ('status', str),
        'CouleurFond': ('background_color', str),
        'estRetenue': ('detention', bool),
        'duree': ('end', int),
        'estSortiePedagogique': ('outing', bool)
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
        if self.end:
            self.end = self.start + client.one_hour_duration * self.end
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
        data = {"_Signature_": {"onglet": 89}, "donnees": {"domaine": {"_T": 8, "V": f"[{week}..{week}]"}}}
        response = self._client.communication.post('PageCahierDeTexte', data)
        contents = {}
        for lesson in response['donneesSec']['donnees']['ListeCahierDeTextes']['V']:
            if lesson['cours']['V']['N'] == self.id:
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
        'descriptif,V': ('description', lambda d: unescape(re.sub(re.compile('<.*?>'), '', d))),
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
        padd = Padding.pad(json.dumps({'N': self.id, 'Actif': True}).replace(' ', '').encode(), 16)
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
    date : str
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
        'descriptif,V': ('description', lambda d: unescape(re.sub(re.compile('<.*?>'), '', d))),
        'TAFFait': ('done', bool),
        'Matiere,V': ('subject', Subject),
        'CouleurFond': ('background_color', str),
        'PourLe,V': ('date', lambda d: datetime.datetime.strptime(d, '%d/%m/%Y').date()),
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
        data = {'_Signature_': {'onglet': 88}, 'donnees': {'listeTAF': [
            {'N': self.id, 'TAFFait': status}
        ]}}
        if self._client.communication.post("SaisieTAFFaitEleve", data):
            self.done = status

    @property
    def files(self):
        """Get all the files attached to the homework"""
        return [File(self._client, jsn) for jsn in self._files]


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
    date : str
        the date when the message was sent
    """

    id: str
    author: str
    recipients: list
    seen: bool
    date: str

    __slots__ = ['id', 'author', 'recipients', 'seen', 'date', '_client', '_listePM']
    attribute_guide = {
        'N': ('id', str),
        'public_gauche': ('author', str),
        'listePublic': ('recipients', list),
        'lu': ('seen', bool),
        'libelleDate': ('date', lambda d: datetime.datetime.strptime(' '.join(d.split()[1:]), '%d/%m/%y %Hh%M'))
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
        data = {'donnees': {'message': {'N': self.id},
                            'marquerCommeLu': False,
                            'estNonPossede': False,
                            'listePossessionsMessages': self._listePM},
                '_Signature_': {'onglet': 131}}
        resp = self._client.communication.post('ListeMessages', data)
        for m in resp['donneesSec']['donnees']['listeMessages']['V']:
            if m['N'] == self.id:
                if type(m['contenu']) == dict:
                    return unescape(re.sub(re.compile('<.*?>'), '', m['contenu']['V']))
                else:
                    return m['contenu']
        return None


class DataError(Exception):
    """
    Base exception for any errors made by creating or manipulating data classes.
    """
    pass


class IncorrectJson(DataError):
    """Bad json"""
    pass
