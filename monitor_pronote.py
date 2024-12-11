"""Surveiller rapidement les notes et les moyennes Pronote."""

import sys
import datetime
from pathlib import Path
import json
from datetime import datetime as dt

import pronotepy

report_card = [{'name': 'Pole artistique',
                'subjects': ['Arts Plastiques',
                             'Éducation musicale'],
                'subjects_average': {},
                'subjects_grades': {},
                'average': None,
                },
               {'name': 'Pole littéraire',
                'subjects': ['Anglais LV1',
                             'Allemand LV2',
                             'Français',
                             'Histoire-Géographie EMC'],
                'subjects_average': {},
                'subjects_grades': {},
                'average': None,
                },
               {'name': 'Pole scientifique',
                'subjects': ['Mathématiques',
                             'Physique-Chimie',
                             'Science Vie et Terre',
                             'Technologie'],
                'subjects_average': {},
                'subjects_grades': {},
                'average': None,
                },
               {'name': 'Pole sportif',
                'subjects': ['Éducation Physique et Sportive'],
                'subjects_average': {},
                'subjects_grades': {},
                'average': None,
                },
               ]

correspondance_matieres_pronote_vers_report_card = {
    'HISTOIRE-GEOGRAPHIE': 'Histoire-Géographie EMC',
    'ARTS PLASTIQUES': 'Arts Plastiques',
    'PHYS-CHIM': 'Physique-Chimie',
    'ALLEMAND LV1': 'Allemand LV2',
    'ALLEMAND': 'Allemand LV2',
    'MATHEMATIQUES': 'Mathématiques',
    'ANGLAIS': 'Anglais LV1',
    'SCIENCES VIE&TERRE': 'Science Vie et Terre',
    "FRANCAIS": "Français",
    "EDUCATION MUSICALE": "Éducation musicale",
    "TECHNOLOGIE": "Technologie",
    "ED.PHYSIQUE & SPORTIVE": "Éducation Physique et Sportive"
}

correspondance_matieres_report_card_vers_pronote = {
    v: k for k, v in correspondance_matieres_pronote_vers_report_card.items()}


def clean_report_card():
    for pole in report_card:
        pole['subjects_average'].clear()
        pole['subjects_grades'].clear()
        pole['average'] = None

def print_grades_report_card(grades):
    if grades:
        print(f'{"-" * 20} Report Card Grades {"-" * 20}')
        for pole in report_card:
            # print(pole)
            print(pole['name'])
            for report_card_subject in pole['subjects']:
                if report_card_subject in correspondance_matieres_report_card_vers_pronote:
                    pronote_subject = correspondance_matieres_report_card_vers_pronote[
                        report_card_subject]
                    no_grade = True
                    for grade in grades:  # iterate over all the grades
                        if grade.subject.name == pronote_subject:
                            no_grade = False
                            print_grade(report_card_subject, grade)
                            save_grade(pole, report_card_subject, grade)
                    if no_grade:
                        print(f'{' ' * 5}{report_card_subject} : -')
                else:
                    print(f'{' ' * 5}{report_card_subject} : -')


def print_grade(subject, grade):
    "print out the grade in this style: 20/20"
    if float(grade.coefficient) != 1:
        print(f'{' ' * 5}{subject} : {grade.grade}/{grade.out_of} le {
            grade.date.strftime("%d/%m/%Y")} (coef. {float(grade.coefficient)})')
    else:
        print(f'{' ' * 5}{subject} : {grade.grade}/{grade.out_of} le {
            grade.date.strftime("%d/%m/%Y")}')
    # print(f'{'*'*20} le {grade.date.strftime("%d/%m/%Y")}')


def save_grade(pole, subject, grade):
    if subject not in pole['subjects_grades']:
        pole['subjects_grades'][subject] = []
    try:
        coef = float(grade.coefficient.replace(',', '.'))
        grade = round(float(grade.grade.replace(',', '.')) / float(
            grade.out_of.replace(',', '.')) * 20, 2) / 20
        pole['subjects_grades'][subject].append(
            {'coefficient': coef, 'grade': grade})
    except ValueError:
        # If grade.grade not float, no grade to record.
        pass


def print_last_grade_date(grades):
    print(f'{"-" * 20} Last Grades {"-" * 20}')
    if grades:
        last_grade = None
        for grade in grades:  # iterate over all the grades
            if last_grade is None:
                last_grade = grade
                continue
            elif last_grade.date < grade.date:
                last_grade = grade
        if last_grade:
            report_card_subject = correspondance_matieres_pronote_vers_report_card[
                        last_grade.subject.name]
            print(f'Dernière note : {report_card_subject} {last_grade.grade}/{last_grade.out_of
                  } le {last_grade.date.strftime("%d/%m/%Y")}')
        else:
            print("Pas de dernière note.")


