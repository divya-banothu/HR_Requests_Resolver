
import pytest # type: ignore

from src.engine.routing_engine import determine_route


@pytest.mark.parametrize(
    "category, expected_queue",
    [
        ("benefits", "HR_BENEFITS"),
        ("leave", "HR_LEAVE"),
        ("payroll", "HR_PAYROLL"),
        ("onboarding", "HR_ONBOARDING"),
        ("employee_relations", "HR_EMPLOYEE_RELATIONS")
    ]
)
def test_category_routing(category, expected_queue):
    result = determine_route({
        "category": category,
        "confidentiality": "Internal"
    })

    assert result["queue"] == expected_queue


def test_restricted_ticket():
    result = determine_route({
        "category": "payroll",
        "confidentiality": "Restricted"
    })

    assert result["queue"] == "HR_EMPLOYEE_RELATIONS"
    assert result["priority_route"] is True


def test_employee_relations_ticket():
    result = determine_route({
        "category": "employee_relations",
        "confidentiality": "Internal"
    })

    assert result["queue"] == "HR_EMPLOYEE_RELATIONS"


def test_unknown_category():
    result = determine_route({
        "category": "unknown",
        "confidentiality": "Internal"
    })

    assert result["queue"] == "HR_GENERAL"
    assert result["routing_reason"] == "DEFAULT_QUEUE"


def test_missing_category():
    result = determine_route({
        "confidentiality": "Internal"
    })

    assert result["queue"] == "HR_GENERAL"


def test_missing_confidentiality():
    result = determine_route({
        "category": "payroll"
    })

    assert result["queue"] == "HR_PAYROLL"
