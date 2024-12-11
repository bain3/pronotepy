"""
This class implements the rules to apply to the report card in order to define the
rewards obtained. These rules are specific to each person and can be configured in a provided JSON.
"""

import copy
import json


class Rules():
    """
    This class implements the rules to apply to the report card in order to define the
    rewards obtained. These rules are specific to each person and can be configured in
    a provided JSON.
    """

    def __init__(self, configuration_json_path):
        with open(configuration_json_path, 'r', encoding='utf-8') as json_file:
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

    def _get_banco_rule(self, cluster):
        "Returns the BANCO rule for the given cluster"
        if cluster:
            if cluster.name in self.banco:
                return self.banco[cluster.name]
        return None

    def _get_boost_rule(self, cluster):
        "Returns the BOOST rule for the given cluster"
        if cluster:
            if cluster.name in self.boost:
                return self.boost[cluster.name]
        return None

    def _get_marathon_rule(self, cluster):
        "Returns the MARATHON rule for the given cluster"
        if cluster:
            if cluster.name in self.marathon:
                return self.marathon[cluster.name]
        return None

    def report_card_is_eligible_for_banco(self, report_card):
        "Indicates if the report card meets the BANCO reward criteria"
        if report_card:
            for cluster in self.banco:
                if not self.cluster_is_eligible_for_banco(
                        report_card.cluster(cluster)):
                    return False
        return True

    def cluster_can_boost_money(self, cluster):
        "Indicates if the cluster has a BOOST option"
        return self._get_boost_rule(cluster) is not None

    def cluster_is_eligible_for_banco(self, cluster):
        "Indicates if the provided cluster is eligible for BANCO"
        if cluster:
            cluster_banco = self._get_banco_rule(cluster)
            if cluster_banco and cluster.average is not None:
                if cluster_banco['min'] <= cluster.average <= cluster_banco['max']:
                    return True
        return False

    def cluster_is_eligible_for_boost(self, cluster):
        "Indicates if the provided cluster is eligible for BOOST"
        if cluster:
            cluster_boost = self._get_boost_rule(cluster)
            if cluster_boost and cluster.average is not None:
                if cluster_boost['min'] <= cluster.average <= cluster_boost['max']:
                    return True
        return False

    def cluster_is_eligible_for_marathon(self, cluster):
        "Indicates if the provided cluster is eligible for MARATHON"
        if cluster:
            cluster_marathon = self._get_marathon_rule(cluster)
            if cluster_marathon and cluster.average is not None:
                if cluster_marathon['min'] <= cluster.average <= cluster_marathon['max']:
                    return True
        return False

    def subject_downgrades_eligible_cluster_for_boost(
            self, cluster, subject_average):
        "Indicates if the subject downgrades the BOOST eligibility of the provided cluster"
        if cluster and subject_average is not None:
            cluster_boost = self._get_boost_rule(cluster)
            if cluster_boost:
                if self.cluster_is_eligible_for_boost(
                        cluster) and cluster_boost['min'] > subject_average:
                    return True
        return False

    def subject_downgrades_eligible_cluster_for_marathon(
            self, cluster, subject_average):
        "Indicates if the subject downgrades the MARATHON eligibility of the provided cluster"
        if cluster and subject_average is not None:
            cluster_marathon = self._get_marathon_rule(cluster)
            if cluster_marathon:
                if cluster_marathon['min'] <= cluster.average <= cluster_marathon['max'] and cluster_marathon['min'] > subject_average:
                    return True
        return False

    def get_cluster_boost_money(self, cluster):
        "Indicates the BOOST reward amount"
        if cluster:
            cluster_boost = self._get_boost_rule(cluster)
            if cluster_boost:
                return cluster_boost['money']
        return None

    def get_cluster_marathon_money(self, cluster):
        "Indicates the MARATHON reward amount"
        if cluster:
            cluster_marathon = self._get_marathon_rule(cluster)
            if cluster_marathon:
                return cluster_marathon['money']
        return None

    def get_cluster_money(self, cluster):
        "Indicates the BOOST and MARATHON reward amount for the cluster"
        if cluster:
            if self.cluster_is_eligible_for_boost(cluster):
                return self.get_cluster_boost_money(
                    cluster) + self.get_cluster_marathon_money(cluster)
            if self.cluster_is_eligible_for_marathon(cluster):
                return self.get_cluster_marathon_money(cluster)
        return None

    def get_report_card_money(self, report_card):
        "Indicates the total reward amount for the report card"
        money_pool = 0
        if report_card:
            for cluster in report_card.clusters:
                gain = self.get_cluster_money(cluster)
                if gain:
                    money_pool += gain
        return money_pool

    def get_banco_rate(self, report_card):
        "Indicates the BANCO success rate"
        nb_banco = 0
        if report_card:
            for cluster in self.banco:
                if self.cluster_is_eligible_for_banco(
                        report_card.cluster(cluster)):
                    nb_banco += 1
        return int(nb_banco / len(self.banco) * 100)

    def get_target_amount_rate(self, report_card=None, money_pool=None):
        """Indicates the acquisition rate of the target reward amount for BOOST and MARATHON.
        Provide the reward amount (money_pool) or the report card (report_card) to estimate"""
        if not money_pool:
            if report_card:
                money_pool = self.get_report_card_money(report_card)
            else:
                return None
        return int(money_pool / self.target_amount * 100)

    def get_banco_description(self):
        "BANCO Description"
        return self.description['Banco']

    def get_boost_description(self):
        "BOOST Description"
        return self.description['Boost']

    def get_marathon_description(self):
        "Marathon Description"
        return self.description['Marathon']
