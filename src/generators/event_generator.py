
from datetime import datetime, timedelta


def generate_ticket_events(tickets):
    events = []

    for i, ticket in enumerate(tickets, 1):
        tid = ticket["ticket_id"]

        created = datetime.fromisoformat(
            ticket["created_at"]
        )

        lifecycle = [
            ("TICKET_CREATED", 0),
            ("TICKET_CLASSIFIED", 5),
            ("TICKET_ASSIGNED", 10)
        ]

        if ticket["status"] == "Pending":
            lifecycle.extend([
                ("CLARIFICATION_REQUESTED", 30),
                ("TICKET_PENDING", 35)
            ])

        elif ticket["status"] == "In Progress":
            lifecycle.extend([
                ("SENSITIVE_CASE_ESCALATED", 30),
                ("TICKET_IN_PROGRESS", 35)
            ])

        else:
            lifecycle.extend([
                ("POLICY_RETRIEVED", 30),
                ("RESPONSE_SENT", 60),
                ("TICKET_RESOLVED", 240)
            ])

        for j, (event_type, minutes) in enumerate(
            lifecycle, 1
        ):
            events.append({
                "event_id": f"EVT-{i:06d}-{j:03d}",
                "ticket_id": tid,
                "event_type": event_type,
                "event_timestamp": (
                    created + timedelta(minutes=minutes)
                ).isoformat(),
                "event_source": "HR_RESOLUTION_ENGINE"
            })

    return events
