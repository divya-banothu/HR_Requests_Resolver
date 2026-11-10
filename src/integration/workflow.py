
import csv
import json
from pathlib import Path
from datetime import datetime, date, timezone

from src.engine.classification import (
    classify_ticket,
    check_ambiguity
)
from src.engine.routing_engine import determine_route
from src.engine.policy_engine import (
    get_effective_policy,
    validate_citation
)
from src.engine.sla_engine import calculate_sla
from src.engine.resolution_engine import resolve_ticket


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
REPORTS = ROOT / "reports" / "integration"


def load_csv(relative_path):
    path = DATA / relative_path

    if not path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {path}"
        )

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def save_csv(filename, rows):
    REPORTS.mkdir(parents=True, exist_ok=True)

    path = REPORTS / filename

    if not rows:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)


def save_json(filename, data):
    REPORTS.mkdir(parents=True, exist_ok=True)

    path = REPORTS / filename

    path.write_text(
        json.dumps(data, indent=2, default=str),
        encoding="utf-8"
    )


def to_bool(value):
    return str(value).strip().lower() in (
        "true", "1", "yes"
    )


def integrate_workflow(as_of=None):
    as_of = as_of or datetime.now(timezone.utc)

    if as_of.tzinfo is not None:
        as_of = as_of.replace(tzinfo=None)

    processing_date = as_of.date()

    # Load master data
    employees = load_csv("master/employees.csv")
    departments = load_csv("master/departments.csv")
    policies = load_csv("master/policy_documents.csv")
    versions = load_csv("master/policy_versions.csv")
    articles = load_csv("master/knowledge_articles.csv")
    categories = load_csv("master/categories.csv")

    # Load transaction data
    tickets = load_csv("transactions/tickets.csv")
    messages = load_csv("transactions/messages.csv")
    assignments = load_csv("transactions/assignments.csv")
    slas = load_csv("transactions/sla.csv")
    resolutions = load_csv("transactions/resolutions.csv")
    article_links = load_csv(
        "transactions/article_policy_versions.csv"
    )

    employee_map = {
        row["employee_id"]: row
        for row in employees
    }

    category_map = {
        row["category_id"]: row["category_name"]
        for row in categories
    }

    resolution_map = {
        row["ticket_id"]: row
        for row in resolutions
    }

    sla_map = {
        row["ticket_id"]: row
        for row in slas
    }

    current_assignment_map = {
        row["ticket_id"]: row
        for row in assignments
        if to_bool(row["is_current"])
    }

    article_map = {
        row["article_id"]: row
        for row in articles
    }

    article_version_map = {}

    for link in article_links:
        article_version_map.setdefault(
            link["article_id"], []
        ).append(link["version_id"])

    message_count = {}

    for message in messages:
        ticket_id = message["ticket_id"]
        message_count[ticket_id] = (
            message_count.get(ticket_id, 0) + 1
        )

    results = []

    for ticket in tickets:
        ticket_id = ticket["ticket_id"]

        employee = employee_map.get(
            ticket["employee_id"], {}
        )

        category = category_map.get(
            ticket["category_id"], "unknown"
        )

        classification = classify_ticket(
            ticket["description"]
        )

        ambiguity = check_ambiguity(
            ticket["description"]
        )

        # Use the resolution engine for the decision.
        decision = resolve_ticket(
            ticket=ticket,
            policies=policies,
            versions=versions,
            today=processing_date
        )

        # Independent routing check.
        routing = determine_route({
            "category": classification["category"],
            "confidentiality": ticket["confidentiality"]
        })

        queue = decision.get(
            "queue",
            routing.get("queue", "HR_GENERAL")
        )

        # Verify the selected policy citation.
        citation_id = decision.get("policy_reference")
        citation_valid = False

        if citation_id:
            version = next(
                (
                    v for v in versions
                    if v["version_id"] == citation_id
                ),
                None
            )

            if version:
                citation_valid = validate_citation(
                    version,
                    processing_date
                )

        # Existing source resolution and SLA data.
        resolution = resolution_map.get(ticket_id)
        sla_source = sla_map.get(ticket_id)

        sla_result = None

        if resolution:
            sla_result = calculate_sla(
                ticket["priority"],
                ticket["created_at"],
                resolution["resolved_at"]
            )

        elif sla_source:
            # Preserve the generated SLA values for unresolved tickets.
            sla_result = {
                "target_hours": float(
                    sla_source["target_hours"]
                ),
                "actual_hours": float(
                    sla_source["actual_hours"]
                ),
                "sla_status": sla_source["sla_status"],
                "breach_hours": max(
                    0,
                    round(
                        float(sla_source["actual_hours"])
                        - float(sla_source["target_hours"]),
                        2
                    )
                ),
                "sla_source": "GENERATED_SOURCE_RECORD"
            }

        # Do not automatically disclose a policy answer
        # if the selected citation is invalid.
        final_decision = decision["decision"]

        if (
            final_decision == "ANSWER_WITH_POLICY"
            and not citation_valid
        ):
            final_decision = "ESCALATE_TO_HR"

        # Flag differences between original and recomputed routing.
        original_assignment = current_assignment_map.get(
            ticket_id, {}
        )

        original_queue = original_assignment.get(
            "queue", ""
        )

        routing_mismatch = (
            original_queue != routing.get("queue", "")
            if original_queue else True
        )

        results.append({
            "ticket_id": ticket_id,
            "employee_id": ticket["employee_id"],
            "department_id": employee.get(
                "department_id", ""
            ),
            "source_category": category,
            "predicted_category": classification["category"],
            "classification_confidence": classification["confidence"],
            "sensitive": classification["sensitive"],
            "ambiguous": ambiguity["is_ambiguous"],
            "missing_context": ambiguity["missing_context"],
            "decision": final_decision,
            "decision_reason": (
                "INVALID_POLICY_CITATION"
                if final_decision != decision["decision"]
                else decision["reason"]
            ),
            "recommended_queue": routing.get(
                "queue", "HR_GENERAL"
            ),
            "resolution_queue": queue,
            "original_queue": original_queue,
            "routing_mismatch": routing_mismatch,
            "policy_version_id": citation_id or "",
            "citation_valid": citation_valid,
            "resolution_status": (
                resolution["outcome"]
                if resolution else "UNRESOLVED"
            ),
            "sla_status": (
                sla_result["sla_status"]
                if sla_result else "NOT_AVAILABLE"
            ),
            "sla_target_hours": (
                sla_result["target_hours"]
                if sla_result else ""
            ),
            "sla_actual_hours": (
                sla_result["actual_hours"]
                if sla_result else ""
            ),
            "message_count": message_count.get(
                ticket_id, 0
            ),
            "processing_date": processing_date.isoformat()
        })

    # Generate measurable outcomes.
    total = len(results)

    metrics = {
        "total_tickets": total,
        "classified_tickets": sum(
            r["predicted_category"] != "unknown"
            for r in results
        ),
        "sensitive_tickets": sum(
            r["sensitive"] for r in results
        ),
        "ambiguous_tickets": sum(
            r["ambiguous"] for r in results
        ),
        "policy_citations_valid": sum(
            r["citation_valid"] for r in results
        ),
        "routing_mismatches": sum(
            r["routing_mismatch"] for r in results
        ),
        "clarification_requests": sum(
            r["decision"] == "REQUEST_CLARIFICATION"
            for r in results
        ),
        "escalations": sum(
            r["decision"] == "ESCALATE_TO_HR"
            for r in results
        ),
        "policy_answers": sum(
            r["decision"] == "ANSWER_WITH_POLICY"
            for r in results
        ),
        "sla_met": sum(
            r["sla_status"] == "MET"
            for r in results
        ),
        "sla_breached": sum(
            r["sla_status"] == "BREACHED"
            for r in results
        )
    }

    metrics["classification_rate"] = round(
        metrics["classified_tickets"] / total * 100, 2
    ) if total else 0

    metrics["routing_mismatch_rate"] = round(
        metrics["routing_mismatches"] / total * 100, 2
    ) if total else 0

    metrics["sla_compliance_rate"] = round(
        metrics["sla_met"] /
        (metrics["sla_met"] + metrics["sla_breached"]) * 100,
        2
    ) if (
        metrics["sla_met"] + metrics["sla_breached"]
    ) else 0

    save_csv("ticket_decisions.csv", results)
    save_json("integration_metrics.json", metrics)

    print(json.dumps(metrics, indent=2))

    return results, metrics


if __name__ == "__main__":
    integrate_workflow()
