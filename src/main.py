import csv
import json
import random
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timedelta

SEED = 20261022
BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"

random.seed(SEED)

def save_csv(name, rows):
    path = DATA / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

def save_json(name, data):
    path = DATA / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

def identifier(prefix, number, width=6):
    return f"{prefix}{number:0{width}d}"

def timestamp(days=0, hours=0):
    base = datetime(2026, 1, 1, 9, 0)
    return (base + timedelta(days=days, hours=hours)).isoformat()

def build_departments():
    names = [
        "Human Resources", "Finance", "Engineering",
        "Sales", "Marketing", "Operations",
        "Customer Support", "Legal", "IT",
        "Recruitment", "Administration", "Compliance"
    ]
    return [
        {"department_id": f"DEPT-{i:03d}", "department_name": n}
        for i, n in enumerate(names, 1)
    ]

def build_employees(departments, count):
    rows = []
    for i in range(1, count + 1):
        rows.append({
            "employee_id": identifier("EMP-", i),
            "department_id": random.choice(departments)["department_id"],
            "employment_type": random.choice(
                ["Full-time", "Part-time", "Contract"]
            ),
            "employment_status": random.choices(
                ["Active", "Inactive"], [0.95, 0.05]
            )[0],
            "audience": random.choice(
                ["Employee", "Manager", "Candidate"]
            ),
            "location": random.choice(
                ["India", "USA", "UK", "Singapore"]
            )
        })
    return rows

def build_categories():
    names = [
        "benefits", "leave", "payroll", "onboarding",
        "employee_relations", "harassment",
        "discrimination", "confidential_complaint"
    ]
    return [
        {"category_id": f"CAT-{i:03d}", "category_name": name}
        for i, name in enumerate(names, 1)
    ]

def build_policies(departments, count=30):
    docs, versions = [], []
    audiences = ["Employee", "Manager", "Candidate", "All"]
    for i in range(1, count + 1):
        pid = f"POL-HR-2026-{i:03d}"
        docs.append({
            "policy_id": pid,
            "policy_title": f"HR Policy {i:03d}",
            "department_id": departments[i % len(departments)]["department_id"],
            "audience": random.choice(audiences),
            "lifecycle_state": "Published"
        })

        for v in range(1, 4):
            versions.append({
                "version_id": f"VER-{pid}-{v:02d}",
                "policy_id": pid,
                "version_number": v,
                "effective_from": f"2025-{v:02d}-01",
                "effective_to": (
                    f"2025-{v+1:02d}-01" if v < 3 else ""
                ),
                "status": "Superseded" if v < 3 else "Active",
                "policy_text": f"Synthetic policy content for {pid}, version {v}"
            })
    return docs, versions

def build_articles(versions, categories, count=150):
    rows, links = [], []
    for i in range(1, count + 1):
        article_id = identifier("KB-", i)
        category = categories[(i - 1) % len(categories)]
        version = versions[(i - 1) % len(versions)]
        rows.append({
            "article_id": article_id,
            "category_id": category["category_id"],
            "title": f"HR Knowledge Article {i:03d}",
            "answer_snippet": f"Refer to the applicable policy: {version['policy_id']}",
            "status": "Published"
        })
        links.append({
            "link_id": f"APL-{i:06d}",
            "article_id": article_id,
            "version_id": version["version_id"]
        })
    return rows, links

def classify(text, sensitive):
    if sensitive:
        return "employee_relations"
    t = text.lower()
    for keyword, category in [
        ("salary", "payroll"), ("payslip", "payroll"),
        ("leave", "leave"), ("holiday", "leave"),
        ("insurance", "benefits"), ("medical", "benefits"),
        ("joining", "onboarding"), ("new hire", "onboarding")
    ]:
        if keyword in t:
            return category
    return "benefits"

def route(category, confidentiality):
    if confidentiality == "Restricted" or category == "employee_relations":
        return "HR_EMPLOYEE_RELATIONS"
    return {
        "benefits": "HR_BENEFITS",
        "leave": "HR_LEAVE",
        "payroll": "HR_PAYROLL",
        "onboarding": "HR_ONBOARDING"
    }.get(category, "HR_GENERAL")

