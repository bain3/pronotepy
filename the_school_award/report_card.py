"""
This class implements a report card corresponding to what an
institution produces. Its format and organization depend on each
institution and are configurable in a provided JSON.
"""

import json


class ReportCard():
    """
    This class implements a report card corresponding to what an
    institution produces. Its format and organization depend on each
    institution and are configurable in a provided JSON.
    """

    def __init__(self, configuration_json_path):
        self.configuration_json_path = configuration_json_path
        with open(configuration_json_path, 'r', encoding='utf-8') as json_file:
            self.configuration = json.load(json_file)
        # print(f"Report card - Configuration : {self.configuration}")
        self.convert_pronote_to_report_card = self.configuration[
            'subject_mapping_pronote_to_report_card']
        self.convert_report_card_to_pronote = {
            v: k for k, v in self.convert_pronote_to_report_card.items()}
        self.infos = None

    def to_dict(self):
        "Convert the report card into a dictionary (for JSON recording)"
        data = {}
        data['infos'] = {}
        data['infos']['username'] = self.infos.username
        data['infos']['class_name'] = self.infos.class_name
        data['infos']['establishment'] = self.infos.establishment
        data['infos']['year'] = self.infos.year
        data['infos']['period_name'] = self.infos.period_name
        data['clusters'] = []
        for cluster in self.clusters:
            data_cluster = {}
            data_cluster['name'] = cluster.name
            data_cluster['subjects'] = []
            for subject in cluster.subjects:
                data_cluster['subjects'].append(subject.name)
            data_cluster['subjects_average'] = {}
            for subject in cluster.subjects_average:
                data_cluster['subjects_average'][subject.name] = subject.average
            data_cluster['average'] = cluster.average
            data['clusters'].append(data_cluster)
        return data

    def save(self, save_json_path):
        "Save the report card in a JSON file"
        with open(save_json_path, 'w', encoding='utf-8') as json_file:
            json.dump(self.to_dict(), json_file, ensure_ascii=False, indent=4)

    def cluster(self, name):
        "Return the information of a cluster based on its 'name' given as a parameter"
        for cluster in self.clusters:
            if name == cluster.name:
                return cluster
        return None

    @property
    def clusters(self):
        "Return the list of clusters"
        class Cluster():
            "Interface to manipulate a discipline cluster"

            def __init__(self, cluster):
                self._cluster = cluster

            def __str__(self):
                return self.name()

            @property
            def name(self):
                "Return the name"
                return self._cluster['name']

            @property
            def subjects(self):
                "Return the subjects of the cluster"
                class Subject():
                    """
                    Interface to manipulate the name of a subject
                    """

                    def __init__(self, subject):
                        self._subject = subject

                    def __str__(self):
                        return self.name()

                    @property
                    def name(self):
                        "Return the name"
                        return self._subject

                return [Subject(subject) for subject in self._cluster['subjects']]

            @property
            def subjects_average(self):
                "Return the averages of the subjects in the cluster"
                class SubjectAverage():
                    """
                    Interface to manipulate the average of a subject
                    """

                    def __init__(self, subject_average):
                        self._name, self._average = subject_average

                    def __str__(self):
                        return f"{self.name()} : {self.average()}"

                    @property
                    def name(self):
                        "Return the name"
                        return self._name

                    @property
                    def average(self):
                        "Return the average"
                        return self._average

                    @average.setter
                    def average(self, average):
                        "Return the average"
                        self._average = average

                return [SubjectAverage(subject_average)
                        for subject_average in self._cluster['subjects_average'].items()]

            def subject_average(self, name):
                "Return the average of a given subject"
                if name in self._cluster['subjects_average']:
                    return self._cluster['subjects_average'].get(name)
                return None

            def write_subject_average(self, name, average):
                "Write the average of a given subject"
                self._cluster['subjects_average'][name] = average

            @property
            def average(self):
                "Return the average of the discipline cluster"
                return self._cluster['average']

            @average.setter
            def average(self, average):
                "Write the average of the discipline cluster"
                self._cluster['average'] = average

        return [Cluster(cluster)
                for cluster in self.configuration['report_card']]

    def __get_pronote_average(self, averages, pronote_subject):
        for average in averages:  # iterate over all the averages
            if average.subject.name == pronote_subject:
                return float(average.student.replace(
                    ',', '.')) / int(average.out_of)
        return None

    def compute_report_card_infos(self, client, period):
        "Record general information from the given Pronote data"
        if client:
            class Infos():
                """
                Interface to manipulate the average of a subject
                """

                def __init__(self, client, period):
                    self._username = client.info.name  # get user's name
                    self._class_name = client.info.class_name
                    self._establishment = client.info.establishment
                    self._year = client.start_day.year
                    self._period_name = period.name
                    self._short_period_name = period.name[0] + period.name[-1]

                def __str__(self):
                    return f"{self.year}-{self.year+1} {self.class_name} : {
                        self.period_name} from {self.username}"

                @property
                def username(self):
                    "Return the name"
                    return self._username

                @property
                def class_name(self):
                    "Return the class name"
                    return self._class_name

                @property
                def establishment(self):
                    "Return the name of the establishment"
                    return self._establishment

                @property
                def year(self):
                    "Return the school year"
                    return self._year

                @property
                def period_name(self):
                    "Return the period name"
                    return self._period_name

                @property
                def short_period_name(self):
                    "Return the short period name"
                    return self._short_period_name

            self.infos = Infos(client, period)

    def compute_report_card_averages(self, averages):
        "Calculate and record the averages from the given Pronote data"
        if averages:
            # Check the completeness of the 'pronote' <=> 'report_card' mapping
            # table
            for average in averages:
                if average.subject.name not in self.convert_pronote_to_report_card:
                    print(f"""
The subject '{average.subject.name}' is not found in the conversion table
    'pronote' <=> 'report_card' (correct the 'subject_mapping_pronote_to_report_card' dictionary
    in the '{self.configuration_json_path}' file : )""")

            # Record the averages
            for cluster in self.clusters:
                # print(cluster)
                cluster_averages = []
                for report_card_subject in cluster.subjects:
                    if report_card_subject.name in self.convert_report_card_to_pronote:
                        pronote_subject = self.convert_report_card_to_pronote[
                            report_card_subject.name]
                        average = self.__get_pronote_average(
                            averages, pronote_subject)
                        if average is not None:
                            cluster_averages.append(average)
                            cluster.write_subject_average(
                                report_card_subject.name, average * 20.)
                if len(cluster_averages) != 0:
                    cluster.average = sum(cluster_averages) / len(cluster_averages) * 20
                # print(cluster)

    def compute_report_card_delays(self, delays):
        """
        Calculate and record delay data from the given Pronote data.
        Delays are integrated into the report card as an average to standardize the processing
        """
        if delays is not None:
            for cluster in self.clusters:
                # print(cluster)
                for report_card_subject in cluster.subjects:
                    if report_card_subject.name == 'Retards':
                        average = float(len(delays))
                        cluster.write_subject_average(
                            report_card_subject.name, average)
                        cluster.average = average
                # print(cluster)
