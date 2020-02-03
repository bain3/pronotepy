import pronotepy
import logging
import datetime

logger = logging.getLogger(pronotepy.pronoteAPI.__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logfile = logging.FileHandler('api.log')
logfile.setFormatter(formatter)
logfile.setLevel(logging.DEBUG)
stream = logging.StreamHandler()
stream.setLevel(20)
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
stream.setFormatter(formatter)
logger.addHandler(logfile)
logger.addHandler(stream)

# example
test = pronotepy.ClientStudent('https://demo.index-education.net/pronote/eleve.html')
if test.login('demonstration', 'pronotevs'):
    print('Student login...OK')

    periods = test.current_periods()

    print('Grades...', end='')
    for period in periods:
        g = period.grades()
    print('OK')

    print('Averages...', end='')
    for period in periods:
        a = period.averages()
    print('OK')

    print('Homework...', end='')
    h = test.homework(datetime.date(2019, 9, 8))
    h[0].set_done(True)
    print('OK')

    print('Lessons...', end='')
    lessons = test.lessons(datetime.date(2019, 9, 8), datetime.date(2019, 10, 8))
    print('OK')

test = pronotepy.ClientTeacher('https://demo.index-education.net/pronote/professeur.html')
if test.login('demonstration', 'pronotevs'):
    print('Teacher login...OK')
    print('Lessons...', end='')
    lessons = test.lessons(datetime.date(2019, 9, 8), datetime.date(2019, 10, 8))
    print('OK')
