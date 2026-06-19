"""
MCP Server: NotificationSystem
Handles notifications, case creation, and compliance actions.
Used by: Compliance & Action Orchestrator Agent

CHANGE: send_notification and create_case now persist to MySQL when DATA_SOURCE = "mysql"
"""
from fastmcp import FastMCP
from datetime import datetime
from config import DATA_SOURCE  # <-- NEW IMPORT

mcp = FastMCP("NotificationSystem")

# In-memory logs — UNCHANGED
notification_log = []
case_registry = []


@mcp.tool()
def send_notification(applicant_id: str, notification_type: str,
                      message: str, channel: str = "email") -> dict:
    """Send notification to applicant about loan decision."""
    notification_id = f"NOTIF-{applicant_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    notification = {
        "notification_id": notification_id,
        "applicant_id": applicant_id,
        "type": notification_type,
        "message": message,
        "channel": channel,
        "sent_at": datetime.utcnow().isoformat(),
        "status": "SENT"
    }

    # Always keep in-memory (existing behavior)
    notification_log.append(notification)

    # --- NEW: Persist to MySQL if enabled ---
    if DATA_SOURCE == "mysql":
        from database.db_connection import execute_query
        try:
            execute_query(
                """INSERT INTO notification_log
                   (notification_id, applicant_id, notification_type, message, channel)
                   VALUES (%s, %s, %s, %s, %s)""",
                (notification_id, applicant_id, notification_type, message, channel)
            )
        except Exception as e:
            print(f"[WARNING] Failed to log notification to MySQL: {e}")
    # --- END NEW ---

    return notification


@mcp.tool()
def create_case(applicant_id: str, classification: str,
                summary: str, priority: str = "NORMAL") -> dict:
    """Create a case record for compliance and audit."""
    case_id = f"CASE-{applicant_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    status = "OPEN" if classification == "MANUAL_REVIEW" else "CLOSED"
    case = {
        "case_id": case_id,
        "applicant_id": applicant_id,
        "classification": classification,
        "summary": summary,
        "priority": priority,
        "created_at": datetime.utcnow().isoformat(),
        "status": status
    }

    # Always keep in-memory (existing behavior)
    case_registry.append(case)

    # --- NEW: Persist to MySQL if enabled ---
    if DATA_SOURCE == "mysql":
        from database.db_connection import execute_query
        try:
            execute_query(
                """INSERT INTO case_registry
                   (case_id, applicant_id, classification, summary, priority, status)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (case_id, applicant_id, classification, summary, priority, status)
            )
        except Exception as e:
            print(f"[WARNING] Failed to create case in MySQL: {e}")
    # --- END NEW ---

    return case


@mcp.tool()
def get_compliance_checklist(classification: str) -> dict:
    """Get compliance actions required based on decision classification."""
    # UNCHANGED — pure logic
    checklists = {
        "APPROVED": {
            "actions": [
                "Generate approval letter",
                "Initiate disbursement process",
                "Send congratulations notification",
                "Update credit bureau",
                "Create loan account"
            ],
            "sla_hours": 24
        },
        "REJECTED": {
            "actions": [
                "Generate rejection letter with reasons",
                "Send notification with appeal process",
                "Log rejection reason for compliance",
                "Schedule follow-up after 6 months"
            ],
            "sla_hours": 48
        },
        "MANUAL_REVIEW": {
            "actions": [
                "Assign to senior loan officer",
                "Request additional documents",
                "Send acknowledgment to applicant",
                "Set review deadline",
                "Flag for priority processing"
            ],
            "sla_hours": 72
        }
    }
    return checklists.get(classification, checklists["MANUAL_REVIEW"])


if __name__ == "__main__":
    mcp.run(transport="stdio")