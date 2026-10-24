"""Regression tests for missing subject-level class statistics (synthetic data)."""

import unittest

from pronotepy.dataClasses import Average
from pronotepy.exceptions import ParsingError


def subject(**overrides):
    data = {
        "N": "synthetic-subject-001",
        "L": "EXAMPLE SUBJECT",
        "G": 12,
        "moyEleve": {"V": "13,75"},
        "baremeMoyEleve": {"V": "20"},
        "baremeMoyEleveParDefault": {"V": "20"},
    }
    data.update(overrides)
    return data


class AverageOptionalClassStatisticsTests(unittest.TestCase):
    def test_missing_class_statistics_keep_student_average(self):
        average = Average(subject())
        self.assertEqual(average.student, "13,75")
        self.assertEqual(average.out_of, "20")
        self.assertEqual(average.subject.name, "EXAMPLE SUBJECT")
        self.assertIsNone(average.class_average)
        self.assertIsNone(average.min)
        self.assertIsNone(average.max)

    def test_present_class_statistics_are_preserved(self):
        average = Average(subject(
            moyClasse={"V": "15,50"},
            moyMin={"V": "8,75"},
            moyMax={"V": "19,90"},
        ))
        self.assertEqual(average.class_average, "15,50")
        self.assertEqual(average.min, "8,75")
        self.assertEqual(average.max, "19,90")

    def test_partially_missing_statistics_are_independently_optional(self):
        average = Average(subject(moyMin={"V": "7,00"}))
        self.assertIsNone(average.class_average)
        self.assertEqual(average.min, "7,00")
        self.assertIsNone(average.max)

    def test_missing_nested_value_is_treated_as_missing(self):
        average = Average(subject(moyClasse={}))
        self.assertIsNone(average.class_average)

    def test_student_average_remains_required(self):
        data = subject()
        del data["moyEleve"]
        with self.assertRaises(ParsingError):
            Average(data)

    def test_student_denominator_remains_required(self):
        data = subject()
        del data["baremeMoyEleve"]
        with self.assertRaises(ParsingError):
            Average(data)

    def test_invalid_present_statistic_is_not_silently_accepted(self):
        with self.assertRaises(ParsingError):
            Average(subject(moyClasse={"V": None}))

    def test_two_subjects_one_without_stats(self):
        data = [subject(), subject(
            L="SECOND EXAMPLE SUBJECT",
            moyClasse={"V": "16,00"},
        )]
        values = [Average(item) for item in data]
        self.assertEqual(len(values), 2)
        self.assertIsNone(values[0].class_average)
        self.assertEqual(values[1].class_average, "16,00")


if __name__ == "__main__":
    unittest.main()
