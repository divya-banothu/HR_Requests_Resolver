
from datetime import datetime, timedelta


def generate_messages(tickets, target_count=None):
    messages = []

    for ticket in tickets:
        tid = ticket["ticket_id"]

        created = datetime.fromisoformat(
            ticket["created_at"]
        )

        status = ticket["status"]
        sensitive = ticket["confidentiality"] == "Restricted"

        if status == "Pending":
            conversation = [
                ("Employee", "Request",
                 ticket["description"]),
                ("HR", "Clarification",
                 "Please provide the missing information."),
                ("Employee", "Response",
                 "Additional information requested."),
                ("HR", "Response",
                 "Your request is awaiting further review.")
            ]

        elif sensitive:
            conversation = [
                ("Employee", "Request",
                 ticket["description"]),
                ("HR", "Response",
                 "Your confidential request has been received."),
                ("HR", "Response",
                 "Your request has been routed for restricted review."),
                ("HR", "Response",
                 "The case remains under HR review.")
            ]

        else:
            conversation = [
                ("Employee", "Request",
                 ticket["description"]),
                ("HR", "Response",
                 "We are reviewing your HR request."),
                ("HR", "Response",
                 "Please refer to the applicable policy guidance."),
                ("HR", "Resolution",
                 "Your request has been resolved.")
            ]

        for j, (sender, message_type, message_text) in enumerate(
            conversation, 1
        ):
            messages.append({
                "message_id": f"MSG-{tid}-{j:03d}",
                "ticket_id": tid,
                "sender_type": sender,
                "message_type": message_type,
                "message_text": message_text,
                "created_at": (
                    created + timedelta(minutes=j * 30)
                ).isoformat()
            })

    if target_count is not None and len(messages) != target_count:
        raise ValueError(
            f"Expected {target_count} messages, "
            f"generated {len(messages)}"
        )

    return messages
