import datetime
import unittest

import pronotepy

client = pronotepy.Client('https://demo.index-education.net/pronote/eleve.html', 'demonstration', 'pronotevs')


class TestClient(unittest.TestCase):
    global client

    def test__get_week(self):
        self.assertEqual(client.get_week(client.start_day + datetime.timedelta(days=8)), 2)

    def test_lessons(self):
        start = client.start_day
        end = client.start_day + datetime.timedelta(days=8)
        lessons = client.lessons(start, end)
        # We assume demo website will always have some lessons
        self.assertGreater(len(lessons), 0)
        for lesson in lessons:
            self.assertLessEqual(start, lesson.start.date())
            self.assertLessEqual(lesson.start.date(), end)

    def test_periods(self):
        self.assertIsNotNone(client.periods)

    def test_current_period(self):
        self.assertIsNotNone(client.current_period)

    def test_homework(self):
        start = client.start_day
        end = client.start_day + datetime.timedelta(days=31)
        homework = client.homework(start, end)

        # We assume demo website will always have homework
        self.assertGreater(len(homework), 0)
        for hw in homework:
            self.assertLessEqual(start, hw.date)
            self.assertLessEqual(hw.date, end)

    def test_information(self):
        information = client.information_and_surveys()
        self.assertGreater(len(information), 0)
        for i in information:
            self.assertIsNotNone(i.author)
            self.assertIsNotNone(i.creation_date)
            self.assertIsInstance(i.survey, bool)

    def test_refresh(self):
        client.refresh()
        self.assertEqual(client.session_check(), True)


class TestPeriod(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        global client
        cls.period = client.current_period

    def test_grades(self):
        # We assume demo website will have grades
        grades = self.period.grades
        self.assertGreater(len(grades), 0)

    def test_averages(self):
        self.assertGreater(len(self.period.averages), 0)

    def test_overall_average(self):
        self.assertIsNotNone(self.period.overall_average)

    def test_evaluations(self):
        evaluations = self.period.evaluations
        self.assertGreater(len(evaluations), 0)
        for evaluation in evaluations:
            for acquisition in evaluation.acquisitions:
                self.assertIsNotNone(acquisition)


class TestLesson(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        global client
        cls.lesson = client.lessons(client.start_day + datetime.timedelta(days=4))[0]

    def test_normal(self):
        self.assertIsNotNone(self.lesson.normal)

    def test_content(self):
        self.assertIsInstance(self.lesson.content, pronotepy.LessonContent)


class TestLessonContent(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        global client
        cls.lessonContent = client.lessons(client.start_day + datetime.timedelta(days=4))[0].content

    def test_files(self):
        self.assertIsNotNone(self.lessonContent.files)


class TestParentClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = pronotepy.ParentClient('https://demo.index-education.net/pronote/parent.html',
                                            'demonstration', 'pronotevs')

    def test_set_child(self):
        self.client.set_child(self.client.children[1])
        self.client.set_child('PARENT Fanny')

    def test_homework(self):
        self.assertIsNotNone(
            self.client.homework(self.client.start_day, self.client.start_day + datetime.timedelta(days=31)))


class TestVieScolaireClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = pronotepy.VieScolaireClient('https://demo.index-education.net/pronote/viescolaire.html',
                                                 'demonstration2', 'pronotevs')

    def test_classes(self):
        self.assertGreater(len(self.client.classes), 0)

        for cls in self.client.classes:
            self.assertIsNotNone(cls.name)

        for student in self.client.classes[0].students():
            self.assertIsInstance(student.identity, pronotepy.Identity)
            self.assertGreater(len(student.guardians), 0)
            for guardian in student.guardians:
                self.assertIsInstance(guardian.identity, pronotepy.Identity)


if __name__ == '__main__':
    unittest.main()
