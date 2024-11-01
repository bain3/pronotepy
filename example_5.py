"""
Objectif de l'exemple :
   - Parcours des données du trimestre en cours
   - Conversion avec la présentation d'un bulletin possible (poles qui regroupent les matières)
   - Affichage d'une IHM qui représente le bulletin (codage par classe et héritage)
   - TODO : Applications de rêgles pour gagner une récompense/cagnotte
   - TODO : Affichage dans l'IHM de l'état de gain de la récompense et du niveau de la cagnotte
   - TODO : Définir une configuration de récompense/cagnotte (Marathon)
               - Banco : Récompense sur un trimestre
               - Marathon : Récompense cumulée sur plusieurs trimestres
               - Boost : Multiplicateur de gain sur un pôle
"""

import sys
from pathlib import Path
import json
import tkinter as tk

import pronotepy


class Bulletin():
    """
    Cette classe implémente un bulletin correspondant à celui que produit un
    établissement. Sa forme et son organisation dépendent de chaque
    établissement et sont configurables dans un JSON à fournir.
    """

    def __init__(self, path_configuration_json):
        self.path_configuration_json = path_configuration_json
        with open(path_configuration_json, 'r', encoding='utf-8') as json_file:
            self.configuration = json.load(json_file)
        # print(f"Bulletin - Configuration : {self.configuration}")
        self.convert_pronote2bulletin = self.configuration[
            'correspondance_matieres_pronote_vers_bulletin']
        self.convert_bulletin2pronote = {
            v: k for k, v in self.convert_pronote2bulletin.items()}

    def pole(self, name):
        "Retourne les information d'un pole à partir de son 'nom' donné en parametre"
        for pole in self.poles():
            if name == pole.name():
                return pole
        return None

    def poles(self):
        "Retourne la liste des poles"
        class Pole():
            "Interface pour manipuler un pole de discipline"

            def __init__(self, pole):
                self.pole = pole

            def __str__(self):
                return self.name()

            def name(self):
                "Retourne le nom"
                return self.pole['name']

            def subjects(self):
                "Retourne les disciplines du pole"
                class Subject():
                    """
                    Interface pour manipuler le nom d'une discipline
                    """

                    def __init__(self, subject):
                        self.subject = subject

                    def __str__(self):
                        return self.name()

                    def name(self):
                        "Retourne le nom"
                        return self.subject

                return [Subject(subject) for subject in self.pole['subjects']]

            def subjects_average(self):
                "Retourne les moyennes des disciplines du pole"
                class SubjectAverage():
                    """
                    Interface pour manipuler la moyenne d'une discipline
                    """

                    def __init__(self, subject_average):
                        self.subject_average = subject_average

                    def __str__(self):
                        return f"{self.name()} : {self.average()}"

                    def name(self):
                        "Retourne le nom"
                        # Retourne la premiere clé du dictionnaire
                        # { 'matiere': moyenne }
                        return next(iter(self.subject_average))

                    def average(self):
                        "Retourne la moyenne"
                        return self.subject_average.get(self.name())

                return [SubjectAverage(subject_average)
                        for subject_average in self.pole['subjects_average']]

            def subject_average(self, name):
                "Retourne la moyenne d'une discipline donnée en paramètre"
                if name in self.pole['subjects_average']:
                    return self.pole['subjects_average'].get(name)
                return None

            def write_subject_average(self, name, average):
                "Ecrit la moyenne d'une discipline donnée en paramètre"
                self.pole['subjects_average'][name] = average

            def average(self):
                "Retourne la moyenne du pole de disciplines"
                if self.pole['average']:
                    return self.pole['average']
                return None

            def write_average(self, average):
                "Ecrit la moyenne du pole de disciplines"
                self.pole['average'] = average

        return [Pole(pole)
                for pole in self.configuration['bulletin']['averages']]

    def delays(self):
        "Retourne le nombre de retards"
        class Retards():
            """
            Interface pour manipuler les retards
            """

            def __init__(self, retards):
                self.retards = retards

            def __str__(self):
                return f"{self.name()} : {self.count()}"

            def name(self):
                "Retourne le nom"
                return 'Retards'

            def average(self):
                "Retourne le décompte comme une moyenne"
                return self.count()

            def count(self):
                "Retourne le décompte"
                return self.retards

        return Retards(self.configuration['delays'])

    def __get_pronote_average(self, averages, pronote_subject):
        for average in averages:  # iterate over all the averages
            if average.subject.name == pronote_subject:
                return float(average.student.replace(
                    ',', '.')) / int(average.out_of)
        return None

    def compute_pole_averages(self, averages):
        "Calcule et enregistre les moyennes à partir des données pronote en parametre"
        if averages:
            for pole in self.poles():
                # print(pole)
                pole_averages = []
                for bulletin_subject in pole.subjects():
                    if bulletin_subject.name() in self.convert_bulletin2pronote:
                        pronote_subject = self.convert_bulletin2pronote[bulletin_subject.name()]
                        average = self.__get_pronote_average(averages, pronote_subject)
                        pole_averages.append(average)
                        pole.write_subject_average(bulletin_subject.name(), average * 20.)
                    else:
                        print(
                            f"""La discipline '{bulletin_subject}' est introuvable dans la table
                             de conversion 'pronote' <=> 'bulletin' (corriger le fichier
                             '{self.path_configuration_json}')""")
                if len(pole_averages) != 0:
                    pole.write_average(
                        sum(pole_averages) / len(pole_averages) * 20)
                # print(pole)

    def compute_pole_delays(self, delays):
        "Calcule et enregistre les données de retards à partir des données pronote en parametre"
        if delays:
            self.configuration['delays'] = len(delays)


