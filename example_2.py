import pronotepy

import datetime
from pathlib import Path
import json

# Objectif de l'exemple : 
#    - Parcours des données du trimestre en cours
#    - Mise en forme des informations.

def print_grades(grades):
    if grades:
        print(f'{"-"*20} Grades {"-"*20}')
        for grade in grades:  # iterate over all the grades
            #print(f'Grade = {grade.to_dict()}')
            if float(grade.coefficient) > 1:
                print(f'{grade.subject.name} : {grade.grade}/{grade.out_of} (coef. {float(grade.coefficient)})')  # print out the grade in this style: 20/20
            else:
                print(f'{grade.subject.name} : {grade.grade}/{grade.out_of}')  # print out the grade in this style: 20/20

def print_report(report):
    if report:
        print(f'report : {report}')


def print_averages(averages):
    if averages:
        print(f'{"-"*20} Averages {"-"*20}')
        for average in averages:
            #print(f'average = {average.to_dict()}')
            print(f'{average.subject.name} : {average.student}/{average.out_of}')

def print_overall_average(overall_average):
    if overall_average:
        print(f'{"-"*20} Overall Averages {"-"*20}')
        print(f'overall average = {overall_average}')

def print_class_overall_average(class_overall_average):
    if class_overall_average:
        print(f'class overall average = {class_overall_average}')

def print_evaluations(evaluations):
    if evaluations:
        print(f'{"-"*20} Evaluations {"-"*20}')
        for evaluation in evaluations:
            #print(f'evaluation = {evaluation.to_dict()}')
            print(f"{evaluation.subject.name} ({evaluation.date.strftime("%d/%m/%Y")})")
            for acquisition in evaluation.acquisitions:
                if acquisition.domain:
                    print(f"     {acquisition.domain}")
                if acquisition.name:
                    print(f"     {acquisition.name}")
                if acquisition.level:
                    print(f"     {acquisition.level}")
                print()

def print_absences(absences):
    if absences:
        print(f'{"-"*20} Absences {"-"*20}')
        for absence in absences:
            #print(f'absence = {absence.to_dict()}')
            print(f'- {absence.from_date.strftime("%d/%m/%Y at %Hh%M")} to {absence.to_date.strftime("%Hh%M")}')

def print_delays(delays):
    if delays:
        print(f'{"-"*20} Delays {"-"*20}')
        for delay in delays:
            #print(f'delay = {delay.to_dict()}')
            print(f'- {delay.date.strftime("%d/%m/%Y at %Hh%M")}')

def print_punishments(punishments):
    if punishments:
        print(f'{"-"*20} Punishments {"-"*20}')
        for punishment in punishments:
            #print(f'punishment = {punishment.to_dict()}')
            print(f'- Gave by {punishment.giver} at {punishment.given.strftime("%d/%m/%Y at %Hh%M")}')
            print(f'  circumstances : {punishment.circumstances}')
            print(f'  {punishment.nature} : ')
            for schedule in punishment.schedule:
                print(f'    - le {schedule.start.strftime("%d/%m/%Y at %Hh%M")}')

def print_period(period):
    #print(f'Period = {period.to_dict()}')
    print(f'{"#"*20} Periode : {period.name} {"#"*20}')
    
    print_grades(period.grades)
    print_report(period.report)
    print_averages(period.averages)
    print_overall_average(period.overall_average)
    print_class_overall_average(period.class_overall_average)
    
    print_evaluations(period.evaluations)
    print_absences(period.absences)
    print_delays(period.delays)
    print_punishments(period.punishments)

def print_homework(homework):
    if len(homework):
        print(f'\r\n{"#"*30} Homework {"#"*30}')
    for hw in homework: # iterate through the list
        print(f"\r\n{"-"*20} {hw.subject.name} {"-"*20}") # print the homework's subject, title and description
        print(f"{hw.description}") # print the homework's subject, title and description
    
# load login from `python3 -m pronotepy.create_login` command
# See quickstart in documentation for other login methods.
credentials = json.loads(Path("credentials.json").read_text())

client = pronotepy.Client.token_login(**credentials)

if client.logged_in: # check if client successfully logged in

    # save new credentials - IMPORTANT
    credentials = client.export_credentials()
    Path("credentials.json").write_text(json.dumps(credentials))

    nom_utilisateur = client.info.name # get users name
    print(f'Logged in as {nom_utilisateur}')
    
    current_period = client.current_period
    print_period(current_period)

    today = datetime.date.today() # store today's date using datetime built-in library
    homework = client.homework(today) # get list of homework for today and later
    print_homework(homework)
    
else: 
    print("Failed to log in")
    exit()
