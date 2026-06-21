"""
Test Suite for Error Handling
Tests logging, custom exceptions, and error recovery.
"""
import pytest
import logging
from unittest.mock import patch, MagicMock
from exceptions import (
    LLMCallError, JSONParseError, ValidationError,
    MCPToolError, TimeoutError as LMTimeoutError
)


class TestCustomExceptions:
    """Tests for custom exception types."""

    def test_llm_call_error(self):
        """Test LLMCallError exception."""
        error = LLMCallError("LLM failed", agent_name="profile_agent")

        assert error.error_code == "LLM_CALL_ERROR"
        assert "profile_agent" in str(error.context)
        assert error.message == "LLM failed"

    def test_json_parse_error(self):
        """Test JSONParseError exception."""
        error = JSONParseError("Invalid JSON", response_text='{"bad": json}')

        assert error.error_code == "JSON_PARSE_ERROR"
        assert "Invalid JSON" in error.message

    def test_validation_error(self):
        """Test ValidationError exception."""
        error = ValidationError(
            "Invalid value",
            field="income",
            value=-1000
        )

        assert error.error_code == "VALIDATION_ERROR"
        assert error.context["field"] == "income"
        assert error.context["value"] == -1000

    def test_timeout_error(self):
        """Test TimeoutError exception."""
        error = LMTimeoutError("Request timed out", timeout_seconds=30)

        assert error.error_code == "TIMEOUT_ERROR"
        assert error.context["timeout_seconds"] == 30


class TestInputValidationErrors:
    """Tests for input validation error handling."""

    def test_mcp_validation_error_on_invalid_dti_income(self):
        """Test that invalid income raises ValidationError."""
        from mcp_servers.risk_rules_db import calculate_dti_ratio

        with pytest.raises(ValidationError) as exc_info:
            calculate_dti_ratio(-100000, 20000, 10000)

        assert exc_info.value.error_code == "VALIDATION_ERROR"
        assert "positive" in exc_info.value.message.lower()

    def test_mcp_validation_error_on_invalid_applicant_id(self):
        """Test that invalid applicant ID raises ValidationError."""
        from mcp_servers.applicant_db import get_applicant_profile

        with pytest.raises(ValidationError):
            get_applicant_profile("")

    def test_mcp_validation_error_on_invalid_type(self):
        """Test that invalid type raises ValidationError."""
        from mcp_servers.notification_system import send_notification

        with pytest.raises(ValidationError):
            send_notification(
                applicant_id=12345,  # Should be string
                notification_type="LOAN_APPROVED",
                message="Test",
                channel="email"
            )


class TestErrorLogging:
    """Tests for error logging."""

    def test_error_is_logged_with_context(self, caplog):
        """Test that errors are logged with full context."""
        from mcp_servers.applicant_db import get_applicant_profile

        with caplog.at_level(logging.ERROR):
            try:
                get_applicant_profile(123)
            except ValidationError:
                pass

        # Check that error was logged
        assert any("validation" in record.message.lower() for record in caplog.records)

    def test_validation_error_logged(self, caplog):
        """Test that validation errors are logged."""
        from mcp_servers.risk_rules_db import calculate_dti_ratio

        with caplog.at_level(logging.ERROR):
            try:
                calculate_dti_ratio(-1000, 100, 50)
            except ValidationError:
                pass

        error_logs = [r for r in caplog.records if r.levelname == "ERROR"]
        assert len(error_logs) > 0


class TestLLMErrorHandling:
    """Tests for LLM error handling."""

    def test_llm_timeout_raises_exception(self):
        """Test that LLM timeout is caught and converted to exception."""
        from agents.profile_agent import run_profile_agent

        applicant = {
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

        with patch("agents.profile_agent.llm.invoke") as mock_invoke:
            mock_invoke.side_effect = TimeoutError("LLM call timed out")

            with pytest.raises(LLMCallError):
                run_profile_agent(applicant)

    def test_llm_connection_error(self):
        """Test that connection errors are handled."""
        from agents.profile_agent import run_profile_agent

        applicant = {
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

        with patch("agents.profile_agent.llm.invoke") as mock_invoke:
            mock_invoke.side_effect = ConnectionError("Failed to connect to LLM")

            with pytest.raises(LLMCallError):
                run_profile_agent(applicant)


class TestJSONParsingErrors:
    """Tests for JSON parsing error handling."""

    def test_malformed_json_uses_fallback(self):
        """Test that malformed JSON triggers fallback strategy."""
        from agents.profile_agent import _parse_json_response

        malformed_json = "This is not valid JSON at all"

        result = _parse_json_response(malformed_json, "APP001")

        # Should return defaults
        assert result["income_stability_score"] == 50
        assert result["employment_risk"] == "MEDIUM"

    def test_json_with_extra_text_parsed(self):
        """Test that JSON embedded in text is extracted."""
        from agents.profile_agent import _parse_json_response

        text_with_json = '''
        Let me analyze this:
        {
            "income_stability_score": 75,
            "employment_risk": "MEDIUM",
            "credit_history_summary": "Fair",
            "completeness_flags": []
        }
        Additional text here.
        '''

        result = _parse_json_response(text_with_json, "APP001")

        assert result["income_stability_score"] == 75
        assert result["employment_risk"] == "MEDIUM"


class TestMCPErrorResilience:
    """Tests for MCP tool error resilience."""

    def test_mcp_error_logged_but_doesnt_block(self):
        """Test that MCP errors are logged but don't stop processing."""
        from agents.decision_agent import run_decision_agent

        applicant = {
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

        profile_output = {"income_stability_score": 85}
        risk_output = {"debt_to_income_ratio": 0.32}

        # MCP log_decision fails but we should still get a decision
        with patch("agents.decision_agent.log_decision") as mock_log, \
             patch("agents.decision_agent.llm.invoke") as mock_llm:

            mock_log.side_effect = Exception("Database error")
            mock_llm.return_value = MagicMock(content='{"classification": "APPROVED", "risk_score": 25}')

            # Should NOT raise exception, should just log warning
            result = run_decision_agent(applicant, profile_output, risk_output)

            assert result["classification"] == "APPROVED"


class TestErrorContext:
    """Tests that errors include full context."""

    def test_validation_error_includes_context(self):
        """Test that ValidationError includes field and value."""
        error = ValidationError(
            "Invalid value",
            field="credit_score",
            value=950
        )

        assert error.context["field"] == "credit_score"
        assert error.context["value"] == 950

    def test_llm_error_includes_agent_name(self):
        """Test that LLMCallError includes agent name."""
        error = LLMCallError(
            "LLM call failed",
            agent_name="risk_agent"
        )

        assert error.context["agent"] == "risk_agent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
