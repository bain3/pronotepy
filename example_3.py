import pronotepy

import datetime
from pathlib import Path
import json

# Gestion du fichier ODF (LibreOffice)
from odf.opendocument import load
from odf.table import Table, TableRow, TableCell
from odf.text import P
path_ods = Path('C:\\','Users','legui','Documents','Organisation famille','Anatole_4eme_v3.ods')

# Objectif de l'exemple : 
#    - Parcours des données du trimestre en cours
#    - Conversion avec la présentation d'un bulletin possible (poles qui regroupent les matières)
#    - Mise à jour d'un fichier ODS (LibreOffice) avec le bulletin

bulletin = [
    {
        'name': 'Pole artistique',
        'subjects': ['Arts Plastiques', 'Éducation musicale'],
        'subjects_average': {},
        'average': None,
        'ods': {'row': 2, 'cell': 7},
    },
    {
        'name': 'Pole littéraire',
        'subjects': ['Anglais LV1', 'Allemand LV2', 'Français', 'Histoire-Géographie EMC'],
        'subjects_average': {},
        'average': None,
        'ods': {'row': 5, 'cell': 7},
    },
    {
        'name': 'Pole scientifique',
        'subjects': ['Mathématiques', 'Physique-Chimie', 'Science Vie et Terre', 'Technologie'],
        'subjects_average': {},
        'average': None,
        'ods': {'row': 10, 'cell': 7},
    },
    {
        'name': 'Pole sportif',
        'subjects': ['Éducation Physique et Sportive'],
        'subjects_average': {},
        'average': None,
        'ods': {'row': 15, 'cell': 7},
    },
]

correspondance_matieres_pronote_vers_bulletin = {
    "HISTOIRE-GEOGRAPHIE": "Histoire-Géographie EMC",
    "ARTS PLASTIQUES": "Arts Plastiques",
    "PHYS-CHIM": "Physique-Chimie",
    "ALLEMAND LV1": "Allemand LV2",
    "MATHEMATIQUES": "Mathématiques",
    "ANGLAIS": "Anglais LV1",
    "SCIENCES VIE&TERRE": "Science Vie et Terre",
    "FRANCAIS": "Français",
    "EDUCATION MUSICALE": "Éducation musicale",
    "TECHNOLOGIE": "Technologie",
    "ED.PHYSIQUE & SPORTIVE": "Éducation Physique et Sportive"
}

correspondance_matieres_bulletin_vers_pronote = {v:k for k,v in correspondance_matieres_pronote_vers_bulletin.items()}

def print_grades_bulletin(grades):
    if grades:
        print(f'{"-"*20} Grades bulletin {"-"*20}')
        for pole in bulletin:
            # print(pole)
            print(pole['name'])
            for bulletin_subject in pole['subjects']:
                if bulletin_subject in correspondance_matieres_bulletin_vers_pronote:
                    pronote_subject = correspondance_matieres_bulletin_vers_pronote[bulletin_subject]
                    no_grade = True
                    for grade in grades:  # iterate over all the grades
                        if grade.subject.name == pronote_subject:
                            no_grade = False
                            if float(grade.coefficient) > 1:
                                print(f'{' '*5}{bulletin_subject} : {grade.grade}/{grade.out_of} le {grade.date.strftime("%d/%m/%Y")} (coef. {float(grade.coefficient)})')  # print out the grade in this style: 20/20
                            else:
                                print(f'{' '*5}{bulletin_subject} : {grade.grade}/{grade.out_of} le {grade.date.strftime("%d/%m/%Y")}')  # print out the grade in this style: 20/20
                    if no_grade:
                        print(f'{' '*5}{bulletin_subject} : -')
                else:
                    print(f'{' '*5}{bulletin_subject} : -')

def compute_pole_averages(averages):
    if averages:
        for pole in bulletin:
            # print(pole)
            pole_averages = list()
            for bulletin_subject in pole['subjects']:
                if bulletin_subject in correspondance_matieres_bulletin_vers_pronote:
                    pronote_subject = correspondance_matieres_bulletin_vers_pronote[bulletin_subject]
                    for average in averages:  # iterate over all the averages
                        if average.subject.name == pronote_subject:
                            pole_averages.append( float(average.student.replace(',','.'))/int(average.out_of) )
                            pole['subjects_average'][bulletin_subject] = f'{average.student}/{average.out_of}'
            if len(pole_averages):
                pole['average'] = f'{sum(pole_averages)/len(pole_averages)*20:.2f}/20'
            #print(pole)

def write_cell_in_ods(cell, value):
    # Modifier la valeur de la cellule
    cell.setAttribute("valuetype", "float")
    cell.setAttribute("value", value)

    # Ajouter un élément de texte pour afficher la valeur
    p = P(text=value)
    cell.addElement(p)

