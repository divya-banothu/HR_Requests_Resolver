PRAGMA foreign_keys = ON;

CREATE TABLE Department (
    department_id TEXT PRIMARY KEY,
    department_name TEXT NOT NULL UNIQUE
);

CREATE TABLE Employee (
    employee_id TEXT PRIMARY KEY,
    department_id TEXT NOT NULL,
    employment_type TEXT NOT NULL,
    employment_status TEXT NOT NULL,
    audience TEXT NOT NULL,
    location TEXT NOT NULL,
    FOREIGN KEY (department_id)
        REFERENCES Department(department_id)
);

CREATE TABLE PolicyDocument (
    policy_id TEXT PRIMARY KEY,
    policy_title TEXT NOT NULL,
    department_id TEXT,
    audience TEXT NOT NULL,
    lifecycle_state TEXT NOT NULL,
    FOREIGN KEY (department_id)
        REFERENCES Department(department_id)
);

CREATE TABLE PolicyVersion (
    version_id TEXT PRIMARY KEY,
    policy_id TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE,
    status TEXT NOT NULL,
    policy_text TEXT NOT NULL,
    UNIQUE(policy_id, version_number),
    FOREIGN KEY (policy_id)
        REFERENCES PolicyDocument(policy_id),
    CHECK (
        effective_to IS NULL
        OR effective_to > effective_from
    )
);

CREATE TABLE Category (
    category_id TEXT PRIMARY KEY,
    category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE KnowledgeArticle (
    article_id TEXT PRIMARY KEY,
    category_id TEXT NOT NULL,
    title TEXT NOT NULL,
    answer_snippet TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (category_id)
        REFERENCES Category(category_id)
);

CREATE TABLE ArticlePolicyVersion (
    link_id TEXT PRIMARY KEY,
    article_id TEXT NOT NULL,
    version_id TEXT NOT NULL,
    FOREIGN KEY (article_id)
        REFERENCES KnowledgeArticle(article_id),
    FOREIGN KEY (version_id)
        REFERENCES PolicyVersion(version_id),
    UNIQUE(article_id, version_id)
);

CREATE TABLE Ticket (
    ticket_id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL,
    category_id TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT NOT NULL,
    confidentiality TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (employee_id)
        REFERENCES Employee(employee_id),
    FOREIGN KEY (category_id)
        REFERENCES Category(category_id)
);

CREATE TABLE Message (
    message_id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL,
    sender_type TEXT NOT NULL,
    message_type TEXT NOT NULL,
    message_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (ticket_id)
        REFERENCES Ticket(ticket_id)
);

CREATE TABLE Assignment (
    assignment_id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL,
    queue TEXT NOT NULL,
    assigned_at TEXT NOT NULL,
    is_current INTEGER NOT NULL,
    FOREIGN KEY (ticket_id)
        REFERENCES Ticket(ticket_id)
);

CREATE TABLE SLA (
    sla_id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL UNIQUE,
    target_hours REAL NOT NULL,
    actual_hours REAL,
    sla_status TEXT NOT NULL,
    FOREIGN KEY (ticket_id)
        REFERENCES Ticket(ticket_id)
);

CREATE TABLE Resolution (
    resolution_id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL UNIQUE,
    article_id TEXT,
    outcome TEXT NOT NULL,
    resolved_at TEXT NOT NULL,
    FOREIGN KEY (ticket_id)
        REFERENCES Ticket(ticket_id),
    FOREIGN KEY (article_id)
        REFERENCES KnowledgeArticle(article_id)
);

CREATE TABLE TicketEvent (
    event_id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_timestamp TEXT NOT NULL,
    FOREIGN KEY (ticket_id)
        REFERENCES Ticket(ticket_id)
);