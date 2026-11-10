
import sqlite3
import pytest # type: ignore


@pytest.fixture
def db_connection(tmp_path):
    db_path = tmp_path / "test_hr.db"

    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")

    schema_path = "sql/relationships.sql"

    with open(schema_path, encoding="utf-8") as file:
        connection.executescript(file.read())

    yield connection

    connection.close()


def insert_reference_data(conn):
    conn.execute("""
        INSERT INTO departments VALUES
        ('DEPT-001', 'Human Resources', 'Manager 001', 'Active')
    """)

    conn.execute("""
        INSERT INTO employees VALUES
        ('EMP-000001', 'DEPT-001', 'Full-time',
        'Active', 'Employee', 'India',
        'employee1@example.test', '2025-01-01')
    """)

    conn.execute("""
        INSERT INTO categories VALUES
        ('CAT-001', 'benefits', 'Benefits', 'Active')
    """)


def test_valid_employee_department_fk(db_connection):
    insert_reference_data(db_connection)

    result = db_connection.execute("""
        SELECT COUNT(*)
        FROM employees e
        JOIN departments d
        ON e.department_id = d.department_id
    """).fetchone()[0]

    assert result == 1


def test_invalid_employee_department_fk(db_connection):
    with pytest.raises(sqlite3.IntegrityError):
        db_connection.execute("""
            INSERT INTO employees VALUES
            ('EMP-000002', 'DEPT-999', 'Full-time',
            'Active', 'Employee', 'India',
            'employee2@example.test', '2025-01-01')
        """)


def test_duplicate_employee_primary_key(db_connection):
    insert_reference_data(db_connection)

    with pytest.raises(sqlite3.IntegrityError):
        db_connection.execute("""
            INSERT INTO employees VALUES
            ('EMP-000001', 'DEPT-001', 'Full-time',
            'Active', 'Employee', 'India',
            'duplicate@example.test', '2025-01-01')
        """)


def test_ticket_employee_fk(db_connection):
    insert_reference_data(db_connection)

    with pytest.raises(sqlite3.IntegrityError):
        db_connection.execute("""
            INSERT INTO tickets VALUES
            ('TKT-2026-000001', 'EMP-999999',
            'CAT-001', 'Benefits request',
            'Medium', 'Internal', 'Open',
            '2026-01-01T09:00:00')
        """)


def test_valid_ticket_relationships(db_connection):
    insert_reference_data(db_connection)

    db_connection.execute("""
        INSERT INTO tickets VALUES
        ('TKT-2026-000001', 'EMP-000001',
        'CAT-001', 'Benefits request',
        'Medium', 'Internal', 'Open',
        '2026-01-01T09:00:00')
    """)

    result = db_connection.execute("""
        SELECT COUNT(*)
        FROM tickets t
        JOIN employees e
            ON t.employee_id = e.employee_id
        JOIN categories c
            ON t.category_id = c.category_id
    """).fetchone()[0]

    assert result == 1


def test_ticket_message_fk(db_connection):
    insert_reference_data(db_connection)

    with pytest.raises(sqlite3.IntegrityError):
        db_connection.execute("""
            INSERT INTO messages VALUES
            ('MSG-TKT-2026-000001-001',
            'TKT-2026-999999', 'Employee',
            'Request', 'Test message',
            '2026-01-01T09:00:00')
        """)


def test_sqlite_foreign_key_check(db_connection):
    violations = db_connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    assert violations == []


def test_foreign_keys_enabled(db_connection):
    enabled = db_connection.execute(
        "PRAGMA foreign_keys"
    ).fetchone()[0]

    assert enabled == 1
