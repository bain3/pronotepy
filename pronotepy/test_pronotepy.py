import unittest

import pronotepy
import datetime

client = pronotepy.Client('https://demo.index-education.net/pronote/eleve.html', 'demonstration', 'pronotevs')


class TestClient(unittest.TestCase):
    global client

    def test__get_week(self):
        self.assertEqual(client.get_week((client.start_day + datetime.timedelta(days=8)).date()), 2)

    def test_lessons(self):
        self.assertIsNotNone(
            client.lessons(client.start_day.date(), (client.start_day + datetime.timedelta(days=8)).date()))

    def test_periods(self):
        self.assertIsNotNone(client.periods)

    def test_current_period(self):
        self.assertIsNotNone(client.current_period)

    def test_homework(self):
        self.assertIsNotNone(
            client.homework(client.start_day.date(), (client.start_day + datetime.timedelta(days=8)).date()))

    def test_refresh(self):
        client.refresh()
        self.assertEqual(client.session_check(), True)


class TestPeriod(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        global client
        cls.period = client.current_period

    def test_grades(self):
        self.assertIsNotNone(self.period.grades)

    def test_averages(self):
        self.assertIsNotNone(self.period.averages)

    def test_overall_average(self):
        self.assertIsNotNone(self.period.overall_average)


class TestLesson(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        global client
        cls.lesson = client.lessons((client.start_day+datetime.timedelta(days=4)).date())[0]

    def test_normal(self):
        self.assertIsNotNone(self.lesson.normal)

    def test_content(self):
        self.assertIsInstance(self.lesson.content, pronotepy.LessonContent)


class TestLessonContent(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        global client
        cls.lessonContent = client.lessons((client.start_day+datetime.timedelta(days=4)).date())[0].content

    def test_files(self):
        self.assertIsNotNone(self.lessonContent.files)


if __name__ == '__main__':
    unittest.main()
