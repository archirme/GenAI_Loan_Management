"""
Test Suite for Orchestrator
Tests the full workflow, conditional edges, and error handling.
"""
import pytest
from unittest.mock import patch, MagicMock
from orchestrator.graph import run_loan_approval


class TestOrchestratorHappyPath:
    """Tests for successful end-to-end workflows."""

    def test_orchestrator_full_flow_approved(self, valid_applicant):
        """Test full orchestrator flow resulting in APPROVED."""
        # Mock all agents to return successful results
        with patch("orchestrator.graph.run_profile_agent") as mock_profile, \
             patch("orchestrator.graph.run_risk_agent") as mock_risk, \
             patch("orchestrator.graph.run_decision_agent") as mock_decision, \
             patch("orchestrator.graph.run_compliance_agent") as mock_compliance:

            mock_profile.return_value = {
                "income_stability_score": 85,
                "employment_risk": "LOW",
                "credit_history_summary": "Good",
                "completeness_flags": []
            }

            mock_risk.return_value = {
                "debt_to_income_ratio": 0.32,
                "credit_score_risk_level": "LOW",
                "loan_amount_risk": "LOW",
                "anomaly_flags": [],
                "reasoning": "Good profile"
            }

            mock_decision.return_value = {
                "classification": "APPROVED",
                "risk_score": 25,
                "confidence_level": 95,
                "key_decision_factors": ["Good credit", "Low DTI"],
                "explanation": "Meets all criteria"
            }

            mock_compliance.return_value = {
                "action_taken": "Approved",
                "case_id": "CASE-001",
                "notification_sent": True,
                "summary": "Approved"
            }

            result = run_loan_approval(valid_applicant)

            assert result["decision"] == "APPROVED"
            assert result["risk_score"] == 25
            assert result["confidence"] == 95
            assert "case_id" in result

    def test_orchestrator_full_flow_manual_review(self, valid_applicant):
        """Test full orchestrator flow resulting in MANUAL_REVIEW."""
        with patch("orchestrator.graph.run_profile_agent") as mock_profile, \
             patch("orchestrator.graph.run_risk_agent") as mock_risk, \
             patch("orchestrator.graph.run_decision_agent") as mock_decision, \
             patch("orchestrator.graph.run_compliance_agent") as mock_compliance:

            mock_profile.return_value = {"income_stability_score": 45}
            mock_risk.return_value = {"debt_to_income_ratio": 0.62}
            mock_decision.return_value = {
                "classification": "MANUAL_REVIEW",
                "risk_score": 65,
                "confidence_level": 70,
                "key_decision_factors": ["Marginal"],
                "explanation": "Review needed"
            }
            mock_compliance.return_value = {"case_id": "CASE-002"}

            result = run_loan_approval(valid_applicant)

            assert result["decision"] == "MANUAL_REVIEW"
            assert result["risk_score"] == 65


class TestOrchestratorErrorHandling:
    """Tests for error handling and conditional routing."""

    def test_orchestrator_profile_agent_fails(self, valid_applicant):
        """Test orchestrator when Profile Agent fails - should skip downstream."""
        from exceptions import LLMCallError

        with patch("orchestrator.graph.run_profile_agent") as mock_profile, \
             patch("orchestrator.graph.run_risk_agent") as mock_risk, \
             patch("orchestrator.graph.run_decision_agent") as mock_decision, \
             patch("orchestrator.graph.run_compliance_agent") as mock_compliance:

            # Profile fails
            mock_profile.side_effect = LLMCallError("LLM timeout", agent_name="profile_agent")

            # These should NOT be called due to conditional routing
            mock_risk.return_value = {}
            mock_decision.return_value = {}
            mock_compliance.return_value = {}

            result = run_loan_approval(valid_applicant)

            # Should have error info
            assert result["workflow_error"] is not None
            assert result["failed_agent"] == "profile_agent"
            # Decision should default to MANUAL_REVIEW
            assert result["decision"] == "MANUAL_REVIEW"

    def test_orchestrator_risk_agent_fails(self, valid_applicant):
        """Test orchestrator when Risk Agent fails."""
        from exceptions import LLMCallError

        with patch("orchestrator.graph.run_profile_agent") as mock_profile, \
             patch("orchestrator.graph.run_risk_agent") as mock_risk, \
             patch("orchestrator.graph.run_decision_agent") as mock_decision, \
             patch("orchestrator.graph.run_compliance_agent") as mock_compliance:

            mock_profile.return_value = {"income_stability_score": 85}
            # Risk fails
            mock_risk.side_effect = LLMCallError("Risk analysis failed", agent_name="risk_agent")
            mock_decision.return_value = {}
            mock_compliance.return_value = {}

            result = run_loan_approval(valid_applicant)

            # Error should be tracked
            assert result["failed_agent"] == "risk_agent"
            assert result["decision"] == "MANUAL_REVIEW"

    def test_orchestrator_decision_agent_fails(self, valid_applicant):
        """Test orchestrator when Decision Agent fails."""
        from exceptions import LLMCallError

        with patch("orchestrator.graph.run_profile_agent") as mock_profile, \
             patch("orchestrator.graph.run_risk_agent") as mock_risk, \
             patch("orchestrator.graph.run_decision_agent") as mock_decision, \
             patch("orchestrator.graph.run_compliance_agent") as mock_compliance:

            mock_profile.return_value = {"income_stability_score": 85}
            mock_risk.return_value = {"debt_to_income_ratio": 0.32}
            # Decision fails
            mock_decision.side_effect = LLMCallError("Decision failed", agent_name="decision_agent")
            mock_compliance.return_value = {}

            result = run_loan_approval(valid_applicant)

            # Error should be tracked
            assert result["failed_agent"] == "decision_agent"
            assert result["decision"] == "MANUAL_REVIEW"

    def test_orchestrator_compliance_agent_fails(self, valid_applicant):
        """Test orchestrator when Compliance Agent fails."""
        from exceptions import LLMCallError

        with patch("orchestrator.graph.run_profile_agent") as mock_profile, \
             patch("orchestrator.graph.run_risk_agent") as mock_risk, \
             patch("orchestrator.graph.run_decision_agent") as mock_decision, \
             patch("orchestrator.graph.run_compliance_agent") as mock_compliance:

            mock_profile.return_value = {"income_stability_score": 85}
            mock_risk.return_value = {"debt_to_income_ratio": 0.32}
            mock_decision.return_value = {
                "classification": "APPROVED",
                "risk_score": 25,
                "confidence_level": 95,
                "key_decision_factors": [],
                "explanation": "Approved"
            }
            # Compliance fails
            mock_compliance.side_effect = LLMCallError("Compliance failed", agent_name="compliance_agent")

            result = run_loan_approval(valid_applicant)

            # Decision should still be APPROVED
            assert result["decision"] == "APPROVED"
            assert result["failed_agent"] == "compliance_agent"


