"""Surveiller rapidement les notes et les moyennes Pronote."""

import sys
import datetime
from pathlib import Path
import json

import pronotepy

bulletin = [{'name': 'Pole artistique',
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

correspondance_matieres_pronote_vers_bulletin = {
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

correspondance_matieres_bulletin_vers_pronote = {
    v: k for k, v in correspondance_matieres_pronote_vers_bulletin.items()}


def print_grades_bulletin(grades):
    if grades:
        print(f'{"-" * 20} Grades Report Card {"-" * 20}')
        for pole in bulletin:
            # print(pole)
            print(pole['name'])
            for bulletin_subject in pole['subjects']:
                if bulletin_subject in correspondance_matieres_bulletin_vers_pronote:
                    pronote_subject = correspondance_matieres_bulletin_vers_pronote[
                        bulletin_subject]
                    no_grade = True
                    for grade in grades:  # iterate over all the grades
                        if grade.subject.name == pronote_subject:
                            no_grade = False
                            print_grade(bulletin_subject, grade)
                            save_grade(pole, bulletin_subject, grade)
                    if no_grade:
                        print(f'{' ' * 5}{bulletin_subject} : -')
                else:
                    print(f'{' ' * 5}{bulletin_subject} : -')

def print_grade(subject, grade):
    "print out the grade in this style: 20/20"
    if float(grade.coefficient) != 1:
        print(f'{' '*5}{subject} : {grade.grade}/{grade.out_of} le {
            grade.date.strftime("%d/%m/%Y")} (coef. {float(grade.coefficient)})')
    else:
        print(f'{' '*5}{subject} : {grade.grade}/{grade.out_of} le {
            grade.date.strftime("%d/%m/%Y")}')

def save_grade(pole, subject, grade):
    if subject not in pole['subjects_grades']:
        pole['subjects_grades'][subject] = []
    try:
        coef = float(grade.coefficient.replace(',','.'))
        grade = round( float(grade.grade.replace(',','.')) / float(
            grade.out_of.replace(',','.')) *20, 2) /20
        pole['subjects_grades'][subject].append({'coefficient': coef, 'grade': grade})
    except ValueError:
        # If grade.grade not float, no grade to record.
        pass

def print_last_grade_date(grades):
    if grades:
        last_date = datetime.date(1, 1, 1)
        for grade in grades:  # iterate over all the grades
            last_date = max(last_date, grade.date)
        if last_date != datetime.date(1, 1, 1):
            print(f'{"-" * 20} Last Grades {"-" * 20}')
            print(f'Dernère note le {last_date.strftime("%d/%m/%Y")}')


def compute_pole_averages(averages):
    if averages:
        for pole in bulletin:
            # print(pole)
            pole_averages = []
            for bulletin_subject in pole['subjects']:
                if bulletin_subject in correspondance_matieres_bulletin_vers_pronote:
                    pronote_subject = correspondance_matieres_bulletin_vers_pronote[
                        bulletin_subject]
                    for average in averages:  # iterate over all the averages
                        if average.subject.name == pronote_subject:
                            f_average = float(average.student.replace(',','.'))/int(average.out_of)
                            pole_averages.append( f_average )
                            s_average = f'{average.student}/{average.out_of}'
                            pole['subjects_average'][bulletin_subject] = s_average
            if pole_averages:
                pole['average'] = f'{
                    sum(pole_averages) /
                    len(pole_averages) *
                    20:.2f}/20'
            # print(pole)


def print_averages_bulletin(averages):
    if averages:
        print(f'{"-" * 20} Averages bulletin {"-" * 20}')
        compute_pole_averages(averages)
        for pole in bulletin:
            # print(pole)
            if 'average' in pole and pole['average']:
                print(f'{pole['name']} : {pole['average']}')
            else:
                print(f'{pole['name']}')
            for bulletin_subject in pole['subjects']:
                if bulletin_subject in correspondance_matieres_bulletin_vers_pronote:
                    pronote_subject = correspondance_matieres_bulletin_vers_pronote[
                        bulletin_subject]
                    no_average = True
                    for average in averages:  # iterate over all the averages
                        if average.subject.name == pronote_subject:
                            no_average = False
                            print_average(bulletin_subject, average)
                    if no_average:
                        print_average(bulletin_subject, None)
                else:
                    print_average(bulletin_subject, None)

def print_average(subject, average):
    if average:
        print(f'{' ' * 5}{subject} : {average.student}/{average.out_of}')
    else:
        print(f'{' ' * 5}{subject} : -')

def print_absences_bulletin(absences):
    if absences:
        print(f'{"-" * 20} Absences {"-" * 20}')
        for absence in absences:
            #print(f'absence = {absence.to_dict()}')
            print(f'- {absence.from_date.strftime("%d/%m/%Y at %Hh%M")
                       } to {absence.to_date.strftime("%Hh%M")}')

def print_delays_bulletin(delays):
    if delays:
        print(f'{"-" * 20} Delays {"-" * 20}')
        print(f'Nombre de retards : {len(delays)}')


def print_punishments_bulletin(punishments):
    if punishments:
        print(f'{"-" * 20} Punishments {"-" * 20}')
        for punishment in punishments:
            #print(f'punishment = {punishment.to_dict()}')
            print(f'- Gave by {punishment.giver} at {
                punishment.given.strftime("%d/%m/%Y at %Hh%M")}')
            print(f'  circumstances : {punishment.circumstances}')
            print(f'  {punishment.nature} : ')
            for schedule in punishment.schedule:
                print(f'    - le {schedule.start.strftime("%d/%m/%Y at %Hh%M")}')

def print_period_bulletin(period):
    # print(f'Period = {period.to_dict()}')
    print(f'{"#" * 20} {period.name} {"#" * 20}')

    print_grades_bulletin(period.grades)
    print_averages_bulletin(period.averages)
    print_last_grade_date(period.grades)


def print_new_subject(period):
    for average in period.averages:
        if average.subject.name not in correspondance_matieres_pronote_vers_bulletin:
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

    current_period = client.current_period
    print_period_bulletin(current_period)

    print_new_subject(current_period)

    input("Appuyez sur Entrée pour quitter...")

else:
    print("Failed to log in")
    sys.exit()
