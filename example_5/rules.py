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
        for condition in self.configuration['Banco']:
            self.banco[condition['Cluster']] = copy.deepcopy(condition)
        self.boost = {}
        for condition in self.configuration['Boost']:
            self.boost[condition['Cluster']] = copy.deepcopy(condition)
        self.marathon = {}
        for condition in self.configuration['Marathon']:
            self.marathon[condition['Cluster']] = copy.deepcopy(condition)

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

    def report_card_is_banco(self, bulletin):
        "Indique si le bulletin remplit la gratification BANCO"
        for cluster in self.banco:
            if not self.cluster_is_bancoed(bulletin.pole(cluster)):
                return False
        return True

    def cluster_has_boost(self, cluster):
        "Indique si le pole a une option de BOOST"
        return self.__get_boost_rule(cluster) is not None

    def cluster_is_bancoed(self, cluster):
        "Indique si le pole fourni en paramètre est BANCOé"
        cluster_banco = self.__get_banco_rule(cluster)
        if cluster_banco and cluster.average():
            if cluster_banco['min'] <= cluster.average(
            ) <= cluster_banco['max']:
                return True
        return False

    def cluster_is_boosted(self, cluster):
        "Indique si le pole fourni en paramètre est BOOSTé"
        cluster_boost = self.__get_boost_rule(cluster)
        if cluster_boost and cluster.average():
            if cluster_boost['min'] <= cluster.average(
            ) <= cluster_boost['max']:
                return True
        return False

    def cluster_is_marathoned(self, cluster):
        "Indique si le pole fourni en paramètre est MARATHONé"
        cluster_marathon = self.__get_marathon_rule(cluster)
        if cluster_marathon and cluster.average():
            if cluster_marathon['min'] <= cluster.average(
            ) <= cluster_marathon['max']:
                return True
        return False

    def subject_downgrades_boosted_cluster(self, cluster, subject_average):
        "Indique si la discipline dégrade le BOOST du pole fourni en paramètre"
        cluster_boost = self.__get_boost_rule(cluster)
        if cluster_boost:
            if self.cluster_is_boosted(
                    cluster) and cluster_boost['min'] > subject_average:
                return True
        return False

    def subject_downgrades_marathon_cluster(self, cluster, subject_average):
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
        "Indique le gain BOOST, MARATHON le plus favorable"
        if self.cluster_is_boosted(cluster):
            return self.get_cluster_boost_money(
                cluster) + self.get_cluster_marathon_money(cluster)
        if self.cluster_is_marathoned(cluster):
            return self.get_cluster_marathon_money(cluster)
        return None

    def get_report_card_money(self, report_card):
        "Indique la gain global du bulletin"
        money_pool = 0
        for cluster in report_card.poles():
            gain = self.get_cluster_money(cluster)
            if gain:
                money_pool += gain
        return money_pool

    def get_banco_rate(self, report_card):
        "Indique le taux de réussite du BANCO"
        nb_banco = 0
        for pole in self.banco:
            if self.cluster_is_bancoed(report_card.pole(pole)):
                nb_banco += 1
        return int(nb_banco / len(self.banco) * 100)

    def get_target_amount_rate(self, report_card):
        "Indique le taux d'acquisition de la cagnotte cible BOOST, MARATHON"
        money_pool = self.get_report_card_money(report_card)
        return int(money_pool / self.target_amount * 100)
