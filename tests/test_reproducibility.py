
import hashlib
import json

from src.generators.master_generator import (
    generate_departments,
    generate_employees,
    generate_categories,
    generate_policy_documents,
    generate_policy_versions,
    generate_knowledge_articles
)

from src.generators.ticket_generator import generate_tickets

from src.generators.message_generator import generate_messages


SEED = 20261022


def generate_test_dataset(seed=SEED, count=100):
    departments = generate_departments()

    employees = generate_employees(
        departments,
        count=50,
        seed=seed
    )

    categories = generate_categories()

    policies = generate_policy_documents(
        departments,
        count=10
    )

    versions = generate_policy_versions(
        policies,
        versions_per_policy=3
    )

    articles, links = generate_knowledge_articles(
        versions,
        categories,
        count=20,
        seed=seed
    )

    transactions = generate_tickets(
        employees,
        categories,
        articles,
        count=count,
        seed=seed
    )

    messages = generate_messages(
        transactions["tickets"]
    )

    return {
        "departments": departments,
        "employees": employees,
        "categories": categories,
        "policies": policies,
        "versions": versions,
        "articles": articles,
        "article_links": links,
        "tickets": transactions["tickets"],
        "messages": messages,
        "assignments": transactions["assignments"],
        "sla": transactions["sla"],
        "resolutions": transactions["resolutions"]
    }


def calculate_dataset_hash(dataset):
    serialized = json.dumps(
        dataset,
        sort_keys=True,
        default=str
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


def test_same_seed_generates_same_data():
    dataset_one = generate_test_dataset(SEED)
    dataset_two = generate_test_dataset(SEED)

    hash_one = calculate_dataset_hash(dataset_one)
    hash_two = calculate_dataset_hash(dataset_two)

    assert hash_one == hash_two


def test_ticket_ids_are_deterministic():
    dataset = generate_test_dataset()

    ticket_ids = [
        ticket["ticket_id"]
        for ticket in dataset["tickets"]
    ]

    assert ticket_ids[0] == "TKT-2026-000001"
    assert ticket_ids[-1] == "TKT-2026-000100"

    assert len(ticket_ids) == len(set(ticket_ids))


def test_employee_ids_are_deterministic():
    dataset = generate_test_dataset()

    employee_ids = [
        employee["employee_id"]
        for employee in dataset["employees"]
    ]

    assert employee_ids[0] == "EMP-000001"
    assert employee_ids[-1] == "EMP-000050"

    assert len(employee_ids) == len(set(employee_ids))


def test_message_ids_are_deterministic():
    dataset = generate_test_dataset()

    messages = dataset["messages"]

    assert messages[0]["message_id"] == (
        "MSG-TKT-2026-000001-001"
    )

    assert len(messages) == 400


def test_dataset_row_counts():
    dataset = generate_test_dataset()

    assert len(dataset["departments"]) == 12
    assert len(dataset["employees"]) == 50
    assert len(dataset["categories"]) == 8
    assert len(dataset["policies"]) == 10
    assert len(dataset["versions"]) == 30
    assert len(dataset["articles"]) == 20
    assert len(dataset["tickets"]) == 100
    assert len(dataset["messages"]) == 400


def test_different_seed_changes_employee_data():
    dataset_one = generate_test_dataset(20261022)
    dataset_two = generate_test_dataset(20261023)

    employees_one = dataset_one["employees"]
    employees_two = dataset_two["employees"]

    assert employees_one != employees_two


def test_full_scale_message_count():
    dataset = generate_test_dataset(
        seed=SEED,
        count=5000
    )

    assert len(dataset["messages"]) == 20000
