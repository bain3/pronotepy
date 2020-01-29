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
    variable_attr = {
        'moyEleve': 'average',
        'baremeMoyEleve': 'out_of',
        'baremeMoyEleveParDefault': 'default_out_of',
        'moyClasse': 'class_average',
        'moyMin': 'min',
        'moyMax': 'max'
    }

    def __init__(self, parsed_json):
        self.id = parsed_json['N']
        self.name = parsed_json['L']
        self.groups = None
        self.average = None
        self.class_average = None
        self.max = None
        self.min = None
        self.out_of = None
        self.default_out_of = None
        if 'estServiceEnGroup' in parsed_json:
            self.groups = parsed_json['estServiceEnGroupe']
        for key in parsed_json:
            if key in self.__class__.variable_attr:
                setattr(self, self.__class__.variable_attr[key], parsed_json[key]['V'])


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
    __slots__ = ['id', 'course', 'teacher_name', 'classroom', 'start', 'canceled', 'outing']

    def __init__(self, parsed_json):
        if 'estSortiePedagogique' in parsed_json:
            self.outing = True
            self.start = datetime.datetime.strptime(parsed_json['DateDuCours']['V'], '%d/%m/%Y %H:%M:%S')
            return
        self.id = parsed_json['N']
        self.course = Course(parsed_json['ListeContenus']['V'][0])
        self.teacher_name = parsed_json['ListeContenus']['V'][1]['L']
        self.classroom = parsed_json['ListeContenus']['V'][2]['L']
        self.canceled = False
        if 'estAnnule' in parsed_json:
            self.canceled = True
        self.outing = False
        self.start = datetime.datetime.strptime(parsed_json['DateDuCours']['V'], '%d/%m/%Y %H:%M:%S')


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

    def __init__(self, client, parsed_json):
        self._client = client
        self.id = parsed_json['N']
        self.course = Course(parsed_json['Matiere']['V'])
        # get rid of this html shait
        self.description = re.sub(re.compile('<.*?>'), '', parsed_json['descriptif']['V'])
        self.done = parsed_json['TAFFait']

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
