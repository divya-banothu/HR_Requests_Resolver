
from datetime import date

from src.engine.classification import (
    classify_ticket,
    check_ambiguity
)

from src.engine.routing_engine import determine_route

from src.engine.policy_engine import (
    get_effective_policy
)


def resolve_ticket(
    ticket,
    policies,
    versions,
    required_fields=None,
    unsupported_claim=False,
    today=None
):
    today = today or date.today()

    classification = classify_ticket(
        ticket["description"]
    )

    if (
        ticket.get("confidentiality") == "Restricted"
        or classification["sensitive"]
    ):
        route = determine_route({
            "category": classification["category"],
            "confidentiality": "Restricted"
        })

        return {
            "ticket_id": ticket["ticket_id"],
            "decision": "ESCALATE_TO_HR",
            "reason": "SENSITIVE_CASE",
            "queue": route["queue"],
            "policy_reference": None
        }

    ambiguity = check_ambiguity(
        ticket["description"],
        required_fields
    )

    if ambiguity["is_ambiguous"]:
        return {
            "ticket_id": ticket["ticket_id"],
            "decision": "REQUEST_CLARIFICATION",
            "reason": "MISSING_CONTEXT",
            "queue": "HR_GENERAL",
            "policy_reference": None
        }

    if unsupported_claim:
        return {
            "ticket_id": ticket["ticket_id"],
            "decision": "ESCALATE_TO_HR",
            "reason": "UNSUPPORTED_POLICY_CLAIM",
            "queue": "HR_GENERAL",
            "policy_reference": None
        }

    matching_policies = [
        p for p in policies
        if p["lifecycle_state"] == "Published"
    ]

    if not matching_policies:
        return {
            "ticket_id": ticket["ticket_id"],
            "decision": "ESCALATE_TO_HR",
            "reason": "NO_POLICY_DOCUMENT",
            "queue": "HR_GENERAL",
            "policy_reference": None
        }

    policy = matching_policies[0]

    result = get_effective_policy(
        versions,
        policy["policy_id"],
        policy["audience"],
        today
    )

    if result["decision"] != "ANSWER_WITH_POLICY":
        return {
            "ticket_id": ticket["ticket_id"],
            "decision": "ESCALATE_TO_HR",
            "reason": result["reason"],
            "queue": "HR_GENERAL",
            "policy_reference": None
        }

    route = determine_route({
    "category": classification["category"],
    "confidentiality": ticket.get(
        "confidentiality", "Internal"
        )
    })

    return {
        "ticket_id": ticket["ticket_id"],
        "decision": "ANSWER_WITH_POLICY",
        "reason": "VALID_POLICY_FOUND",
        "queue": route["queue"],
        "policy_reference": result["version_id"]
    }
