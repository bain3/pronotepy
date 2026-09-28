import unittest
from typing import Any, Dict, List, Optional, Tuple

import pronotepy
from pronotepy.ent.generic_func import _educonnect, _educonnect_user_type

IDP = "https://educonnect.education.gouv.fr/idp/profile/SAML2/POST/SSO"
CAS_ACS = "https://cas.example.fr/saml/SAMLAssertionConsumer"

# Local-storage check page served at execution=e1s1 since 2025.
LOCAL_STORAGE_PAGE = """
<form action="/idp/profile/SAML2/POST/SSO?execution=e1s1" method="post">
  <input type="hidden" name="csrf_token" value="csrf-1">
  <input type="hidden" name="shib_idp_ls_exception.shib_idp_session_ss" value="">
  <input type="hidden" name="shib_idp_ls_success.shib_idp_session_ss" value="true">
  <input type="hidden" name="shib_idp_ls_value.shib_idp_persistent_ss" value="">
  <input name="_eventId_proceed" type="hidden" value="">
</form>
"""

# Login page with profile selection, served at execution=e1s2.
LOGIN_PAGE = """
<form action="/idp/profile/SAML2/POST/SSO?execution=e1s2" method="post">
  <input type="hidden" name="csrf_token" value="csrf-2">
  <input type="hidden" name="typeUser" value="">
  <input type="text" name="j_username">
  <input type="password" name="j_password">
  <button name="_eventId_proceed">Se connecter</button>
</form>
<a onclick="selectionProfil('responsable')">Responsable d'élève</a>
<a onclick="selectionProfil('eleve')">Élève</a>
"""

# Pre-2025 login page: credentials posted straight to the landing URL.
LEGACY_LOGIN_PAGE = """
<form action="/idp/profile/SAML2/POST/SSO?execution=e1s1" method="post">
  <input type="text" name="j_username">
  <input type="password" name="j_password">
  <button name="_eventId_proceed">Se connecter</button>
</form>
"""

SAML_RESPONSE_PAGE = f"""
<form action="{CAS_ACS}" method="post">
  <input type="hidden" name="SAMLResponse" value="saml-ok">
  <input type="hidden" name="RelayState" value="relay">
</form>
"""


class FakeResponse:
    def __init__(self, url: str, text: str, status_code: int = 200) -> None:
        self.url = url
        self.text = text
        self.status_code = status_code


class FakeSession:
    """Serves canned pages and records every request made by the flow."""

    def __init__(
        self,
        gets: Dict[str, FakeResponse],
        posts: Dict[str, FakeResponse],
    ) -> None:
        self.gets = gets
        self.posts = posts
        self.requests: List[Tuple[str, str, Optional[Dict[str, Any]]]] = []

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.requests.append(("GET", url, None))
        return self.gets[url]

    def post(self, url: str, data: Any = None, **kwargs: Any) -> FakeResponse:
        self.requests.append(("POST", url, dict(data or {})))
        return self.posts[url]

    def posted(self, url: str) -> Dict[str, Any]:
        for method, request_url, data in self.requests:
            if method == "POST" and request_url == url:
                assert data is not None
                return data
        raise AssertionError(f"no POST to {url}")


def three_step_session(login_result: FakeResponse) -> FakeSession:
    e1s1, e1s2 = f"{IDP}?execution=e1s1", f"{IDP}?execution=e1s2"
    return FakeSession(
        gets={e1s1: FakeResponse(e1s1, LOCAL_STORAGE_PAGE)},
        posts={
            e1s1: FakeResponse(e1s2, LOGIN_PAGE),
            e1s2: login_result,
            CAS_ACS: FakeResponse("https://pronote.example.fr/", "ok"),
        },
    )


class TestEduConnectLogin(unittest.TestCase):
    def test_three_step_flow_as_parent(self) -> None:
        e1s1, e1s2 = f"{IDP}?execution=e1s1", f"{IDP}?execution=e1s2"
        session = three_step_session(FakeResponse(e1s2, SAML_RESPONSE_PAGE))

        response = _educonnect(
            session,
            "user",
            "secret",
            e1s1,
            pronote_url="https://0060000x.index-education.net/pronote/parent.html",
        )

        self.assertIsNotNone(response)
        local_storage = session.posted(e1s1)
        self.assertNotIn("j_password", local_storage)
        self.assertEqual(local_storage["csrf_token"], "csrf-1")
        self.assertIn("_eventId_proceed", local_storage)

        login = session.posted(e1s2)
        self.assertEqual(login["j_username"], "user")
        self.assertEqual(login["j_password"], "secret")
        self.assertEqual(login["csrf_token"], "csrf-2")
        self.assertEqual(login["typeUser"], "responsable")
        self.assertIn("_eventId_proceed", login)

        self.assertEqual(session.posted(CAS_ACS)["SAMLResponse"], "saml-ok")

    def test_three_step_flow_as_student(self) -> None:
        e1s1, e1s2 = f"{IDP}?execution=e1s1", f"{IDP}?execution=e1s2"
        session = three_step_session(FakeResponse(e1s2, SAML_RESPONSE_PAGE))

        _educonnect(
            session,
            "user",
            "secret",
            e1s1,
            pronote_url="https://0060000x.index-education.net/pronote/eleve.html",
        )

        self.assertEqual(session.posted(e1s2)["typeUser"], "eleve")

    def test_legacy_single_step_flow_still_works(self) -> None:
        e1s1 = f"{IDP}?execution=e1s1"
        session = FakeSession(
            gets={e1s1: FakeResponse(e1s1, LEGACY_LOGIN_PAGE)},
            posts={
                e1s1: FakeResponse(e1s1, SAML_RESPONSE_PAGE),
                CAS_ACS: FakeResponse("https://pronote.example.fr/", "ok"),
            },
        )

        response = _educonnect(session, "user", "secret", e1s1)

        self.assertIsNotNone(response)
        login = session.posted(e1s1)
        self.assertEqual(login["j_username"], "user")
        self.assertNotIn("typeUser", login)

    def test_wrong_credentials_raise(self) -> None:
        e1s2 = f"{IDP}?execution=e1s2"
        session = three_step_session(FakeResponse(e1s2, LOGIN_PAGE))

        with self.assertRaises(pronotepy.ENTLoginError):
            _educonnect(session, "user", "wrong", f"{IDP}?execution=e1s1")

    def test_wrong_credentials_without_exceptions_return_none(self) -> None:
        e1s2 = f"{IDP}?execution=e1s2"
        session = three_step_session(FakeResponse(e1s2, LOGIN_PAGE))

        response = _educonnect(
            session, "user", "wrong", f"{IDP}?execution=e1s1", exceptions=False
        )

        self.assertIsNone(response)


class TestEduConnectUserType(unittest.TestCase):
    def test_parent_space(self) -> None:
        self.assertEqual(
            _educonnect_user_type({"pronote_url": "https://x/pronote/parent.html"}),
            "responsable",
        )

    def test_student_space(self) -> None:
        self.assertEqual(
            _educonnect_user_type({"pronote_url": "https://x/pronote/eleve.html?a=1"}),
            "eleve",
        )

    def test_explicit_override_wins(self) -> None:
        self.assertEqual(
            _educonnect_user_type(
                {
                    "pronote_url": "https://x/pronote/eleve.html",
                    "type_user": "responsable",
                }
            ),
            "responsable",
        )

    def test_unknown_space(self) -> None:
        self.assertIsNone(_educonnect_user_type({}))
        self.assertIsNone(
            _educonnect_user_type({"pronote_url": "https://x/pronote/professeur.html"})
        )


if __name__ == "__main__":
    unittest.main()
