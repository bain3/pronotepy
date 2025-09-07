import unittest
from pathlib import Path

import rules

class Cluster():
    "Interface to manipulate a discipline cluster"
    def __init__(self, name, average):
        self._name = name
        self._average = average
    @property
    def name(self):
        "Return the name"
        return self._name
    @property
    def average(self):
        "Return the average of the discipline cluster"
        return self._average

class ReportCard():
    def __init__(self, clusters):
        self._clusters = clusters
    def cluster(self, name):
        if name in self._clusters:
            return self._clusters[name]
        else:
            return None
    @property
    def clusters(self):
        return self._clusters.values()


class TestRules(unittest.TestCase):
    def test__get_banco_rule(self):
        r = rules.Rules('test_rules.json')
        cluster1 = Cluster("cluster1", 15.0)
        rule1 = r._get_banco_rule(cluster1)
        self.assertEqual(rule1['Cluster'], "cluster1")
        self.assertEqual(rule1['min'], 15.0)
        self.assertEqual(rule1['max'], 20.0)

        cluster2 = Cluster("cluster2", 15.0)
        rule2 = r._get_banco_rule(cluster2)
        self.assertEqual(rule2['Cluster'], "cluster2")
        self.assertEqual(rule2['min'], 13.0)
        self.assertEqual(rule2['max'], 20.0)

        cluster_psp = Cluster("unknown", 15.0)
        psp = r._get_banco_rule(cluster_psp)
        self.assertIsNone(psp)

    def test__get_boost_rule(self):
        r = rules.Rules('test_rules.json')
        cluster1 = Cluster("cluster1", 15.0)
        rule1 = r._get_boost_rule(cluster1)
        self.assertIsNone(rule1)

        cluster2 = Cluster("cluster2", 15.0)
        rule2 = r._get_boost_rule(cluster2)
        self.assertEqual(rule2['Cluster'], "cluster2")
        self.assertEqual(rule2['min'], 12.0)
        self.assertEqual(rule2['max'], 20.0)
        self.assertEqual(rule2['money'], 60)

        cluster_psp = Cluster("unknown", 15.0)
        psp = r._get_boost_rule(cluster_psp)
        self.assertIsNone(psp)

    def test__get_marathon_rule(self):
        r = rules.Rules('test_rules.json')
        cluster1 = Cluster("cluster1", 15.0)
        rule1 = r._get_marathon_rule(cluster1)
        self.assertEqual(rule1['Cluster'], "cluster1")
        self.assertEqual(rule1['min'], 11.0)
        self.assertEqual(rule1['max'], 20.0)
        self.assertEqual(rule1['money'], 40)

        cluster2 = Cluster("cluster2", 15.0)
        rule2 = r._get_marathon_rule(cluster2)
        self.assertEqual(rule2['Cluster'], "cluster2")
        self.assertEqual(rule2['min'], 10.0)
        self.assertEqual(rule2['max'], 20.0)
        self.assertEqual(rule2['money'], 30)

        cluster_psp = Cluster("unknown", 15.0)
        psp = r._get_marathon_rule(cluster_psp)
        self.assertIsNone(psp)

    def test_report_card_is_eligible_for_banco(self):
        r = rules.Rules('test_rules.json')
        clusters = {
            "cluster1": Cluster("cluster1", 15.0),
            "cluster2": Cluster("cluster2", 13.0)
        }
        rc = ReportCard(clusters)
        self.assertTrue(r.report_card_is_eligible_for_banco(rc))

        clusters = {
            "cluster1": Cluster("cluster1", 14.0),
            "cluster2": Cluster("cluster2", 13.0)
        }
        rc = ReportCard(clusters)
        self.assertFalse(r.report_card_is_eligible_for_banco(rc))

        clusters = {
            "cluster1": Cluster("cluster1", 15.0),
            "cluster2": Cluster("cluster2", 12.0)
        }
        rc = ReportCard(clusters)
        self.assertFalse(r.report_card_is_eligible_for_banco(rc))

        clusters = {
            "cluster1": Cluster("cluster1", 15.0),
            "cluster2": Cluster("cluster2", None)
        }
        rc = ReportCard(clusters)
        self.assertFalse(r.report_card_is_eligible_for_banco(rc))

    def test_cluster_can_boost_money(self):
        r = rules.Rules('test_rules.json')
        cluster1 = Cluster("cluster1", 15.0)
        can_boost = r.cluster_can_boost_money(cluster1)
        self.assertFalse(can_boost)

        cluster2 = Cluster("cluster2", 12.0)
        can_boost = r.cluster_can_boost_money(cluster2)
        self.assertTrue(can_boost)

        cluster2 = Cluster("unknown", 12.0)
        can_boost = r.cluster_can_boost_money(cluster2)
        self.assertFalse(can_boost)

    def test_cluster_is_eligible_for_banco(self):
        r = rules.Rules('test_rules.json')
        cluster1 = Cluster("cluster1", 15.0)
        is_eligible = r.cluster_is_eligible_for_banco(cluster1)
        self.assertTrue(is_eligible)

        cluster2 = Cluster("cluster2", 13.0)
        is_eligible = r.cluster_is_eligible_for_banco(cluster2)
        self.assertTrue(is_eligible)

        cluster_unknown = Cluster("unknown", 13.0)
        is_eligible = r.cluster_is_eligible_for_banco(cluster_unknown)
        self.assertFalse(is_eligible)

        cluster1 = Cluster("cluster1", 13.0)
        is_eligible = r.cluster_is_eligible_for_banco(cluster1)
        self.assertFalse(is_eligible)

        cluster2 = Cluster("cluster2", 11.0)
        is_eligible = r.cluster_is_eligible_for_banco(cluster2)
        self.assertFalse(is_eligible)

        cluster2 = Cluster("cluster2", None)
        is_eligible = r.cluster_is_eligible_for_banco(cluster2)
        self.assertFalse(is_eligible)

    def test_cluster_is_eligible_for_boost(self):
        r = rules.Rules('test_rules.json')
        cluster2 = Cluster("cluster2", 12.0)
        is_eligible = r.cluster_is_eligible_for_boost(cluster2)
        self.assertTrue(is_eligible)

        cluster_unknown = Cluster("unknown", 13.0)
        is_eligible = r.cluster_is_eligible_for_boost(cluster_unknown)
        self.assertFalse(is_eligible)

        cluster1 = Cluster("cluster1", 20.0)
        is_eligible = r.cluster_is_eligible_for_boost(cluster1)
        self.assertFalse(is_eligible)

        cluster2 = Cluster("cluster2", 11.0)
        is_eligible = r.cluster_is_eligible_for_boost(cluster2)
        self.assertFalse(is_eligible)

        cluster2 = Cluster("cluster2", None)
        is_eligible = r.cluster_is_eligible_for_boost(cluster2)
        self.assertFalse(is_eligible)

    def test_cluster_is_eligible_for_marathon(self):
        r = rules.Rules('test_rules.json')
        cluster1 = Cluster("cluster1", 11.0)
        is_eligible = r.cluster_is_eligible_for_marathon(cluster1)
        self.assertTrue(is_eligible)

        cluster2 = Cluster("cluster2", 10.0)
        is_eligible = r.cluster_is_eligible_for_marathon(cluster2)
        self.assertTrue(is_eligible)

        cluster_unknown = Cluster("unknown", 13.0)
        is_eligible = r.cluster_is_eligible_for_marathon(cluster_unknown)
        self.assertFalse(is_eligible)

        cluster1 = Cluster("cluster1", 10.0)
        is_eligible = r.cluster_is_eligible_for_marathon(cluster1)
        self.assertFalse(is_eligible)

        cluster2 = Cluster("cluster2", 9.5)
        is_eligible = r.cluster_is_eligible_for_marathon(cluster2)
        self.assertFalse(is_eligible)

        cluster2 = Cluster("cluster2", None)
        is_eligible = r.cluster_is_eligible_for_marathon(cluster2)
        self.assertFalse(is_eligible)

    def test_subject_downgrades_eligible_cluster_for_boost(self):
        r = rules.Rules('test_rules.json')
        cluster2 = Cluster("cluster2", 12.0)
        downgrades = r.subject_downgrades_eligible_cluster_for_boost(cluster2, 11.0)
        self.assertTrue(downgrades)

        downgrades = r.subject_downgrades_eligible_cluster_for_boost(cluster2, 0.0)
        self.assertTrue(downgrades)

        downgrades = r.subject_downgrades_eligible_cluster_for_boost(cluster2, 12.0)
        self.assertFalse(downgrades)

        downgrades = r.subject_downgrades_eligible_cluster_for_boost(cluster2, None)
        self.assertFalse(downgrades)

        cluster_unknown = Cluster("unknown", 13.0)
        downgrades = r.subject_downgrades_eligible_cluster_for_boost(cluster_unknown, 15.0)
        self.assertFalse(downgrades)

    def test_subject_downgrades_eligible_cluster_for_marathon(self):
        r = rules.Rules('test_rules.json')
        cluster1 = Cluster("cluster1", 11.0)
        downgrades = r.subject_downgrades_eligible_cluster_for_marathon(cluster1, 9.5)
        self.assertTrue(downgrades)

        cluster2 = Cluster("cluster2", 10.0)
        downgrades = r.subject_downgrades_eligible_cluster_for_marathon(cluster2, 9.5)
        self.assertTrue(downgrades)

        downgrades = r.subject_downgrades_eligible_cluster_for_marathon(cluster2, 0.0)
        self.assertTrue(downgrades)

        downgrades = r.subject_downgrades_eligible_cluster_for_marathon(cluster1, 11.0)
        self.assertFalse(downgrades)

        downgrades = r.subject_downgrades_eligible_cluster_for_marathon(cluster2, 10.0)
        self.assertFalse(downgrades)

        downgrades = r.subject_downgrades_eligible_cluster_for_marathon(cluster2, None)
        self.assertFalse(downgrades)

    def test_get_cluster_boost_money(self):
        r = rules.Rules('test_rules.json')
        cluster2 = Cluster("cluster2", 12.0)
        money = r.get_cluster_boost_money(cluster2)
        self.assertEqual(money, 60)

        cluster2 = Cluster("cluster2", 0.0)
        money = r.get_cluster_boost_money(cluster2)
        self.assertEqual(money, 60)

        cluster1 = Cluster("cluster1", 11.0)
        money = r.get_cluster_boost_money(cluster1)
        self.assertIsNone(money)

        cluster_unknown = Cluster("unknown", 13.0)
        money = r.get_cluster_boost_money(cluster_unknown)
        self.assertIsNone(money)

    def test_get_cluster_marathon_money(self):
        r = rules.Rules('test_rules.json')
        cluster1 = Cluster("cluster1", 11.0)
        money = r.get_cluster_marathon_money(cluster1)
        self.assertEqual(money, 40)

        cluster2 = Cluster("cluster2", 12.0)
        money = r.get_cluster_marathon_money(cluster2)
        self.assertEqual(money, 30)

        cluster2 = Cluster("cluster2", 0.0)
        money = r.get_cluster_marathon_money(cluster2)
        self.assertEqual(money, 30)

        cluster_unknown = Cluster("unknown", 13.0)
        money = r.get_cluster_marathon_money(cluster_unknown)
        self.assertIsNone(money)

    def test_get_cluster_money(self):
        r = rules.Rules('test_rules.json')
        cluster1 = Cluster("cluster1", 11.0)
        money = r.get_cluster_money(cluster1)
        self.assertEqual(money, 40)

        cluster1 = Cluster("cluster1", 0.0)
        money = r.get_cluster_money(cluster1)
        self.assertIsNone(money)

        cluster2 = Cluster("cluster2", 12.0)
        money = r.get_cluster_money(cluster2)
        self.assertEqual(money, 90)

        cluster2 = Cluster("cluster2", 10.0)
        money = r.get_cluster_money(cluster2)
        self.assertEqual(money, 30)

        cluster2 = Cluster("cluster2", 0.0)
        money = r.get_cluster_money(cluster2)
        self.assertIsNone(money)

        cluster_unknown = Cluster("unknown", 13.0)
        money = r.get_cluster_money(cluster_unknown)
        self.assertIsNone(money)

    def test_get_report_card_money(self):
        r = rules.Rules('test_rules.json')
        clusters = {
            "cluster1": Cluster("cluster1", 15.0),
            "cluster2": Cluster("cluster2", 15.0)
        }
        rc = ReportCard(clusters)
        money = r.get_report_card_money(rc)
        self.assertEqual(money, 130)

        clusters = {
            "cluster1": Cluster("cluster1", 15.0),
            "cluster2": Cluster("cluster2", 12.0)
        }
        rc = ReportCard(clusters)
        money = r.get_report_card_money(rc)
        self.assertEqual(money, 130)

        clusters = {
            "cluster1": Cluster("cluster1", 15.0),
            "cluster2": Cluster("cluster2", 11.0)
        }
        rc = ReportCard(clusters)
        money = r.get_report_card_money(rc)
        self.assertEqual(money, 70)

        clusters = {
            "cluster1": Cluster("cluster1", 10.0),
            "cluster2": Cluster("cluster2", 11.0)
        }
        rc = ReportCard(clusters)
        money = r.get_report_card_money(rc)
        self.assertEqual(money, 30)

        clusters = {
            "cluster1": Cluster("cluster1", 11.0),
            "cluster2": Cluster("cluster2", 9.0)
        }
        rc = ReportCard(clusters)
        money = r.get_report_card_money(rc)
        self.assertEqual(money, 40)

        clusters = {
            "cluster1": Cluster("cluster1", 9.0),
            "cluster2": Cluster("cluster2", 9.0)
        }
        rc = ReportCard(clusters)
        money = r.get_report_card_money(rc)
        self.assertEqual(money, 0)

        clusters = {
            "cluster1": Cluster("cluster1", 0.0),
            "cluster2": Cluster("cluster2", 0.0)
        }
        rc = ReportCard(clusters)
        money = r.get_report_card_money(rc)
        self.assertEqual(money, 0)

        clusters = {
            "cluster1": Cluster("cluster1", 15.0),
            "cluster2": Cluster("cluster2", None)
        }
        rc = ReportCard(clusters)
        money = r.get_report_card_money(rc)
        self.assertEqual(money, 40)

        clusters = {
            "cluster1": Cluster("cluster1", None),
            "cluster2": Cluster("cluster2", 15.0)
        }
        rc = ReportCard(clusters)
        money = r.get_report_card_money(rc)
        self.assertEqual(money, 90)

        clusters = {
            "unknown": Cluster("unknown", 15.0)
        }
        rc = ReportCard(clusters)
        money = r.get_report_card_money(rc)
        self.assertEqual(money, 0)

    def test_get_banco_rate(self):
        r = rules.Rules('test_rules.json')
        clusters = {
            "cluster1": Cluster("cluster1", 15.0),
            "cluster2": Cluster("cluster2", 13.0)
        }
        rc = ReportCard(clusters)
        rate = r.get_banco_rate(rc)
        self.assertEqual(rate, 100)

        clusters = {
            "cluster1": Cluster("cluster1", 15.0),
            "cluster2": Cluster("cluster2", 12.0)
        }
        rc = ReportCard(clusters)
        rate = r.get_banco_rate(rc)
        self.assertEqual(rate, 50)

        clusters = {
            "cluster1": Cluster("cluster1", 14.0),
            "cluster2": Cluster("cluster2", 12.0)
        }
        rc = ReportCard(clusters)
        rate = r.get_banco_rate(rc)
        self.assertEqual(rate, 0)

        clusters = {
            "cluster1": Cluster("cluster1", 15.0),
            "cluster2": Cluster("cluster2", None)
        }
        rc = ReportCard(clusters)
        rate = r.get_banco_rate(rc)
        self.assertEqual(rate, 50)

        clusters = {
            "cluster1": Cluster("cluster1", None),
            "cluster2": Cluster("cluster2", 15.0)
        }
        rc = ReportCard(clusters)
        rate = r.get_banco_rate(rc)
        self.assertEqual(rate, 50)

        clusters = {
            "unknown": Cluster("unknown", 15.0)
        }
        rc = ReportCard(clusters)
        rate = r.get_banco_rate(rc)
        self.assertEqual(rate, 0)


    def test_get_target_amount_rate(self):
        r = rules.Rules('test_rules.json')
        clusters = {
            "cluster1": Cluster("cluster1", 15.0),
            "cluster2": Cluster("cluster2", 15.0)
        }
        rc = ReportCard(clusters)
        rate = r.get_target_amount_rate(rc)
        self.assertEqual(rate, 130/200.*100)

        clusters = {
            "cluster1": Cluster("cluster1", 15.0),
            "cluster2": Cluster("cluster2", 12.0)
        }
        rc = ReportCard(clusters)
        rate = r.get_target_amount_rate(rc)
        self.assertEqual(rate, 130/200.*100)

        clusters = {
            "cluster1": Cluster("cluster1", 15.0),
            "cluster2": Cluster("cluster2", 11.0)
        }
        rc = ReportCard(clusters)
        rate = r.get_target_amount_rate(rc)
        self.assertEqual(rate, 70/200.*100)

        clusters = {
            "cluster1": Cluster("cluster1", 10.0),
            "cluster2": Cluster("cluster2", 11.0)
        }
        rc = ReportCard(clusters)
        rate = r.get_target_amount_rate(rc)
        self.assertEqual(rate, 30/200.*100)

        clusters = {
            "cluster1": Cluster("cluster1", 11.0),
            "cluster2": Cluster("cluster2", 9.0)
        }
        rc = ReportCard(clusters)
        rate = r.get_target_amount_rate(rc)
        self.assertEqual(rate, 40/200.*100)

        clusters = {
            "cluster1": Cluster("cluster1", 9.0),
            "cluster2": Cluster("cluster2", 9.0)
        }
        rc = ReportCard(clusters)
        rate = r.get_target_amount_rate(rc)
        self.assertEqual(rate, 0.)

        clusters = {
            "cluster1": Cluster("cluster1", 0.0),
            "cluster2": Cluster("cluster2", 0.0)
        }
        rc = ReportCard(clusters)
        rate = r.get_target_amount_rate(rc)
        self.assertEqual(rate, 0.)

        clusters = {
            "cluster1": Cluster("cluster1", 15.0),
            "cluster2": Cluster("cluster2", None)
        }
        rc = ReportCard(clusters)
        rate = r.get_target_amount_rate(rc)
        self.assertEqual(rate, 40/200.*100)

        clusters = {
            "cluster1": Cluster("cluster1", None),
            "cluster2": Cluster("cluster2", 15.0)
        }
        rc = ReportCard(clusters)
        rate = r.get_target_amount_rate(rc)
        self.assertEqual(rate, 90/200.*100)

        clusters = {
            "unknown": Cluster("unknown", 15.0)
        }
        rc = ReportCard(clusters)
        rate = r.get_target_amount_rate(rc)
        self.assertEqual(rate, 0.)


    def test_get_banco_description(self):
        r = rules.Rules('test_rules.json')
        self.assertEqual(r.get_banco_description(), "Banco description")

    def test_get_boost_description(self):
        r = rules.Rules('test_rules.json')
        self.assertEqual(r.get_boost_description(), "Boost description")

    def test_get_marathon_description(self):
        r = rules.Rules('test_rules.json')
        self.assertEqual(r.get_marathon_description(), "Marathon description")

if __name__ == "__main__":
    unittest.main()