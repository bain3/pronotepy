import datetime
import unittest

import pronotepy

client = pronotepy.Client('https://demo.index-education.net/pronote/eleve.html', 'demonstration', 'pronotevs')


class TestClient(unittest.TestCase):
    global client

    def test__get_week(self) -> None:
        self.assertEqual(client.get_week(client.start_day + datetime.timedelta(days=8)), 2)

    def test_lessons(self) -> None:
        start = client.start_day
        end = client.start_day + datetime.timedelta(days=8)
        lessons = client.lessons(start, end)
        # We assume demo website will always have some lessons
        self.assertGreater(len(lessons), 0)
        for lesson in lessons:
            self.assertLessEqual(start, lesson.start.date())
            self.assertLessEqual(lesson.start.date(), end)

    def test_periods(self) -> None:
        self.assertIsNotNone(client.periods)

    def test_current_period(self) -> None:
        self.assertIsNotNone(client.current_period)

    def test_homework(self) -> None:
        start = client.start_day
        end = client.start_day + datetime.timedelta(days=31)
        homework = client.homework(start, end)

        # We assume demo website will always have homework
        self.assertGreater(len(homework), 0)
        for hw in homework:
            self.assertLessEqual(start, hw.date)
            self.assertLessEqual(hw.date, end)

    def test_menus(self) -> None:
        start = client.start_day
        end = client.start_day + datetime.timedelta(days=8)
        menus = client.menus(start, end)
        for menu in menus:
            self.assertLessEqual(start, menu.date)
            self.assertLessEqual(menu.date, end)

    def test_export_ical(self) -> None:
        import requests
        ical = client.export_ical()
        resp = requests.get(ical)
        self.assertEqual(resp.status_code, 200)

    def test_refresh(self) -> None:
        client.refresh()
        self.assertEqual(client.session_check(), True)


class TestPeriod(unittest.TestCase):
    period: pronotepy.Period

    @classmethod
    def setUpClass(cls) -> None:
        global client
        cls.period = client.current_period

    def test_grades(self) -> None:
        # We assume demo website will have grades
        grades = self.period.grades
        self.assertGreater(len(grades), 0)

    def test_averages(self) -> None:
        self.assertGreater(len(self.period.averages), 0)

    def test_overall_average(self) -> None:
        self.assertIsNotNone(self.period.overall_average)

    def test_evaluations(self) -> None:
        evaluations = self.period.evaluations
        self.assertGreater(len(evaluations), 0)
        for evaluation in evaluations:
            for acquisition in evaluation.acquisitions:
                self.assertIsNotNone(acquisition)

    def test_absences(self) -> None:
        all_absences = [period.absences for period in client.periods]
        self.assertGreater(len(all_absences), 0)


class TestInformation(unittest.TestCase):

    def test_unread(self) -> None:
        information = client.information_and_surveys(only_unread=True)
        for info in information:
            self.assertFalse(info.read)

    def test_time_delta(self) -> None:
        start = datetime.datetime(year=client.start_day.year, month=client.start_day.month, day=client.start_day.day)
        end = start + datetime.timedelta(days=100)
        information = client.information_and_surveys(date_from=start, date_to=end)
        for info in information:
            self.assertTrue(start <= info.start_date <= end, msg="date outside the research limits")


class TestLesson(unittest.TestCase):
    lesson: pronotepy.Lesson

    @classmethod
    def setUpClass(cls) -> None:
        global client
        cls.lesson = client.lessons(client.start_day + datetime.timedelta(days=4))[0]

    def test_normal(self) -> None:
        self.assertIsNotNone(self.lesson.normal)

    def test_content(self) -> None:
        self.assertIsInstance(self.lesson.content, pronotepy.LessonContent)


class TestLessonContent(unittest.TestCase):
    lessonContent: pronotepy.LessonContent

    @classmethod
    def setUpClass(cls) -> None:
        global client
        content = client.lessons(client.start_day + datetime.timedelta(days=4))[0].content
        if content is None:
            raise Exception("Content is None!")
        cls.lessonContent = content

    def test_files(self) -> None:
        self.assertIsNotNone(self.lessonContent.files)


class TestMenu(unittest.TestCase):
    menu: pronotepy.Menu

    @classmethod
    def setUpClass(cls) -> None:
        global client
        i = 0
        menus = client.menus(client.start_day + datetime.timedelta(days=i))
        while len(menus) == 0:
            i += 1
            menus = client.menus(client.start_day + datetime.timedelta(days=i))
        cls.menu = menus[0]

    def test_lunch_dinner(self) -> None:
        self.assertNotEqual(self.menu.is_lunch, self.menu.is_dinner, 'The menu is neither a lunch nor a dinner or is both')


class TestParentClient(unittest.TestCase):
    client: pronotepy.ParentClient

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = pronotepy.ParentClient('https://demo.index-education.net/pronote/parent.html',
                                            'demonstration', 'pronotevs')

    def test_set_child(self) -> None:
        self.client.set_child(self.client.children[1])
        self.client.set_child('PARENT Fanny')

    def test_homework(self) -> None:
        self.assertIsNotNone(
            self.client.homework(self.client.start_day, self.client.start_day + datetime.timedelta(days=31)))


class TestVieScolaireClient(unittest.TestCase):
    client: pronotepy.VieScolaireClient

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = pronotepy.VieScolaireClient('https://demo.index-education.net/pronote/viescolaire.html',
                                                 'demonstration2', 'pronotevs')

    def test_classes(self) -> None:
        self.assertGreater(len(self.client.classes), 0)

        for cls in self.client.classes:
            self.assertIsNotNone(cls.name)

        for student in self.client.classes[0].students():
            self.assertIsInstance(student.identity, pronotepy.Identity)
            self.assertGreater(len(student.guardians), 0)
            for guardian in student.guardians:
                self.assertIsInstance(guardian.identity, pronotepy.Identity)


class TestClientInfo(unittest.TestCase):
    info: pronotepy.ClientInfo

    @classmethod
    def setUpClass(cls) -> None:
        global client
        cls.info = client.info

    def test_address(self) -> None:
        address = self.info.address
        self.assertIsNotNone(address, "Address was None")
        self.assertEqual(len(address), 8, "Address information was not 8 elements long")
        for i in address:
            self.assertTrue(type(i) == str, f"Address information was not a string: {i}")

    def test_ine_number(self) -> None:
        self.assertEqual(self.info.ine_number, "001")

    def test_phone(self) -> None:
        self.assertRegex(self.info.phone, "\+[0-9]+")

    def test_email(self) -> None:
        self.assertRegex(
            self.info.email,
            "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
            "email did not match regex"
        )


if __name__ == '__main__':
    unittest.main()
