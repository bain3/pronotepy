import pytest
from pronotepy import PronoteSession, Spaces, UserPass


@pytest.fixture
async def session():
    session, _options, _auth_resp = await PronoteSession.login(
        UserPass(
            "https://demo.index-education.net/pronote/",
            Spaces.STUDENT,
            "demonstration",
            "pronotevs",
        ),
    )

    yield session

    await session.close()


async def test_authenticated_endpoint(session: PronoteSession):
    await session.post("PageInfosPerso", {})
