import datetime
import re


class Util:
    """Utilities for the API wrapper"""
    @classmethod
    def get(cls, iterable, **kwargs) -> list:
        """
        Gets items from the list with the attributes specified.

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
    def prepare_json(cls, clss, json_dict):
        attribute_dict = clss.attribute_guide
        output = {}
        for key in attribute_dict:
            actual_dict = key.split(',')
            try:
                out = json_dict
                for level in actual_dict:
                    out = out[level]
            except KeyError:
                out = None

            output[attribute_dict[key]] = out
        return output


class Grade:
    """
    Represents a grade. You shouldn't have to create this class manually.

    -- Attributes --
    id = the id of the grade (used internally)
    grade = the actual grade
    out_of = the maximum amount of points
    default_out_of = the default maximum amount of points
    date = the date on which the grade was given
    course = the course in which the grade was given
    period = the period in which the grade was given
    average = the average of the class
    max = the highest grade of the test
    min = the lowest grade of the test
    coefficient = the coefficient of the grade
    """
    variable_attr = {
        "note": "grade",
        "bareme": "out_of",
        "baremeParDefault": "default_out_of",
        "date": "date",
        "service": "course",
        "periode": "period",
        "moyenne": "average",
        "noteMax": "max",
        "noteMin": "min"
    }

    instances = set()

    __slots__ = ['id', 'grade', 'out_of', 'default_out_of', 'date', 'course',
                 'period', 'average', 'max', 'min', 'coefficient']

    def __init__(self, parsed_json):
        if parsed_json['G'] != 60:
            raise IncorrectJson('The json received was not the same as expected.')
        self.id = parsed_json["N"]
        self.grade = None
        self.out_of = None
        self.default_out_of = None
        self.date = None
        self.course = {}
        self.period = {}
        self.average = None
        self.max = None
        self.min = None
        self.coefficient = 1
        for key in parsed_json:
            if key in self.__class__.variable_attr:
                setattr(self, self.__class__.variable_attr[key], parsed_json[key]['V'])
        if self.course:
            self.course = Course(self.course)
        if self.period:
            self.period = Util.get(Period.instances, id=self.period['N'])
        if self.date:
            self.date = datetime.datetime.strptime(self.date, '%d/%m/%Y').date()
        if 'coefficient' in parsed_json:
            self.coefficient = parsed_json['coefficient']


class Course:
    """
    Represents a course. You shouldn't have to create this class manually.

    -- Attributes --
    id = the id of the course (used internally)
    name = name of the course
    -- all attributes under this may not be present at all times --
    groups = if the course is in groups
    average = users average in the course
    class_average = classes average in the course
    max = the highest grade in the class
    min = the lowest grade in the class
    out_of = the maximum amount of points
    default_out_of = the default maximum amount of points
    """
    __slots__ = ['id', 'name', 'groups', 'average', 'class_average', 'max', 'min', 'out_of', 'default_out_of']
    attribute_guide = {
        'moyEleve,V': 'average',
        'baremeMoyEleve,V': 'out_of',
        'baremeMoyEleveParDefault,V': 'default_out_of',
        'moyClasse,V': 'class_average',
        'moyMin,V': 'min',
        'moyMax,V': 'max',
        'N': 'id',
        'L': 'name',
        'estServiceEnGroupe': 'groups'
    }

    def __init__(self, parsed_json):
        prepared_json = Util.prepare_json(self.__class__, parsed_json)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])


class Lesson:
    """
    Represents a lesson with a given time. You shouldn't have to create this class manually.

    !!If a lesson is a pedagogical outing, it will only have the "outing" and "start" attributes!!
    FIXME: Date is not date but str

    -- Attributes --
    id = the id of the lesson (used internally)
    course = the course that the lesson is from
    teacher_name = name of the teacher
    classroom = name of the classroom
    canceled = if the lesson is canceled
    outing = if it is a pedagogical outing
    start = starting time of the lesson
    """
    __slots__ = ['id', 'course', 'teacher_name', 'classroom', 'start', 'canceled', 'outing', '_liste_contenus']
    attribute_guide = {
        'DateDuCours,V': 'start',
        'N': 'id',
        'estAnnule': 'canceled'
    }

    def __init__(self, parsed_json):
        prepared_json = Util.prepare_json(self.__class__, parsed_json)
        self._liste_contenus = parsed_json['ListeContenus']['V']
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])

        if self.start:
            self.start = datetime.datetime.strptime(self.start, '%d/%m/%Y %H:%M:%S')

        for d in self._liste_contenus:
            if 'G' not in d:
                continue
            elif d['G'] == 16:
                self.course = Course(d)
            elif d['G'] == 3:
                self.teacher_name = d['L']
            elif d['G'] == 17:
                self.classroom = d['L']
        self.outing = False


class Homework:
    """
    Represents a homework. You shouldn't have to create this class manually.

    -- Attributes --
    id = the id of the homework (used internally)
    course = the course that the homework is for
    description = the description of the homework
    done = if the homework is marked done
    """
    __slots__ = ['id', 'course', 'description', 'done', '_client']
    attribute_guide = {
        'N': 'id',
        'descriptif,V': 'description',
        'TAFFait': 'done',
        'Matiere,V': 'course'
    }

    def __init__(self, client, parsed_json):
        self._client = client
        self.id = self.description = self.done = self.course = None
        prepared_json = Util.prepare_json(self.__class__, parsed_json)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])
        if self.course:
            self.course = Course(self.course)
        if self.description:
            self.description = re.sub(re.compile('<.*?>'), '', self.description)

    def set_done(self, status: bool):
        data = {'_Signature_': {'onglet': 88}, 'donnees': {'listeTAF': [
            {'N': self.id, 'TAFFait': status}
        ]}}
        r = self._client.communication.post("SaisieTAFFaitEleve", data)
        self.done = status


class Period:
    """
    Represents a period of the school year. You shouldn't have to create this class manually.

    -- Attributes --
    id = the id of the period (used internally)
    name = name of the period
    start = date on which the period starts
    end = date on which the period ends
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

    def grades(self):
        json_data = {'donnees': {'Periode': {'N': self.id, 'L': self.name}}, "_Signature_": {"onglet": 198}}
        response = self._client.communication.post('DernieresNotes', json_data)
        grades = response.json()['donneesSec']['donnees']['listeDevoirs']['V']
        return [Grade(g) for g in grades]

    def averages(self):
        json_data = {'donnees': {'Periode': {'N': self.id, 'L': self.name}}, "_Signature_": {"onglet": 198}}
        response = self._client.communication.post('DernieresNotes', json_data)
        crs = response.json()['donneesSec']['donnees']['listeServices']['V']
        return [Course(c) for c in crs]


class DataError(Exception):
    pass


class IncorrectJson(DataError):
    pass
