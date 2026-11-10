from datetime import datetime
from src.engine.sla_engine import business_hours_between

def test_normal_business_hours():
    start = datetime(2026, 11, 9, 9, 0)
    end = datetime(2026, 11, 9, 12, 0)

    assert business_hours_between(start, end) == 3

def test_weekend_excluded():
    start = datetime(2026, 11, 6, 16, 0)
    end = datetime(2026, 11, 9, 10, 0)

    assert business_hours_between(start, end) == 2