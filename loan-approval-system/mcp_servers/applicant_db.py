"""
MCP Server: ApplicantDB with Input Validation and Logging
Provides applicant profile data and credit history information.
Used by: Applicant Profile Agent
"""
from fastmcp import FastMCP
from config import DATA_SOURCE
from logging_config import get_logger
from exceptions import ValidationError

logger = get_logger(__name__)
mcp = FastMCP("ApplicantDB")

# Simulated applicant database
APPLICANT_DATABASE = {
    "APP001": {
        "name": "Rahul Sharma",
        "age": 32,
        "income": 85000,
        "employment_type": "Salaried",
        "employer": "TCS",
        "years_employed": 5,
        "location": "Mumbai",
        "existing_accounts": 3,
        "previous_loans_cleared": 2,
    },
    "APP002": {
        "name": "Priya Patel",
        "age": 28,
        "income": 45000,
        "employment_type": "Self-Employed",
        "business_type": "Retail",
        "years_in_business": 3,
        "location": "Ahmedabad",
        "existing_accounts": 2,
        "previous_loans_cleared": 1,
    },
    "APP003": {
        "name": "Vikram Singh",
        "age": 45,
        "income": 150000,
        "employment_type": "Salaried",
        "employer": "Infosys",
        "years_employed": 15,
        "location": "Bangalore",
        "existing_accounts": 5,
        "previous_loans_cleared": 4,
    },
}

CREDIT_HISTORY = {
    "APP001": {
        "credit_score": 720,
        "total_credit_lines": 3,
        "defaults": 0,
        "late_payments": 1,
        "oldest_account_years": 8,
        "credit_utilization": 35,
    },
    "APP002": {
        "credit_score": 580,
        "total_credit_lines": 2,
        "defaults": 1,
        "late_payments": 4,
        "oldest_account_years": 3,
        "credit_utilization": 78,
    },
    "APP003": {
        "credit_score": 810,
        "total_credit_lines": 5,
        "defaults": 0,
        "late_payments": 0,
        "oldest_account_years": 18,
        "credit_utilization": 15,
    },
}

# ============================================================
# NEW: MySQL HELPER FUNCTIONS
# ============================================================

def _get_applicant_from_db(applicant_id: str) -> dict:
    """Fetch applicant from MySQL database."""
    from database.db_connection import execute_query
    row = execute_query(
        "SELECT * FROM applicants WHERE applicant_id = %s",
        (applicant_id,),
        fetch_one=True
    )
    if row:
        data = dict(row)
        data.pop("applicant_id", None)
        if data.get("income"):
            data["income"] = float(data["income"])
        data = {k: v for k, v in data.items() if v is not None}
        return data
    return None


def _get_credit_from_db(applicant_id: str) -> dict:
    """Fetch credit history from MySQL database."""
    from database.db_connection import execute_query
    row = execute_query(
        "SELECT * FROM credit_history WHERE applicant_id = %s",
        (applicant_id,),
        fetch_one=True
    )
    if row:
        data = dict(row)
        data.pop("applicant_id", None)
        if data.get("credit_utilization"):
            data["credit_utilization"] = float(data["credit_utilization"])
        if "defaults_count" in data:
            data["defaults"] = data.pop("defaults_count")
        return data
    return None


# ============================================================
# MCP TOOLS — MODIFIED (if/else on DATA_SOURCE)
# ============================================================

@mcp.tool()
def get_applicant_profile(applicant_id: str) -> dict:
    """Fetch applicant profile details from the database with validation."""
    # Validate input
    if not isinstance(applicant_id, str):
        logger.error(f"Profile fetch validation failed: applicant_id must be string, got {type(applicant_id)}")
        raise ValidationError("Applicant ID must be a string", field="applicant_id", value=applicant_id)

    if not applicant_id or len(applicant_id.strip()) == 0:
        logger.error("Profile fetch validation failed: applicant_id cannot be empty")
        raise ValidationError("Applicant ID cannot be empty", field="applicant_id")

    applicant_id = applicant_id.strip()
    logger.debug(f"Fetching applicant profile: {applicant_id}")

    if DATA_SOURCE == "mysql":
        data = _get_applicant_from_db(applicant_id)
        if data:
            logger.debug(f"Profile found in MySQL for {applicant_id}")
            return {"status": "found", "data": data, "source": "mysql"}
        logger.warning(f"Applicant {applicant_id} not found in MySQL database")
        return {"status": "not_found", "data": None,
                "message": f"Applicant {applicant_id} not found in MySQL database",
                "source": "mysql"}

    else:  # mock
        if applicant_id in APPLICANT_DATABASE:
            logger.debug(f"Profile found in mock database for {applicant_id}")
            return {"status": "found", "data": APPLICANT_DATABASE[applicant_id], "source": "mock"}
        logger.warning(f"Applicant {applicant_id} not found in mock database")
        return {"status": "not_found", "data": None,
                "message": f"Applicant {applicant_id} not found in database",
                "source": "mock"}


@mcp.tool()
def get_credit_history(applicant_id: str) -> dict:
    """Fetch credit history and score for an applicant with validation."""
    # Validate input
    if not isinstance(applicant_id, str):
        logger.error(f"Credit history validation failed: applicant_id must be string")
        raise ValidationError("Applicant ID must be a string", field="applicant_id")

    if not applicant_id or len(applicant_id.strip()) == 0:
        logger.error("Credit history validation failed: applicant_id cannot be empty")
        raise ValidationError("Applicant ID cannot be empty", field="applicant_id")

    applicant_id = applicant_id.strip()
    logger.debug(f"Fetching credit history: {applicant_id}")

    if DATA_SOURCE == "mysql":
        data = _get_credit_from_db(applicant_id)
        if data:
            logger.debug(f"Credit history found in MySQL for {applicant_id}")
            return {"status": "found", "data": data, "source": "mysql"}
        logger.warning(f"Credit history for {applicant_id} not found in MySQL")
        return {"status": "not_found", "data": None,
                "message": f"Credit history for {applicant_id} not found in MySQL",
                "source": "mysql"}

    else:  # mock
        if applicant_id in CREDIT_HISTORY:
            logger.debug(f"Credit history found in mock database for {applicant_id}")
            return {"status": "found", "data": CREDIT_HISTORY[applicant_id], "source": "mock"}
        logger.warning(f"Credit history for {applicant_id} not found in mock database")
        return {"status": "not_found", "data": None,
                "message": f"Credit history for {applicant_id} not found",
                "source": "mock"}


@mcp.tool()
def check_application_completeness(applicant_data: dict) -> dict:
    """Validate if all required fields are present in the application."""
    # Validate input
    if not isinstance(applicant_data, dict):
        logger.error(f"Completeness validation failed: applicant_data must be dict, got {type(applicant_data)}")
        raise ValidationError("Applicant data must be a dictionary", field="applicant_data")

    logger.debug(f"Checking application completeness for {applicant_data.get('applicant_id', 'UNKNOWN')}")

    required_fields = ["applicant_id", "age", "income", "employment_type",
                       "credit_score", "loan_amount", "loan_tenure",
                       "existing_liabilities", "location"]

    missing_fields = [f for f in required_fields if f not in applicant_data or applicant_data[f] is None]
    completeness_score = ((len(required_fields) - len(missing_fields)) / len(required_fields)) * 100

    logger.debug(f"Completeness check: {len(required_fields) - len(missing_fields)}/{len(required_fields)} fields present ({completeness_score:.0f}%)")

    return {
        "is_complete": len(missing_fields) == 0,
        "missing_fields": missing_fields,
        "completeness_score": completeness_score
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")