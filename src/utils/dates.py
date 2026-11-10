
from datetime import datetime, date, timedelta, time


BUSINESS_START = time(9, 0)
BUSINESS_END = time(17, 0)

WORKING_DAYS = {0, 1, 2, 3, 4}


def is_business_day(day, holidays=None):
    """
    Monday-Friday are working days.
    Configured holidays are excluded.
    """
    holidays = holidays or set()

    return (
        day.weekday() in WORKING_DAYS
        and day not in holidays
    )


def business_hours_between(
    start,
    end,
    holidays=None
):
    """
    Calculate working hours between two timestamps.

    Business hours: 09:00 to 17:00.
    Weekends and configured holidays are excluded.
    """

    if end < start:
        raise ValueError("End cannot precede start")

    holidays = holidays or set()

    total_hours = 0.0
    current_day = start.date()

    while current_day <= end.date():

        if is_business_day(current_day, holidays):

            day_start = datetime.combine(
                current_day, BUSINESS_START
            )

            day_end = datetime.combine(
                current_day, BUSINESS_END
            )

            interval_start = max(start, day_start)
            interval_end = min(end, day_end)

            if interval_end > interval_start:
                total_hours += (
                    interval_end - interval_start
                ).total_seconds() / 3600

        current_day += timedelta(days=1)

    return round(total_hours, 2)


def add_business_days(start_date, days, holidays=None):
    """
    Add working days while excluding weekends and holidays.
    """

    holidays = holidays or set()

    current = start_date
    added = 0

    while added < days:
        current += timedelta(days=1)

        if is_business_day(current, holidays):
            added += 1

    return current


def generate_timestamp(
    start_date,
    day_offset=0,
    hour_offset=0,
    minute_offset=0
):
    """
    Generate a deterministic synthetic timestamp.
    """

    if isinstance(start_date, date) and not isinstance(
        start_date, datetime
    ):
        start_date = datetime.combine(
            start_date, time(9, 0)
        )

    result = start_date + timedelta(
        days=day_offset,
        hours=hour_offset,
        minutes=minute_offset
    )

    return result.isoformat()


def is_policy_effective(version, check_date):
    """
    Check policy version validity using a half-open interval:
    effective_from <= check_date < effective_to.
    """

    start = date.fromisoformat(
        version["effective_from"]
    )

    end_value = version.get("effective_to")

    if isinstance(check_date, datetime):
        check_date = check_date.date()

    end = (
        date.fromisoformat(end_value)
        if end_value else None
    )

    return (
        start <= check_date
        and (end is None or check_date < end)
    )


def get_current_timestamp():
    return datetime.now().astimezone().isoformat()
