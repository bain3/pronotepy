import datetime
import re
import json
from urllib.parse import quote
from . import pronoteAPI
from Crypto.Util import Padding


def _get_l(d): return d['L']


class Util:
    """Utilities for the API wrapper"""

    @classmethod
    def get(cls, iterable, **kwargs) -> list:
        """Gets items from the list with the attributes specified.

        :param iterable: The iterable to loop over
        :type iterable: list
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


class Subject:
    """
    Represents a subject. You shouldn't have to create this class manually.

    **Attributes**

    :var id: the id of the subject (used internally)
    :var name: name of the subject
    :var groups: if the subject is in groups
    """
    __slots__ = ['id', 'name', 'groups']

    attribute_guide = {
        'N':                          ('id', str),
        'L':                          ('name', str),
        'estServiceEnGroupe':         ('groups', bool)
    }

    def __init__(self, parsed_json):
        prepared_json = Util.prepare_json(self.__class__, parsed_json)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])


class Period:
    """
    Represents a period of the school year. You shouldn't have to create this class manually.

    **Attributes**

    :var id: the id of the period (used internally)
    :var name: name of the period
    :var start: date on which the period starts
    :var end: date on which the period ends
    """

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
        grades = response.json()['donneesSec']['donnees']['listeDevoirs']['V']
        return [Grade(g) for g in grades]

    @property
    def averages(self):
        """Get averages from the period."""
        json_data = {'donnees': {'Periode': {'N': self.id, 'L': self.name}}, "_Signature_": {"onglet": 198}}
        response = self._client.communication.post('DernieresNotes', json_data)
        crs = response.json()['donneesSec']['donnees']['listeServices']['V']
        return [Average(c) for c in crs]

    @property
    def overall_average(self):
        """Get overall average from the period. If the period average is not provided by pronote, then it's calculated.
        Calculation may not be the same as the actual average. (max difference 0.01)"""
        json_data = {'donnees': {'Periode': {'N': self.id, 'L': self.name}}, "_Signature_": {"onglet": 198}}
        response = self._client.communication.post('DernieresNotes', json_data)
        average = response.json()['donneesSec']['donnees'].get('moyGenerale')
        if average:
            average = average['V']
        elif response.json()['donneesSec']['donnees']['listeServices']['V']:
            a = 0
            total = 0
            services = response.json()['donneesSec']['donnees']['listeServices']['V']
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
                average = round(a/total, 2)
            else:
                average = -1
        else:
            average = -1
        return average


class Average:
    """
    Represents an Average.

    **Attributes**

    :var student: students average in the subject
    :var class: classes average in the subject
    :var max: highest average in the class
    :var min: lowest average in the class
    :var out_of: maximum amount of points
    :var default_out_of: he default maximum amount of points
    :var subject: subject the average is from
    """
    attribute_guide = {
        'moyEleve,V': ('student', str),
        'baremeMoyEleve,V': ('out_of', str),
        'baremeMoyEleveParDefault,V': ('default_out_of', str),
        'moyClasse,V': ('class', str),
        'moyMin,V': ('min', str),
        'moyMax,V': ('max', str)
    }
    __slots__ = ['student', 'out_of', 'default_out_of', 'class', 'min', 'max', 'subject']

    def __init__(self, parsed_json):
        prepared_json = Util.prepare_json(self.__class__, parsed_json)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])
        self.subject = Subject(parsed_json)



class Grade:
    """Represents a grade. You shouldn't have to create this class manually.

    **Attributes**

    :var id: the id of the grade (used internally)
    :var grade: the actual grade
    :var out_of: the maximum amount of points
    :var default_out_of: the default maximum amount of points
    :var date: the date on which the grade was given
    :var subject: the subject in which the grade was given
    :var period: the period in which the grade was given
    :var average: the average of the class
    :var max: the highest grade of the test
    :var min: the lowest grade of the test
    :var coefficient: the coefficient of the grade"""
    attribute_guide = {
        "N":                  ("id", str),
        "note,V":             ("grade", str),
        "bareme,V":           ("out_of", str),
        "baremeParDefault,V": ("default_out_of", str),
        "date,V":             ("date", lambda d: datetime.datetime.strptime(d, '%d/%m/%Y').date()),
        "service,V":          ("subject", Subject),
        "periode,V,N":        ("period", lambda p: Util.get(Period.instances, id=p)),
        "moyenne,V":          ("average", str),
        "noteMax,V":          ("max", str),
        "noteMin,V":          ("min", str),
        "coefficient":        ("coefficient", int),
        "commentaire":        ("comment", str)
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


class Student:
    """Represents a class of students

    **Attributes**

    :var id: ID of the class
    :var name: name of the class"""
    attribute_guide = {
        'N': ('id', str),
        'L': ('name', str)
    }

    def __init__(self, parsed_json):
        prepared_json = Util.prepare_json(self.__class__, parsed_json)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])


class StudentClass:
    """Represents a class of students

    **Attributes**

    :var id: ID of the class
    :var name: name of the class"""
    attribute_guide = {
        'N': ('id', str),
        'L': ('name', str)
    }

    def __init__(self, parsed_json):
        prepared_json = Util.prepare_json(self.__class__, parsed_json)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])


class Lesson:
    """
    Represents a lesson with a given time. You shouldn't have to create this class manually.

    !!If a lesson is a pedagogical outing, it will only have the "outing" and "start" attributes!!

    **Attributes**

    :var id: the id of the lesson (used internally)
    :var subject: the subject that the lesson is from
    :var teacher_name: name of the teacher
    :var classroom: name of the classroom
    :var canceled: if the lesson is canceled
    :var outing: if it is a pedagogical outing
    :var start: starting time of the lesson
    :var group_name: Name of the group.
    :var student_class: Teachers only. Class of the students"""
    __slots__ = ['id', 'subject', 'teacher_name', 'classroom', 'start',
                 'canceled', 'detention', 'end', 'outing', 'group_name', 'student_class', '_client', '_content']
    attribute_guide = {
        'DateDuCours,V':        ('start', lambda d: datetime.datetime.strptime(d, '%d/%m/%Y %H:%M:%S')),
        'N':                    ('id', str),
        'estAnnule':            ('canceled', bool),
        'estRetenue':           ('detention', bool),
        'duree':                ('end', int),
        'estSortiePedagogique': ('outing', bool)
    }
    transformers = {
        16: ('subject', Subject),
        3:  ('teacher_name', _get_l),
        17: ('classroom', _get_l),
        2:  ('group_name', _get_l),
        1:  ('student_class', StudentClass)
    }

    def __init__(self, client, parsed_json):
        self._client = client
        self._content = None
        prepared_json = Util.prepare_json(self.__class__, parsed_json)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])
        if self.end:
            self.end = self.start + client.one_hour_duration * self.end
        self.subject = self.teacher_name = self.classroom = self.group_name = self.student_class = None
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
    def absences(self):
        """
        Teachers only. Get the absences from the lesson.
        """
        user = self._client.auth_response.json()['donneesSec']['donnees']['ressource']
        data = {'_Signature_': {'onglet': 113},
                'donnees': {
                    'Professeur': user,
                    'Ressource': {'N': self.id},
                    'Date': {'_T': 7, 'V': self.start.strftime('%d/%m%Y 0:0:0')}
                }}
        return Absences(self._client.communication.post("PageSaisieAbsences", data).json())

    @property
    def content(self):
        """
        Gets content of the lesson.
        .. note:: This property is very inefficient and will send a request to pronote, so don't use it often.
        """
        if self._content:
            return self._content
        week = self._client._get_week(self.start.date())
        data = {"_Signature_": {"onglet": 89}, "donnees": {"domaine": {"_T": 8, "V": f"[{week}..{week}]"}}}
        response = self._client.communication.post('PageCahierDeTexte', data)
        contents = {}
        for lesson in response.json()['donneesSec']['donnees']['ListeCahierDeTextes']['V']:
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

    **Attributes**

    :var title: title of the lesson content
    :var description: description of the lesson content
    """
    attribute_guide = {
        'L': ('title', str),
        'descriptif,V': ('description', lambda d: re.sub(re.compile('<.*?>'), '', d)),
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

    **Attributes**

    :var name: Name of the file.
    :var id: id of the file (used internally and for url)
    :var url: url of the file
    """
    attribute_guide = {
        'L': ('name', str),
        'N': ('id', str)
    }

    __slots__ = ['name', 'id', '_client', 'url']

    def __init__(self, client, parsed_json):
        e = pronoteAPI._Encryption()
        e.aes_iv = client.encryption.aes_iv

        prepared_json = Util.prepare_json(self.__class__, parsed_json)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])
        self._client = client
        padd = Padding.pad(json.dumps({'N': self.id, 'Actif': True}).replace(' ', '').encode(), 16)
        magic_stuff = client.communication.encryption.aes_encrypt(padd).hex()
        self.url = client.communication.root_site+'/FichiersExternes/'+magic_stuff+'/'+quote(self.name, safe='~()*!.\'')+'?Session='+client.attributes['h']

    def save(self, file_name=None):
        """
        Saves the file.

        :param file_name: file name
        :type file_name: str
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
        response = self._client.communication.session.get(self.url)
        return response.content


class Absences:
    """Teachers only. Represents the absences in a class."""
    def __init__(self, parsed_json):
        self.json = parsed_json


class Homework:
    """
    Represents a homework. You shouldn't have to create this class manually.

    **Attributes**

    :var id: the id of the homework (used internally)
    :var subject: the subject that the homework is for
    :var description: the description of the homework
    :var done: if the homework is marked done
    :var date: deadline"""
    __slots__ = ['id', 'subject', 'description', 'done', '_client', 'date']
    attribute_guide = {
        'N':            ('id', str),
        'descriptif,V': ('description', lambda d: re.sub(re.compile('<.*?>'), '', d)),
        'TAFFait':      ('done', bool),
        'Matiere,V':    ('subject', Subject),
        'PourLe,V':     ('date', lambda d: datetime.datetime.strptime(d, '%d/%m/%Y').date())
    }

    def __init__(self, client, parsed_json):
        self.done = None
        self._client = client
        prepared_json = Util.prepare_json(self.__class__, parsed_json)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])

    def set_done(self, status: bool):
        """
        Sets the status of the homework.

        :param status: The status to wich to change
        :type status: bool
        """
        data = {'_Signature_': {'onglet': 88}, 'donnees': {'listeTAF': [
            {'N': self.id, 'TAFFait': status}
        ]}}
        if self._client.communication.post("SaisieTAFFaitEleve", data):
            self.done = status


class DataError(Exception):
    """
    Base exception for any errors made by creating or manipulating data classes.
    """
    pass


class IncorrectJson(DataError):
    """Bad json"""
    pass
