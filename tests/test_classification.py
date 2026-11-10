import pytest # type: ignore

from src.engine.classification import (
    classify_ticket,
    check_ambiguity
)


def test_classify_payroll():
    result = classify_ticket(
        "How can I check my salary payslip?"
    )
    assert result["category"] == "payroll"


def test_classify_leave():
    result = classify_ticket(
        "I want to apply for annual leave"
    )
    assert result["category"] == "leave"


def test_classify_benefits():
    result = classify_ticket(
        "I need information about health insurance"
    )
    assert result["category"] == "benefits"


def test_classify_onboarding():
    result = classify_ticket(
        "What documents are required for joining?"
    )
    assert result["category"] == "onboarding"


def test_classify_sensitive_case():
    result = classify_ticket(
        "I want to report workplace harassment"
    )
    assert result["category"] == "employee_relations"
    assert result["sensitive"] is True


def test_classify_unknown():
    result = classify_ticket(
        "I have a question about something"
    )
    assert result["category"] == "unknown"


def test_ambiguous_ticket():
    result = check_ambiguity(
        "Please help me"
    )
    assert result["is_ambiguous"] is True
    assert result["action"] == "REQUEST_CLARIFICATION"


def test_non_ambiguous_ticket():
    result = check_ambiguity(
        "I need information about my salary payslip"
    )
    assert result["is_ambiguous"] is False


def test_missing_required_fields():
    result = check_ambiguity(
        "I need leave assistance",
        required_fields=[
            {"name": "leave_start_date", "value": None},
            {"name": "leave_type", "value": "Annual"}
        ]
    )
    assert result["is_ambiguous"] is True
    assert "leave_start_date" in result["missing_fields"]