from __future__ import annotations
from dataclasses import dataclass, field
import datetime
from typing import TYPE_CHECKING, NamedTuple

from .err import ParsingError

from .simple_objects import Absence, Average, Delay, Grade

from . import parse
from .parse import locator

if TYPE_CHECKING:
    from .clients import Client


class TermGrades(NamedTuple):
    grades: list[Grade]
    subject_avgs: list[Average] | None
    student_overall_average: str | None
    class_overall_average: str | None


class TermAbsencesAndPunishments(NamedTuple):
    absences: list[Absence]
    delays: list[Delay]
    # punishments: list[Punishment]


@dataclass(init=False)
class Term:
    """A portion of the school year"""

    id: str = field(compare=False)
    """Session-specific ID of the object"""
    name: str
    """Period name"""
    start: datetime.datetime
    """Start of the period"""
    end: datetime.datetime
    """End of the period"""

    def __init__(self, client: Client, json_dict: dict) -> None:
        get = locator(json_dict)

        self.id = get(str, "N")
        self.name = get(str, "L")
        self.start = get(parse.datetime, "dateDebut", "V")
        self.end = get(parse.datetime, "dateFin", "V")

        self._client = client

    async def grades(self) -> TermGrades:
        """Get grades and averages from this term

        Returns:
            A (named) tuple of the grades and averages. Averages might be None if they're hidden
            on PRONOTE.
        """

        json_data = {"Periode": {"N": self.id, "L": self.name}}
        response = locator(await self._client.post("DernieresNotes", 198, json_data))

        avgs = None

        try:
            avgs = response(parse.many(Average), *parse.data_path, "listeServices", "V")
        except ParsingError as e:
            if e.path != ["moyEleve", "V"]:
                raise

        return TermGrades(
            response(parse.many(Grade), *parse.data_path, "listeDevoirs", "V"),
            avgs,
            response(str, *parse.data_path, "moyGenerale", "V"),
            response(str, *parse.data_path, "moyGeneraleClasse", "V"),
        )

    async def absences_and_punishments(self) -> TermAbsencesAndPunishments:
        """All absences, delays, and punishments from this term

        Returns:
            A (named) tuple of the absences, delays, and punishments.
        """

        json_data = {
            "periode": {"N": self.id, "L": self.name, "G": 2},
            "DateDebut": {"_T": 7, "V": self.start.strftime("%d/%m/%Y %H:%M:%S")},
            "DateFin": {"_T": 7, "V": self.end.strftime("%d/%m/%Y %H:%M:%S")},
        }

        response = locator(await self._client.post("PagePresence", 19, json_data))
        absences = response(list, *parse.data_path, "listeAbsences", "V")

        return TermAbsencesAndPunishments(
            [Absence(a) for a in absences if a["G"] == 13],
            [Delay(a) for a in absences if a["G"] == 14],
            # [Punishment(self._client, a) for a in absences if a["G"] == 41]
        )

    # @property
    # def evaluations(self) -> List["Evaluation"]:
    #     """
    #     All evaluations from this period
    #     """
    #     json_data = {"periode": {"N": self.id, "L": self.name, "G": 2}}
    #     response = self._client.post("DernieresEvaluations", 201, json_data)
    #     evaluations = response["dataSec"]["data"]["listeEvaluations"]["V"]
    #     return [Evaluation(e) for e in evaluations]

    # @property
    # def report(self) -> Optional[Report]:
    #     """
    #     Gets a report from a period.
    #
    #     Returns:
    #         Optional[Report]:
    #             When ``None``, then the report is not yet published or is unavailable for any other reason
    #     """
    #     json_data = {"periode": {"G": 2, "N": self.id, "L": self.name}}
    #     data = self._client.post("PageBulletins", 13, json_data)["dataSec"]["data"]
    #     return Report(data) if "Message" not in data else None
