
"""
Business rule validation for HR Policy Resolution System.
"""

import csv
import json
from pathlib import Path
from datetime import date

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data"
REPORTS = BASE / "reports" / "validation"


def load_csv(relative_path):
    path = DATA / relative_path

    if not path.exists():
        raise FileNotFoundError(path)

    with path.open(
        "r", newline="", encoding="utf-8-sig"
    ) as file:
        return list(csv.DictReader(file))


def load_tables():
    return {
        "tickets": load_csv("transactions/tickets.csv"),
        "policy_documents": load_csv(
            "master/policy_documents.csv"
        ),
        "policy_versions": load_csv(
            "master/policy_versions.csv"
        ),
        "assignments": load_csv(
            "transactions/assignments.csv"
        ),
        "resolutions": load_csv(
            "transactions/resolutions.csv"
        ),
        "sla": load_csv("transactions/sla.csv"),
        "articles": load_csv(
            "master/knowledge_articles.csv"
        ),
        "article_policy_versions": load_csv(
            "transactions/article_policy_versions.csv"
        ),
    }


def load_ground_truth():
    path = DATA / "ground_truth" / "ground_truth.json"

    if not path.exists():
        return []

    return json.loads(path.read_text(encoding="utf-8"))


def validate_business_rules(tables, ground_truth=None):
    errors = []
    warnings = []
    expected_anomalies = []

    ground_truth = ground_truth or []

    known_anomaly_map = {
        item["ticket_id"]: item
        for item in ground_truth
    }

    assignments = {}

    for assignment in tables["assignments"]:
        if assignment.get("is_current", "").lower() == "true":
            assignments[assignment["ticket_id"]] = (
                assignment["queue"]
            )

    # Rule 1: Sensitive case routing.
    for ticket in tables["tickets"]:
        if ticket["confidentiality"] == "Restricted":
            actual_queue = assignments.get(
                ticket["ticket_id"]
            )

            if actual_queue != "HR_EMPLOYEE_RELATIONS":
                anomaly = known_anomaly_map.get(
                    ticket["ticket_id"]
                )

                if anomaly and anomaly["issue_type"] == (
                    "SENSITIVE_CASE_WRONG_QUEUE"
                ):
                    expected_anomalies.append({
                        "rule": "SENSITIVE_ROUTING",
                        "ticket_id": ticket["ticket_id"],
                        "issue_type": anomaly["issue_type"]
                    })
                else:
                    errors.append({
                        "rule": "SENSITIVE_ROUTING",
                        "ticket_id": ticket["ticket_id"],
                        "message": "Restricted ticket routed incorrectly"
                    })

    # Rule 2: Policy effective date validation.
    for version in tables["policy_versions"]:
        start = date.fromisoformat(
            version["effective_from"]
        )

        end_value = version.get("effective_to", "")

        if end_value:
            end = date.fromisoformat(end_value)

            if end <= start:
                errors.append({
                    "rule": "POLICY_DATE_ORDER",
                    "version_id": version["version_id"]
                })

    # Rule 3: Duplicate resolutions.
    resolution_ticket_ids = [
        row["ticket_id"]
        for row in tables["resolutions"]
    ]

    if len(resolution_ticket_ids) != len(
        set(resolution_ticket_ids)
    ):
        errors.append({
            "rule": "DUPLICATE_RESOLUTION",
            "message": "Multiple resolutions for a ticket"
        })

    # Rule 4: SLA arithmetic reconciliation.
    for sla in tables["sla"]:
        actual = float(sla["actual_hours"])
        target = float(sla["target_hours"])

        if actual < 0 or target <= 0:
            errors.append({
                "rule": "SLA_INVALID_DURATION",
                "ticket_id": sla["ticket_id"]
            })
            continue

        expected_status = (
            "BREACHED" if actual > target else "MET"
        )

        if sla["sla_status"] != expected_status:
            errors.append({
                "rule": "SLA_STATUS",
                "ticket_id": sla["ticket_id"],
                "expected": expected_status,
                "actual": sla["sla_status"]
            })

    # Rule 5: Article policy links must reference existing versions.
    version_ids = {
        row["version_id"]
        for row in tables["policy_versions"]
    }

    article_ids = {
        row["article_id"]
        for row in tables["articles"]
    }

    for link in tables["article_policy_versions"]:
        if link["version_id"] not in version_ids:
            errors.append({
                "rule": "INVALID_ARTICLE_POLICY_VERSION",
                "link_id": link["link_id"]
            })

        if link["article_id"] not in article_ids:
            errors.append({
                "rule": "INVALID_ARTICLE_LINK",
                "link_id": link["link_id"]
            })

    # Rule 6: Policy citation anomalies.
    for item in ground_truth:
        if item["issue_type"] in (
            "OBSOLETE_POLICY_CITATION",
            "UNSUPPORTED_POLICY_CLAIM"
        ):
            expected_anomalies.append({
                "ticket_id": item["ticket_id"],
                "issue_type": item["issue_type"],
                "classification": "KNOWN_TEST_ANOMALY"
            })

    return {
        "errors": errors,
        "warnings": warnings,
        "expected_anomalies": expected_anomalies,
        "error_count": len(errors),
        "expected_anomaly_count": len(expected_anomalies),
        "passed": len(errors) == 0
    }


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)

    tables = load_tables()
    ground_truth = load_ground_truth()

    result = validate_business_rules(
        tables, ground_truth
    )

    output = REPORTS / "business_rules_report.json"

    output.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8"
    )

    print("\n========== BUSINESS RULE VALIDATION ==========")
    print(f"Errors: {result['error_count']}")
    print(
        "Known anomalies:",
        result["expected_anomaly_count"]
    )
    print(f"Warnings: {len(result['warnings'])}")
    print(
        "Status:",
        "PASS" if result["passed"] else "FAIL"
    )
    print(f"Report saved: {output}")

    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
