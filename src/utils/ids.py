
from datetime import date


def generate_id(prefix, number, width=6):
    """
    Generate a zero-padded ID.

    Example:
    generate_id("EMP-", 1)
    Returns EMP-000001
    """
    if number < 1:
        raise ValueError("ID counter must be positive")

    return f"{prefix}{number:0{width}d}"


def generate_employee_id(number):
    return generate_id("EMP-", number)


def generate_department_id(number):
    return generate_id("DEPT-", number, 3)


def generate_ticket_id(number, year=2026):
    return f"TKT-{year}-{number:06d}"


def generate_policy_id(number, year=2026):
    return f"POL-HR-{year}-{number:03d}"


def generate_policy_version_id(policy_id, version):
    if version < 1:
        raise ValueError("Version must be positive")

    return f"VER-{policy_id}-{version:02d}"


def generate_knowledge_id(number):
    return generate_id("KB-", number)


def generate_message_id(ticket_id, message_number):
    if message_number < 1:
        raise ValueError("Message counter must be positive")

    return f"MSG-{ticket_id}-{message_number:03d}"


def generate_assignment_id(ticket_number, assignment_number=1):
    return f"ASN-{ticket_number:06d}-{assignment_number:02d}"


def generate_resolution_id(ticket_number):
    return f"RES-{ticket_number:06d}"


def generate_sla_id(ticket_number):
    return f"SLA-{ticket_number:06d}"


def generate_event_id(ticket_number, event_number):
    return f"EVT-{ticket_number:06d}-{event_number:03d}"


def generate_policy_date_id(policy_id, version):
    return {
        "policy_id": policy_id,
        "version_id": generate_policy_version_id(
            policy_id, version
        )
    }


def validate_ticket_id(ticket_id):
    import re

    return bool(
        re.fullmatch(r"TKT-\d{4}-\d{6}", ticket_id)
    )
