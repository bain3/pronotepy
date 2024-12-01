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

    def to_dict(self):
        "Conversion du bulletin en dictionnaire (pour enregistrement JSON)"
        data = {}
        data['infos'] = {}
        data['infos']['username'] = self.infos._username
        data['infos']['class_name'] = self.infos._class_name
        data['infos']['establishment'] = self.infos._establishment
        data['infos']['year'] = self.infos._year
        data['infos']['period_name'] = self.infos._period_name
        data['clusters'] = []
        for cluster in self.clusters():
            data_cluster = {}
            data_cluster['name'] = cluster.name()
            data_cluster['subjects'] = []
            for subject in cluster.subjects():
                data_cluster['subjects'].append(subject.name())
            data_cluster['subjects_average'] = {}
            for subject in cluster.subjects_average():
                data_cluster['subjects_average'][subject.name()] = subject.average()
            data_cluster['average'] = cluster.average()
            data['clusters'].append(data_cluster)
        return data

    def save(self, path_save_json):
        "Enregistre le bulletin dans un fichier JSON"
        with open(path_save_json, 'w', encoding='utf-8') as json_file:
            json.dump(self.to_dict(), json_file, ensure_ascii=False, indent=4)

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
                        self._name, self._average = subject_average

                    def __str__(self):
                        return f"{self.name()} : {self.average()}"

                    def name(self):
                        "Retourne le nom"
                        return self._name

                    def average(self):
                        "Retourne la moyenne"
                        return self._average

                return [SubjectAverage(subject_average)
                        for subject_average in self.cluster['subjects_average'].items()]

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
                if self.cluster['average'] is not None:
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

    def compute_report_card_infos(self, client, period):
        "Enregistre les informations générales à partir des données pronote en parametre"
        if client:
            class Infos():
                """
                Interface pour manipuler la moyenne d'une discipline
                """

                def __init__(self, client, period):
                    self._username = client.info.name  # get users name
                    self._class_name = client.info.class_name
                    self._establishment = client.info.establishment
                    self._year = client.start_day.year
                    self._period_name = period.name

                def __str__(self):
                    return f"{self.year()}-{self.year()+1} {self.class_name()} : {self.period_name()} de {self.username()}"

                def username(self):
                    "Retourne le nom"
                    return self._username

                def class_name(self):
                    "Retourne le nom de la classe"
                    return self._class_name

                def establishment(self):
                    "Retourne le nom de l'établissement"
                    return self._establishment

                def year(self):
                    "Retourne l'année de scolarité"
                    return self._year

                def period_name(self):
                    "Retourne le nom du trimestre"
                    return self._period_name

                def short_period_name(self):
                    "Retourne le nom court du trimestre"
                    return self._period_name[0]+self._period_name[-1]

            self.infos = Infos(client, period)

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
                        if average is not None:
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
