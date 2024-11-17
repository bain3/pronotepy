"""
Cette classe implémente les rêgles à appliquer sur le bulletin de notes afin de définir les
gratifications obtenues. Ces rêgles sont propres à chacun et sont configurables dans un JSON
à fournir.
"""

import copy
import json


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
        self.target_amount = self.configuration['Target amount']
        self.banco = {}
        for condition in self.configuration['Banco']['Rules']:
            self.banco[condition['Cluster']] = copy.deepcopy(condition)
        self.boost = {}
        for condition in self.configuration['Boost']['Rules']:
            self.boost[condition['Cluster']] = copy.deepcopy(condition)
        self.marathon = {}
        for condition in self.configuration['Marathon']['Rules']:
            self.marathon[condition['Cluster']] = copy.deepcopy(condition)
        
        self.description = {}
        self.description['Banco'] = self.configuration['Banco']['Description']
        self.description['Boost'] = self.configuration['Boost']['Description']
        self.description['Marathon'] = self.configuration['Marathon']['Description']

    def __get_banco_rule(self, cluster):
        "Retourne la regle de BANCO du pole de discipline"
        if cluster.name() in self.banco:
            return self.banco[cluster.name()]
        return None

    def __get_boost_rule(self, cluster):
        "Retourne la regle de BOOST du pole de discipline"
        if cluster.name() in self.boost:
            return self.boost[cluster.name()]
        return None

    def __get_marathon_rule(self, cluster):
        "Retourne la regle du MARATHON du pole de discipline"
        if cluster.name() in self.marathon:
            return self.marathon[cluster.name()]
        return None

    def report_card_is_eligible_banco(self, report_card):
        "Indique si le bulletin remplit la gratification BANCO"
        for cluster in self.banco:
            if not self.cluster_is_eligible_for_banco(report_card.cluster(cluster)):
                return False
        return True

    def cluster_can_boost_money(self, cluster):
        "Indique si le pole a une option de BOOST"
        return self.__get_boost_rule(cluster) is not None

    def cluster_is_eligible_for_banco(self, cluster):
        "Indique si le pole fourni en paramètre est éligible au BANCO"
        cluster_banco = self.__get_banco_rule(cluster)
        if cluster_banco and cluster.average():
            if cluster_banco['min'] <= cluster.average(
            ) <= cluster_banco['max']:
                return True
        return False

    def cluster_is_eligible_for_boost(self, cluster):
        "Indique si le pole fourni en paramètre est éligible au BOOST"
        cluster_boost = self.__get_boost_rule(cluster)
        if cluster_boost and cluster.average():
            if cluster_boost['min'] <= cluster.average(
            ) <= cluster_boost['max']:
                return True
        return False

    def cluster_is_eligible_for_marathon(self, cluster):
        "Indique si le pole fourni en paramètre est éligible au MARATHON"
        cluster_marathon = self.__get_marathon_rule(cluster)
        if cluster_marathon and cluster.average():
            if cluster_marathon['min'] <= cluster.average(
            ) <= cluster_marathon['max']:
                return True
        return False

    def subject_downgrades_eligible_cluster_for_boost(self, cluster, subject_average):
        "Indique si la discipline dégrade le BOOST du pole fourni en paramètre"
        cluster_boost = self.__get_boost_rule(cluster)
        if cluster_boost:
            if self.cluster_is_eligible_for_boost(
                    cluster) and cluster_boost['min'] > subject_average:
                return True
        return False

    def subject_downgrades_eligible_cluster_for_marathon(self, cluster, subject_average):
        "Indique si la discipline dégrade le MARATHON du pole fourni en paramètre"
        cluster_marathon = self.__get_marathon_rule(cluster)
        if cluster_marathon:
            if cluster_marathon['min'] <= cluster.average(
            ) <= cluster_marathon['max'] and cluster_marathon['min'] > subject_average:
                return True
        return False

    def get_cluster_boost_money(self, cluster):
        "Indique le gain de BOOST"
        cluster_boost = self.__get_boost_rule(cluster)
        if cluster_boost:
            return cluster_boost['money']
        return None

    def get_cluster_marathon_money(self, cluster):
        "Indique le gain de MARATHON"
        cluster_marathon = self.__get_marathon_rule(cluster)
        if cluster_marathon:
            return cluster_marathon['money']
        return None

    def get_cluster_money(self, cluster):
        "Indique le gain BOOST, MARATHON du pole"
        if self.cluster_is_eligible_for_boost(cluster):
            return self.get_cluster_boost_money(
                cluster) + self.get_cluster_marathon_money(cluster)
        if self.cluster_is_eligible_for_marathon(cluster):
            return self.get_cluster_marathon_money(cluster)
        return None

    def get_report_card_money(self, report_card):
        "Indique le gain global du bulletin"
        money_pool = 0
        for cluster in report_card.clusters():
            gain = self.get_cluster_money(cluster)
            if gain:
                money_pool += gain
        return money_pool

    def get_banco_rate(self, report_card):
        "Indique le taux de réussite du BANCO"
        nb_banco = 0
        for cluster in self.banco:
            if self.cluster_is_eligible_for_banco(report_card.cluster(cluster)):
                nb_banco += 1
        return int(nb_banco / len(self.banco) * 100)

    def get_target_amount_rate(self, report_card):
        "Indique le taux d'acquisition de la cagnotte cible BOOST, MARATHON"
        money_pool = self.get_report_card_money(report_card)
        return int(money_pool / self.target_amount * 100)

    def get_banco_description(self):
        return self.description['Banco']

    def get_boost_description(self):
        return self.description['Boost']

    def get_marathon_description(self):
        return self.description['Marathon']