"""
Test Suite for Agents
Tests agent functionality, caching, JSON parsing, and output validation.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from exceptions import LLMCallError, JSONParseError


class TestProfileAgent:
    """Tests for Profile Agent."""

    def test_run_profile_agent_valid(self, valid_applicant, mock_mcp_applicant_db, mock_llm_agent):
        """Test profile agent with valid applicant."""
        from agents.profile_agent import run_profile_agent

        with patch.dict("agents.profile_agent.__dict__", {"llm": mock_llm_agent}):
            mock_llm_agent.invoke.return_value = MagicMock(
                content=json.dumps({
                    "income_stability_score": 85,
                    "employment_risk": "LOW",
                    "credit_history_summary": "Good credit",
                    "completeness_flags": []
                })
            )

            result = run_profile_agent(valid_applicant)

            assert result["income_stability_score"] == 85
            assert result["employment_risk"] == "LOW"
            assert result["agent"] == "profile_agent"

    def test_profile_agent_cache_hit(self, valid_applicant, mock_llm_agent):
        """Test that profile agent uses cache on repeated calls."""
        from agents.profile_agent import run_profile_agent
        from cache import set_cache, get_cache, cache_key

        app_id = valid_applicant["applicant_id"]
        cache_key_str = cache_key(app_id, "profile")

        # Pre-populate cache
        cached_data = {
            "income_stability_score": 90,
            "employment_risk": "LOW",
            "credit_history_summary": "Cached response",
            "completeness_flags": []
        }
        set_cache(cache_key_str, cached_data)

        with patch.dict("agents.profile_agent.__dict__", {"llm": mock_llm_agent}):
            result = run_profile_agent(valid_applicant)

            # Should return cached data without calling LLM
            assert result["credit_history_summary"] == "Cached response"
            mock_llm_agent.invoke.assert_not_called()

    def test_profile_agent_json_parsing_direct(self, valid_applicant, mock_llm_agent):
        """Test profile agent with direct JSON parsing."""
        from agents.profile_agent import run_profile_agent

        response_json = {
            "income_stability_score": 75,
            "employment_risk": "MEDIUM",
            "credit_history_summary": "Fair credit",
            "completeness_flags": []
        }

        with patch.dict("agents.profile_agent.__dict__", {"llm": mock_llm_agent}):
            mock_llm_agent.invoke.return_value = MagicMock(
                content=json.dumps(response_json)
            )

            result = run_profile_agent(valid_applicant)

            assert result["income_stability_score"] == 75
            assert result["employment_risk"] == "MEDIUM"

    def test_profile_agent_json_parsing_markdown(self, valid_applicant, mock_llm_agent):
        """Test profile agent with markdown-formatted JSON."""
        from agents.profile_agent import run_profile_agent

        response_text = """
        Here's the analysis:
        ```json
        {
            "income_stability_score": 70,
            "employment_risk": "HIGH",
            "credit_history_summary": "Poor credit",
            "completeness_flags": ["MISSING_DOCS"]
        }
        ```
        Some extra text after.
        """

        with patch.dict("agents.profile_agent.__dict__", {"llm": mock_llm_agent}):
            mock_llm_agent.invoke.return_value = MagicMock(content=response_text)

            result = run_profile_agent(valid_applicant)

            assert result["income_stability_score"] == 70
            assert result["employment_risk"] == "HIGH"

    def test_profile_agent_json_parsing_fallback(self, valid_applicant, mock_llm_agent):
        """Test profile agent with unparseable JSON (uses defaults)."""
        from agents.profile_agent import run_profile_agent

        response_text = "This is completely unparseable text with no JSON at all."

        with patch.dict("agents.profile_agent.__dict__", {"llm": mock_llm_agent}):
            mock_llm_agent.invoke.return_value = MagicMock(content=response_text)

            result = run_profile_agent(valid_applicant)

            # Should fall back to defaults
            assert result["income_stability_score"] == 50
            assert result["employment_risk"] == "MEDIUM"
            assert "LLM_RESPONSE_PARSE_ERROR" in result["completeness_flags"]


class TestRiskAgent:
    """Tests for Risk Agent."""

    def test_run_risk_agent_valid(self, valid_applicant, mock_llm_agent):
        """Test risk agent with valid inputs."""
        from agents.risk_agent import run_risk_agent

        profile_output = {
            "income_stability_score": 85,
            "employment_risk": "LOW",
            "credit_history_summary": "Good credit",
            "completeness_flags": []
        }

        response_json = {
            "debt_to_income_ratio": 0.32,
            "credit_score_risk_level": "LOW",
            "loan_amount_risk": "LOW",
            "anomaly_flags": [],
            "reasoning": "Good profile"
        }

        with patch.dict("agents.risk_agent.__dict__", {"llm": mock_llm_agent}):
            mock_llm_agent.invoke.return_value = MagicMock(
                content=json.dumps(response_json)
            )

            result = run_risk_agent(valid_applicant, profile_output)

            assert result["debt_to_income_ratio"] == 0.32
            assert result["credit_score_risk_level"] == "LOW"
            assert result["agent"] == "risk_agent"

    def test_risk_agent_parse_error_fix(self, valid_applicant, mock_llm_agent):
        """Test that risk agent handles parse errors gracefully (fixes PARSE_ERROR anomaly)."""
        from agents.risk_agent import run_risk_agent

        profile_output = {
            "income_stability_score": 85,
            "employment_risk": "LOW",
            "credit_history_summary": "Good credit",
            "completeness_flags": []
        }

        # Return unparseable text
        with patch.dict("agents.risk_agent.__dict__", {"llm": mock_llm_agent}):
            mock_llm_agent.invoke.return_value = MagicMock(
                content="Unparseable text"
            )

            result = run_risk_agent(valid_applicant, profile_output)

            # Should use MCP-calculated values as fallback
            assert "debt_to_income_ratio" in result
            assert "LLM_RESPONSE_PARSE_ERROR" in result["anomaly_flags"]
            # Should NOT have just "PARSE_ERROR" - should include MCP data
            assert result["debt_to_income_ratio"] > 0


class TestDecisionAgent:
    """Tests for Decision Agent."""

    def test_run_decision_agent_approved(self, valid_applicant, mock_llm_agent):
        """Test decision agent making APPROVED decision."""
        from agents.decision_agent import run_decision_agent

        profile_output = {"income_stability_score": 85, "employment_risk": "LOW"}
        risk_output = {"debt_to_income_ratio": 0.32, "credit_score_risk_level": "LOW"}

        response_json = {
            "classification": "APPROVED",
            "risk_score": 25,
            "confidence_level": 95,
            "key_decision_factors": ["Good credit", "Low DTI"],
            "explanation": "Meets all criteria"
        }

        with patch.dict("agents.decision_agent.__dict__", {"llm": mock_llm_agent}):
            mock_llm_agent.invoke.return_value = MagicMock(
                content=json.dumps(response_json)
            )

            result = run_decision_agent(valid_applicant, profile_output, risk_output)

            assert result["classification"] == "APPROVED"
            assert result["risk_score"] == 25
            assert result["confidence_level"] == 95

    def test_run_decision_agent_manual_review(self, valid_applicant, mock_llm_agent):
        """Test decision agent making MANUAL_REVIEW decision."""
        from agents.decision_agent import run_decision_agent

        profile_output = {"income_stability_score": 45, "employment_risk": "MEDIUM"}
        risk_output = {"debt_to_income_ratio": 0.62, "credit_score_risk_level": "HIGH"}

        response_json = {
            "classification": "MANUAL_REVIEW",
            "risk_score": 65,
            "confidence_level": 70,
            "key_decision_factors": ["Marginal DTI", "Fair credit"],
            "explanation": "Requires review"
        }

        with patch.dict("agents.decision_agent.__dict__", {"llm": mock_llm_agent}):
            mock_llm_agent.invoke.return_value = MagicMock(
                content=json.dumps(response_json)
            )

            result = run_decision_agent(valid_applicant, profile_output, risk_output)

            assert result["classification"] == "MANUAL_REVIEW"
            assert result["risk_score"] == 65


class TestComplianceAgent:
    """Tests for Compliance Agent."""

    def test_run_compliance_agent_approved(self, valid_applicant, mock_llm_agent):
        """Test compliance agent processing APPROVED decision."""
        from agents.compliance_agent import run_compliance_agent

        decision_output = {
            "classification": "APPROVED",
            "explanation": "Approved applicant"
        }

        response_json = {
            "action_taken": "Loan approved - automated processing",
            "notification_sent": True,
            "notification_channel": "email",
            "notification_message": "Congratulations! Your loan is approved.",
            "case_id": "CASE-APP001-001",
            "timestamp": "2026-06-21T14:00:00",
            "summary": "Application approved"
        }

        with patch.dict("agents.compliance_agent.__dict__", {"llm": mock_llm_agent}):
            mock_llm_agent.invoke.return_value = MagicMock(
                content=json.dumps(response_json)
            )

            with patch("agents.compliance_agent.get_compliance_checklist") as mock_checklist, \
                 patch("agents.compliance_agent.create_case") as mock_case, \
                 patch("agents.compliance_agent.send_notification") as mock_notify:

                mock_checklist.return_value = {"actions": ["Action 1"], "sla_hours": 24}
                mock_case.return_value = {"case_id": "CASE-APP001-001"}
                mock_notify.return_value = {"notification_id": "NOTIF-001"}

                result = run_compliance_agent(valid_applicant, decision_output)

                assert result["action_taken"] == "Loan approved - automated processing"
                assert result["notification_sent"] is True
                assert "case_id" in result

    def test_run_compliance_agent_manual_review(self, valid_applicant, mock_llm_agent):
        """Test compliance agent processing MANUAL_REVIEW decision."""
        from agents.compliance_agent import run_compliance_agent

        decision_output = {
            "classification": "MANUAL_REVIEW",
            "explanation": "Requires review"
        }

        response_json = {
            "action_taken": "Case created for manual review",
            "notification_sent": True,
            "notification_channel": "email",
            "notification_message": "Your application is under review",
            "case_id": "CASE-APP001-002",
            "timestamp": "2026-06-21T14:00:00",
            "summary": "Manual review case"
        }

        with patch.dict("agents.compliance_agent.__dict__", {"llm": mock_llm_agent}):
            mock_llm_agent.invoke.return_value = MagicMock(
                content=json.dumps(response_json)
            )

            with patch("agents.compliance_agent.get_compliance_checklist") as mock_checklist, \
                 patch("agents.compliance_agent.create_case") as mock_case, \
                 patch("agents.compliance_agent.send_notification") as mock_notify:

                mock_checklist.return_value = {"actions": ["Assign to officer"], "sla_hours": 72}
                mock_case.return_value = {"case_id": "CASE-APP001-002", "status": "OPEN"}
                mock_notify.return_value = {"notification_id": "NOTIF-002"}

                result = run_compliance_agent(valid_applicant, decision_output)

                assert result["action_taken"] == "Case created for manual review"
                assert "case_id" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
