
PRAGMA foreign_keys = ON;

-- ==========================================
-- 1. DEPARTMENT
-- ==========================================

CREATE TABLE IF NOT EXISTS departments (
    department_id TEXT PRIMARY KEY,
    department_name TEXT NOT NULL UNIQUE,
    department_head TEXT,
    status TEXT NOT NULL DEFAULT 'Active'
        CHECK(status IN ('Active', 'Inactive'))
);

-- ==========================================
-- 2. EMPLOYEE
-- ==========================================

CREATE TABLE IF NOT EXISTS employees (
    employee_id TEXT PRIMARY KEY,
    department_id TEXT NOT NULL,
    employment_type TEXT NOT NULL
        CHECK(employment_type IN (
            'Full-time', 'Part-time', 'Contract'
        )),
    employment_status TEXT NOT NULL
        CHECK(employment_status IN ('Active', 'Inactive')),
    audience TEXT NOT NULL
        CHECK(audience IN ('Employee', 'Manager', 'Candidate')),
    location TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    joining_date TEXT NOT NULL,

    FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
);

-- ==========================================
-- 3. CATEGORY
-- ==========================================

CREATE TABLE IF NOT EXISTS categories (
    category_id TEXT PRIMARY KEY,
    category_code TEXT NOT NULL UNIQUE,
    category_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Active'
);

-- ==========================================
-- 4. POLICY DOCUMENT
-- ==========================================

CREATE TABLE IF NOT EXISTS policy_documents (
    policy_id TEXT PRIMARY KEY,
    policy_title TEXT NOT NULL,
    department_id TEXT NOT NULL,
    audience TEXT NOT NULL
        CHECK(audience IN (
            'Employee', 'Manager', 'Candidate', 'All'
        )),
    owner TEXT NOT NULL,
    lifecycle_state TEXT NOT NULL
        CHECK(lifecycle_state IN (
            'Draft', 'Published', 'Retired'
        )),
    created_date TEXT NOT NULL,

    FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
);

-- ==========================================
-- 5. POLICY VERSION
-- ==========================================

CREATE TABLE IF NOT EXISTS policy_versions (
    version_id TEXT PRIMARY KEY,
    policy_id TEXT NOT NULL,
    version_number INTEGER NOT NULL CHECK(version_number > 0),
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    status TEXT NOT NULL
        CHECK(status IN ('Active', 'Superseded', 'Draft')),
    policy_text TEXT NOT NULL,
    approval_status TEXT NOT NULL
        CHECK(approval_status IN ('Approved', 'Pending', 'Rejected')),

    UNIQUE(policy_id, version_number),

    CHECK(
        effective_to IS NULL
        OR effective_to > effective_from
    ),

    FOREIGN KEY (policy_id)
        REFERENCES policy_documents(policy_id)
);

CREATE INDEX IF NOT EXISTS idx_policy_effective
ON policy_versions(policy_id, effective_from, effective_to);

-- ==========================================
-- 6. KNOWLEDGE ARTICLE
-- ==========================================

CREATE TABLE IF NOT EXISTS knowledge_articles (
    article_id TEXT PRIMARY KEY,
    category_id TEXT NOT NULL,
    title TEXT NOT NULL,
    answer_snippet TEXT NOT NULL,
    status TEXT NOT NULL
        CHECK(status IN ('Draft', 'Published', 'Archived')),
    created_at TEXT NOT NULL,

    FOREIGN KEY (category_id)
        REFERENCES categories(category_id)
);

-- ==========================================
-- 7. ARTICLE POLICY VERSION BRIDGE
-- ==========================================

CREATE TABLE IF NOT EXISTS article_policy_versions (
    link_id TEXT PRIMARY KEY,
    article_id TEXT NOT NULL,
    version_id TEXT NOT NULL,

    UNIQUE(article_id, version_id),

    FOREIGN KEY (article_id)
        REFERENCES knowledge_articles(article_id),

    FOREIGN KEY (version_id)
        REFERENCES policy_versions(version_id)
);