class Rules():
    """
    Cette classe implémente les rêgles à appliquer sur le bulletin de notes afin de définir les
    gratifications obtenues. Ces rêgles sont propres à chacun et sont configurables dans un JSON
    à fournir.
    """

    def __init__(self, path_configuration_json):
        with open(path_configuration_json, 'r', encoding='utf-8') as json_file:
            self.configuration = json.load(json_file)
        # print(f"Rules - Configuration : {self.configuration}")

    def get_background_for_pole(self, name, average):
        "Personnalise la couleur de fond d'un pole"

    def get_foreground_for_average_pole(self, name, subject, average):
        "Personnalise la couleur d'écriture de la moyenne d'un pole"

    def get_background_for_delays(self, name, average):
        "Personnalise la couleur de fond des retards"

    def is_banco(self, bulletin):
        "Indique si le bulletin remplit la gratification BANCO"
        for conditions_banco in self.configuration['Banco']:
            for condition in conditions_banco:
                pole, average_min, average_max = condition['Pole'], float(
                    condition['min']), float(condition['max'])
                if pole == 'Retards':
                    if not average_min <= bulletin.delays() <= average_max:
                        return False
                else:
                    if not bulletin.pole(pole).average() or not average_min <= bulletin.pole(
                            pole).average() <= average_max:
                        return False
        return True

    def has_boost(self, pole_bulletin):
        "Indique si le pole a une option de BOOST"
        for condition in self.configuration['Boost']:
            pole = condition['Pole']
            if pole == pole_bulletin.name():
                return True
        return False

    def is_boosted(self, pole_bulletin):
        "Indique si le pole fourni en paramètre est BOOSTé"
        for condition in self.configuration['Boost']:
            pole, average_min, average_max = condition['Pole'], float(
                condition['min']), float(
                condition['max'])
            if pole == pole_bulletin.name():
                if average_min <= pole_bulletin.average() <= average_max:
                    return True
        return False

    def get_boosted_gain(self, pole_bulletin):
        "Indique le gain de BOOST"
        for condition in self.configuration['Boost']:
            pole, gain = condition['Pole'], int(condition['gain'])
            if pole == pole_bulletin.name():
                return gain
        return None

    def get_marathon_gain(self, pole_bulletin):
        "Indique le gain de MARATHON"
        for condition in self.configuration['Marathon']:
            pole, gain = condition['Pole'], int(condition['gain'])
            if pole == pole_bulletin.name():
                return gain
        return None

    def get_gain(self, pole_bulletin):
        "Indique le gain BOOST, MARATHON le plus favorable"
        if self.is_boosted(pole_bulletin):
            return self.get_boosted_gain(pole_bulletin)
        return self.get_marathon_gain(pole_bulletin)


class SubjectAveragesFrame(tk.Frame):
    "Frame dédiée aux moyennes de disciplines (dans la frame des poles)"
    def __init__(self, container, bg):
        # frame 'bulletin'
        super().__init__(container, relief=tk.GROOVE, background=bg, padx=5)
        self.container = container

        self.pack(side=tk.RIGHT)
        self.bg = bg
        self.labels = []

    def write(self, text, fg):
        "Ecriture de la moyenne de discipline"
        self.labels.append(
            tk.Label(
                self,
                text=text,
                background=self.bg,
                anchor='e',
                foreground=fg).pack(
                fill='x'))


