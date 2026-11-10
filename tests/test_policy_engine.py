from datetime import date
from src.engine.policy_engine import validate_citation

def test_obsolete_policy_rejected():
    version = {
        "status": "Superseded",
        "effective_from": "2025-01-01",
        "effective_to": "2025-02-01"
    }

    assert validate_citation(version, date(2026, 11, 10)) is False

def test_current_policy_accepted():
    version = {
        "status": "Active",
        "effective_from": "2025-03-01",
        "effective_to": ""
    }

    assert validate_citation(version, date(2026, 11, 10)) is True