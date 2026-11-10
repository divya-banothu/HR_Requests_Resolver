
from datetime import date

def get_effective_policy(versions, policy_id, audience, on_date):
    candidates = [
        v for v in versions
        if v["policy_id"] == policy_id
        and v["status"] == "Active"
        and date.fromisoformat(v["effective_from"]) <= on_date
        and (
            not v["effective_to"]
            or on_date < date.fromisoformat(v["effective_to"])
        )
    ]

    if not candidates:
        return {
            "decision": "ESCALATE_TO_HR",
            "reason": "NO_EFFECTIVE_POLICY"
        }

    version = max(candidates, key=lambda x: x["version_number"])

    return {
        "decision": "ANSWER_WITH_POLICY",
        "version_id": version["version_id"],
        "policy_id": policy_id,
        "reason": "EFFECTIVE_POLICY_FOUND"
    }

def validate_citation(version, on_date):
    if version["status"] != "Active":
        return False

    start = date.fromisoformat(version["effective_from"])
    end = (
        date.fromisoformat(version["effective_to"])
        if version["effective_to"] else None
    )

    return start <= on_date and (end is None or on_date < end)
