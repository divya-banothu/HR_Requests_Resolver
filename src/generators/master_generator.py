
import random
from datetime import date, timedelta


def generate_departments():
    names = [
        "Human Resources",
        "Finance",
        "Engineering",
        "Sales",
        "Marketing",
        "Operations",
        "Customer Support",
        "Legal",
        "IT",
        "Recruitment",
        "Administration",
        "Compliance"
    ]

    return [
        {
            "department_id": f"DEPT-{i:03d}",
            "department_name": name,
            "department_head": f"Manager {i:03d}",
            "status": "Active"
        }
        for i, name in enumerate(names, 1)
    ]


def generate_employees(departments, count=1000, seed=20261022):
    rng = random.Random(seed)

    employment_types = ["Full-time", "Part-time", "Contract"]
    statuses = ["Active", "Inactive"]
    audiences = ["Employee", "Manager", "Candidate"]
    locations = ["India", "USA", "UK", "Singapore"]

    employees = []

    for i in range(1, count + 1):
        employees.append({
            "employee_id": f"EMP-{i:06d}",
            "department_id": rng.choice(departments)["department_id"],
            "employment_type": rng.choice(employment_types),
            "employment_status": rng.choices(
                statuses, weights=[95, 5]
            )[0],
            "audience": rng.choice(audiences),
            "location": rng.choice(locations),
            "email": f"employee{i:06d}@example.test",
            "joining_date": (
                date(2020, 1, 1) +
                timedelta(days=rng.randint(0, 2400))
            ).isoformat()
        })

    return employees


def generate_categories():
    names = [
        ("benefits", "Benefits"),
        ("leave", "Leave Management"),
        ("payroll", "Payroll"),
        ("onboarding", "Onboarding"),
        ("employee_relations", "Employee Relations"),
        ("harassment", "Harassment"),
        ("discrimination", "Discrimination"),
        ("confidential_complaint", "Confidential Complaint")
    ]

    return [
        {
            "category_id": f"CAT-{i:03d}",
            "category_code": code,
            "category_name": name,
            "status": "Active"
        }
        for i, (code, name) in enumerate(names, 1)
    ]


def generate_policy_documents(departments, count=30):
    rng = random.Random(20261022)

    titles = [
        "Employee Benefits Policy",
        "Annual Leave Policy",
        "Payroll Processing Policy",
        "Employee Onboarding Policy",
        "Work From Home Policy",
        "Employee Conduct Policy",
        "Grievance Handling Policy",
        "Health Insurance Policy"
    ]

    audiences = ["Employee", "Manager", "Candidate", "All"]

    policies = []

    for i in range(1, count + 1):
        policy_id = f"POL-HR-2026-{i:03d}"

        policies.append({
            "policy_id": policy_id,
            "policy_title": rng.choice(titles) + f" {i:03d}",
            "department_id": rng.choice(departments)["department_id"],
            "audience": rng.choice(audiences),
            "owner": "Human Resources",
            "lifecycle_state": "Published",
            "created_date": "2025-01-01"
        })

    return policies


def generate_policy_versions(policies, versions_per_policy=3):
    versions = []

    for policy in policies:
        pid = policy["policy_id"]

        for v in range(1, versions_per_policy + 1):
            start = date(2024 + (v - 1), 1, 1)

            end = (
                date(2024 + v, 1, 1)
                if v < versions_per_policy
                else None
            )

            versions.append({
                "version_id": f"VER-{pid}-{v:02d}",
                "policy_id": pid,
                "version_number": v,
                "effective_from": start.isoformat(),
                "effective_to": end.isoformat() if end else "",
                "status": (
                    "Active"
                    if v == versions_per_policy
                    else "Superseded"
                ),
                "policy_text": (
                    f"Synthetic policy content for {pid}, "
                    f"version {v}"
                ),
                "approval_status": "Approved"
            })

    return versions


def generate_knowledge_articles(
    versions,
    categories,
    count=150,
    seed=20261022
):
    rng = random.Random(seed)

    active_versions = [
        v for v in versions if v["status"] == "Active"
    ]

    articles = []
    links = []

    for i in range(1, count + 1):
        article_id = f"KB-{i:06d}"

        category = rng.choice(categories)
        version = active_versions[(i - 1) % len(active_versions)]

        articles.append({
            "article_id": article_id,
            "category_id": category["category_id"],
            "title": f"HR Knowledge Article {i:03d}",
            "answer_snippet": (
                f"Please refer to {version['policy_id']} "
                f"for the applicable HR guidance."
            ),
            "status": "Published",
            "created_at": "2026-01-01"
        })

        links.append({
            "link_id": f"APL-{i:06d}",
            "article_id": article_id,
            "version_id": version["version_id"]
        })

    return articles, links