def select_row_cell_in_sheet(sheet, row_index, cell_index):
    # Accéder à la 'row_index + 1' ligne
    rows = sheet.getElementsByType(TableRow)
    row = rows[row_index]

    # Accéder à la 'cell_index + 1' cellule
    cells = row.getElementsByType(TableCell)
    cell = cells[cell_index]
    return cell

def write_delays_bulletin_to_ods(delays):
    if delays:
        # Charger le fichier Calc
        doc = load(path_ods)

        # Accéder à la première feuille
        sheets = doc.spreadsheet.getElementsByType(Table)
        sheet = sheets[0]

        cell = select_row_cell_in_sheet(sheet, 20, 7)
        write_cell_in_ods(cell, str(len(delays)))
        print(f"Ecriture ODS : Retards (20, 7) = {len(delays)}")

        doc.save(path_ods)

def write_bulletin_to_ods():
    # Charger le fichier Calc
    doc = load(path_ods)

    # Accéder à la première feuille
    sheets = doc.spreadsheet.getElementsByType(Table)
    sheet = sheets[0]

    for pole in bulletin:
        # print(pole)
        row_index = pole['ods']['row']
        cell_index = pole['ods']['cell']
        if pole['average']:
            # Write pole average
            cell = select_row_cell_in_sheet(sheet, row_index, cell_index)
            write_cell_in_ods(cell, pole['average'])
            print(f"Ecriture ODS : {pole['name']} ({cell_index}, {row_index}) = {pole['average'].replace(',','.')}")
        for bulletin_subject in pole['subjects']:
            # Write subject average
            row_index += 1
            if bulletin_subject in pole['subjects_average']:
                cell = select_row_cell_in_sheet(sheet, row_index, cell_index)
                write_cell_in_ods(cell, pole['subjects_average'][bulletin_subject].replace(',','.'))
                print(f"Ecriture ODS : {bulletin_subject} ({cell_index}, {row_index}) = {pole['subjects_average'][bulletin_subject].replace(',','.')}")

    # Sauvegarder le document modifié
    #doc.save(path_ods[:-4]+"_bak"+path_ods[-4:])
    doc.save(path_ods)

def print_averages_bulletin(averages):
    if averages:
        print(f'{"-"*20} Averages bulletin {"-"*20}')
        compute_pole_averages(averages)
        for pole in bulletin:
            # print(pole)
            if 'average' in pole and pole['average']:
                print(f'{pole['name']} : {pole['average']}')
            else:
                print(f'{pole['name']}')
            for bulletin_subject in pole['subjects']:
                if bulletin_subject in correspondance_matieres_bulletin_vers_pronote:
                    pronote_subject = correspondance_matieres_bulletin_vers_pronote[bulletin_subject]
                    no_average = True
                    for average in averages:  # iterate over all the averages
                        if average.subject.name == pronote_subject:
                            no_average = False
                            print(f'{' '*5}{bulletin_subject} : {average.student}/{average.out_of}')  # print out the average in this style: 20/20
                    if no_average:
                        print(f'{' '*5}{bulletin_subject} : -')
                else:
                    print(f'{' '*5}{bulletin_subject} : -')

def print_absences_bulletin(absences):
    if absences:
        print(f'{"-"*20} Absences {"-"*20}')
        for absence in absences:
            #print(f'absence = {absence.to_dict()}')
            print(f'- {absence.from_date.strftime("%d/%m/%Y at %Hh%M")} to {absence.to_date.strftime("%Hh%M")}')

def print_delays_bulletin(delays):
    if delays:
        print(f'{"-"*20} Delays {"-"*20}')
        print(f'Nombre de retards : {len(delays)}')

def print_punishments_bulletin(punishments):
    if punishments:
        print(f'{"-"*20} Punishments {"-"*20}')
        for punishment in punishments:
            #print(f'punishment = {punishment.to_dict()}')
            print(f'- Gave by {punishment.giver} at {punishment.given.strftime("%d/%m/%Y at %Hh%M")}')
            print(f'  circumstances : {punishment.circumstances}')
            print(f'  {punishment.nature} : ')
            for schedule in punishment.schedule:
                print(f'    - le {schedule.start.strftime("%d/%m/%Y at %Hh%M")}')

def print_period_bulletin(period):
    #print(f'Period = {period.to_dict()}')
    print(f'{"#"*20} {period.name} {"#"*20}')
    
    print_grades_bulletin(period.grades)
    print_averages_bulletin(period.averages)
    
    print_absences_bulletin(period.absences)
    print_delays_bulletin(period.delays)
    print_punishments_bulletin(period.punishments)

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
    print_period_bulletin(current_period)
    write_bulletin_to_ods()
    write_delays_bulletin_to_ods(current_period.delays)

    
else: 
    print("Failed to log in")
    exit()
