"""
MCP Server: NotificationSystem
Handles notifications, case creation, and compliance actions.
Used by: Compliance & Action Orchestrator Agent
"""
from fastmcp import FastMCP
from datetime import datetime

mcp = FastMCP("NotificationSystem")

# Notification log
notification_log = []
case_registry = []


@mcp.tool()
def send_notification(applicant_id: str, notification_type: str, 
                      message: str, channel: str = "email") -> dict:
    """Send notification to applicant about loan decision."""
    notification = {
        "notification_id": f"NOTIF-{applicant_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "applicant_id": applicant_id,
        "type": notification_type,
        "message": message,
        "channel": channel,
        "sent_at": datetime.utcnow().isoformat(),
        "status": "SENT"
    }
    notification_log.append(notification)
    return notification


@mcp.tool()
def create_case(applicant_id: str, classification: str, 
                summary: str, priority: str = "NORMAL") -> dict:
    """Create a case record for compliance and audit."""
    case = {
        "case_id": f"CASE-{applicant_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "applicant_id": applicant_id,
        "classification": classification,
        "summary": summary,
        "priority": priority,
        "created_at": datetime.utcnow().isoformat(),
        "status": "OPEN" if classification == "MANUAL_REVIEW" else "CLOSED"
    }
    case_registry.append(case)
    return case


@mcp.tool()
def get_compliance_checklist(classification: str) -> dict:
    """Get compliance actions required based on decision classification."""
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