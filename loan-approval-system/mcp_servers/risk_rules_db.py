"""
MCP Server: RiskRulesDB
Provides risk assessment rules and thresholds.
Used by: Financial Risk Analysis Agent
"""
from fastmcp import FastMCP

mcp = FastMCP("RiskRulesDB")

# Risk rules configuration
RISK_RULES = {
    "credit_score_thresholds": {
        "excellent": {"min": 750, "risk_level": "LOW"},
        "good": {"min": 700, "max": 749, "risk_level": "LOW"},
        "fair": {"min": 650, "max": 699, "risk_level": "MEDIUM"},
        "poor": {"min": 580, "max": 649, "risk_level": "HIGH"},
        "very_poor": {"max": 579, "risk_level": "CRITICAL"},
    },
    "dti_thresholds": {
        "safe": {"max": 0.35, "risk_level": "LOW"},
        "moderate": {"min": 0.35, "max": 0.45, "risk_level": "MEDIUM"},
        "high": {"min": 0.45, "max": 0.55, "risk_level": "HIGH"},
        "critical": {"min": 0.55, "risk_level": "CRITICAL"},
    },
    "loan_amount_rules": {
        "max_multiplier_salaried": 20,      # Max loan = 20x monthly income
        "max_multiplier_self_employed": 12,  # Max loan = 12x monthly income
        "min_age": 21,
        "max_age": 60,
        "min_tenure_months": 12,
        "max_tenure_months": 360,
    },
    "anomaly_rules": {
        "income_loan_ratio_alert": 25,  # Flag if loan > 25x income
        "age_risk_min": 23,
        "age_risk_max": 55,
        "high_utilization_threshold": 70,
    }
}


@mcp.tool()
def get_risk_rules() -> dict:
    """Get all risk assessment rules and thresholds."""
    return RISK_RULES


@mcp.tool()
def get_credit_score_risk_level(credit_score: int) -> dict:
    """Determine risk level based on credit score."""
    if credit_score >= 750:
        return {"risk_level": "LOW", "category": "Excellent"}
    elif credit_score >= 700:
        return {"risk_level": "LOW", "category": "Good"}
    elif credit_score >= 650:
        return {"risk_level": "MEDIUM", "category": "Fair"}
    elif credit_score >= 580:
        return {"risk_level": "HIGH", "category": "Poor"}
    else:
        return {"risk_level": "CRITICAL", "category": "Very Poor"}


@mcp.tool()
def calculate_dti_ratio(monthly_income: float, existing_liabilities: float, proposed_emi: float) -> dict:
    """Calculate Debt-to-Income ratio."""
    if monthly_income <= 0:
        return {"error": "Invalid income", "dti_ratio": None}
    
    total_debt = existing_liabilities + proposed_emi
    dti_ratio = round(total_debt / monthly_income, 4)
    
    if dti_ratio <= 0.35:
        risk_level = "LOW"
    elif dti_ratio <= 0.45:
        risk_level = "MEDIUM"
    elif dti_ratio <= 0.55:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"
    
    return {
        "dti_ratio": dti_ratio,
        "total_monthly_debt": total_debt,
        "monthly_income": monthly_income,
        "risk_level": risk_level
    }


@mcp.tool()
def detect_anomalies(applicant_data: dict) -> dict:
    """Detect anomalies in the application data."""
    anomalies = []
    
    income = applicant_data.get("income", 0)
    loan_amount = applicant_data.get("loan_amount", 0)
    age = applicant_data.get("age", 0)
    credit_score = applicant_data.get("credit_score", 0)
    
    # Check income-loan ratio
    if income > 0 and loan_amount / income > 25:
        anomalies.append({
            "type": "HIGH_LOAN_TO_INCOME",
            "severity": "HIGH",
            "detail": f"Loan amount is {loan_amount/income:.1f}x monthly income"
        })
    
    # Check age risk
    if age < 23 or age > 55:
        anomalies.append({
            "type": "AGE_RISK",
            "severity": "MEDIUM",
            "detail": f"Applicant age {age} is outside optimal range (23-55)"
        })
    
    # Check credit score vs loan amount mismatch
    if credit_score < 650 and loan_amount > income * 10:
        anomalies.append({
            "type": "CREDIT_LOAN_MISMATCH",
            "severity": "HIGH",
            "detail": "Low credit score with high loan amount request"
        })
    
    return {
        "anomalies_found": len(anomalies) > 0,
        "count": len(anomalies),
        "anomalies": anomalies
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")