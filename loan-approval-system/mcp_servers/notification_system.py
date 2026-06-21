"""
MCP Server: NotificationSystem with Input Validation and Logging
Handles notifications, case creation, and compliance actions.
Used by: Compliance & Action Orchestrator Agent

Features:
- Input validation for all parameters
- Logging of notifications and case events
- MySQL persistence when DATA_SOURCE = "mysql"
"""
from fastmcp import FastMCP
from datetime import datetime
from config import DATA_SOURCE
from logging_config import get_logger
from exceptions import ValidationError

logger = get_logger(__name__)
mcp = FastMCP("NotificationSystem")

# In-memory logs — UNCHANGED
notification_log = []
case_registry = []


@mcp.tool()
def send_notification(applicant_id: str, notification_type: str,
                      message: str, channel: str = "email") -> dict:
    """Send notification to applicant about loan decision with validation."""
    # Validate inputs
    if not isinstance(applicant_id, str) or not applicant_id.strip():
        logger.error("Notification validation failed: applicant_id must be non-empty string")
        raise ValidationError("Applicant ID must be a non-empty string", field="applicant_id")

    if not isinstance(notification_type, str) or not notification_type.strip():
        logger.error("Notification validation failed: notification_type must be non-empty string")
        raise ValidationError("Notification type must be a non-empty string", field="notification_type")

    if not isinstance(message, str) or not message.strip():
        logger.error("Notification validation failed: message must be non-empty string")
        raise ValidationError("Message must be a non-empty string", field="message")

    valid_channels = ["email", "sms", "both"]
    if channel not in valid_channels:
        logger.error(f"Notification validation failed: invalid channel {channel}")
        raise ValidationError(f"Channel must be one of {valid_channels}", field="channel", value=channel)

    logger.info(f"Sending {notification_type} notification to {applicant_id} via {channel}")

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

    # Always keep in-memory
    notification_log.append(notification)
    logger.debug(f"Notification queued: {notification_id}. Total notifications: {len(notification_log)}")

    # Persist to MySQL if enabled
    if DATA_SOURCE == "mysql":
        from database.db_connection import execute_query
        try:
            execute_query(
                """INSERT INTO notification_log
                   (notification_id, applicant_id, notification_type, message, channel)
                   VALUES (%s, %s, %s, %s, %s)""",
                (notification_id, applicant_id, notification_type, message, channel)
            )
            logger.info(f"Notification persisted to MySQL: {notification_id}")
        except Exception as e:
            logger.warning(f"Failed to log notification to MySQL: {e}")

    return notification


@mcp.tool()
def create_case(applicant_id: str, classification: str,
                summary: str, priority: str = "NORMAL") -> dict:
    """Create a case record for compliance and audit with validation."""
    # Validate inputs
    if not isinstance(applicant_id, str) or not applicant_id.strip():
        logger.error("Case creation validation failed: applicant_id must be non-empty string")
        raise ValidationError("Applicant ID must be a non-empty string", field="applicant_id")

    valid_classifications = ["APPROVED", "REJECTED", "MANUAL_REVIEW"]
    if classification not in valid_classifications:
        logger.error(f"Case creation validation failed: invalid classification {classification}")
        raise ValidationError(f"Classification must be one of {valid_classifications}",
                            field="classification", value=classification)

    if not isinstance(summary, str):
        logger.error("Case creation validation failed: summary must be string")
        raise ValidationError("Summary must be a string", field="summary")

    valid_priorities = ["LOW", "NORMAL", "HIGH", "CRITICAL"]
    if priority not in valid_priorities:
        logger.error(f"Case creation validation failed: invalid priority {priority}")
        raise ValidationError(f"Priority must be one of {valid_priorities}",
                            field="priority", value=priority)

    logger.info(f"Creating case for {applicant_id} with priority {priority} for {classification}")

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

    # Always keep in-memory
    case_registry.append(case)
    logger.debug(f"Case created in memory: {case_id}. Total cases: {len(case_registry)}")

    # Persist to MySQL if enabled
    if DATA_SOURCE == "mysql":
        from database.db_connection import execute_query
        try:
            execute_query(
                """INSERT INTO case_registry
                   (case_id, applicant_id, classification, summary, priority, status)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (case_id, applicant_id, classification, summary, priority, status)
            )
            logger.info(f"Case persisted to MySQL: {case_id}")
        except Exception as e:
            logger.warning(f"Failed to create case in MySQL: {e}")

    return case


@mcp.tool()
def get_compliance_checklist(classification: str) -> dict:
    """Get compliance actions required based on decision classification with validation."""
    # Validate input
    valid_classifications = ["APPROVED", "REJECTED", "MANUAL_REVIEW"]
    if not isinstance(classification, str) or classification not in valid_classifications:
        logger.error(f"Compliance checklist validation failed: invalid classification {classification}")
        raise ValidationError(f"Classification must be one of {valid_classifications}",
                            field="classification", value=classification)

    logger.debug(f"Fetching compliance checklist for {classification}")

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
    result = checklists.get(classification, checklists["MANUAL_REVIEW"])
    logger.debug(f"Compliance checklist returned: {len(result['actions'])} actions, {result['sla_hours']} hour SLA")
    return result


if __name__ == "__main__":
    mcp.run(transport="stdio")