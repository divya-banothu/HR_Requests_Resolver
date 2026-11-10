
import random
from datetime import datetime, timedelta


TICKET_TEMPLATES = {
    "benefits": [
        "How can I check my health insurance benefits?",
        "Please explain my medical coverage.",
        "I need information about employee benefits.",
        "How can I add a dependent to my insurance?"
    ],
    "leave": [
        "How can I apply for annual leave?",
        "Please explain my leave balance.",
        "Can I carry forward unused leave?",
        "How do I request sick leave?"
    ],
    "payroll": [
        "How can I download my payslip?",
        "My salary payment is delayed.",
        "Please explain my salary deductions.",
        "How can I update payroll details?"
    ],
    "onboarding": [
        "What documents are required for joining?",
        "Please explain the onboarding process.",
        "How do I complete my joining formalities?",
        "I need help with my employee account."
    ]
}


PRIORITIES = ["Low", "Medium", "High", "Critical"]

PRIORITY_WEIGHTS = [30, 45, 20, 5]


def determine_queue(category, confidentiality):
    if confidentiality == "Restricted":
        return "HR_EMPLOYEE_RELATIONS"

    mapping = {
        "benefits": "HR_BENEFITS",
        "leave": "HR_LEAVE",
        "payroll": "HR_PAYROLL",
        "onboarding": "HR_ONBOARDING"
    }

    return mapping.get(category, "HR_GENERAL")


def generate_tickets(
    employees,
    categories,
    articles,
    count=5000,
    seed=20261022
):
    rng = random.Random(seed)

    tickets = []
    assignments = []
    slas = []
    resolutions = []
    ground_truth = []

    category_lookup = {
        c["category_code"]: c["category_id"]
        for c in categories
    }

    start_date = datetime(2026, 1, 1, 9, 0)

    for i in range(1, count + 1):

        ticket_id = f"TKT-2026-{i:06d}"

        employee = rng.choice(employees)

        # Request category distribution
        category = rng.choices(
            ["benefits", "leave", "payroll", "onboarding"],
            weights=[25, 30, 25, 20]
        )[0]

        sensitive = rng.random() < 0.04
        ambiguous = rng.random() < 0.12
        missing_context = rng.random() < 0.06

        confidentiality = (
            "Restricted" if sensitive else "Internal"
        )

        if sensitive:
            category = "employee_relations"
            description = (
                "Confidential employee relations complaint"
            )
        elif missing_context:
            description = "Please help me with my request"
        else:
            description = rng.choice(
                TICKET_TEMPLATES[category]
            )

        priority = rng.choices(
            PRIORITIES,
            weights=PRIORITY_WEIGHTS
        )[0]

        expected_queue = determine_queue(
            category, confidentiality
        )

        assigned_queue = expected_queue
        issue_type = ""
        expected_action = (
            "ESCALATE_TO_HR" if sensitive
            else "REQUEST_CLARIFICATION"
            if ambiguous or missing_context
            else "ANSWER_WITH_POLICY"
        )

        # Exception 1: Sensitive case sent to general queue
        if i % 100 == 0:
            assigned_queue = "HR_GENERAL"
            issue_type = "SENSITIVE_CASE_WRONG_QUEUE"

        # Exception 2: Obsolete policy citation
        if i % 101 == 0:
            issue_type = "OBSOLETE_POLICY_CITATION"
            expected_action = "REJECT_OBSOLETE_POLICY_CITATION"

        # Exception 3: Unsupported policy claim
        if i % 103 == 0:
            issue_type = "UNSUPPORTED_POLICY_CLAIM"
            expected_action = "ESCALATE_UNSUPPORTED_CLAIM"

        created_at = start_date + timedelta(
            days=i % 300,
            hours=i % 8
        )

        target_hours = {
            "Critical": 8,
            "High": 24,
            "Medium": 40,
            "Low": 80
        }[priority]

        # Placeholder duration: production SLA engine
        # must calculate business hours independently.
        estimated_hours = round(
            rng.uniform(1, target_hours * 1.5), 2
        )

        sla_status = (
            "BREACHED"
            if estimated_hours > target_hours
            else "MET"
        )

        ticket = {
            "ticket_id": ticket_id,
            "employee_id": employee["employee_id"],
            "category_id": category_lookup.get(
                category, category_lookup["benefits"]
            ),
            "description": description,
            "priority": priority,
            "confidentiality": confidentiality,
            "status": (
                "Pending" if ambiguous or missing_context
                else "In Progress" if sensitive
                else "Resolved"
            ),
            "created_at": created_at.isoformat(),
            "issue_type": issue_type
        }

        tickets.append(ticket)

        assignments.append({
            "assignment_id": f"ASN-{i:06d}-01",
            "ticket_id": ticket_id,
            "queue": assigned_queue,
            "assigned_at": created_at.isoformat(),
            "is_current": True
        })

        slas.append({
            "sla_id": f"SLA-{i:06d}",
            "ticket_id": ticket_id,
            "target_hours": target_hours,
            "actual_hours": estimated_hours,
            "sla_status": sla_status
        })

        if ticket["status"] == "Resolved":
            article = rng.choice(articles)

            resolutions.append({
                "resolution_id": f"RES-{i:06d}",
                "ticket_id": ticket_id,
                "article_id": article["article_id"],
                "outcome": "Resolved",
                "resolved_at": (
                    created_at + timedelta(hours=4)
                ).isoformat()
            })

        if issue_type:
            ground_truth.append({
                "ticket_id": ticket_id,
                "issue_type": issue_type,
                "expected_queue": expected_queue,
                "actual_queue": assigned_queue,
                "expected_action": expected_action,
                "ground_truth": "ANOMALY"
            })

    return {
        "tickets": tickets,
        "assignments": assignments,
        "sla": slas,
        "resolutions": resolutions,
        "ground_truth": ground_truth
    }
