"""
Test Suite for MCP Servers
Tests all MCP tool inputs, outputs, and error handling.
"""
import pytest
from exceptions import ValidationError


class TestRiskRulesDB:
    """Tests for RiskRulesDB MCP server."""

    def test_calculate_dti_ratio_valid(self):
        """Test DTI calculation with valid inputs."""
        from mcp_servers.risk_rules_db import calculate_dti_ratio

        result = calculate_dti_ratio(
            monthly_income=100000,
            existing_liabilities=20000,
            proposed_emi=10000
        )

        assert result["dti_ratio"] == 0.3
        assert result["risk_level"] == "LOW"
        assert result["total_monthly_debt"] == 30000

    def test_calculate_dti_ratio_invalid_income(self):
        """Test DTI calculation with invalid income (negative)."""
        from mcp_servers.risk_rules_db import calculate_dti_ratio

        with pytest.raises(ValidationError) as exc_info:
            calculate_dti_ratio(
                monthly_income=-100000,
                existing_liabilities=20000,
                proposed_emi=10000
            )
        assert "positive" in str(exc_info.value.message).lower()

    def test_calculate_dti_ratio_invalid_liabilities(self):
        """Test DTI calculation with invalid liabilities (negative)."""
        from mcp_servers.risk_rules_db import calculate_dti_ratio

        with pytest.raises(ValidationError) as exc_info:
            calculate_dti_ratio(
                monthly_income=100000,
                existing_liabilities=-20000,
                proposed_emi=10000
            )
        assert "negative" in str(exc_info.value.message).lower()

    def test_calculate_dti_ratio_type_error(self):
        """Test DTI calculation with invalid type."""
        from mcp_servers.risk_rules_db import calculate_dti_ratio

        with pytest.raises(ValidationError):
            calculate_dti_ratio(
                monthly_income="100000",  # String instead of float
                existing_liabilities=20000,
                proposed_emi=10000
            )

    def test_detect_anomalies_valid(self):
        """Test anomaly detection with valid inputs."""
        from mcp_servers.risk_rules_db import detect_anomalies

        result = detect_anomalies({
            "income": 100000,
            "loan_amount": 500000,
            "age": 35,
            "credit_score": 750
        })

        assert isinstance(result["anomalies"], list)
        assert result["count"] == 0  # No anomalies for good profile

    def test_detect_anomalies_high_loan_to_income(self):
        """Test anomaly detection for high loan-to-income ratio."""
        from mcp_servers.risk_rules_db import detect_anomalies

        result = detect_anomalies({
            "income": 50000,
            "loan_amount": 2000000,  # 40x income
            "age": 35,
            "credit_score": 750
        })

        assert result["anomalies_found"] is True
        assert result["count"] > 0
        anomaly_types = [a["type"] for a in result["anomalies"]]
        assert "HIGH_LOAN_TO_INCOME" in anomaly_types

    def test_detect_anomalies_invalid_type(self):
        """Test anomaly detection with invalid type."""
        from mcp_servers.risk_rules_db import detect_anomalies

        with pytest.raises(ValidationError):
            detect_anomalies("not a dict")


class TestApplicantDB:
    """Tests for ApplicantDB MCP server."""

    def test_get_applicant_profile_valid(self):
        """Test getting applicant profile with valid ID."""
        from mcp_servers.applicant_db import get_applicant_profile

        result = get_applicant_profile("APP001")

        assert result["status"] in ["found", "not_found"]
        if result["status"] == "found":
            assert "data" in result
            assert isinstance(result["data"], dict)

    def test_get_applicant_profile_empty_id(self):
        """Test getting applicant profile with empty ID."""
        from mcp_servers.applicant_db import get_applicant_profile

        with pytest.raises(ValidationError):
            get_applicant_profile("")

    def test_get_applicant_profile_invalid_type(self):
        """Test getting applicant profile with invalid type."""
        from mcp_servers.applicant_db import get_applicant_profile

        with pytest.raises(ValidationError):
            get_applicant_profile(12345)

    def test_get_credit_history_valid(self):
        """Test getting credit history with valid ID."""
        from mcp_servers.applicant_db import get_credit_history

        result = get_credit_history("APP001")

        assert result["status"] in ["found", "not_found"]
        if result["status"] == "found":
            assert "data" in result

    def test_check_application_completeness_complete(self):
        """Test completeness check with complete application."""
        from mcp_servers.applicant_db import check_application_completeness

        app_data = {
            "applicant_id": "APP001",
            "age": 32,
            "income": 85000,
            "employment_type": "Salaried",
            "credit_score": 720,
            "loan_amount": 500000,
            "loan_tenure": 60,
            "existing_liabilities": 15000,
            "location": "Mumbai"
        }

        result = check_application_completeness(app_data)

        assert result["is_complete"] is True
        assert len(result["missing_fields"]) == 0
        assert result["completeness_score"] == 100

    def test_check_application_completeness_incomplete(self):
        """Test completeness check with incomplete application."""
        from mcp_servers.applicant_db import check_application_completeness

        app_data = {
            "applicant_id": "APP001",
            "age": 32,
            # Missing other fields
        }

        result = check_application_completeness(app_data)

        assert result["is_complete"] is False
        assert len(result["missing_fields"]) > 0
        assert result["completeness_score"] < 100

    def test_check_application_completeness_invalid_type(self):
        """Test completeness check with invalid type."""
        from mcp_servers.applicant_db import check_application_completeness

        with pytest.raises(ValidationError):
            check_application_completeness("not a dict")


