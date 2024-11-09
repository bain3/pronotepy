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
        self.banco = {}
        for condition in self.configuration['Banco']:
            self.banco[condition['Pole']] = copy.deepcopy(condition)
        self.boost = {}
        for condition in self.configuration['Boost']:
            self.boost[condition['Pole']] = copy.deepcopy(condition)
        self.marathon = {}
        for condition in self.configuration['Marathon']:
            self.marathon[condition['Pole']] = copy.deepcopy(condition)

    def __get_banco_rule(self, pole_bulletin):
        "Retourne la regle de BANCO du pole de discipline"
        if pole_bulletin.name() in self.banco:
            return self.banco[pole_bulletin.name()]
        return None

    def __get_boost_rule(self, pole_bulletin):
        "Retourne la regle de BOOST du pole de discipline"
        if pole_bulletin.name() in self.boost:
            return self.boost[pole_bulletin.name()]
        return None

    def __get_marathon_rule(self, pole_bulletin):
        "Retourne la regle du MARATHON du pole de discipline"
        if pole_bulletin.name() in self.marathon:
            return self.marathon[pole_bulletin.name()]
        return None

    def bulletin_is_banco(self, bulletin):
        "Indique si le bulletin remplit la gratification BANCO"
        for pole in self.banco:
            if not self.pole_is_bancoed(bulletin.pole(pole)):
                return False
        return True

    def pole_has_boost(self, pole_bulletin):
        "Indique si le pole a une option de BOOST"
        return self.__get_boost_rule(pole_bulletin) is not None

    def pole_is_bancoed(self, pole_bulletin):
        "Indique si le pole fourni en paramètre est BANCOé"
        pole_banco = self.__get_banco_rule(pole_bulletin)
        if pole_banco and pole_bulletin.average():
            if pole_banco['min'] <= pole_bulletin.average(
            ) <= pole_banco['max']:
                return True
        return False

    def pole_is_boosted(self, pole_bulletin):
        "Indique si le pole fourni en paramètre est BOOSTé"
        pole_boost = self.__get_boost_rule(pole_bulletin)
        if pole_boost and pole_bulletin.average():
            if pole_boost['min'] <= pole_bulletin.average(
            ) <= pole_boost['max']:
                return True
        return False

    def pole_is_marathoned(self, pole_bulletin):
        "Indique si le pole fourni en paramètre est MARATHONé"
        pole_marathon = self.__get_marathon_rule(pole_bulletin)
        if pole_marathon and pole_bulletin.average():
            if pole_marathon['min'] <= pole_bulletin.average(
            ) <= pole_marathon['max']:
                return True
        return False

    def subject_downgrade_boosted_pole(self, pole_bulletin, subject_average):
        "Indique si la discipline dégrade le BOOST du pole fourni en paramètre"
        pole_boost = self.__get_boost_rule(pole_bulletin)
        if pole_boost:
            if self.pole_is_boosted(
                    pole_bulletin) and pole_boost['min'] > subject_average:
                return True
        return False

    def subject_downgrade_marathon_pole(self, pole_bulletin, subject_average):
        "Indique si la discipline dégrade le MARATHON du pole fourni en paramètre"
        pole_marathon = self.__get_marathon_rule(pole_bulletin)
        if pole_marathon:
            if pole_marathon['min'] <= pole_bulletin.average(
            ) <= pole_marathon['max'] and pole_marathon['min'] > subject_average:
                return True
        return False

    def get_pole_boost_gain(self, pole_bulletin):
        "Indique le gain de BOOST"
        pole_boost = self.__get_boost_rule(pole_bulletin)
        if pole_boost:
            return pole_boost['gain']
        return None

    def get_pole_marathon_gain(self, pole_bulletin):
        "Indique le gain de MARATHON"
        pole_marathon = self.__get_marathon_rule(pole_bulletin)
        if pole_marathon:
            return pole_marathon['gain']
        return None

    def get_pole_gain(self, pole_bulletin):
        "Indique le gain BOOST, MARATHON le plus favorable"
        if self.pole_is_boosted(pole_bulletin):
            return self.get_pole_boost_gain(
                pole_bulletin) + self.get_pole_marathon_gain(pole_bulletin)
        if self.pole_is_marathoned(pole_bulletin):
            return self.get_pole_marathon_gain(pole_bulletin)
        return None