class SubjectsFrame(tk.Frame):
    "Frame dédiée aux disciplines (dans la frame des poles)"
    def __init__(self, container, bg):
        # frame 'bulletin'
        super().__init__(container, relief=tk.GROOVE, background=bg, padx=5)
        self.container = container

        self.pack(side=tk.LEFT)
        self.bg = bg
        self.labels = []

    def write(self, text):
        "Ecriture de la discipline"
        self.labels.append(
            tk.Label(
                self,
                text=text,
                background=self.bg,
                anchor='w').pack(
                fill='x'))


class PoleFrame(tk.LabelFrame):
    "Frame dédiée au poles de disciplines (dans la frame des moyennes)"
    def __init__(self, container, pole):
        self.container = container
        # Apply rules on background
        bg = None
        if pole.average():
            if pole.average() >= 15.0:
                bg = 'SpringGreen'
            elif pole.average() >= 13.0:
                bg = 'LightGreen'

        if pole.average():
            text = f"{pole.name()} : {pole.average():.2f}/20"
        else:
            text = pole.name()
        super().__init__(container, text=text, background=bg)
        self.pack(fill="both", expand="yes", padx=5, pady=5)

        # frame 'subjects' et 'grades'
        self.frame_subjects = SubjectsFrame(self, bg)
        self.frame_subject_averages = SubjectAveragesFrame(self, bg)

        for bulletin_subject in pole.subjects():
            self.frame_subjects.write(bulletin_subject)

            # Apply rules on foreground
            # TODO : get_foreground_for_average_pole((pole['name'],
            #                                   pole['subjects'],
            #                                   pole['subjects_average'][bulletin_subject])
            average_fg = None
            subject_average = pole.subject_average(bulletin_subject.name())
            if subject_average:
                if pole.average() >= 13.0 > subject_average:
                    average_fg = 'Red'
                elif pole.average() >= 15.0 > subject_average >= 13.0:
                    average_fg = 'FireBrick'

            if subject_average:
                self.frame_subject_averages.write(
                    f"{subject_average:.2f}/20", average_fg)
            else:
                self.frame_subject_averages.write('-', average_fg)


class AveragesFrame(tk.Frame):
    "Frames dédiée aux moyennes"
    def __init__(self, container):
        # frame 'bulletin'
        super().__init__(container, relief=tk.GROOVE)
        self.container = container
        self.pack(side=tk.TOP)
        self.pole_frame = []
        for pole in self.container.bulletin.poles():
            self.pole_frame.append(PoleFrame(self, pole))


class DelaysFrames(tk.Frame):
    "Frame dédiée aux retards"
    def __init__(self, container):
        # frame 'retards'
        super().__init__(container, relief=tk.GROOVE)
        self.container = container
        self.pack(side=tk.BOTTOM)

        if self.container.bulletin.delays() is not None:
            # Apply rules on background
            # TODO : get_background_for_delays(pole['name'], pole['average'])
            bg = None
            if self.container.bulletin.delays().count() == 0:
                bg = 'SpringLight'
            elif self.container.bulletin.delays().count() <= 5:
                bg = 'LightGreen'
            tk.Label(
                self,
                text=self.container.bulletin.delays(),
                background=bg,
                anchor='w').pack(
                fill='x')


class AppBulletin(tk.Tk):
    "Application graphique"
    def __init__(self, rules, bulletin):
        super().__init__()
        self.rules = rules
        self.bulletin = bulletin

        self.title('PS5 ?')
        self.resizable(False, False)

        self.averages = AveragesFrame(self)
        self.averages = DelaysFrames(self)


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

    current_period = client.current_period

    bulletin_actuel = Bulletin('example_5_bulletin.json')
    try:
        bulletin_actuel.compute_pole_averages(current_period.averages)
    except KeyError as e:
        print(f"Erreur sur le bulletin : {e}")
    bulletin_actuel.compute_pole_delays(current_period.delays)

    ps5_rules = Rules('example_5_rules.json')
    print(f"Banco = {ps5_rules.is_banco(bulletin_actuel)}")
    for pole_de_disiplines in bulletin_actuel.poles():
        print(
            f"{
                pole_de_disiplines.name()}: has BOOST = {
                ps5_rules.has_boost(pole_de_disiplines)} ; Boost = {
                ps5_rules.is_boosted(pole_de_disiplines)}")
    print(
        f"Retards: has BOOST = {
            ps5_rules.has_boost(
                bulletin_actuel.delays())} ; Boost = {
            ps5_rules.is_boosted(
                bulletin_actuel.delays())}")

    fenetre = AppBulletin(ps5_rules, bulletin_actuel)
    fenetre.mainloop()

else:
    print("Failed to log in")
    sys.exit()
