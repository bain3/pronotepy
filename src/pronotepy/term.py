from __future__ import annotations
from dataclasses import dataclass, field
import datetime
from typing import TYPE_CHECKING

from .simple_objects import Grade

from . import parse
from .parse import locator

if TYPE_CHECKING:
    from .clients import Client


@dataclass(init=False)
class Term:
    """A portion of the school year"""

    """Session-specific ID of the object"""
    id: str = field(compare=False)

    """Period name"""
    name: str

    """Start of the period"""
    start: datetime.datetime

    """End of the period"""
    end: datetime.datetime

    def __init__(self, client: Client, json_dict: dict) -> None:
        get = locator(json_dict)

        self.id = get(str, "N")
        self.name = get(str, "L")
        self.start = get(parse.datetime, "dateDebut", "V")
        self.end = get(parse.datetime, "dateFin", "V")

        self._client = client

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
    #
    async def grades(self) -> list[Grade]:
        """Get grades from the term"""
        json_data = {"Periode": {"N": self.id, "L": self.name}}
        response = await self._client.post("DernieresNotes", 198, json_data)

        return locator(response)(parse.many(Grade), *parse.data_path, "listeDevoirs", "V")

    #
    # @property
    # def averages(self) -> List["Average"]:
    #     """Get averages from the period."""
    #
    #     json_data = {"Periode": {"N": self.id, "L": self.name}}
    #     response = self._client.post("DernieresNotes", 198, json_data)
    #     crs = response["dataSec"]["data"]["listeServices"]["V"]
    #     try:
    #         return [Average(c) for c in crs]
    #     except ParsingError as e:
    #         if e.path == ["moyEleve", "V"]:
    #             raise UnsupportedOperation("Could not get averages")
    #         raise
    #
    # @property
    # def overall_average(self) -> str:
    #     """Get overall average from the period. If the period average is not provided by pronote, then it's calculated.
    #     Calculation may not be the same as the actual average. (max difference 0.01)"""
    #     json_data = {"Periode": {"N": self.id, "L": self.name}}
    #     response = self._client.post("DernieresNotes", 198, json_data)
    #     average = response["dataSec"]["data"].get("moyGenerale")
    #     return average["V"] if average else None
    #
    # @property
    # def class_overall_average(self) -> Optional[str]:
    #     """Get group average from the period."""
    #     json_data = {"Periode": {"N": self.id, "L": self.name}}
    #     response = self._client.post("DernieresNotes", 198, json_data)
    #     average = response["dataSec"]["data"].get("moyGeneraleClasse")
    #     if average:
    #         return average["V"]
    #     else:
    #         return None
    #
    # @property
    # def evaluations(self) -> List["Evaluation"]:
    #     """
    #     All evaluations from this period
    #     """
    #     json_data = {"periode": {"N": self.id, "L": self.name, "G": 2}}
    #     response = self._client.post("DernieresEvaluations", 201, json_data)
    #     evaluations = response["dataSec"]["data"]["listeEvaluations"]["V"]
    #     return [Evaluation(e) for e in evaluations]
    #
    # @property
    # def absences(self) -> List[Absence]:
    #     """
    #     All absences from this period
    #     """
    #     json_data = {
    #         "periode": {"N": self.id, "L": self.name, "G": 2},
    #         "DateDebut": {"_T": 7, "V": self.start.strftime("%d/%m/%Y %H:%M:%S")},
    #         "DateFin": {"_T": 7, "V": self.end.strftime("%d/%m/%Y %H:%M:%S")},
    #     }
    #
    #     response = self._client.post("PagePresence", 19, json_data)
    #     absences = response["dataSec"]["data"]["listeAbsences"]["V"]
    #     return [Absence(a) for a in absences if a["G"] == 13]
    #
    # @property
    # def delays(self) -> List[Delay]:
    #     """
    #     All delays from this period
    #     """
    #     json_data = {
    #         "periode": {"N": self.id, "L": self.name, "G": 2},
    #         "DateDebut": {"_T": 7, "V": self.start.strftime("%d/%m/%Y %H:%M:%S")},
    #         "DateFin": {"_T": 7, "V": self.end.strftime("%d/%m/%Y %H:%M:%S")},
    #     }
    #
    #     response = self._client.post("PagePresence", 19, json_data)
    #     delays = response["dataSec"]["data"]["listeAbsences"]["V"]
    #     return [Delay(a) for a in delays if a["G"] == 14]
    #
    # @property
    # def punishments(self) -> List[Punishment]:
    #     """
    #     All punishments from a given period
    #     """
    #     json_data = {
    #         "periode": {"N": self.id, "L": self.name, "G": 2},
    #         "DateDebut": {"_T": 7, "V": self.start.strftime("%d/%m/%Y %H:%M:%S")},
    #         "DateFin": {"_T": 7, "V": self.end.strftime("%d/%m/%Y %H:%M:%S")},
    #     }
    #
    #     response = self._client.post("PagePresence", 19, json_data)
    #     absences = response["dataSec"]["data"]["listeAbsences"]["V"]
    #     return [Punishment(self._client, a) for a in absences if a["G"] == 41]
