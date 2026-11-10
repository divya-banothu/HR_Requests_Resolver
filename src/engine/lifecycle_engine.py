
from datetime import datetime, timezone


ALLOWED_TRANSITIONS = {
    "Open": ["In Progress", "Pending", "Escalated"],
    "In Progress": ["Pending", "Resolved", "Escalated"],
    "Pending": ["In Progress", "Escalated", "Closed"],
    "Escalated": ["In Progress", "Resolved", "Closed"],
    "Resolved": ["Closed"],
    "Closed": []
}


def validate_transition(current_status, new_status):
    allowed = ALLOWED_TRANSITIONS.get(current_status, [])

    return {
        "current_status": current_status,
        "new_status": new_status,
        "is_valid": new_status in allowed,
        "reason": (
            "VALID_TRANSITION"
            if new_status in allowed
            else "INVALID_TRANSITION"
        )
    }


def create_ticket_event(
    ticket_id,
    event_type,
    previous_status=None,
    new_status=None,
    event_number=1
):
    return {
        "event_id": f"EVT-{ticket_id}-{event_number:03d}",
        "ticket_id": ticket_id,
        "event_type": event_type,
        "previous_status": previous_status,
        "new_status": new_status,
        "event_timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "event_source": "HR_RESOLUTION_ENGINE"
    }


def get_current_status(events, ticket_id):
    ticket_events = [
        event for event in events
        if event["ticket_id"] == ticket_id
        and event.get("new_status")
    ]

    if not ticket_events:
        return "Open"

    latest = max(
        ticket_events,
        key=lambda event: event["event_timestamp"]
    )

    return latest["new_status"]


def apply_transition(ticket, new_status, events):
    current = ticket["status"]

    result = validate_transition(current, new_status)

    if not result["is_valid"]:
        raise ValueError(
            f"Invalid transition: {current} -> {new_status}"
        )

    event = create_ticket_event(
        ticket["ticket_id"],
        "STATUS_CHANGED",
        current,
        new_status,
        len(events) + 1
    )

    # Return a new state and event.
    # Do not overwrite the original event history.
    updated_ticket = dict(ticket)
    updated_ticket["status"] = new_status

    return updated_ticket, event
