# HR Routine Requests Resolver — Frontend Web App & Studio

An executive dashboard and real-time interactive resolution studio for the **HR Routine Requests Resolver** system.

---

## 🚀 Quick Start Options

You can launch and use the frontend in two different ways:

### Option 1: Live Interactive Server (Recommended)
This connects the frontend to the actual Python backend, datasets (5,000 tickets, 30 policies, 1,000 employees), and runs the live classification, routing, and resolution engines on real requests.

```powershell
# From the project root (HR_Routine_Requests_Resolver):
python serve.py
```

Then open your browser to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

*(Zero extra dependencies required — uses Python's standard library).*

---

### Option 2: Direct Browser Launch (No Server Needed)
You can directly open `frontend/index.html` in any web browser (Chrome, Edge, Safari, Firefox). The application automatically switches to **Client Preview Mode** with offline simulation fallback if the backend server is not running.

---

## ✨ Features

### 1. Executive Operations Dashboard
- **6 Core KPI Metric Cards**:
  - **Total Inquiries**: 5,000 processed tickets across 12 departments.
  - **Classification Accuracy**: 94.08% auto-classification (4,704 classified, 296 flagged ambiguous).
  - **SLA Compliance**: 92.60% (4,630 met, 370 breached).
  - **Policy Auto-Answers**: 3,758 verified policy answers (75.16% automated resolution).
  - **Sensitive Cases**: 946 restricted tickets isolated to `HR_EMPLOYEE_RELATIONS`.
  - **Smart Router Correction**: 21.78% (1,089 tickets redirected from general to specialist queues).
- **Interactive Chart.js Visualizations**:
  - Inquiries distribution across categories (Benefits, Leave, Payroll, Onboarding, Relations).
  - SLA performance stacked breakdown by Priority (Critical 8h, High 24h, Medium 40h, Low 80h).
  - Engine decisions (Policy Auto-Answer vs Escalate to Specialist vs Clarify).
  - Departmental queue allocations.

### 2. Live Request Resolver Studio
- **Interactive Query Sandbox**:
  - Type or paste any employee query.
  - Select confidentiality (`Internal` vs `Restricted`), priority, employee audience, and as-of date.
  - **5 One-Click Presets**:
    1. 🩺 *Health Insurance Coverage*: Evaluates benefits policy and generates policy answer.
    2. 🛑 *Misconduct Report*: Flags restricted harassment keywords and routes to `HR_EMPLOYEE_RELATIONS`.
    3. ❓ *Vague Request*: Detects missing context and prompts for employee clarification.
    4. 💰 *Payroll / Tax Cutoff*: Matches payroll category and verifies tax guidelines.
    5. 🌴 *Annual Vacation Balance*: Directs to leave entitlement rules.
- **Pipeline Stepper Visualizer**:
  - **Step 1: Classification Engine** (Confidence %, Category, Sensitivity flag, Keyword match reason).
  - **Step 2: Ambiguity Engine** (Checks for vague context or missing fields).
  - **Step 3: Smart Routing Engine** (Computes target queue & priority flag).
  - **Step 4: Policy & Citation Engine** (Finds published policy document & active version).
  - **Step 5: SLA Prediction** (Target hours based on priority and business hour schedules).

### 3. Audited Ticket Explorer
- Search across Ticket ID, Employee ID, inquiry description, or department.
- Multi-attribute filters: Category, Decision, SLA Status (Met / Breached), and Confidentiality.
- Interactive table with paginated display (20 per page).
- **Click-to-Inspect Drawer**:
  - Full employee metadata (department, location, employment type, audience).
  - Policy citation verification details.
  - SLA adherence timeline (target vs actual business hours).
  - Complete chronological message transcript between Employee and HR.

### 4. Policy Knowledge Base Browser
- Search and browse all 30 enterprise HR policies.
- Expandable version accordion showing Version history (v1, v2, v3), effective date ranges, and policy text.
- Verified active status vs superseded version auditing.

### 5. Validation & Compliance Audit
- Summarizes data integrity checks (Foreign key matching, 0 orphan records).
- Seed reproducibility verification (Deterministic seed `20261022`).
- Business rules compliance guardrail summary.

---

## 📡 REST API Reference

When `serve.py` is running, the following JSON endpoints are available:

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/metrics` | `GET` | System summary statistics, queue counts, category breakdowns, and SLA ratios |
| `/api/tickets` | `GET` | Paginated and filtered ticket list (`search`, `category`, `decision`, `sla_status`, `page`, `limit`) |
| `/api/tickets/<ticket_id>` | `GET` | Detailed record with linked messages, employee profile, policy citation, and SLA info |
| `/api/resolve` | `POST` | Executes the real-time resolution pipeline on an arbitrary query payload |
| `/api/policies` | `GET` | All 30 master policy documents with versions and linked knowledge articles |
| `/api/validation` | `GET` | Validation reports (summary, integrity, and business rules) |

