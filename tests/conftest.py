"""
Pytest Configuration and Shared Fixtures
Provides mock data and test utilities for all test modules.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Test applicants with known outcomes
TEST_APPLICANTS = {
    "APP001": {
        "applicant_id": "APP001",
        "age": 32,
        "income": 85000,
        "employment_type": "Salaried",
        "credit_score": 720,
        "loan_amount": 500000,
        "loan_tenure": 60,
        "existing_liabilities": 15000,
        "location": "Mumbai",
        "expected_decision": "APPROVED",
        "expected_risk_level": "LOW"
    },
    "APP002": {
        "applicant_id": "APP002",
        "age": 28,
        "income": 45000,
        "employment_type": "Self-Employed",
        "credit_score": 580,
        "loan_amount": 300000,
        "loan_tenure": 60,
        "existing_liabilities": 20000,
        "location": "Ahmedabad",
        "expected_decision": "MANUAL_REVIEW",
        "expected_risk_level": "MEDIUM"
    },
    "APP003": {
        "applicant_id": "APP003",
        "age": 45,
        "income": 150000,
        "employment_type": "Salaried",
        "credit_score": 810,
        "loan_amount": 1000000,
        "loan_tenure": 84,
        "existing_liabilities": 25000,
        "location": "Bangalore",
        "expected_decision": "APPROVED",
        "expected_risk_level": "LOW"
    },
    "INVALID_AGE": {
        "applicant_id": "INVALID_AGE",
        "age": 5,  # Invalid: < 18
        "income": 85000,
        "employment_type": "Salaried",
        "credit_score": 720,
        "loan_amount": 500000,
        "loan_tenure": 60,
        "existing_liabilities": 15000,
        "location": "Mumbai",
        "should_fail": True
    },
    "INVALID_INCOME": {
        "applicant_id": "INVALID_INCOME",
        "age": 32,
        "income": -1000,  # Invalid: negative
        "employment_type": "Salaried",
        "credit_score": 720,
        "loan_amount": 500000,
        "loan_tenure": 60,
        "existing_liabilities": 15000,
        "location": "Mumbai",
        "should_fail": True
    }
}

# Expected MCP responses
MOCK_MCP_RESPONSES = {
    "profile": {
        "APP001": {
            "income_stability_score": 85,
            "employment_risk": "LOW",
            "credit_history_summary": "Good credit history with score 720",
            "completeness_flags": []
        },
        "APP002": {
            "income_stability_score": 45,
            "employment_risk": "MEDIUM",
            "credit_history_summary": "Fair credit with some late payments",
            "completeness_flags": ["HIGH_DTI"]
        }
    },
    "risk": {
        "APP001": {
            "debt_to_income_ratio": 0.32,
            "credit_score_risk_level": "LOW",
            "loan_amount_risk": "LOW",
            "anomaly_flags": [],
            "reasoning": "Good profile with acceptable DTI ratio"
        },
        "APP002": {
            "debt_to_income_ratio": 0.62,
            "credit_score_risk_level": "HIGH",
            "loan_amount_risk": "HIGH",
            "anomaly_flags": ["HIGH_LOAN_TO_INCOME"],
            "reasoning": "High DTI ratio with low credit score"
        }
    },
    "decision": {
        "APP001": {
            "classification": "APPROVED",
            "risk_score": 25,
            "confidence_level": 95,
            "key_decision_factors": ["Good credit score", "Low DTI", "Stable employment"],
            "explanation": "Applicant meets all approval criteria"
        },
        "APP002": {
            "classification": "MANUAL_REVIEW",
            "risk_score": 65,
            "confidence_level": 70,
            "key_decision_factors": ["Marginal DTI", "Fair credit"],
            "explanation": "Requires manual review due to mixed risk factors"
        }
    }
}


@pytest.fixture
def valid_applicant():
    """Provide a valid test applicant (APP001)."""
    return TEST_APPLICANTS["APP001"].copy()


@pytest.fixture
def invalid_applicant_age():
    """Provide an applicant with invalid age."""
    return TEST_APPLICANTS["INVALID_AGE"].copy()


@pytest.fixture
def invalid_applicant_income():
    """Provide an applicant with invalid income."""
    return TEST_APPLICANTS["INVALID_INCOME"].copy()


@pytest.fixture
def all_test_applicants():
    """Provide all valid test applicants."""
    return {k: v.copy() for k, v in TEST_APPLICANTS.items() if "INVALID" not in k}


@pytest.fixture
def mock_llm_response_valid():
    """Provide a valid LLM response (JSON string)."""
    response_data = {
        "income_stability_score": 85,
        "employment_risk": "LOW",
        "credit_history_summary": "Good credit history",
        "completeness_flags": []
    }
    return json.dumps(response_data)


@pytest.fixture
def mock_llm_response_malformed():
    """Provide a malformed LLM response (needs parsing)."""
    return """
    Here's the analysis:
    ```json
    {
        "income_stability_score": 85,
        "employment_risk": "LOW",
        "credit_history_summary": "Good credit history",
        "completeness_flags": []
    }
    ```
    Some extra text here.
    """


@pytest.fixture
def mock_llm_response_invalid():
    """Provide an invalid LLM response (cannot parse)."""
    return "This is just plain text with no JSON at all."


@pytest.fixture
def mock_cache():
    """Provide a mock cache object."""
    cache = {
        "APP001:profile": {"income_stability_score": 85, "employment_risk": "LOW"},
        "APP001:risk": {"debt_to_income_ratio": 0.32, "credit_score_risk_level": "LOW"},
    }
    return cache


@pytest.fixture
def mock_mcp_applicant_db():
    """Mock the ApplicantDB MCP server."""
    with patch("agents.profile_agent.get_applicant_profile") as mock_profile, \
         patch("agents.profile_agent.get_credit_history") as mock_credit, \
         patch("agents.profile_agent.check_application_completeness") as mock_complete:

        mock_profile.return_value = {
            "status": "found",
            "data": {
                "name": "Test User",
                "years_employed": 5,
                "existing_accounts": 3
            }
        }

        mock_credit.return_value = {
            "status": "found",
            "data": {
                "total_credit_lines": 3,
                "defaults": 0,
                "late_payments": 1,
                "oldest_account_years": 8,
                "credit_utilization": 35
            }
        }

        mock_complete.return_value = {
            "is_complete": True,
            "missing_fields": [],
            "completeness_score": 100
        }

        yield {"profile": mock_profile, "credit": mock_credit, "complete": mock_complete}


@pytest.fixture
def mock_mcp_risk_rules():
    """Mock the RiskRulesDB MCP server."""
    with patch("agents.risk_agent.get_risk_rules") as mock_rules, \
         patch("agents.risk_agent.get_credit_score_risk_level") as mock_credit_risk, \
         patch("agents.risk_agent.calculate_dti_ratio") as mock_dti, \
         patch("agents.risk_agent.detect_anomalies") as mock_anomalies:

        mock_rules.return_value = {
            "credit_score_thresholds": {
                "excellent": {"min": 750, "risk_level": "LOW"},
                "good": {"min": 700, "max": 749, "risk_level": "LOW"}
            },
            "dti_thresholds": {
                "safe": {"max": 0.35, "risk_level": "LOW"}
            }
        }

        mock_credit_risk.return_value = {"risk_level": "LOW", "category": "Good"}
        mock_dti.return_value = {"dti_ratio": 0.32, "risk_level": "LOW"}
        mock_anomalies.return_value = {"anomalies_found": False, "count": 0, "anomalies": []}

        yield {
            "rules": mock_rules,
            "credit_risk": mock_credit_risk,
            "dti": mock_dti,
            "anomalies": mock_anomalies
        }


@pytest.fixture
def mock_mcp_decision():
    """Mock the DecisionSynthesis MCP server."""
    with patch("agents.decision_agent.get_decision_rules") as mock_rules, \
         patch("agents.decision_agent.get_decision_precedents") as mock_precedents, \
         patch("agents.decision_agent.log_decision") as mock_log:

        mock_rules.return_value = {
            "auto_approve": {"conditions": {"credit_risk_level": ["LOW"]}},
            "auto_reject": {"conditions": {"credit_risk_level": ["CRITICAL"]}}
        }

        mock_precedents.return_value = [
            {"case_id": "HIST001", "decision": "APPROVED"}
        ]

        mock_log.return_value = {"status": "logged", "decision_id": "DEC-001"}

        yield {"rules": mock_rules, "precedents": mock_precedents, "log": mock_log}


@pytest.fixture
def mock_mcp_notification():
    """Mock the NotificationSystem MCP server."""
    with patch("agents.compliance_agent.send_notification") as mock_notify, \
         patch("agents.compliance_agent.create_case") as mock_case, \
         patch("agents.compliance_agent.get_compliance_checklist") as mock_checklist:

        mock_notify.return_value = {
            "notification_id": "NOTIF-001",
            "status": "SENT",
            "channel": "email"
        }

        mock_case.return_value = {
            "case_id": "CASE-APP001-20260621",
            "status": "OPEN"
        }

        mock_checklist.return_value = {
            "actions": ["Generate approval letter"],
            "sla_hours": 24
        }

        yield {
            "notify": mock_notify,
            "case": mock_case,
            "checklist": mock_checklist
        }


@pytest.fixture
def mock_llm_agent():
    """Mock ChatAnthropic LLM client."""
    with patch("agents.profile_agent.llm") as mock:
        mock.invoke.return_value = MagicMock(content='{"income_stability_score": 85}')
        yield mock


def assert_valid_application(app_data):
    """Assert that application data is valid."""
    required = ["applicant_id", "age", "income", "employment_type",
                "credit_score", "loan_amount", "loan_tenure",
                "existing_liabilities", "location"]
    for field in required:
        assert field in app_data, f"Missing required field: {field}"


def assert_valid_profile_output(output):
    """Assert profile agent output is valid."""
    required = ["income_stability_score", "employment_risk", "credit_history_summary"]
    for field in required:
        assert field in output, f"Missing required field in profile output: {field}"

    assert 0 <= output["income_stability_score"] <= 100
    assert output["employment_risk"] in ["LOW", "MEDIUM", "HIGH"]


def assert_valid_risk_output(output):
    """Assert risk agent output is valid."""
    required = ["debt_to_income_ratio", "credit_score_risk_level", "loan_amount_risk"]
    for field in required:
        assert field in output, f"Missing required field in risk output: {field}"

    assert 0 <= output["debt_to_income_ratio"] <= 10
    assert output["credit_score_risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def assert_valid_decision_output(output):
    """Assert decision agent output is valid."""
    required = ["classification", "risk_score", "confidence_level", "explanation"]
    for field in required:
        assert field in output, f"Missing required field in decision output: {field}"

    assert output["classification"] in ["APPROVED", "REJECTED", "MANUAL_REVIEW"]
    assert 0 <= output["risk_score"] <= 100
    assert 0 <= output["confidence_level"] <= 100


def assert_valid_compliance_output(output):
    """Assert compliance agent output is valid."""
    required = ["action_taken", "case_id", "notification_sent"]
    for field in required:
        assert field in output, f"Missing required field in compliance output: {field}"

    assert isinstance(output["notification_sent"], bool)


@pytest.fixture(scope="session")
def test_data():
    """Provide all test data for the session."""
    return {
        "applicants": TEST_APPLICANTS,
        "mcp_responses": MOCK_MCP_RESPONSES,
        "assert_funcs": {
            "valid_app": assert_valid_application,
            "valid_profile": assert_valid_profile_output,
            "valid_risk": assert_valid_risk_output,
            "valid_decision": assert_valid_decision_output,
            "valid_compliance": assert_valid_compliance_output
        }
    }
