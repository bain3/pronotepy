import datetime
import logging
from time import time
from typing import List, Callable, Optional, Union, TypeVar, Type

from Crypto.Hash import SHA256
from uuid import uuid4
import re

from . import dataClasses
from .exceptions import *
from .pronoteAPI import (
    _Communication,
    _Encryption,
    _KeepAlive,
    _enleverAlea,
    _prepare_onglets,
    log,
)

T = TypeVar("T", bound="_ClientBase")


class _ClientBase:
    """
    Base for every PRONOTE client. Ensures login.

    Parameters
    ----------
    pronote_url : str
        URL of the server
    username : str
    password : str
    ent : Callable
        Cookies for ENT connections

    Attributes
    ----------
    start_day : datetime.datetime
        The first day of the school year
    week : int
        The current week of the school year
    logged_in : bool
        If the user is successfully logged in
    username : str
    password : str
    pronote_url : str
    info: dataClasses.ClientInfo
        Provides information about the current client. Name etc...
    """

    def __init__(
        self,
        pronote_url: str,
        username: str = "",
        password: str = "",
        ent: Optional[Callable] = None,
        qr_code: bool = False,
    ) -> None:
        log.info("INIT")
        # start communication session
        if not len(password) + len(username):
            raise PronoteAPIError(
                "Please provide login credentials. Cookies are None, and username and password are empty."
            )

        self.ent = ent
        if ent:
            pronote_url = pronote_url.replace("login=true", "")
            cookies = ent(username, password)
        else:
            cookies = None

        self.uuid = str(uuid4())
        self.mobile = qr_code

        self.username = username
        self.password = password
        self.pronote_url = pronote_url
        self.communication = _Communication(pronote_url, cookies, self)
        self.attributes, self.func_options = self.communication.initialise()

        # set up encryption
        self.encryption = _Encryption()
        self.encryption.aes_iv = self.communication.encryption.aes_iv

        # some other attribute creation
        self._last_ping = time()

        self.parametres_utilisateur: dict = {}
        self.auth_cookie: dict = {}
        self.info: dataClasses.ClientInfo

        self.start_day = datetime.datetime.strptime(
            self.func_options["donneesSec"]["donnees"]["General"]["PremierLundi"]["V"],
            "%d/%m/%Y",
        ).date()
        self.week = self.get_week(datetime.date.today())

        self._refreshing = False

        self.periods_: Optional[List[dataClasses.Period]]
        self.periods_ = self.periods
        self.logged_in = self._login()
        self._expired = False

    @classmethod
    def qrcode_login(cls: Type[T], qr_code: dict, pin: str) -> T:
        """
        Login with QR code

        qr_code: dict
            JSON store in the QR code
        pin: str
            4-digit confirmation code created during QR code setup
        """
        encryption = _Encryption()
        encryption.aes_set_key(pin.encode())

        short_token = bytes.fromhex(qr_code["login"])
        long_token = bytes.fromhex(qr_code["jeton"])

        try:
            login = encryption.aes_decrypt(short_token).decode()
            jeton = encryption.aes_decrypt(long_token).decode()
        except CryptoError as ex:
            ex.args += (
                "exception happened during login -> probably the confirmation code is not valid",
            )
            raise

        # add ?login=true at the end of the url
        url = re.sub(r"(\?.*)|( *)$", "?login=true", qr_code["url"], 0)

        return cls(url, login, jeton, qr_code=True)

    def _login(self) -> bool:
        """
        Logs in the user.

        Returns
        -------
        bool
            True if logged in, False if not
        """
        if self.ent:
            self.username = self.attributes["e"]
            self.password = self.attributes["f"]
        # identification phase
        ident_json = {
            "genreConnexion": 0,
            "genreEspace": int(self.attributes["a"]),
            "identifiant": self.username,
            "pourENT": True if self.ent else False,
            "enConnexionAuto": False,
            "demandeConnexionAuto": False,
            "demandeConnexionAppliMobile": self.mobile,
            "demandeConnexionAppliMobileJeton": self.mobile,
            "uuidAppliMobile": self.uuid if self.mobile else "",
            "loginTokenSAV": "",
        }
        idr = self.post("Identification", data=ident_json)
        log.debug("indentification")

        # creating the authentification data
        log.debug(str(idr))
        challenge = idr["donneesSec"]["donnees"]["challenge"]
        e = _Encryption()
        e.aes_set_iv(self.communication.encryption.aes_iv)

        # key gen
        if self.ent:
            motdepasse = SHA256.new(str(self.password).encode()).hexdigest().upper()
            e.aes_set_key(motdepasse.encode())
        elif self.mobile:
            u = self.username
            p = self.password
            if idr["donneesSec"]["donnees"]["modeCompLog"]:
                u = u.lower()
            if idr["donneesSec"]["donnees"]["modeCompMdp"]:
                p = p.lower()
            motdepasse = SHA256.new(p.encode()).hexdigest().upper()
            e.aes_set_key((u + motdepasse).encode())
        else:
            u = self.username
            p = self.password
            if idr["donneesSec"]["donnees"]["modeCompLog"]:
                u = u.lower()
            if idr["donneesSec"]["donnees"]["modeCompMdp"]:
                p = p.lower()
            alea = idr["donneesSec"]["donnees"]["alea"]
            motdepasse = SHA256.new((alea + p).encode()).hexdigest().upper()
            e.aes_set_key((u + motdepasse).encode())

        # challenge
        try:
            dec = e.aes_decrypt(bytes.fromhex(challenge))
            dec_no_alea = _enleverAlea(dec.decode())
            ch = e.aes_encrypt(dec_no_alea.encode()).hex()
        except CryptoError as ex:
            if self.mobile:
                ex.args += (
                    "exception happened during login -> probably the qr code has expired (qr code is valid during 10 minutes)",
                )
            else:
                ex.args += (
                    "exception happened during login -> probably bad username/password",
                )
            raise

        # send
        auth_json = {
            "connexion": 0,
            "challenge": ch,
            "espace": int(self.attributes["a"]),
        }
        auth_response = self.post("Authentification", data=auth_json)
        if "cle" in auth_response["donneesSec"]["donnees"]:
            self.communication.after_auth(auth_response, e.aes_key)
            self.encryption.aes_key = e.aes_key
            log.info(f"successfully logged in as {self.username}")

            if self.mobile and auth_response["donneesSec"]["donnees"].get(
                "jetonConnexionAppliMobile"
            ):
                self.password = auth_response["donneesSec"]["donnees"][
                    "jetonConnexionAppliMobile"
                ]

            # getting listeOnglets separately because of pronote API change
            self.parametres_utilisateur = self.post("ParametresUtilisateur")
            self.info = dataClasses.ClientInfo(
                self, self.parametres_utilisateur["donneesSec"]["donnees"]["ressource"]
            )
            self.communication.authorized_onglets = _prepare_onglets(
                self.parametres_utilisateur["donneesSec"]["donnees"]["listeOnglets"]
            )
            log.info("got onglets data.")
            return True
        else:
            log.info("login failed")
            return False

    def get_week(self, date: Union[datetime.date, datetime.datetime]) -> int:
        if isinstance(date, datetime.datetime):
            return 1 + int((date.date() - self.start_day).days / 7)
        return 1 + int((date - self.start_day).days / 7)

    @property
    def periods(self) -> List[dataClasses.Period]:
        """
        Get all of the periods of the year.

        Returns
        -------
        List[Period]
            All the periods of the year
        """
        if hasattr(self, "periods_") and self.periods_:
            return self.periods_
        json = self.func_options["donneesSec"]["donnees"]["General"]["ListePeriodes"]
        return [dataClasses.Period(self, j) for j in json]

    def keep_alive(self) -> _KeepAlive:
        """
        Returns a context manager to keep the connection alive. When inside the context manager,
        it sends a "Presence" packet to the server after 5 minutes of inactivity from another thread.
        """
        return _KeepAlive(self)

    def refresh(self) -> None:
        """
        Now this is the true jank part of this program. It refreshes the connection if something went wrong.
        This is the classical procedure if something is broken.
        """
        logging.debug("Reinitialisation")
        self.communication.session.close()

        if self.ent:
            cookies = self.ent(self.username, self.password)
        else:
            cookies = None

        self.communication = _Communication(self.pronote_url, cookies, self)
        self.attributes, self.func_options = self.communication.initialise()

        # set up encryption

        self.encryption = _Encryption()
        self.encryption.aes_iv = self.communication.encryption.aes_iv
        self._login()
        self.periods_ = None
        self.periods_ = self.periods
        self.week = self.get_week(datetime.date.today())
        self._expired = True

    def session_check(self) -> bool:
        """Checks if the session has expired and refreshes it if it had (returns bool signifying if it was expired)"""
        self.post("Presence", 7, {})
        if self._expired:
            self._expired = False
            return True
        return False

    def post(self, function_name: str, onglet: int = None, data: dict = None) -> dict:
        """
        Preforms a raw post to the PRONOTE server. Adds signature, then passes it to _Communication.post

        Parameters
        ----------
        function_name: str
        onglet: int
        data: dict

        Returns
        -------
        Raw JSON
        """
        post_data = {}
        if onglet:
            post_data["_Signature_"] = {"onglet": onglet}
        if data:
            post_data["donnees"] = data

        try:
            return self.communication.post(function_name, post_data)
        except PronoteAPIError as e:
            if isinstance(e, ExpiredObject):
                raise e

            log.info(
                f"Have you tried turning it off and on again? ERROR: {e.pronote_error_code} | {e.pronote_error_msg}"
            )

            # prevent refresh recursion
            if self._refreshing:
                raise e
            else:
                self._refreshing = True
                self.refresh()
                self._refreshing = False

            return self.communication.post(function_name, post_data)


