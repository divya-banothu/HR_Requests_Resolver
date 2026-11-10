
import csv
import json
import hashlib
import sqlite3

from pathlib import Path


def export_csv(rows, file_path):
    """
    Export list of dictionaries to CSV.
    """

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        path.write_text("", encoding="utf-8")
        return path

    fieldnames = list(rows[0].keys())

    with open(
        path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)

    return path


def export_json(rows, file_path):
    """
    Export records into JSON.
    """

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(
            rows,
            file,
            indent=4,
            ensure_ascii=False
        )

    return path


def sql_value(value):
    """
    Convert Python values into SQLite-safe literals.
    """

    if value is None:
        return "NULL"

    if isinstance(value, bool):
        return "1" if value else "0"

    if isinstance(value, (int, float)):
        return str(value)

    escaped = str(value).replace("'", "''")

    return f"'{escaped}'"


def export_sql(rows, table_name, file_path):
    """
    Generate SQL INSERT statements.

    Table must already exist in the database schema.
    """

    if not table_name.replace("_", "").isalnum():
        raise ValueError("Invalid SQL table name")

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        path.write_text("", encoding="utf-8")
        return path

    columns = list(rows[0].keys())

    column_sql = ", ".join(
        f'"{column}"' for column in columns
    )

    statements = []

    for row in rows:
        values = ", ".join(
            sql_value(row[column])
            for column in columns
        )

        statements.append(
            f'INSERT INTO "{table_name}" '
            f'({column_sql}) VALUES ({values});'
        )

    path.write_text(
        "\n".join(statements),
        encoding="utf-8"
    )

    return path


def export_sqlite(rows, table_name, database_path):
    """
    Insert records into an existing SQLite table.

    Schema and foreign-key constraints must be created first.
    """

    if not table_name.replace("_", "").isalnum():
        raise ValueError("Invalid SQL table name")

    if not rows:
        return 0

    columns = list(rows[0].keys())

    if any(set(row.keys()) != set(columns) for row in rows):
        raise ValueError("Inconsistent record columns")

    column_sql = ", ".join(
        f'"{column}"' for column in columns
    )

    placeholders = ", ".join(
        ["?"] * len(columns)
    )

    query = (
        f'INSERT INTO "{table_name}" '
        f'({column_sql}) VALUES ({placeholders})'
    )

    values = [
        tuple(row[column] for column in columns)
        for row in rows
    ]

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executemany(query, values)

    return len(rows)


def calculate_file_checksum(file_path):
    """
    Calculate SHA-256 checksum for reproducibility.
    """

    sha = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(
            lambda: file.read(8192), b""
        ):
            sha.update(chunk)

    return sha.hexdigest()


def export_checksum_manifest(folder, output_file):
    """
    Generate checksum manifest for all files.
    """

    folder = Path(folder)
    manifest = {}

    for file in sorted(folder.rglob("*")):
        if file.is_file():
            relative_path = str(
                file.relative_to(folder)
            )

            manifest[relative_path] = (
                calculate_file_checksum(file)
            )

    export_json(manifest, output_file)

    return manifest
