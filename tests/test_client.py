from pronotepy import Client, UserPass, Spaces
import pytest

from utils import warn, warn_empty

@pytest.fixture(scope="session")
async def client():
    client = await Client.login(
        UserPass(
            "https://demo.index-education.net/pronote/",
            Spaces.STUDENT,
            "demonstration",
            "pronotevs",
        ),
    )

    yield client

    await client.close()


async def test_grades_and_averages(client: Client):
    grades, averages, *_ = await client.terms[0].grades()

    warn_empty(grades)
    assert len(grades) > 0
    warn(averages is not None and len(averages) > 0, "Averages are empty")


async def test_absences_and_punishments(client: Client):
    absences, delays = await client.terms[0].absences_and_punishments()

    warn_empty(absences)
    warn_empty(delays)
