
import pytest # type: ignore

from src.engine.lifecycle_engine import (
    validate_transition,
    create_ticket_event,
    get_current_status,
    apply_transition
)


def test_valid_transition():
    result = validate_transition("Open", "In Progress")

    assert result["is_valid"] is True


def test_invalid_transition():
    result = validate_transition("Closed", "Open")

    assert result["is_valid"] is False


def test_resolved_to_closed():
    result = validate_transition("Resolved", "Closed")

    assert result["is_valid"] is True


def test_closed_has_no_transitions():
    result = validate_transition("Closed", "Resolved")

    assert result["is_valid"] is False


def test_create_ticket_event():
    event = create_ticket_event(
        "TKT-2026-000001",
        "STATUS_CHANGED",
        "Open",
        "In Progress",
        1
    )

    assert event["ticket_id"] == "TKT-2026-000001"
    assert event["previous_status"] == "Open"
    assert event["new_status"] == "In Progress"
    assert event["event_type"] == "STATUS_CHANGED"


def test_current_status():
    events = [
        {
            "ticket_id": "TKT-2026-000001",
            "event_timestamp": "2026-11-09T09:00:00+00:00",
            "new_status": "Open"
        },
        {
            "ticket_id": "TKT-2026-000001",
            "event_timestamp": "2026-11-09T10:00:00+00:00",
            "new_status": "In Progress"
        }
    ]

    assert get_current_status(
        events,
        "TKT-2026-000001"
    ) == "In Progress"


def test_no_events_returns_open():
    assert get_current_status([], "TKT-2026-000001") == "Open"


def test_apply_transition_preserves_history():
    ticket = {
        "ticket_id": "TKT-2026-000001",
        "status": "Open"
    }

    events = [
        {"event_id": "EVT-001"}
    ]

    updated, event = apply_transition(
        ticket,
        "In Progress",
        events
    )

    assert ticket["status"] == "Open"
    assert updated["status"] == "In Progress"
    assert len(events) == 1
    assert event["new_status"] == "In Progress"


def test_apply_invalid_transition():
    ticket = {
        "ticket_id": "TKT-2026-000001",
        "status": "Closed"
    }

    with pytest.raises(ValueError):
        apply_transition(ticket, "Open", [])