def compute_pole_averages(averages):
    if averages:
        for pole in report_card:
            # print(pole)
            pole_averages = []
            for report_card_subject in pole['subjects']:
                if report_card_subject in correspondance_matieres_report_card_vers_pronote:
                    pronote_subject = correspondance_matieres_report_card_vers_pronote[
                        report_card_subject]
                    for average in averages:  # iterate over all the averages
                        if average.subject.name == pronote_subject:
                            f_average = float(average.student.replace(',','.'))/int(average.out_of)
                            pole_averages.append( f_average )
                            s_average = f'{average.student}/{average.out_of}'
                            pole['subjects_average'][report_card_subject] = s_average
            if pole_averages:
                pole['average'] = f'{
                    sum(pole_averages) /
                    len(pole_averages) *
                    20:.2f}/20'
            # print(pole)


def print_averages_report_card(averages):
    if averages:
        print(f'{"-" * 20} Report Card Averages {"-" * 20}')
        compute_pole_averages(averages)
        for pole in report_card:
            # print(pole)
            if 'average' in pole and pole['average']:
                print(f'{pole['name']} : {pole['average']}')
            else:
                print(f'{pole['name']}')
            for report_card_subject in pole['subjects']:
                if report_card_subject in correspondance_matieres_report_card_vers_pronote:
                    pronote_subject = correspondance_matieres_report_card_vers_pronote[
                        report_card_subject]
                    no_average = True
                    for average in averages:  # iterate over all the averages
                        if average.subject.name == pronote_subject:
                            no_average = False
                            print_average(report_card_subject, average)
                    if no_average:
                        print_average(report_card_subject, None)
                else:
                    print_average(report_card_subject, None)


def print_average(subject, average):
    if average:
        print(f'{' ' * 5}{subject} : {average.student}/{average.out_of}')
    else:
        print(f'{' ' * 5}{subject} : -')


def print_absences_report_card(absences):
    if absences:
        print(f'{"-" * 20} Absences {"-" * 20}')
        for absence in absences:
            # print(f'absence = {absence.to_dict()}')
            print(f'- {absence.from_date.strftime("%d/%m/%Y at %Hh%M")
                       } to {absence.to_date.strftime("%Hh%M")}')


def print_delays_report_card(delays):
    if delays:
        print(f'{"-" * 20} Delays {"-" * 20}')
        print(f'Nombre de retards : {len(delays)}')


def print_punishments_report_card(punishments):
    if punishments:
        print(f'{"-" * 20} Punishments {"-" * 20}')
        for punishment in punishments:
            # print(f'punishment = {punishment.to_dict()}')
            print(f'- Gave by {punishment.giver} at {
                punishment.given.strftime("%d/%m/%Y at %Hh%M")}')
            print(f'  circumstances : {punishment.circumstances}')
            print(f'  {punishment.nature} : ')
            for schedule in punishment.schedule:
                print(f'    - le {schedule.start.strftime("%d/%m/%Y at %Hh%M")}')

def print_period_report_card(period):
    # print(f'Period = {period.to_dict()}')
    print(f'{"#" * 20} {period.name} {"#" * 20}')

    print_grades_report_card(period.grades)
    print_averages_report_card(period.averages)
    if dt.now() <= period.end:
        print_last_grade_date(period.grades)


def print_new_subject(period):
    for average in period.averages:
        if average.subject.name not in correspondance_matieres_pronote_vers_report_card:
            print(f"La discipline '{average.subject.name}' est introuvable dans la table de "
                  "conversion 'pronote' <=> 'report_card' (corriger le fichier "
                  "'the_school_award\\report_card.json')")


# load login from `python3 -m pronotepy.create_login` command
# See quickstart in documentation for other login methods.
credentials = json.loads(Path("credentials.json").read_text(encoding='utf-8'))

client = pronotepy.Client.token_login(**credentials)

if client.logged_in:  # check if client successfully logged in

    # save new credentials - IMPORTANT
    credentials = client.export_credentials()
    Path("credentials.json").write_text(json.dumps(credentials), encoding='utf-8')

    nom_utilisateur = client.info.name  # get users name
    print(f'Logged in as {nom_utilisateur}')

    now = dt.now()
    for period in client.periods:
        # Period.name : 'Trimestre x', 'Semestre x', 'Annee continue' ...
        if not period.name.startswith('Trimestre'):
            continue
        if period.start <= now:
            clean_report_card()
            print_period_report_card(period)
            print_new_subject(period)

    input("Appuyez sur Entrée pour quitter...")

else:
    print("Failed to log in")
    sys.exit()
