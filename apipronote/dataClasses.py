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
    def prepare_json(cls, data_class, json_dict):
        """
        Prepares json for the data class.
        TODO: Maybe remove None if didn't find? It is already done in the class.
        """
        attribute_dict = data_class.attribute_guide
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
    attribute_guide = {
        "N": "id",
        "note,V": "grade",
        "bareme,V": "out_of",
        "baremeParDefault,V": "default_out_of",
        "date,V": "date",
        "service,V": "course",
        "periode,V": "period",
        "moyenne,V": "average",
        "noteMax,V": "max",
        "noteMin,V": "min",
        "coefficient": "coefficient"
    }

    instances = set()

    __slots__ = ['id', 'grade', 'out_of', 'default_out_of', 'date', 'course',
                 'period', 'average', 'max', 'min', 'coefficient']

    def __init__(self, parsed_json):
        if parsed_json['G'] != 60:
            raise IncorrectJson('The json received was not the same as expected.')
        prepared_json = Util.prepare_json(self.__class__, parsed_json)
        self.grade = self.out_of = self.default_out_of = self.date = self.average = self.max = self.id = self.min = None
        self.course = None
        self.period = None
        self.coefficient = 1
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])
        if self.course:
            self.course = Course(self.course)
        if self.period:
            # noinspection PyTypeChecker
            self.period = Util.get(Period.instances, id=self.period['N'])
        if self.date:
            self.date = datetime.datetime.strptime(self.date, '%d/%m/%Y').date()


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

    -- Attributes --
    id = the id of the lesson (used internally)
    course = the course that the lesson is from
    teacher_name = name of the teacher
    classroom = name of the classroom
    canceled = if the lesson is canceled
    outing = if it is a pedagogical outing
    start = starting time of the lesson
    """
    __slots__ = ['id', 'course', 'teacher_name', 'classroom', 'start', 'canceled', '_liste_contenus', 'detention', 'end', 'outing']
    attribute_guide = {
        'DateDuCours,V': 'start',
        'N': 'id',
        'estAnnule': 'canceled',
        'estRetenue': 'detention',
        'duree': 'end',
        'estSortiePedagogique': 'outing'
    }

    def __init__(self, client, parsed_json):
        self.id = self.course = self.teacher_name = self.classroom = \
            self.start = self.canceled = self.detention = self.end = self.outing = None

        prepared_json = Util.prepare_json(self.__class__, parsed_json)
        for key in prepared_json:
            self.__setattr__(key, prepared_json[key])

        if self.start:
            self.start = datetime.datetime.strptime(self.start, '%d/%m/%Y %H:%M:%S')
        if self.end:
            self.end = self.start + client.one_hour_duration * self.end

        if 'ListeContenus' in parsed_json:
            for d in parsed_json['ListeContenus']['V']:
                if 'G' not in d:
                    continue
                elif d['G'] == 16:
                    self.course = Course(d)
                elif d['G'] == 3:
                    self.teacher_name = d['L']
                elif d['G'] == 17:
                    self.classroom = d['L']


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
        self._client.communication.post("SaisieTAFFaitEleve", data)
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
