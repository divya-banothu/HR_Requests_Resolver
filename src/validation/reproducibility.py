
"""
SHA-256 dataset reproducibility comparison.
Compares two independently generated dataset directories.
"""

import argparse
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
REPORTS = BASE / "reports" / "validation"


def calculate_checksum(file_path):
    sha = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            sha.update(chunk)

    return sha.hexdigest()


def generate_checksum_manifest(folder):
    folder = Path(folder)

    if not folder.is_dir():
        raise FileNotFoundError(
            f"Dataset directory not found: {folder}"
        )

    manifest = {}

    for file in sorted(folder.rglob("*")):
        if file.is_file():
            relative = str(file.relative_to(folder))
            manifest[relative] = calculate_checksum(file)

    return manifest


def compare_checksums(folder_one, folder_two):
    first = generate_checksum_manifest(folder_one)
    second = generate_checksum_manifest(folder_two)

    all_files = set(first) | set(second)
    differences = []

    for filename in sorted(all_files):
        if filename not in first:
            differences.append({
                "file": filename,
                "status": "MISSING_IN_FIRST"
            })

        elif filename not in second:
            differences.append({
                "file": filename,
                "status": "MISSING_IN_SECOND"
            })

        elif first[filename] != second[filename]:
            differences.append({
                "file": filename,
                "status": "CHECKSUM_MISMATCH"
            })

    return {
        "reproducible": len(differences) == 0,
        "files_compared": len(all_files),
        "first_file_count": len(first),
        "second_file_count": len(second),
        "differences": differences
    }


def main():
    parser = argparse.ArgumentParser(
        description="Compare two HR synthetic datasets."
    )

    parser.add_argument(
        "--first",
        required=True,
        help="First generated dataset directory"
    )

    parser.add_argument(
        "--second",
        required=True,
        help="Second generated dataset directory"
    )

    args = parser.parse_args()

    result = compare_checksums(
        args.first,
        args.second
    )

    REPORTS.mkdir(parents=True, exist_ok=True)

    output = REPORTS / "reproducibility_report.json"

    output.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8"
    )

    print("\n========== REPRODUCIBILITY CHECK ==========")
    print(f"Files compared: {result['files_compared']}")
    print(f"First dataset files: {result['first_file_count']}")
    print(f"Second dataset files: {result['second_file_count']}")
    print(
        "Status:",
        "PASS" if result["reproducible"] else "FAIL"
    )

    for difference in result["differences"]:
        print(
            f"[DIFFERENCE] {difference['file']}: "
            f"{difference['status']}"
        )

    print(f"Report saved: {output}")

    if not result["reproducible"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
