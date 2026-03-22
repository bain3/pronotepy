"""Tests for Grade parsing with missing optional fields.

Some Pronote instances (e.g. 0941093c.index-education.net) do not include
fields like noteMax, noteMin, coefficient, etc. in their grade JSON data.
These tests verify that Grade objects can be constructed without crashing
when those fields are absent.
"""

import unittest
from unittest.mock import MagicMock

from pronotepy.dataClasses import Grade, Period


def _make_grade_json(
    include_noteMax=True,
    include_noteMin=True,
    include_coefficient=True,
    include_commentaire=True,
    include_estBonus=True,
    include_estFacultatif=True,
    include_estRamenerSur20=True,
    include_moyenne=True,
):
    """Build a grade JSON dict with optional fields toggled on/off."""
    # Minimal required fields
    json_dict = {
        "N": "001",
        "note": {"V": "15"},
        "bareme": {"V": "20"},
        "baremeParDefaut": {"V": "20"},
        "date": {"V": "15/01/2026"},
        "service": {"V": {"N": "101", "L": "MATHEMATIQUES", "estServiceGroupe": False}},
        "periode": {"V": {"N": "test_period_id"}},
    }
    if include_noteMax:
        json_dict["noteMax"] = {"V": "19"}
    if include_noteMin:
        json_dict["noteMin"] = {"V": "5"}
    if include_coefficient:
        json_dict["coefficient"] = "1"
    if include_commentaire:
        json_dict["commentaire"] = "Good work"
    if include_estBonus:
        json_dict["estBonus"] = False
    if include_estFacultatif:
        json_dict["estFacultatif"] = False
    if include_estRamenerSur20:
        json_dict["estRamenerSur20"] = False
    if include_moyenne:
        json_dict["moyenne"] = {"V": "12"}
    return json_dict


class TestGradeMissingFields(unittest.TestCase):
    """Test that Grade parsing handles missing optional fields gracefully."""

    @classmethod
    def setUpClass(cls):
        # Create a mock Period instance so the period resolver can find it
        mock_period = MagicMock(spec=Period)
        mock_period.id = "test_period_id"
        Period.instances.add(mock_period)

    @classmethod
    def tearDownClass(cls):
        # Clean up mock period instances
        Period.instances = {p for p in Period.instances if not isinstance(p, MagicMock)}

    def test_all_fields_present(self):
        """Parsing works when all fields are present."""
        json_dict = _make_grade_json()
        grade = Grade(json_dict)
        self.assertEqual(grade.grade, "15")
        self.assertEqual(grade.max, "19")
        self.assertEqual(grade.min, "5")
        self.assertEqual(grade.coefficient, "1")
        self.assertEqual(grade.comment, "Good work")
        self.assertFalse(grade.is_bonus)
        self.assertFalse(grade.is_optionnal)
        self.assertFalse(grade.is_out_of_20)

    def test_missing_noteMax(self):
        """Parsing does not crash when noteMax is missing."""
        json_dict = _make_grade_json(include_noteMax=False)
        grade = Grade(json_dict)
        self.assertIsNone(grade.max)
        # Other fields should still be parsed correctly
        self.assertEqual(grade.grade, "15")
        self.assertEqual(grade.min, "5")

    def test_missing_noteMin(self):
        """Parsing does not crash when noteMin is missing."""
        json_dict = _make_grade_json(include_noteMin=False)
        grade = Grade(json_dict)
        self.assertIsNone(grade.min)

    def test_missing_coefficient(self):
        """Parsing does not crash when coefficient is missing."""
        json_dict = _make_grade_json(include_coefficient=False)
        grade = Grade(json_dict)
        self.assertIsNone(grade.coefficient)

    def test_missing_commentaire(self):
        """Parsing does not crash when commentaire is missing."""
        json_dict = _make_grade_json(include_commentaire=False)
        grade = Grade(json_dict)
        self.assertIsNone(grade.comment)

    def test_missing_estBonus(self):
        """Parsing does not crash when estBonus is missing."""
        json_dict = _make_grade_json(include_estBonus=False)
        grade = Grade(json_dict)
        self.assertFalse(grade.is_bonus)

    def test_missing_estFacultatif(self):
        """Parsing does not crash when estFacultatif is missing."""
        json_dict = _make_grade_json(include_estFacultatif=False)
        grade = Grade(json_dict)
        self.assertFalse(grade.is_optionnal)

    def test_missing_estRamenerSur20(self):
        """Parsing does not crash when estRamenerSur20 is missing."""
        json_dict = _make_grade_json(include_estRamenerSur20=False)
        grade = Grade(json_dict)
        self.assertFalse(grade.is_out_of_20)

    def test_missing_moyenne(self):
        """Parsing does not crash when moyenne is missing."""
        json_dict = _make_grade_json(include_moyenne=False)
        grade = Grade(json_dict)
        self.assertIsNone(grade.average)

    def test_all_optional_fields_missing(self):
        """Parsing does not crash when ALL optional fields are missing.

        This simulates the worst case scenario where a Pronote instance
        returns only the bare minimum grade data.
        """
        json_dict = _make_grade_json(
            include_noteMax=False,
            include_noteMin=False,
            include_coefficient=False,
            include_commentaire=False,
            include_estBonus=False,
            include_estFacultatif=False,
            include_estRamenerSur20=False,
            include_moyenne=False,
        )
        grade = Grade(json_dict)
        self.assertEqual(grade.grade, "15")
        self.assertEqual(grade.out_of, "20")
        self.assertIsNone(grade.max)
        self.assertIsNone(grade.min)
        self.assertIsNone(grade.coefficient)
        self.assertIsNone(grade.comment)
        self.assertFalse(grade.is_bonus)
        self.assertFalse(grade.is_optionnal)
        self.assertFalse(grade.is_out_of_20)
        self.assertIsNone(grade.average)


if __name__ == "__main__":
    unittest.main()
