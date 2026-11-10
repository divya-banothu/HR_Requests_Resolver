
"""
Consolidated validation report generator.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

from src.validation.integrity import (
    load_tables as load_integrity_tables,
    validate_all
)

from src.validation.business_rules import (
    load_tables as load_business_tables,
    load_ground_truth,
    validate_business_rules
)

BASE = Path(__file__).resolve().parents[2]
REPORTS = BASE / "reports" / "validation"


def generate_validation_report(
    integrity_result,
    business_result,
    output_path=None
):
    integrity_passed = (
        integrity_result["overall_status"] == "PASS"
    )

    business_passed = business_result["passed"]

    report = {
        "project": "HR Policy Resolution System",
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "overall_status": (
            "PASS"
            if integrity_passed and business_passed
            else "FAIL"
        ),

        "integrity": integrity_result,
        "business_rules": business_result,

        "total_errors": (
            integrity_result["failed"]
            + business_result["error_count"]
        ),

        "total_warnings": len(
            business_result["warnings"]
        ),

        "known_anomalies": business_result[
            "expected_anomaly_count"
        ]
    }

    path = Path(
        output_path
        if output_path
        else REPORTS / "validation_summary.json"
    )

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8"
    )

    return report


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)

    print("\nLoading generated datasets...")

    integrity_tables = load_integrity_tables()
    business_tables = load_business_tables()
    ground_truth = load_ground_truth()

    print("Running integrity validation...")

    integrity_result = validate_all(
        integrity_tables
    )

    print("Running business rule validation...")

    business_result = validate_business_rules(
        business_tables,
        ground_truth
    )

    # Save individual reports.
    (REPORTS / "integrity_report.json").write_text(
        json.dumps(integrity_result, indent=2),
        encoding="utf-8"
    )

    (REPORTS / "business_rules_report.json").write_text(
        json.dumps(business_result, indent=2),
        encoding="utf-8"
    )

    report = generate_validation_report(
        integrity_result,
        business_result
    )

    print("\n========== FINAL VALIDATION REPORT ==========")

    print(
        "Integrity:",
        integrity_result["overall_status"]
    )

    print(
        "Business rules:",
        "PASS" if business_result["passed"] else "FAIL"
    )

    print(
        "Known anomalies:",
        business_result["expected_anomaly_count"]
    )

    print("Total unexpected errors:", report["total_errors"])

    print(
        "Overall status:",
        report["overall_status"]
    )

    print(f"\nReports saved in: {REPORTS}")

    if report["overall_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
