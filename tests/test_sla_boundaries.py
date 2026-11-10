
from datetime import datetime

import pytest # type: ignore

from src.engine.sla_engine import (
    business_hours_between,
    calculate_sla
)


def test_full_business_day():
    start = datetime(2026, 11, 9, 9, 0)
    end = datetime(2026, 11, 9, 17, 0)

    assert business_hours_between(start, end) == 8.0


def test_outside_business_hours():
    start = datetime(2026, 11, 9, 17, 0)
    end = datetime(2026, 11, 9, 20, 0)

    assert business_hours_between(start, end) == 0.0


def test_partial_business_hours():
    start = datetime(2026, 11, 9, 10, 0)
    end = datetime(2026, 11, 9, 14, 0)

    assert business_hours_between(start, end) == 4.0


def test_weekend_excluded():
    start = datetime(2026, 11, 6, 9, 0)
    end = datetime(2026, 11, 9, 17, 0)

    assert business_hours_between(start, end) == 16.0


def test_invalid_date_order():
    start = datetime(2026, 11, 10, 12, 0)
    end = datetime(2026, 11, 9, 12, 0)

    with pytest.raises(ValueError):
        business_hours_between(start, end)


def test_sla_met():
    result = calculate_sla(
        "High",
        "2026-11-09T09:00:00",
        "2026-11-09T17:00:00"
    )

    assert result["actual_hours"] == 8.0
    assert result["sla_status"] == "MET"
    assert result["breach_hours"] == 0


def test_sla_breached():
    result = calculate_sla(
        "Critical",
        "2026-11-09T09:00:00",
        "2026-11-10T17:00:00"
    )

    assert result["actual_hours"] == 16.0
    assert result["sla_status"] == "BREACHED"
    assert result["breach_hours"] == 8.0


def test_invalid_priority():
    with pytest.raises(KeyError):
        calculate_sla(
            "Urgent",
            "2026-11-09T09:00:00",
            "2026-11-09T10:00:00"
        )