def build_tickets(employees, categories, articles, count):
    tickets, messages, assignments = [], [], []
    slas, resolutions, events, truth = [], [], [], []

    templates = [
        "How can I check my salary payslip?",
        "I need to apply for annual leave.",
        "Please explain my health insurance benefits.",
        "What documents are required for joining?",
        "I have a confidential employee relations complaint.",
        "I need clarification regarding my leave balance."
    ]

    for i in range(1, count + 1):
        tid = f"TKT-2026-{i:06d}"
        employee = random.choice(employees)

        sensitive = random.random() < 0.04
        ambiguous = random.random() < 0.12
        missing = random.random() < 0.06

        question = random.choice(templates)
        if sensitive:
            question = "Confidential employee relations complaint"
        if missing:
            question = "Please help me with my request"

        category = classify(question, sensitive)
        confidentiality = "Restricted" if sensitive else "Internal"
        priority = random.choices(
            ["Low", "Medium", "High", "Critical"],
            [0.30, 0.45, 0.20, 0.05]
        )[0]

        expected_queue = route(category, confidentiality)
        assigned_queue = expected_queue
        issue = ""

        # Labelled anomaly injection
        if i % 100 == 0:
            assigned_queue = "HR_GENERAL"
            issue = "SENSITIVE_CASE_WRONG_QUEUE"

        article = random.choice(articles)
        expected_action = (
            "REQUEST_CLARIFICATION" if ambiguous or missing
            else "ESCALATE_TO_HR" if sensitive
            else "ANSWER_WITH_POLICY"
        )

        if i % 101 == 0:
            expected_action = "REJECT_OBSOLETE_POLICY_CITATION"
            issue = issue or "OBSOLETE_POLICY_CITATION"

        if i % 103 == 0:
            expected_action = "ESCALATE_UNSUPPORTED_CLAIM"
            issue = issue or "UNSUPPORTED_POLICY_CLAIM"

        created = timestamp(i % 300, i % 8)
        status = "Pending" if ambiguous or missing else (
            "In Progress" if sensitive else "Resolved"
        )

        tickets.append({
            "ticket_id": tid,
            "employee_id": employee["employee_id"],
            "category_id": next(
                c["category_id"] for c in categories
                if c["category_name"] == category
            ),
            "description": question,
            "priority": priority,
            "confidentiality": confidentiality,
            "status": status,
            "created_at": created
        })

        assignments.append({
            "assignment_id": f"ASN-{i:06d}-01",
            "ticket_id": tid,
            "queue": assigned_queue,
            "assigned_at": created,
            "is_current": True
        })

        target = {
            "Critical": 8, "High": 24,
            "Medium": 40, "Low": 80
        }[priority]

        actual = round(random.uniform(1, target * 1.5), 2)
        slas.append({
            "sla_id": f"SLA-{i:06d}",
            "ticket_id": tid,
            "target_hours": target,
            "actual_hours": actual,
            "sla_status": "BREACHED" if actual > target else "MET"
        })

        # Four messages per ticket = exactly 20,000 at 5,000 tickets.
        message_types = [
            ("Request", "Employee"),
            ("Clarification", "HR"),
            ("Response", "HR"),
            ("Resolution", "HR")
        ]
        for j, (mtype, sender) in enumerate(message_types, 1):
            messages.append({
                "message_id": f"MSG-{tid}-{j:03d}",
                "ticket_id": tid,
                "sender_type": sender,
                "message_type": mtype,
                "message_text": (
                    question if j == 1 else
                    "Additional context requested" if j == 2 else
                    "Please refer to the applicable HR policy" if j == 3 else
                    "Request outcome recorded"
                ),
                "created_at": timestamp(i % 300, i % 8 + j)
            })

        events.append({
            "event_id": f"EVT-{i:06d}-01",
            "ticket_id": tid,
            "event_type": "TICKET_CREATED",
            "event_timestamp": created
        })
        events.append({
            "event_id": f"EVT-{i:06d}-02",
            "ticket_id": tid,
            "event_type": status.upper().replace(" ", "_"),
            "event_timestamp": timestamp(i % 300, i % 8 + 1)
        })

        if status == "Resolved":
            resolutions.append({
                "resolution_id": f"RES-{i:06d}",
                "ticket_id": tid,
                "article_id": article["article_id"],
                "outcome": "Resolved",
                "resolved_at": timestamp(i % 300, i % 8 + 4)
            })

        if issue:
            truth.append({
                "ticket_id": tid,
                "issue_type": issue,
                "expected_queue": expected_queue,
                "actual_queue": assigned_queue,
                "expected_action": expected_action,
                "ground_truth": "ANOMALY"
            })

    return tickets, messages, assignments, slas, resolutions, events, truth

def validate(all_tables):
    errors = []
    for name, rows, key in all_tables:
        values = [r[key] for r in rows]
        if len(values) != len(set(values)):
            errors.append(f"Duplicate primary key in {name}")

    tickets = all_tables[0][1]
    employees = {x["employee_id"] for x in all_tables[1][1]}
    for ticket in tickets:
        if ticket["employee_id"] not in employees:
            errors.append(f"Invalid employee FK: {ticket['ticket_id']}")

    return errors

def export_all(tables):
    for name, rows in tables.items():
        save_csv(f"master/{name}.csv" if name in [
            "employees", "departments", "policy_documents",
            "policy_versions", "knowledge_articles", "categories"
        ] else f"transactions/{name}.csv", rows)

    save_json("ground_truth/ground_truth.json", tables["ground_truth"])

    for name, rows in tables.items():
        save_json(f"exports/{name}.json", rows)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickets", type=int, default=5000)
    parser.add_argument("--employees", type=int, default=1000)
    parser.add_argument("--articles", type=int, default=150)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    random.seed(args.seed)

    departments = build_departments()
    employees = build_employees(departments, args.employees)
    categories = build_categories()
    policies, versions = build_policies(departments)
    articles, links = build_articles(
        versions, categories, args.articles
    )

    result = build_tickets(
        employees, categories, articles, args.tickets
    )
    tickets, messages, assignments, slas, resolutions, events, truth = result

    tables = {
        "departments": departments,
        "employees": employees,
        "categories": categories,
        "policy_documents": policies,
        "policy_versions": versions,
        "knowledge_articles": articles,
        "article_policy_versions": links,
        "tickets": tickets,
        "messages": messages,
        "assignments": assignments,
        "sla": slas,
        "resolutions": resolutions,
        "ticket_events": events,
        "ground_truth": truth
    }

    errors = validate([
        ("tickets", tickets, "ticket_id"),
        ("employees", employees, "employee_id"),
        ("departments", departments, "department_id"),
        ("messages", messages, "message_id")
    ])

    if errors:
        raise ValueError(errors)

    export_all(tables)

    summary = {
        "seed": args.seed,
        "tickets": len(tickets),
        "employees": len(employees),
        "articles": len(articles),
        "messages": len(messages),
        "anomalies": len(truth),
        "validation_errors": errors
    }
    #save_json("reports/validation_summary.json", summary)
    report_path = BASE / "reports" / "generation"
    report_path.mkdir(parents=True, exist_ok=True)

    (report_path / "generation_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
