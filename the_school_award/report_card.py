"""
Cette classe implémente un bulletin correspondant à celui que produit un
établissement. Sa forme et son organisation dépendent de chaque
établissement et sont configurables dans un JSON à fournir.
"""

import json


class ReportCard():
    """
    Cette classe implémente un bulletin correspondant à celui que produit un
    établissement. Sa forme et son organisation dépendent de chaque
    établissement et sont configurables dans un JSON à fournir.
    """

    def __init__(self, path_configuration_json):
        self.path_configuration_json = path_configuration_json
        with open(path_configuration_json, 'r', encoding='utf-8') as json_file:
            self.configuration = json.load(json_file)
        # print(f"Report card - Configuration : {self.configuration}")
        self.convert_pronote2report_card = self.configuration[
            'subject_mapping_pronote_to_report_card']
        self.convert_report_card2pronote = {
            v: k for k, v in self.convert_pronote2report_card.items()}

    def cluster(self, name):
        "Retourne les information d'un pole à partir de son 'nom' donné en parametre"
        for cluster in self.clusters():
            if name == cluster.name():
                return cluster
        return None

    def clusters(self):
        "Retourne la liste des poles"
        class Cluster():
            "Interface pour manipuler un pole de discipline"

            def __init__(self, cluster):
                self.cluster = cluster

            def __str__(self):
                return self.name()

            def name(self):
                "Retourne le nom"
                return self.cluster['name']

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

                return [Subject(subject) for subject in self.cluster['subjects']]

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
                        for subject_average in self.cluster['subjects_average']]

            def subject_average(self, name):
                "Retourne la moyenne d'une discipline donnée en paramètre"
                if name in self.cluster['subjects_average']:
                    return self.cluster['subjects_average'].get(name)
                return None

            def write_subject_average(self, name, average):
                "Ecrit la moyenne d'une discipline donnée en paramètre"
                self.cluster['subjects_average'][name] = average

            def average(self):
                "Retourne la moyenne du pole de disciplines"
                if self.cluster['average']:
                    return self.cluster['average']
                return None

            def write_average(self, average):
                "Ecrit la moyenne du pole de disciplines"
                self.cluster['average'] = average

        return [Cluster(cluster)
                for cluster in self.configuration['report_card']]

    def __get_pronote_average(self, averages, pronote_subject):
        for average in averages:  # iterate over all the averages
            if average.subject.name == pronote_subject:
                return float(average.student.replace(
                    ',', '.')) / int(average.out_of)
        return None

    def compute_report_card_averages(self, averages):
        "Calcule et enregistre les moyennes à partir des données pronote en parametre"
        if averages:
            # Vérifier la complétude de la table de correspondance 'pronote' <=> 'report_card'
            for average in averages:
                if average.subject.name not in self.convert_pronote2report_card:
                    print(f"""
La discipline '{average.subject.name}' est introuvable dans la table de conversion
    'pronote' <=> 'report_card' (corriger le dictionnaire 'subject_mapping_pronote_to_report_card'
    dans le fichier '{self.path_configuration_json} : ')""")

            # Réaliser l'enregistrement des moyennes
            for cluster in self.clusters():
                # print(cluster)
                cluster_averages = []
                for report_card_subject in cluster.subjects():
                    if report_card_subject.name() in self.convert_report_card2pronote:
                        pronote_subject = self.convert_report_card2pronote[report_card_subject.name(
                        )]
                        average = self.__get_pronote_average(
                            averages, pronote_subject)
                        cluster_averages.append(average)
                        cluster.write_subject_average(
                            report_card_subject.name(), average * 20.)
                if len(cluster_averages) != 0:
                    cluster.write_average(
                        sum(cluster_averages) / len(cluster_averages) * 20)
                # print(cluster)

    def compute_report_card_delays(self, delays):
        """
        Calcule et enregistre les données de retards à partir des données pronote en parametre.
        Les retards sont intégrés au bulletin comme une moyenne pour uniformiser les traitements
        """
        if delays:
            for cluster in self.clusters():
                # print(cluster)
                for report_card_subject in cluster.subjects():
                    if report_card_subject.name() == 'Retards':
                        average = float(len(delays))
                        cluster.write_subject_average(
                            report_card_subject.name(), average)
                        cluster.write_average(average)
                # print(cluster)
