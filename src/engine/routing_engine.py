
"""
HR ticket routing engine.

Routes requests to the appropriate HR queue.
Sensitive requests always receive restricted routing.
"""


ROUTING_RULES = {
    "benefits": "HR_BENEFITS",
    "leave": "HR_LEAVE",
    "payroll": "HR_PAYROLL",
    "onboarding": "HR_ONBOARDING",
    "employee_relations": "HR_EMPLOYEE_RELATIONS"
}


def determine_route(ticket):
    """
    Determine the destination queue for an HR ticket.

    Args:
        ticket: Dictionary containing category and confidentiality.

    Returns:
        Dictionary containing routing decision and queue.
    """

    category = ticket.get("category", "unknown")
    confidentiality = ticket.get("confidentiality", "Internal")

    # Sensitive requests must never enter general queues.
    if (
        confidentiality == "Restricted"
        or category == "employee_relations"
    ):
        return {
            "queue": "HR_EMPLOYEE_RELATIONS",
            "routing_reason": "SENSITIVE_CASE",
            "priority_route": True
        }

    queue = ROUTING_RULES.get(category, "HR_GENERAL")

    return {
        "queue": queue,
        "routing_reason": (
            "CATEGORY_MATCH"
            if category in ROUTING_RULES
            else "DEFAULT_QUEUE"
        ),
        "priority_route": False
    }