class TestOrchestratorPartialResults:
    """Tests for partial result aggregation."""

    def test_orchestrator_returns_partial_results_on_error(self, valid_applicant):
        """Test that orchestrator returns best available results on error."""
        from exceptions import LLMCallError

        with patch("orchestrator.graph.run_profile_agent") as mock_profile, \
             patch("orchestrator.graph.run_risk_agent") as mock_risk, \
             patch("orchestrator.graph.run_decision_agent") as mock_decision, \
             patch("orchestrator.graph.run_compliance_agent") as mock_compliance:

            mock_profile.return_value = {"income_stability_score": 85}
            mock_risk.side_effect = LLMCallError("Risk failed")
            mock_decision.return_value = {}
            mock_compliance.return_value = {}

            result = run_loan_approval(valid_applicant)

            # Should have profile info in agent_details even though risk failed
            assert "agent_details" in result
            assert result["agent_details"]["profile"]["income_stability_score"] == 85


class TestOrchestratorStateManagement:
    """Tests for state management and context."""

    def test_orchestrator_tracks_applicant_id(self, valid_applicant):
        """Test that applicant ID is tracked through workflow."""
        with patch("orchestrator.graph.run_profile_agent") as mock_profile, \
             patch("orchestrator.graph.run_risk_agent") as mock_risk, \
             patch("orchestrator.graph.run_decision_agent") as mock_decision, \
             patch("orchestrator.graph.run_compliance_agent") as mock_compliance:

            mock_profile.return_value = {"income_stability_score": 85}
            mock_risk.return_value = {"debt_to_income_ratio": 0.32}
            mock_decision.return_value = {"classification": "APPROVED", "risk_score": 25}
            mock_compliance.return_value = {"case_id": "CASE-001"}

            result = run_loan_approval(valid_applicant)

            assert result["applicant_id"] == valid_applicant["applicant_id"]

    def test_orchestrator_provides_complete_summary(self, valid_applicant):
        """Test that orchestrator provides complete decision summary."""
        with patch("orchestrator.graph.run_profile_agent") as mock_profile, \
             patch("orchestrator.graph.run_risk_agent") as mock_risk, \
             patch("orchestrator.graph.run_decision_agent") as mock_decision, \
             patch("orchestrator.graph.run_compliance_agent") as mock_compliance:

            mock_profile.return_value = {"income_stability_score": 85}
            mock_risk.return_value = {"debt_to_income_ratio": 0.32}
            mock_decision.return_value = {
                "classification": "APPROVED",
                "risk_score": 25,
                "confidence_level": 95,
                "key_decision_factors": ["Good credit"],
                "explanation": "Meets criteria"
            }
            mock_compliance.return_value = {"case_id": "CASE-001", "summary": "Approved"}

            result = run_loan_approval(valid_applicant)

            # Verify complete result structure
            assert result["decision"] == "APPROVED"
            assert result["risk_score"] == 25
            assert result["confidence"] == 95
            assert len(result["key_factors"]) > 0
            assert result["case_id"] == "CASE-001"
            assert result["agent_details"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
