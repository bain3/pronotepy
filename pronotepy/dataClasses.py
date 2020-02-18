import datetime
import re


def _get_l(d): return d['L']


class Util:
    """Utilities for the API wrapper"""

    @classmethod
    def get(cls, iterable, **kwargs) -> list:
        """Gets items from the list with the attributes specified.

        :param iterable:The iterable to loop over
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

    -- Attributes --
    id: str = the id of the subject (used internally)
    name: str = name of the subject
    groups: bool = if the subject is in groups
    average: str = users average in the subject
    class_average: str = classes average in the subject
    max: str = the highest grade in the class
    min: str = the lowest grade in the class
    out_of: str = the maximum amount of points
    default_out_of: str = the default maximum amount of points"""
    __slots__ = ['id', 'name', 'groups', 'average', 'class_average', 'max', 'min', 'out_of', 'default_out_of']
    attribute_guide = {
        'moyEleve,V':                 ('average', str),
        'baremeMoyEleve,V':           ('out_of', str),
        'baremeMoyEleveParDefault,V': ('default_out_of', str),
        'moyClasse,V':                ('class_average', str),
        'moyMin,V':                   ('min', str),
        'moyMax,V':                   ('max', str),
        'N':                          ('id', str),
        'L':                          ('name', str),
        'estServiceEnGroupe':         ('groups', bool)
    }

    def __init__(self, parsed_json):
        self.id = self.name = self.groups = self.average = self.class_average = \
            self.max = self.min = self.out_of = self.default_out_of = None
        prepared_json = Util.prepare_json(self.__class__, parsed_json)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])


class Period:
    """
    Represents a period of the school year. You shouldn't have to create this class manually.

    -- Attributes --
    id: str = the id of the period (used internally)
    name: str = name of the period
    start: datetime.datetime = date on which the period starts
    end: datetime.datetime = date on which the period ends"""

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
        return [Subject(c) for c in crs]


class Grade:
    """Represents a grade. You shouldn't have to create this class manually.

    -- Attributes --
    id: str = the id of the grade (used internally)
    grade: str = the actual grade
    out_of: str = the maximum amount of points
    default_out_of: str = the default maximum amount of points
    date: datetime.datetime = the date on which the grade was given
    subject: Subject = the subject in which the grade was given
    period: Period = the period in which the grade was given
    average: str = the average of the class
    max: str = the highest grade of the test
    min: str = the lowest grade of the test
    coefficient: int = the coefficient of the grade"""
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
        -- Attributes --
        id: str = ID of the class
        name: str = name of the class"""
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
    -- Attributes --
    id: str = ID of the class
    name: str = name of the class"""
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

    -- Attributes --
    id: str = the id of the lesson (used internally)
    subject: Subject = the subject that the lesson is from
    teacher_name: str = name of the teacher
    classroom: str = name of the classroom
    canceled: str = if the lesson is canceled
    outing: bool = if it is a pedagogical outing
    start: datetime.datetime = starting time of the lesson
    group_name: str = Name of the group.
    student_class: StudentClass = Teachers only. Class of the students"""
    __slots__ = ['id', 'subject', 'teacher_name', 'classroom', 'start',
                 'canceled', 'detention', 'end', 'outing', 'group_name', 'student_class', '_client']
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


class Absences:
    """Teachers only. Represents the absences in a class."""
    def __init__(self, parsed_json):
        self.json = parsed_json


class Homework:
    """
    Represents a homework. You shouldn't have to create this class manually.

    -- Attributes --
    id: str = the id of the homework (used internally)
    subject: Subject = the subject that the homework is for
    description: str = the description of the homework
    done: bool = if the homework is marked done
    date: datetime.date = deadline"""
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
        :param status:The status to which to change
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
