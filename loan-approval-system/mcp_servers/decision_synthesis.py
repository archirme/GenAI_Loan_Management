"""
MCP Server: DecisionSynthesis with Input Validation and Logging
Provides decision rules, precedents, and logging.
Used by: Loan Decision Agent

Features:
- Input validation for all parameters
- Logging of decision events
- MySQL persistence when DATA_SOURCE = "mysql"
"""
from fastmcp import FastMCP
import json
from datetime import datetime
from config import DATA_SOURCE
from logging_config import get_logger
from exceptions import ValidationError

logger = get_logger(__name__)
mcp = FastMCP("DecisionSynthesis")

# Decision rules — UNCHANGED
DECISION_MATRIX = {
    "auto_approve": {
        "conditions": {
            "credit_risk_level": ["LOW"],
            "dti_risk_level": ["LOW"],
            "anomalies": False,
            "completeness": 100,
        },
        "classification": "APPROVED"
    },
    "auto_reject": {
        "conditions": {
            "credit_risk_level": ["CRITICAL"],
            "dti_risk_level": ["CRITICAL"],
            "anomalies_severity": ["HIGH"],
        },
        "classification": "REJECTED"
    },
    "manual_review": {
        "conditions": {
            "description": "All cases not matching auto_approve or auto_reject"
        },
        "classification": "MANUAL_REVIEW"
    }
}

# Historical decision precedents — UNCHANGED
DECISION_PRECEDENTS = [
    {
        "case_id": "HIST001",
        "credit_score": 720,
        "dti_ratio": 0.32,
        "loan_amount": 500000,
        "decision": "APPROVED",
        "outcome": "Loan fully repaid"
    },
    {
        "case_id": "HIST002",
        "credit_score": 550,
        "dti_ratio": 0.62,
        "loan_amount": 1000000,
        "decision": "REJECTED",
        "outcome": "N/A"
    },
    {
        "case_id": "HIST003",
        "credit_score": 660,
        "dti_ratio": 0.45,
        "loan_amount": 300000,
        "decision": "MANUAL_REVIEW",
        "outcome": "Approved after review, loan active"
    },
]

# In-memory decision log — UNCHANGED
decision_log = []


@mcp.tool()
def get_decision_rules() -> dict:
    """Get the decision matrix rules for loan classification."""
    return DECISION_MATRIX


@mcp.tool()
def get_decision_precedents(credit_score_range: str = "all") -> list:
    """Get historical decision precedents for reference."""
    return DECISION_PRECEDENTS


@mcp.tool()
def log_decision(applicant_id: str, classification: str, risk_score: float,
                 confidence: float, factors: list, explanation: str) -> dict:
    """Log a loan decision for audit trail with validation."""
    # Validate inputs
    if not isinstance(applicant_id, str) or not applicant_id.strip():
        logger.error("Decision logging validation failed: applicant_id must be non-empty string")
        raise ValidationError("Applicant ID must be a non-empty string", field="applicant_id")

    if classification not in ["APPROVED", "REJECTED", "MANUAL_REVIEW"]:
        logger.error(f"Decision logging validation failed: invalid classification {classification}")
        raise ValidationError("Classification must be APPROVED, REJECTED, or MANUAL_REVIEW",
                            field="classification", value=classification)

    if not isinstance(risk_score, (int, float)):
        logger.error("Decision logging validation failed: risk_score must be numeric")
        raise ValidationError("Risk score must be numeric", field="risk_score")

    if not (0 <= risk_score <= 100):
        logger.error(f"Decision logging validation failed: risk_score {risk_score} out of range")
        raise ValidationError("Risk score must be between 0 and 100", field="risk_score", value=risk_score)

    if not isinstance(confidence, (int, float)):
        logger.error("Decision logging validation failed: confidence must be numeric")
        raise ValidationError("Confidence must be numeric", field="confidence")

    if not (0 <= confidence <= 100):
        logger.error(f"Decision logging validation failed: confidence {confidence} out of range")
        raise ValidationError("Confidence must be between 0 and 100", field="confidence", value=confidence)

    if not isinstance(factors, list):
        logger.error("Decision logging validation failed: factors must be list")
        raise ValidationError("Factors must be a list", field="factors")

    if not isinstance(explanation, str) or not explanation.strip():
        logger.error("Decision logging validation failed: explanation must be non-empty string")
        raise ValidationError("Explanation must be a non-empty string", field="explanation")

    logger.info(f"Logging decision for {applicant_id}: {classification} (score={risk_score}, conf={confidence})")

    decision_id = f"DEC-{applicant_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    record = {
        "applicant_id": applicant_id,
        "classification": classification,
        "risk_score": risk_score,
        "confidence": confidence,
        "key_factors": factors,
        "explanation": explanation,
        "timestamp": datetime.utcnow().isoformat(),
        "decision_id": decision_id
    }

    # Always keep in-memory log
    decision_log.append(record)
    logger.debug(f"Decision logged to memory. Total decisions: {len(decision_log)}")

    # Persist to MySQL if enabled
    if DATA_SOURCE == "mysql":
        from database.db_connection import execute_query
        try:
            execute_query(
                """INSERT INTO decision_log
                   (decision_id, applicant_id, classification, risk_score, confidence, key_factors, explanation)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (decision_id, applicant_id, classification, risk_score,
                 confidence, json.dumps(factors), explanation)
            )
            logger.info(f"Decision logged to MySQL database. Decision ID: {decision_id}")
        except Exception as e:
            logger.warning(f"Failed to log decision to MySQL: {e}")

    return {"status": "logged", "decision_id": decision_id}


if __name__ == "__main__":
    mcp.run(transport="stdio")