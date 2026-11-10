-- 1. Total ticket volume by category
SELECT
    c.category_name,
    COUNT(*) AS ticket_count
FROM Ticket t
JOIN Category c
    ON t.category_id = c.category_id
GROUP BY c.category_name;

-- 2. SLA compliance
SELECT
    sla_status,
    COUNT(*) AS total_tickets
FROM SLA
GROUP BY sla_status;

-- 3. Sensitive tickets
SELECT
    confidentiality,
    COUNT(*) AS total
FROM Ticket
GROUP BY confidentiality;

-- 4. Resolution distribution
SELECT
    outcome,
    COUNT(*) AS total
FROM Resolution
GROUP BY outcome;

-- 5. Tickets with multiple assignments
SELECT
    ticket_id,
    COUNT(*) AS assignment_count
FROM Assignment
GROUP BY ticket_id
HAVING COUNT(*) > 1;

-- 6. Policy versions currently active
SELECT
    policy_id,
    version_id,
    effective_from,
    effective_to
FROM PolicyVersion
WHERE status = 'Active';

-- 7. Potential sensitive-routing violations
SELECT
    t.ticket_id,
    a.queue,
    t.confidentiality
FROM Ticket t
JOIN Assignment a
    ON t.ticket_id = a.ticket_id
WHERE t.confidentiality = 'Restricted'
AND a.is_current = 1
AND a.queue <> 'HR_EMPLOYEE_RELATIONS';