class Client(_ClientBase):
    """
    A PRONOTE client.

    Parameters
    ----------
    pronote_url : str
        URL of the server
    username : str
    password : str
    ent : Callable
        Cookies for ENT connections

    Attributes
    ----------
    start_day : datetime.datetime
        The first day of the school year
    week : int
        The current week of the school year
    logged_in : bool
        If the user is successfully logged in
    username : str
    password : str
    pronote_url : str
    info: dataClasses.ClientInfo
        Provides information about the current client. Name etc...
    """

    def __init__(
        self,
        pronote_url: str,
        username: str = "",
        password: str = "",
        ent: Optional[Callable] = None,
        qr_code: bool = False,
    ) -> None:
        super().__init__(pronote_url, username, password, ent, qr_code)

    def lessons(
        self,
        date_from: Union[datetime.date, datetime.datetime],
        date_to: Union[datetime.date, datetime.datetime] = None,
    ) -> List[dataClasses.Lesson]:
        """
        Gets all lessons in a given timespan.

        :rtype: List[dataClasses.Lesson]
        :returns: List of lessons

        :param date_from: Union[datetime.date, datetime.datetime]
            first date
        :param date_to: Union[datetime.date, datetime.datetime]
            second date
        """
        user = self.parametres_utilisateur["donneesSec"]["donnees"]["ressource"]
        data = {
            "ressource": user,
            "avecAbsencesEleve": False,
            "avecConseilDeClasse": True,
            "estEDTPermanence": False,
            "avecAbsencesRessource": True,
            "avecDisponibilites": True,
            "avecInfosPrefsGrille": True,
            "Ressource": user,
        }
        output = []

        # convert date to datetime
        if isinstance(date_from, datetime.date):
            date_from = datetime.datetime.combine(
                date_from, datetime.datetime.min.time()
            )

        if isinstance(date_to, datetime.date):
            date_to = datetime.datetime.combine(date_to, datetime.datetime.min.time())

        if not date_to:
            date_to = datetime.datetime.combine(date_from, datetime.datetime.max.time())

        first_week = self.get_week(date_from)
        last_week = self.get_week(date_to)

        # getting lessons for all the weeks.
        for week in range(first_week, last_week + 1):
            data["NumeroSemaine"] = data["numeroSemaine"] = week
            response = self.post("PageEmploiDuTemps", 16, data)
            l_list = response["donneesSec"]["donnees"]["ListeCours"]
            for lesson in l_list:
                output.append(dataClasses.Lesson(self, lesson))

        # since we only have week precision, we need to make it more precise on our own
        return [lesson for lesson in output if date_from <= lesson.start <= date_to]

    def export_ical(self, timezone_shift: int = 0) -> str:
        """
        Exports ICal URL for the client's timetable
        Parameters
        ----------
        timezone_shift : int
            in what timezone should the exported calendar be in (hour shift)

        Returns
        -------
        URL for the exported ICal file
        """
        user = self.parametres_utilisateur["donneesSec"]["donnees"]["ressource"]
        data = {
            "ressource": user,
            "avecAbsencesEleve": False,
            "avecConseilDeClasse": True,
            "estEDTPermanence": False,
            "avecAbsencesRessource": True,
            "avecDisponibilites": True,
            "avecInfosPrefsGrille": True,
            "Ressource": user,
            "NumeroSemaine": 1,
            "numeroSemaine": 1,
        }
        response = self.post("PageEmploiDuTemps", 16, data)
        icalsecurise = response["donneesSec"]["donnees"].get("ParametreExportiCal")
        if not icalsecurise:
            raise ICalExportError("Pronote did not return ICal token")

        ver = self.func_options["donneesSec"]["donnees"]["General"]["versionPN"]
        param = f"lh={timezone_shift}".encode().hex()

        return f"{self.communication.root_site}/ical/Edt.ics?icalsecurise={icalsecurise}&version={ver}&param={param}"

    def homework(
        self, date_from: datetime.date, date_to: datetime.date = None
    ) -> List[dataClasses.Homework]:
        """
        Get homework between two given points.

        date_from : datetime
            The first date
        date_to : datetime
            The second date. If unspecified to the end of the year.

        Returns
        -------
        List[Homework]
            Homework between two given points
        """
        if not date_to:
            date_to = datetime.datetime.strptime(
                self.func_options["donneesSec"]["donnees"]["General"]["DerniereDate"][
                    "V"
                ],
                "%d/%m/%Y",
            ).date()
        json_data = {
            "domaine": {
                "_T": 8,
                "V": f"[{self.get_week(date_from)}..{self.get_week(date_to)}]",
            }
        }

        response = self.post("PageCahierDeTexte", 88, json_data)
        h_list = response["donneesSec"]["donnees"]["ListeTravauxAFaire"]["V"]
        out = []
        for h in h_list:
            hw = dataClasses.Homework(self, h)
            if date_from <= hw.date <= date_to:
                out.append(hw)
        return out

    def get_recipients(self) -> List[dataClasses.Recipient]:
        """
        Get recipients for new discussion

        Returns
        -------
        List[dataClasses.Recipient]
        """
        # add teacher
        data = {"onglet": {"N": 0, "G": 3}}
        recipients = self.post("ListeRessourcesPourCommunication", 131, data)[
            "donneesSec"
        ]["donnees"]["listeRessourcesPourCommunication"]["V"]
        # add staff
        data = {"onglet": {"N": 0, "G": 34}}
        recipients += self.post("ListeRessourcesPourCommunication", 131, data)[
            "donneesSec"
        ]["donnees"]["listeRessourcesPourCommunication"]["V"]

        return [dataClasses.Recipient(self, r) for r in recipients]

    def new_discussion(
        self, subjet: str, message: str, recipients: List[dataClasses.Recipient]
    ) -> None:
        """
        Create a new discussion
        """
        recipients_json = [{"N": r.id, "G": r._type, "L": r.name} for r in recipients]
        data = {
            "objet": subjet,
            "contenu": message,
            "listeDestinataires": recipients_json,
        }

        self.post("SaisieMessage", 131, data)

    def discussions(self) -> List[dataClasses.Discussion]:
        """
        Gets all the discussions in the discussions tab

        Returns
        -------
        List[Discussion]
        """
        discussions = self.post(
            "ListeMessagerie", 131, {"avecMessage": True, "avecLu": True}
        )
        return [
            dataClasses.Discussion(self, d)
            for d in discussions["donneesSec"]["donnees"]["listeMessagerie"]["V"]
            if d.get("estUneDiscussion")
        ]

    def information_and_surveys(
        self,
        date_from: datetime.datetime = None,
        date_to: datetime.datetime = None,
        only_unread: bool = False,
    ) -> List[dataClasses.Information]:
        """
        Gets all the information and surveys in the information and surveys tab.

        Parameters
        ----------
        only_unread : bool
            Return only unread information
        date_from : datetime.datetime
            The first date
        date_to : datetime.datetime
            The second date

        Returns
        -------
        List[Information]
            Information
        """
        response = self.post("PageActualites", 8, {"estAuteur": False})
        info = [
            dataClasses.Information(self, info)
            for info in response["donneesSec"]["donnees"]["listeActualites"]["V"]
        ]

        if only_unread:
            info = [i for i in info if not i.read]

        if date_from is not None:
            info = [i for i in info if i.start_date >= date_from]

        if date_to is not None:
            info = [i for i in info if i.start_date <= date_to]

        return info

    def menus(
        self, date_from: datetime.date, date_to: datetime.date = None
    ) -> List[dataClasses.Menu]:
        """
        Get menus between two given points.

        date_from : datetime
            The first date
        date_to : datetime
            The second date. If unspecified to the end of the year.

        Returns
        -------
        List[Menu]
            Menu between two given points
        """
        output = []

        if not date_to:
            date_to = date_from

        first_day = date_from - datetime.timedelta(days=date_from.weekday())

        # getting menus for all the weeks.
        while first_day <= date_to:
            data = {"date": {"_T": 7, "V": first_day.strftime("%d/%m/%Y") + " 0:0:0"}}
            response = self.post("PageMenus", 10, data)
            l_list = response["donneesSec"]["donnees"]["ListeJours"]["V"]
            for day in l_list:
                for menu in day["ListeRepas"]["V"]:
                    menu["Date"] = day["Date"]
                    output.append(dataClasses.Menu(self, menu))
            first_day += datetime.timedelta(days=7)

        # since we only have week precision, we need to make it more precise on our own
        return [menu for menu in output if date_from <= menu.date <= date_to]

    @property
    def current_period(self) -> dataClasses.Period:
        """Get the current period."""
        id_period = self.parametres_utilisateur["donneesSec"]["donnees"]["ressource"][
            "listeOngletsPourPeriodes"
        ]["V"][0]["periodeParDefaut"]["V"]["N"]
        return dataClasses.Util.get(self.periods, id=id_period)[0]


