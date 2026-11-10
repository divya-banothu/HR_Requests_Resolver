"""
HR Routine Requests Resolver - Backend API & Frontend Server
Serves the web UI and provides REST APIs for live simulation, ticket exploration, and analytics.
Zero external dependencies required (uses Python standard library).
"""

import csv
import json
import mimetypes
import os
import sys
from datetime import datetime, date, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Set up project root and import engines
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.engine.classification import classify_ticket, check_ambiguity
from src.engine.routing_engine import determine_route
from src.engine.policy_engine import get_effective_policy, validate_citation
from src.engine.resolution_engine import resolve_ticket
from src.engine.sla_engine import calculate_sla, TARGETS

FRONTEND_DIR = ROOT / "frontend"
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"


def load_csv(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_json(path, default=None):
    if not path.exists():
        return default if default is not None else {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


print("[*] Loading HR Resolver datasets...")

# Master data
departments = load_csv(DATA_DIR / "master" / "departments.csv")
categories = load_csv(DATA_DIR / "master" / "categories.csv")
employees = load_csv(DATA_DIR / "master" / "employees.csv")
policy_docs = load_csv(DATA_DIR / "master" / "policy_documents.csv")
policy_versions = load_csv(DATA_DIR / "master" / "policy_versions.csv")
knowledge_articles = load_csv(DATA_DIR / "master" / "knowledge_articles.csv")

# Reports and decisions
metrics = load_json(REPORTS_DIR / "integration" / "integration_metrics.json", default={})
validation_summary = load_json(REPORTS_DIR / "validation" / "validation_summary.json", default={})
integrity_report = load_json(REPORTS_DIR / "validation" / "integrity_report.json", default={})
business_rules_report = load_json(REPORTS_DIR / "validation" / "business_rules_report.json", default={})
ticket_decisions = load_csv(REPORTS_DIR / "integration" / "ticket_decisions.csv")
transactions_tickets = load_csv(DATA_DIR / "transactions" / "tickets.csv")
messages = load_csv(DATA_DIR / "transactions" / "messages.csv")
assignments = load_csv(DATA_DIR / "transactions" / "assignments.csv")
resolutions = load_csv(DATA_DIR / "transactions" / "resolutions.csv")
slas = load_csv(DATA_DIR / "transactions" / "sla.csv")

# Build quick lookup indexes
emp_map = {e["employee_id"]: e for e in employees}
dept_map = {d["department_id"]: d["department_name"] for d in departments}
cat_map = {c["category_id"]: c["category_name"] for c in categories}
policy_map = {p["policy_id"]: p for p in policy_docs}
version_map = {v["version_id"]: v for v in policy_versions}
ticket_desc_map = {t["ticket_id"]: t for t in transactions_tickets}

messages_by_ticket = {}
for m in messages:
    tid = m["ticket_id"]
    messages_by_ticket.setdefault(tid, []).append(m)

assignments_by_ticket = {}
for a in assignments:
    tid = a["ticket_id"]
    assignments_by_ticket.setdefault(tid, []).append(a)

resolutions_by_ticket = {r["ticket_id"]: r for r in resolutions}
sla_by_ticket = {s["ticket_id"]: s for s in slas}

# Enrich ticket decisions with descriptions, priority, confidentiality, dept names
enriched_tickets = []
for td in ticket_decisions:
    tid = td["ticket_id"]
    t_raw = ticket_desc_map.get(tid, {})
    emp = emp_map.get(td.get("employee_id"), {})
    item = dict(td)
    item["description"] = t_raw.get("description", "")
    item["priority"] = t_raw.get("priority", "Medium")
    item["confidentiality"] = t_raw.get("confidentiality", "Internal")
    item["created_at"] = t_raw.get("created_at", "")
    item["department_name"] = dept_map.get(td.get("department_id"), td.get("department_id", "Unknown"))
    item["employee_location"] = emp.get("location", "Global")
    item["employee_type"] = emp.get("employment_type", "Full-time")
    item["employee_audience"] = emp.get("audience", "Employee")
    enriched_tickets.append(item)

print(f"[+] Loaded {len(enriched_tickets)} tickets, {len(policy_docs)} policies, {len(employees)} employees.")


class HRResolverHandler(SimpleHTTPRequestHandler):
    """Custom request handler that serves both static frontend files and API endpoints."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path.startswith("/api/"):
            self.handle_api_get(path, query)
        else:
            # If requesting root or a non-existent static file, serve index.html
            target = FRONTEND_DIR / path.lstrip("/")
            if path == "/" or not target.exists() or target.is_dir():
                self.serve_file(FRONTEND_DIR / "index.html", "text/html; charset=utf-8")
            else:
                super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/resolve":
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)
            try:
                data = json.loads(raw_body.decode("utf-8"))
            except Exception as e:
                self.send_json({"error": f"Invalid JSON payload: {str(e)}"}, status=400)
                return
            self.handle_resolve(data)
        else:
            self.send_json({"error": "Endpoint not found"}, status=404)

    def handle_api_get(self, path, query):
        if path == "/api/metrics":
            # Compute distributions
            cat_counts = {}
            queue_counts = {}
            priority_sla = {}
            decision_counts = {}

            for t in enriched_tickets:
                c = t.get("predicted_category") or t.get("source_category", "other")
                cat_counts[c] = cat_counts.get(c, 0) + 1

                q = t.get("recommended_queue", "HR_GENERAL")
                queue_counts[q] = queue_counts.get(q, 0) + 1

                d = t.get("decision", "OTHER")
                decision_counts[d] = decision_counts.get(d, 0) + 1

                p = t.get("priority", "Medium")
                if p not in priority_sla:
                    priority_sla[p] = {"total": 0, "met": 0, "breached": 0}
                priority_sla[p]["total"] += 1
                if t.get("sla_status") == "MET":
                    priority_sla[p]["met"] += 1
                else:
                    priority_sla[p]["breached"] += 1

            payload = {
                "summary": metrics,
                "categories": cat_counts,
                "queues": queue_counts,
                "priority_sla": priority_sla,
                "decisions": decision_counts,
                "departments": departments,
                "total_tickets": len(enriched_tickets),
                "total_policies": len(policy_docs),
                "total_versions": len(policy_versions),
                "total_articles": len(knowledge_articles)
            }
            self.send_json(payload)

        elif path == "/api/tickets":
            # Search & Filter
            search = query.get("search", [""])[0].strip().lower()
            category = query.get("category", [""])[0].strip()
            queue = query.get("queue", [""])[0].strip()
            decision = query.get("decision", [""])[0].strip()
            sla_status = query.get("sla_status", [""])[0].strip().upper()
            sensitive = query.get("sensitive", [""])[0].strip().lower()
            page = max(1, int(query.get("page", [1])[0]))
            limit = min(100, max(1, int(query.get("limit", [20])[0])))

            filtered = enriched_tickets

            if search:
                filtered = [
                    t for t in filtered
                    if search in t["ticket_id"].lower()
                    or search in t["employee_id"].lower()
                    or search in t.get("description", "").lower()
                    or search in t.get("predicted_category", "").lower()
                    or search in t.get("department_name", "").lower()
                ]

            if category:
                filtered = [t for t in filtered if t.get("predicted_category") == category or t.get("source_category") == category]

            if queue:
                filtered = [t for t in filtered if t.get("recommended_queue") == queue or t.get("resolution_queue") == queue]

            if decision:
                filtered = [t for t in filtered if t.get("decision") == decision]

            if sla_status:
                filtered = [t for t in filtered if t.get("sla_status") == sla_status]

            if sensitive in ("true", "1"):
                filtered = [t for t in filtered if str(t.get("sensitive")).lower() in ("true", "1")]
            elif sensitive in ("false", "0"):
                filtered = [t for t in filtered if str(t.get("sensitive")).lower() in ("false", "0")]

            total = len(filtered)
            total_pages = max(1, (total + limit - 1) // limit)
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            page_items = filtered[start_idx:end_idx]

            self.send_json({
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "tickets": page_items
            })

        elif path.startswith("/api/tickets/"):
            ticket_id = path.replace("/api/tickets/", "").strip()
            ticket = next((t for t in enriched_tickets if t["ticket_id"] == ticket_id), None)
            if not ticket:
                self.send_json({"error": f"Ticket {ticket_id} not found"}, status=404)
                return

            # Attach messages, assignments, resolution details, policy details
            t_messages = messages_by_ticket.get(ticket_id, [])
            t_assignments = assignments_by_ticket.get(ticket_id, [])
            t_resolution = resolutions_by_ticket.get(ticket_id, {})
            t_sla = sla_by_ticket.get(ticket_id, {})

            policy_detail = None
            if ticket.get("policy_version_id"):
                vid = ticket["policy_version_id"]
                v = version_map.get(vid)
                if v:
                    p = policy_map.get(v.get("policy_id"), {})
                    policy_detail = {
                        "version_id": vid,
                        "policy_id": v.get("policy_id"),
                        "title": p.get("policy_title", ""),
                        "audience": p.get("audience", ""),
                        "effective_from": v.get("effective_from"),
                        "effective_to": v.get("effective_to"),
                        "status": v.get("status"),
                        "policy_text": v.get("policy_text")
                    }

            self.send_json({
                "ticket": ticket,
                "messages": t_messages,
                "assignments": t_assignments,
                "resolution": t_resolution,
                "sla": t_sla,
                "policy": policy_detail
            })

        elif path == "/api/policies":
            # Group versions by policy
            policies_with_versions = []
            for p in policy_docs:
                pid = p["policy_id"]
                p_versions = [v for v in policy_versions if v["policy_id"] == pid]
                p_articles = [a for a in knowledge_articles if pid in a.get("answer_snippet", "")]
                policies_with_versions.append({
                    **p,
                    "versions": p_versions,
                    "articles": p_articles
                })
            self.send_json(policies_with_versions)

        elif path == "/api/validation":
            self.send_json({
                "summary": validation_summary,
                "integrity": integrity_report,
                "business_rules": business_rules_report
            })

        else:
            self.send_json({"error": "Unknown API endpoint"}, status=404)

    def handle_resolve(self, data):
        """Live simulation of resolution pipeline on arbitrary user input."""
        description = data.get("description", "").strip()
        confidentiality = data.get("confidentiality", "Internal")
        priority = data.get("priority", "Medium")
        employee_id = data.get("employee_id", "EMP-000001")
        audience = data.get("audience", "Employee")
        as_of_str = data.get("as_of_date")

        if not description:
            self.send_json({"error": "Ticket description is required"}, status=400)
            return

        as_of = date.today()
        if as_of_str:
            try:
                as_of = datetime.fromisoformat(as_of_str).date()
            except Exception:
                pass

        # Step 1: Classification Engine
        classification = classify_ticket(description)

        # Step 2: Ambiguity Engine
        ambiguity = check_ambiguity(description)

        # Step 3: Routing Engine
        routing = determine_route({
            "category": classification["category"],
            "confidentiality": confidentiality
        })

        # Step 4: Resolution Decision Engine
        ticket_mock = {
            "ticket_id": "SIM-" + datetime.now().strftime("%Y%m%d%H%M%S"),
            "description": description,
            "confidentiality": confidentiality,
            "priority": priority,
            "employee_id": employee_id,
            "created_at": datetime.now().isoformat()
        }

        decision = resolve_ticket(
            ticket=ticket_mock,
            policies=policy_docs,
            versions=policy_versions,
            today=as_of
        )

        citation_id = decision.get("policy_reference")
        citation_valid = False
        cited_version = None
        cited_policy = None

        if citation_id:
            cited_version = version_map.get(citation_id)
            if cited_version:
                citation_valid = validate_citation(cited_version, as_of)
                cited_policy = policy_map.get(cited_version.get("policy_id"))

        final_decision = decision["decision"]
        decision_reason = decision["reason"]
        if final_decision == "ANSWER_WITH_POLICY" and not citation_valid:
            final_decision = "ESCALATE_TO_HR"
            decision_reason = "INVALID_POLICY_CITATION"

        # Step 5: SLA Prediction
        target_hours = TARGETS.get(priority, 40)

        response_payload = {
            "simulated_ticket_id": ticket_mock["ticket_id"],
            "timestamp": datetime.now().isoformat(),
            "pipeline": {
                "classification": {
                    "category": classification["category"],
                    "confidence": classification["confidence"],
                    "sensitive": classification["sensitive"],
                    "reason": classification["classification_reason"]
                },
                "ambiguity": {
                    "is_ambiguous": ambiguity["is_ambiguous"],
                    "missing_context": ambiguity["missing_context"],
                    "missing_fields": ambiguity["missing_fields"]
                },
                "routing": {
                    "recommended_queue": routing.get("queue", "HR_GENERAL"),
                    "priority_route": routing.get("priority_route", False),
                    "routing_reason": routing.get("routing_reason", "")
                },
                "resolution": {
                    "decision": final_decision,
                    "reason": decision_reason,
                    "policy_reference": citation_id,
                    "citation_valid": citation_valid,
                    "policy_doc": cited_policy,
                    "policy_version": cited_version
                },
                "sla": {
                    "priority": priority,
                    "target_hours": target_hours,
                    "business_hours_summary": f"Target completion within {target_hours} business hours (9am - 5pm, Mon-Fri)."
                }
            }
        }

        self.send_json(response_payload)

    def send_json(self, data, status=200):
        body = json.dumps(data, indent=2, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def serve_file(self, filepath, mime_type):
        if not filepath.exists():
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"File not found")
            return
        content = filepath.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def run_server(port=8000):
    for p in range(port, port + 10):
        try:
            server = HTTPServer(("127.0.0.1", p), HRResolverHandler)
            print(f"\n=======================================================")
            print(f" HR Routine Requests Resolver Frontend Server Online!")
            print(f" Local Web App: http://127.0.0.1:{p}")
            print(f" REST API:      http://127.0.0.1:{p}/api/metrics")
            print(f"=======================================================\n")
            server.serve_forever()
            return
        except OSError as e:
            if "address already in use" in str(e).lower() or e.errno == 98 or e.errno == 10048:
                continue
            raise


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    run_server(port)

