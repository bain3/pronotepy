import datetime


def date2week(date: datetime.date, start_day: datetime.date) -> int:
    return 1 + int((date - start_day).days / 7)


def place2time(listeHeures: list, place: int) -> datetime.time:
    if place > len(listeHeures):
        # might be wrong... works with demo
        place = place % (len(listeHeures) - 1)

    start_time = next(
        (p for p in listeHeures if p["G"] == place),
        None,
    )
    if start_time is None:
        raise ValueError(f"Could not find starting time for place {place}")

    start_time = datetime.datetime.strptime(start_time["L"], "%Hh%M").time()
    return start_time
