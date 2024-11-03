"""
Cette classe implémente un bulletin correspondant à celui que produit un
établissement. Sa forme et son organisation dépendent de chaque
établissement et sont configurables dans un JSON à fournir.
"""

import json


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
                        pronote_subject = self.convert_bulletin2pronote[bulletin_subject.name(
                        )]
                        average = self.__get_pronote_average(
                            averages, pronote_subject)
                        pole_averages.append(average)
                        pole.write_subject_average(
                            bulletin_subject.name(), average * 20.)
                    else:
                        print(f"""
La discipline '{bulletin_subject}' est introuvable dans la table de
conversion 'pronote' <=> 'bulletin' (corriger le fichier '{self.path_configuration_json}')""")
                if len(pole_averages) != 0:
                    pole.write_average(
                        sum(pole_averages) / len(pole_averages) * 20)
                # print(pole)

    def compute_pole_delays(self, delays):
        "Calcule et enregistre les données de retards à partir des données pronote en parametre"
        if delays:
            self.configuration['delays'] = len(delays)