class ParentClient(Client):
    """
    A parent PRONOTE client.

    Parameters
    ----------
    pronote_url : str
        URL of the server
    username : str
    password : str
    ent : Callable
        Cookies for ENT connections

    Attributes
    ----------
    start_day : datetime.datetime
        The first day of the school year
    week : int
        The current week of the school year
    logged_in : bool
        If the user is successfully logged in
    info: dataClasses.ClientInfo
        Provides information about the current client. Name etc...
    children: List[dataClasses.ClientInfo]
        List of sub-clients representing all the children connected to the main parent account.
    """

    def __init__(
        self,
        pronote_url: str,
        username: str = "",
        password: str = "",
        ent: Optional[Callable] = None,
        qr_code: bool = False,
    ) -> None:
        super().__init__(pronote_url, username, password, ent, qr_code)

        self.children: List[dataClasses.ClientInfo] = []
        for c in self.parametres_utilisateur["donneesSec"]["donnees"]["ressource"][
            "listeRessources"
        ]:
            self.children.append(dataClasses.ClientInfo(self, c))

        if not self.children:
            raise ChildNotFound("No children were found.")

        self._selected_child: dataClasses.ClientInfo = self.children[0]
        self.parametres_utilisateur["donneesSec"]["donnees"][
            "ressource"
        ] = self._selected_child.raw_resource

    def set_child(self, child: Union[str, dataClasses.ClientInfo]) -> None:
        """
        Select a child

        Parameters
        ----------
        child: Union[str, dataClasses.ClientInfo]
            Name or ClientInfo of a child.
        """
        if type(child) == str:
            candidates = dataClasses.Util.get(self.children, name=child)
            c = candidates[0] if candidates else None
        else:
            c = child

        if not c:
            raise ChildNotFound(f"A child with the name {child} was not found.")

        self._selected_child = c
        self.parametres_utilisateur["donneesSec"]["donnees"][
            "ressource"
        ] = self._selected_child.raw_resource

    def post(self, function_name: str, onglet: int = None, data: dict = None) -> dict:
        """
        Preforms a raw post to the PRONOTE server. Adds signature, then passes it to _Communication.post

        Parameters
        ----------
        function_name: str
        onglet: int
        data: dict

        Returns
        -------
        Raw JSON
        """
        post_data = {}
        if onglet:
            post_data["_Signature_"] = {
                "onglet": onglet,
                "membre": {"N": self._selected_child.id, "G": 4},
            }

        if data:
            post_data["donnees"] = data

        try:
            return self.communication.post(function_name, post_data)
        except PronoteAPIError as e:
            if isinstance(e, ExpiredObject):
                raise e

            log.info(
                f"Have you tried turning it off and on again? ERROR: {e.pronote_error_code} | {e.pronote_error_msg}"
            )
            self.refresh()
            return self.communication.post(function_name, post_data)


class VieScolaireClient(_ClientBase):
    """
    A PRONOTE client for Vie Scolaire accounts.

    Parameters
    ----------
    pronote_url : str
        URL of the server
    username : str
    password : str
    ent : Callable
        Cookies for ENT connections

    Attributes
    ----------
    start_day : datetime.datetime
        The first day of the school year
    week : int
        The current week of the school year
    logged_in : bool
        If the user is successfully logged in
    info: dataClasses.ClientInfo
        Provides information about the current client. Name etc...
    classes: List[dataClasses.StudentClass]
        List of all classes this account has access to.
    """

    def __init__(
        self,
        pronote_url: str,
        username: str = "",
        password: str = "",
        ent: Optional[Callable] = None,
        qr_code: bool = False,
    ) -> None:
        super().__init__(pronote_url, username, password, ent, qr_code)
        self.classes = [
            dataClasses.StudentClass(self, json)
            for json in self.parametres_utilisateur["donneesSec"]["donnees"][
                "listeClasses"
            ]["V"]
        ]
