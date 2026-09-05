import pronotepy

from pathlib import Path
import json

import tkinter as tk

# Objectif de l'exemple : 
#    - Parcours des données du trimestre en cours
#    - Conversion avec la présentation d'un bulletin possible (poles qui regroupent les matières)
#    - Affichage d'une IHM qui représente le bulletin (codage monolitique)
#    - TODO : Applications de rêgles pour gagner une récompense/cagnotte
#    - TODO : Affichage dans l'IHM de l'état de gain de la récompense et du niveau de la cagnotte
#    - TODO : Définir une configuration de récompense/cagnotte (Marathon)
#                - Banco : Récompense sur un trimestre
#                - Marathon : Récompense cumulée sur plusieurs trimestres
#                - Boost : Multiplicateur de gain sur un pôle


bulletin = {
    'averages' : [
        {
            'name': 'Pole artistique',
            'subjects': ['Arts Plastiques', 'Éducation musicale'],
            'subjects_average': {},
            'average': None,
        },
        {
            'name': 'Pole littéraire',
            'subjects': ['Anglais LV1', 'Allemand LV2', 'Français', 'Histoire-Géographie EMC'],
            'subjects_average': {},
            'average': None,
        },
        {
            'name': 'Pole scientifique',
            'subjects': ['Mathématiques', 'Physique-Chimie', 'Science Vie et Terre', 'Technologie'],
            'subjects_average': {},
            'average': None,
        },
        {
            'name': 'Pole sportif',
            'subjects': ['Éducation Physique et Sportive'],
            'subjects_average': {},
            'average': None,
        },
    ],
    'delays' : None
}

correspondance_matieres_pronote_vers_bulletin = {
    'HISTOIRE-GEOGRAPHIE': 'Histoire-Géographie EMC',
    'ARTS PLASTIQUES': 'Arts Plastiques',
    'PHYS-CHIM': 'Physique-Chimie',
    'ALLEMAND LV1': 'Allemand LV2',
    'MATHEMATIQUES': 'Mathématiques',
    'ANGLAIS': 'Anglais LV1',
    'SCIENCES VIE&TERRE': 'Science Vie et Terre',
    "FRANCAIS": "Français",
    "EDUCATION MUSICALE": "Éducation musicale",
    "TECHNOLOGIE": "Technologie",
    "ED.PHYSIQUE & SPORTIVE": "Éducation Physique et Sportive"
}

correspondance_matieres_bulletin_vers_pronote = {v:k for k,v in correspondance_matieres_pronote_vers_bulletin.items()}

def compute_pole_averages(averages):
    if averages:
        for pole in bulletin['averages']:
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
                pole['average'] = f'{sum(pole_averages)/len(pole_averages)*20:.2f}/20'.replace('.',',')
            #print(pole)

def compute_pole_delays(delays):
    if delays:
        bulletin['delays'] = len(delays)

def tk_bulletin():
    fenetre = tk.Tk()
    fenetre.title('old')
    fenetre.resizable(False, False)

    # frame 'bulletin'
    pole_frame_bulletin = tk.Frame(fenetre, relief=tk.GROOVE)
    pole_frame_bulletin.pack(side=tk.TOP)
    for pole in bulletin['averages']:
        # Convert 'average' to float
        bg=None
        if 'average' in pole and pole['average']:
            average_float = float(pole['average'].split('/')[0].replace(',','.'))
            if average_float >= 15.0:
                bg='SpringGreen'
            elif average_float >= 13.0:
                bg='LightGreen'
            labelframe = tk.LabelFrame(pole_frame_bulletin, text=f"{pole['name']} : {pole['average']}", background=bg)
        else:
            labelframe = tk.LabelFrame(pole_frame_bulletin, text=f"{pole['name']}")
        labelframe.pack(fill="both", expand="yes", padx=5, pady=5)

        # frame 'subjects'
        pole_frame_subjects = tk.Frame(labelframe, relief=tk.GROOVE, background=bg, padx=5)
        pole_frame_subjects.pack(side=tk.LEFT)
        # frame 'grades'
        pole_frame_grades = tk.Frame(labelframe, relief=tk.GROOVE, background=bg, padx=5)
        pole_frame_grades.pack(side=tk.RIGHT)

        for bulletin_subject in pole['subjects']:
            tk.Label(pole_frame_subjects, text=bulletin_subject, background=bg, anchor='w').pack(fill='x')
            subjects_fg=None
            if bulletin_subject in pole['subjects_average']:
                subjects_average_float = float(pole['subjects_average'][bulletin_subject].split('/')[0].replace(',','.'))
                if average_float >= 15.0 > subjects_average_float:
                    subjects_fg='Red'
                elif average_float >= 13.0 > subjects_average_float:
                    subjects_fg='Red'
                tk.Label(pole_frame_grades, text=pole['subjects_average'][bulletin_subject], background=bg, anchor='e', foreground=subjects_fg).pack(fill='x')
            else:
                tk.Label(pole_frame_grades, text='-', background=bg, anchor='e').pack(fill='x')

    if 'delays' in bulletin and bulletin['delays'] != None:
        # frame 'retards'
        frame_retards = tk.Frame(fenetre, relief=tk.GROOVE)
        frame_retards.pack(side=tk.BOTTOM)

        bg=None
        if bulletin['delays'] == 0:
            bg='SpringLight'
        elif bulletin['delays'] <= 5:
            bg='LightGreen'
        tk.Label(frame_retards, text=f"retards : {bulletin['delays']}", background=bg, anchor='w').pack(fill='x')

    fenetre.mainloop()


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
    compute_pole_averages(current_period.averages)
    compute_pole_delays(current_period.delays)
    tk_bulletin()
    
else: 
    print("Failed to log in")
    exit()
