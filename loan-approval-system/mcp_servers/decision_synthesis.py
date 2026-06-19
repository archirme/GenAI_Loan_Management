"""
MCP Server: DecisionSynthesis
Provides decision rules, precedents, and logging.
Used by: Loan Decision Agent

CHANGE: log_decision now persists to MySQL when DATA_SOURCE = "mysql"
"""
from fastmcp import FastMCP
import json
from datetime import datetime
from config import DATA_SOURCE  # <-- NEW IMPORT

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
    """Log a loan decision for audit trail."""
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

    # Always keep in-memory log (existing behavior)
    decision_log.append(record)

    # --- NEW: Also persist to MySQL if enabled ---
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
        except Exception as e:
            print(f"[WARNING] Failed to log decision to MySQL: {e}")
    # --- END NEW ---

    return {"status": "logged", "decision_id": decision_id}


if __name__ == "__main__":
    mcp.run(transport="stdio")