class TestDecisionSynthesis:
    """Tests for DecisionSynthesis MCP server."""

    def test_log_decision_valid(self):
        """Test logging decision with valid inputs."""
        from mcp_servers.decision_synthesis import log_decision

        result = log_decision(
            applicant_id="APP001",
            classification="APPROVED",
            risk_score=25,
            confidence=95,
            factors=["Good credit", "Low DTI"],
            explanation="Applicant meets criteria"
        )

        assert result["status"] == "logged"
        assert "decision_id" in result

    def test_log_decision_invalid_classification(self):
        """Test logging decision with invalid classification."""
        from mcp_servers.decision_synthesis import log_decision

        with pytest.raises(ValidationError) as exc_info:
            log_decision(
                applicant_id="APP001",
                classification="INVALID",
                risk_score=25,
                confidence=95,
                factors=[],
                explanation="Test"
            )
        assert "classification" in str(exc_info.value.message).lower()

    def test_log_decision_invalid_risk_score_range(self):
        """Test logging decision with out-of-range risk score."""
        from mcp_servers.decision_synthesis import log_decision

        with pytest.raises(ValidationError):
            log_decision(
                applicant_id="APP001",
                classification="APPROVED",
                risk_score=150,  # Out of range
                confidence=95,
                factors=[],
                explanation="Test"
            )

    def test_log_decision_invalid_confidence_range(self):
        """Test logging decision with out-of-range confidence."""
        from mcp_servers.decision_synthesis import log_decision

        with pytest.raises(ValidationError):
            log_decision(
                applicant_id="APP001",
                classification="APPROVED",
                risk_score=25,
                confidence=150,  # Out of range
                factors=[],
                explanation="Test"
            )

    def test_log_decision_invalid_factors_type(self):
        """Test logging decision with invalid factors type."""
        from mcp_servers.decision_synthesis import log_decision

        with pytest.raises(ValidationError):
            log_decision(
                applicant_id="APP001",
                classification="APPROVED",
                risk_score=25,
                confidence=95,
                factors="not a list",  # Should be list
                explanation="Test"
            )

    def test_log_decision_empty_explanation(self):
        """Test logging decision with empty explanation."""
        from mcp_servers.decision_synthesis import log_decision

        with pytest.raises(ValidationError):
            log_decision(
                applicant_id="APP001",
                classification="APPROVED",
                risk_score=25,
                confidence=95,
                factors=[],
                explanation=""  # Empty
            )


class TestNotificationSystem:
    """Tests for NotificationSystem MCP server."""

    def test_send_notification_valid(self):
        """Test sending notification with valid inputs."""
        from mcp_servers.notification_system import send_notification

        result = send_notification(
            applicant_id="APP001",
            notification_type="LOAN_APPROVED",
            message="Your loan has been approved",
            channel="email"
        )

        assert result["status"] == "SENT"
        assert "notification_id" in result

    def test_send_notification_invalid_channel(self):
        """Test sending notification with invalid channel."""
        from mcp_servers.notification_system import send_notification

        with pytest.raises(ValidationError):
            send_notification(
                applicant_id="APP001",
                notification_type="LOAN_APPROVED",
                message="Test",
                channel="invalid_channel"
            )

    def test_send_notification_empty_applicant_id(self):
        """Test sending notification with empty applicant ID."""
        from mcp_servers.notification_system import send_notification

        with pytest.raises(ValidationError):
            send_notification(
                applicant_id="",
                notification_type="LOAN_APPROVED",
                message="Test",
                channel="email"
            )

    def test_create_case_valid(self):
        """Test creating case with valid inputs."""
        from mcp_servers.notification_system import create_case

        result = create_case(
            applicant_id="APP001",
            classification="APPROVED",
            summary="Applicant approved",
            priority="NORMAL"
        )

        assert "case_id" in result
        assert result["status"] in ["OPEN", "CLOSED"]

    def test_create_case_invalid_classification(self):
        """Test creating case with invalid classification."""
        from mcp_servers.notification_system import create_case

        with pytest.raises(ValidationError):
            create_case(
                applicant_id="APP001",
                classification="INVALID",
                summary="Test",
                priority="NORMAL"
            )

    def test_create_case_invalid_priority(self):
        """Test creating case with invalid priority."""
        from mcp_servers.notification_system import create_case

        with pytest.raises(ValidationError):
            create_case(
                applicant_id="APP001",
                classification="APPROVED",
                summary="Test",
                priority="INVALID"
            )

    def test_get_compliance_checklist_valid(self):
        """Test getting compliance checklist with valid classification."""
        from mcp_servers.notification_system import get_compliance_checklist

        result = get_compliance_checklist("APPROVED")

        assert "actions" in result
        assert "sla_hours" in result
        assert isinstance(result["actions"], list)
        assert len(result["actions"]) > 0

    def test_get_compliance_checklist_invalid(self):
        """Test getting compliance checklist with invalid classification."""
        from mcp_servers.notification_system import get_compliance_checklist

        with pytest.raises(ValidationError):
            get_compliance_checklist("INVALID")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