-- ==========================================
-- 8. TICKET
-- ==========================================

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL,
    category_id TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT NOT NULL
        CHECK(priority IN ('Low', 'Medium', 'High', 'Critical')),
    confidentiality TEXT NOT NULL
        CHECK(confidentiality IN ('Internal', 'Restricted')),
    status TEXT NOT NULL
        CHECK(status IN (
            'Open', 'In Progress', 'Pending',
            'Escalated', 'Resolved', 'Closed'
        )),
    created_at TEXT NOT NULL,

    FOREIGN KEY (employee_id)
        REFERENCES employees(employee_id),

    FOREIGN KEY (category_id)
        REFERENCES categories(category_id)
);

-- ==========================================
-- 9. MESSAGE
-- ==========================================

CREATE TABLE IF NOT EXISTS messages (
    message_id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL,
    sender_type TEXT NOT NULL
        CHECK(sender_type IN (
            'Employee', 'HR', 'Manager', 'System', 'IT'
        )),
    message_type TEXT NOT NULL
        CHECK(message_type IN (
            'Request', 'Clarification',
            'Response', 'Resolution'
        )),
    message_text TEXT NOT NULL,
    created_at TEXT NOT NULL,

    FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id)
);

-- ==========================================
-- 10. ASSIGNMENT
-- ==========================================

CREATE TABLE IF NOT EXISTS assignments (
    assignment_id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL,
    queue TEXT NOT NULL,
    assigned_at TEXT NOT NULL,
    is_current INTEGER NOT NULL DEFAULT 1
        CHECK(is_current IN (0, 1)),

    FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id)
);

CREATE INDEX IF NOT EXISTS idx_assignment_ticket
ON assignments(ticket_id);

-- ==========================================
-- 11. SLA
-- ==========================================

CREATE TABLE IF NOT EXISTS sla (
    sla_id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL UNIQUE,
    target_hours REAL NOT NULL CHECK(target_hours >= 0),
    actual_hours REAL NOT NULL CHECK(actual_hours >= 0),
    sla_status TEXT NOT NULL
        CHECK(sla_status IN ('MET', 'BREACHED', 'PENDING')),

    FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id)
);

-- ==========================================
-- 12. RESOLUTION
-- ==========================================

CREATE TABLE IF NOT EXISTS resolutions (
    resolution_id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL UNIQUE,
    article_id TEXT,
    outcome TEXT NOT NULL,
    resolved_at TEXT NOT NULL,

    FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id),

    FOREIGN KEY (article_id)
        REFERENCES knowledge_articles(article_id)
);

-- ==========================================
-- 13. TICKET EVENT HISTORY
-- ==========================================

CREATE TABLE IF NOT EXISTS ticket_events (
    event_id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT,
    event_timestamp TEXT NOT NULL,
    event_source TEXT NOT NULL,

    FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id)
);

CREATE INDEX IF NOT EXISTS idx_ticket_events
ON ticket_events(ticket_id, event_timestamp);

-- ==========================================
-- 14. AUDIT HISTORY
-- ==========================================

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_name TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_at TEXT NOT NULL,
    changed_by TEXT NOT NULL
);

-- ==========================================
-- 15. HELPFUL VIEWS
-- ==========================================

CREATE VIEW IF NOT EXISTS ticket_overview AS
SELECT
    t.ticket_id,
    t.employee_id,
    e.department_id,
    c.category_code,
    t.priority,
    t.status,
    t.confidentiality,
    a.queue,
    s.target_hours,
    s.actual_hours,
    s.sla_status
FROM tickets t
JOIN employees e
    ON t.employee_id = e.employee_id
JOIN categories c
    ON t.category_id = c.category_id
LEFT JOIN assignments a
    ON t.ticket_id = a.ticket_id
    AND a.is_current = 1
LEFT JOIN sla s
    ON t.ticket_id = s.ticket_id;

-- ==========================================
-- 16. CURRENT POLICY VERSION VIEW
-- ==========================================

CREATE VIEW IF NOT EXISTS current_policy_versions AS
SELECT
    pv.version_id,
    pv.policy_id,
    pv.version_number,
    pv.effective_from,
    pv.effective_to,
    pd.policy_title,
    pd.audience
FROM policy_versions pv
JOIN policy_documents pd
    ON pv.policy_id = pd.policy_id
WHERE pv.status = 'Active'
AND pv.approval_status = 'Approved';
