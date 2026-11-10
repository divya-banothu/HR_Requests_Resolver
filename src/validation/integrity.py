
"""
Integrity validation for HR Policy Resolution System.
Checks primary keys, foreign keys and duplicate records.
"""

import csv
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data"
REPORTS = BASE / "reports" / "validation"

FILES = {
    "departments": "master/departments.csv",
    "employees": "master/employees.csv",
    "categories": "master/categories.csv",
    "policy_documents": "master/policy_documents.csv",
    "policy_versions": "master/policy_versions.csv",
    "knowledge_articles": "master/knowledge_articles.csv",
    "article_policy_versions": "transactions/article_policy_versions.csv",
    "tickets": "transactions/tickets.csv",
    "messages": "transactions/messages.csv",
    "assignments": "transactions/assignments.csv",
    "sla": "transactions/sla.csv",
    "resolutions": "transactions/resolutions.csv",
    "ticket_events": "transactions/ticket_events.csv",
}


def load_tables():
    tables = {}

    for name, relative_path in FILES.items():
        path = DATA / relative_path

        if not path.exists():
            raise FileNotFoundError(
                f"Missing required dataset: {path}"
            )

        with path.open(
            "r", newline="", encoding="utf-8-sig"
        ) as file:
            tables[name] = list(csv.DictReader(file))

    return tables


def check_unique(rows, key):
    values = [row.get(key) for row in rows]
    return (
        all(value not in (None, "") for value in values)
        and len(values) == len(set(values))
    )


def check_foreign_keys(
    child_rows, child_key, parent_rows, parent_key
):
    parent_ids = {
        row.get(parent_key) for row in parent_rows
    }

    return all(
        row.get(child_key) in parent_ids
        for row in child_rows
    )


def validate_all(tables):
    checks = {}

    primary_keys = {
        "departments": ("departments", "department_id"),
        "employees": ("employees", "employee_id"),
        "categories": ("categories", "category_id"),
        "policy_documents": ("policy_documents", "policy_id"),
        "policy_versions": ("policy_versions", "version_id"),
        "knowledge_articles": ("knowledge_articles", "article_id"),
        "article_policy_versions": (
            "article_policy_versions", "link_id"
        ),
        "tickets": ("tickets", "ticket_id"),
        "messages": ("messages", "message_id"),
        "assignments": ("assignments", "assignment_id"),
        "sla": ("sla", "sla_id"),
        "resolutions": ("resolutions", "resolution_id"),
        "ticket_events": ("ticket_events", "event_id"),
    }

    for name, (table, key) in primary_keys.items():
        checks[f"{name}_primary_key"] = check_unique(
            tables[table], key
        )

    foreign_keys = [
        ("employee_department_fk", "employees",
         "department_id", "departments", "department_id"),

        ("policy_department_fk", "policy_documents",
         "department_id", "departments", "department_id"),

        ("version_policy_fk", "policy_versions",
         "policy_id", "policy_documents", "policy_id"),

        ("article_category_fk", "knowledge_articles",
         "category_id", "categories", "category_id"),

        ("article_version_fk", "article_policy_versions",
         "version_id", "policy_versions", "version_id"),

        ("article_link_article_fk", "article_policy_versions",
         "article_id", "knowledge_articles", "article_id"),

        ("ticket_employee_fk", "tickets",
         "employee_id", "employees", "employee_id"),

        ("ticket_category_fk", "tickets",
         "category_id", "categories", "category_id"),

        ("message_ticket_fk", "messages",
         "ticket_id", "tickets", "ticket_id"),

        ("assignment_ticket_fk", "assignments",
         "ticket_id", "tickets", "ticket_id"),

        ("sla_ticket_fk", "sla",
         "ticket_id", "tickets", "ticket_id"),

        ("resolution_ticket_fk", "resolutions",
         "ticket_id", "tickets", "ticket_id"),

        ("resolution_article_fk", "resolutions",
         "article_id", "knowledge_articles", "article_id"),

        ("event_ticket_fk", "ticket_events",
         "ticket_id", "tickets", "ticket_id"),
    ]

    for name, child, child_key, parent, parent_key in foreign_keys:
        checks[name] = check_foreign_keys(
            tables[child], child_key,
            tables[parent], parent_key
        )

    failed_checks = [
        name for name, passed in checks.items()
        if not passed
    ]

    return {
        "checks": checks,
        "total_checks": len(checks),
        "passed": sum(checks.values()),
        "failed": len(failed_checks),
        "failed_checks": failed_checks,
        "overall_status": (
            "PASS" if not failed_checks else "FAIL"
        )
    }


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)

    tables = load_tables()
    result = validate_all(tables)

    output = REPORTS / "integrity_report.json"
    output.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8"
    )

    print("\n========== INTEGRITY VALIDATION ==========")
    print(f"Tables loaded: {len(tables)}")
    print(f"Total checks: {result['total_checks']}")
    print(f"Passed: {result['passed']}")
    print(f"Failed: {result['failed']}")
    print(f"Status: {result['overall_status']}")

    for name in result["failed_checks"]:
        print(f"[FAIL] {name}")

    print(f"Report saved: {output}")

    if result["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
