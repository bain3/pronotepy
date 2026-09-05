"""Vérifie les moyennes Pronote et indique l'écart avec le calcul théorique."""
import sys
from pathlib import Path
import json
from datetime import datetime as dt

import pronotepy

# Objectif de l'exemple :
#    - Parcours des données du trimestre en cours
#    - Conversion avec la présentation d'un bulletin possible (poles qui regroupent les matières)

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


def compute_pole_grades(grades):
    if grades:
        for pole in bulletin:
            pole['subjects_average'].clear()
            pole['subjects_grades'].clear()
            for bulletin_subject in pole['subjects']:
                if bulletin_subject in correspondance_matieres_bulletin_vers_pronote:
                    pronote_subject = correspondance_matieres_bulletin_vers_pronote[
                        bulletin_subject]
                    for grade in grades:  # iterate over all the grades
                        if grade.subject.name == pronote_subject:
                            save_grade(pole, bulletin_subject, grade)


def save_grade(pole, subject, grade):
    if subject not in pole['subjects_grades']:
        pole['subjects_grades'][subject] = []
    try:
        f_coef = float(grade.coefficient.replace(',', '.'))
        f_grade = float(grade.grade.replace(',', '.'))
        f_out_of = float(grade.out_of.replace(',', '.'))
        pole['subjects_grades'][subject].append(
            {'coefficient': f_coef, 'grade': f_grade, 'out_of': f_out_of})
    except ValueError:
        # If grade.grade not float, no grade to record.
        pass


def compute_pole_averages(averages):
    if averages:
        for pole in bulletin:
            pole['average'] = None
            pole_averages = get_averages_list(averages, pole)
            if pole_averages:
                pole['average'] = f'{
                    sum(pole_averages) /
                    len(pole_averages) *
                    20:.2f}/20'


def get_averages_list(averages, pole):
    pole_averages = []
    if averages:
        for bulletin_subject in pole['subjects']:
            if bulletin_subject in correspondance_matieres_bulletin_vers_pronote:
                pronote_subject = correspondance_matieres_bulletin_vers_pronote[
                    bulletin_subject]
                for average in averages:  # iterate over all the averages
                    if average.subject.name == pronote_subject:
                        f_average = average_str2float(average)
                        pole_averages.append(f_average)
                        pole['subjects_average'][bulletin_subject] = round(
                            f_average * 20., 2)
                        break
    return pole_averages


def average_str2float(average):
    return float(average.student.replace(',', '.')) / int(average.out_of)


def get_average_calculation(pole, subject):
    if subject not in pole['subjects_grades']:
        return None
    sum_grades = sum_coef = 0
    for grade in pole['subjects_grades'][subject]:
        coef_out_of_20 = grade['coefficient'] * grade['out_of'] / 20.
        sum_grades += grade['grade'] * grade['coefficient']
        sum_coef += coef_out_of_20
    return round(sum_grades / sum_coef, 2)


def print_average_calculation(pole, subject, pronote_average):
    if subject not in pole['subjects_grades']:
        return
    sum_grades = sum_coef = index = 0
    for grade in pole['subjects_grades'][subject]:
        coef_out_of_20 = grade['coefficient'] * grade['out_of'] / 20.
        sum_grades += grade['grade'] * grade['coefficient']
        sum_coef += coef_out_of_20
        index += 1
        print(f'{' '*5}Calculation : grade {index} = {
            grade['grade']} / {grade['out_of']} coef. {grade['coefficient']}')
    average = round(sum_grades / sum_coef, 2)
    if average > pronote_average:
        result = 'You LOSE'
    else:
        result = 'You win'
    print(f'{' ' * 5}Calculation : SUM grades = {sum_grades} for {sum_coef} grades')
    print(f'{' ' * 5}Calculation : average = {average} / 20 {result} {
        round(abs(average - pronote_average), 2)} points.')


def print_average_pronote(pole, subject):
    print(f'{' ' * 5}Pronote{' ' * (len('Calculation') - len('Pronote'))} : average = {
        pole['subjects_average'][subject]} / 20')


def compute_period_bulletin(period):
    compute_pole_grades(period.grades)
    compute_pole_averages(period.averages)


def print_delta_average():
    for pole in bulletin:
        for bulletin_subject in pole['subjects']:
            average_calculation = get_average_calculation(
                pole, bulletin_subject)
            if average_calculation is not None:
                average_pronote = pole['subjects_average'][bulletin_subject]
                if abs(average_calculation - average_pronote) > 0.01:
                    print(f"{bulletin_subject} : !")
                    print_average_calculation(
                        pole, bulletin_subject, average_pronote)
                    print_average_pronote(pole, bulletin_subject)
                else:
                    print(f"{bulletin_subject} : =")
            else:
                print(f"{bulletin_subject} : -")


# load login from `python3 -m pronotepy.create_login` command
# See quickstart in documentation for other login methods.
credentials = json.loads(Path("credentials.json").read_text(encoding='utf-8'))

client = pronotepy.Client.token_login(**credentials)

if client.logged_in:  # check if client successfully logged in

    # save new credentials - IMPORTANT
    credentials = client.export_credentials()
    Path("credentials.json").write_text(
        json.dumps(credentials), encoding='utf-8')

    nom_utilisateur = client.info.name  # get users name
    print(f'Logged in as {nom_utilisateur}')

    now = dt.now()
    report_cards = []
    for period in client.periods:
        # Period.name : 'Trimestre x', 'Semestre x', 'Annee continue' ...
        if not period.name.startswith('Trimestre'):
            continue
        if period.start <= now:
            print(f"{'#' * 20} {period.name} {'#' * 20}")
            compute_period_bulletin(period)
            print_delta_average()

    input("Appuyez sur Entrée pour quitter...")

else:
    print("Failed to log in")
    sys.exit()
