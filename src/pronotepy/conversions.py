import datetime


def date2week(date: datetime.date, start_day: datetime.date) -> int:
    return 1 + int((date - start_day).days / 7)
