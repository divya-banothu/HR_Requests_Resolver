
from datetime import datetime, timedelta, time

TARGETS = {
    "Critical": 8,
    "High": 24,
    "Medium": 40,
    "Low": 80
}

def business_hours_between(start, end):
    if end < start:
        raise ValueError("End must not precede start")

    total = 0.0
    current = start

    while current.date() <= end.date():
        if current.weekday() < 5:
            day_start = datetime.combine(
                current.date(), time(9, 0)
            )
            day_end = datetime.combine(
                current.date(), time(17, 0)
            )

            interval_start = max(start, day_start)
            interval_end = min(end, day_end)

            if interval_end > interval_start:
                total += (
                    interval_end - interval_start
                ).total_seconds() / 3600

        current = datetime.combine(
            current.date() + timedelta(days=1),
            time(0, 0)
        )

    return round(total, 2)

def calculate_sla(priority, created_at, resolved_at):
    start = datetime.fromisoformat(created_at)
    end = datetime.fromisoformat(resolved_at)

    actual = business_hours_between(start, end)
    target = TARGETS[priority]

    return {
        "target_hours": target,
        "actual_hours": actual,
        "sla_status": "MET" if actual <= target else "BREACHED",
        "breach_hours": max(0, round(actual - target, 2))
    }
