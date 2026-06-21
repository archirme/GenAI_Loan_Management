"""
LangGraph Orchestration Engine with Conditional Edges
Coordinates the multi-agent workflow for loan approval.
Implements: Profile → Risk → Decision → Compliance pipeline with error routing.
"""
from langgraph.graph import StateGraph, END
from orchestrator.state import LoanApplicationState
from agents.profile_agent import run_profile_agent
from agents.risk_agent import run_risk_agent
from agents.decision_agent import run_decision_agent
from agents.compliance_agent import run_compliance_agent
from logging_config import get_logger
from exceptions import LoanManagementException

logger = get_logger(__name__)


def profile_node(state: LoanApplicationState) -> dict:
    """Node 1: Applicant Profile Analysis (Haiku)"""
    applicant_id = state["applicant_data"].get("applicant_id", "UNKNOWN")
    logger.info(f"[{applicant_id}] Profile Agent (Haiku) - Starting profile analysis")

    try:
        result = run_profile_agent(state["applicant_data"])
        logger.info(f"[{applicant_id}] Profile Agent completed successfully")
        return {
            "profile_output": result,
            "current_agent": "profile_agent",
            "workflow_status": "RUNNING"
        }
    except LoanManagementException as e:
        logger.error(f"[{applicant_id}] Profile Agent error: {e.error_code} - {e.message}", exc_info=True)
        return {
            "profile_output": {"error": e.message, "error_code": e.error_code},
            "workflow_status": "ERROR",
            "error_message": f"Profile Agent failed: {e.message}",
            "error_agent": "profile_agent"
        }
    except Exception as e:
        logger.error(f"[{applicant_id}] Profile Agent unexpected error", exc_info=True)
        return {
            "profile_output": {"error": str(e)},
            "workflow_status": "ERROR",
            "error_message": f"Profile Agent failed: {str(e)}",
            "error_agent": "profile_agent"
        }


def risk_node(state: LoanApplicationState) -> dict:
    """Node 2: Financial Risk Analysis (Sonnet)"""
    applicant_id = state["applicant_data"].get("applicant_id", "UNKNOWN")

    # Skip if profile failed
    if state.get("workflow_status") == "ERROR":
        logger.warning(f"[{applicant_id}] Risk Agent skipped due to upstream error")
        return {
            "risk_output": {"skipped": True, "reason": "Profile agent failed"},
            "current_agent": "risk_agent",
            "workflow_status": "ERROR"
        }

    logger.info(f"[{applicant_id}] Risk Agent (Sonnet) - Starting risk analysis")
    try:
        result = run_risk_agent(state["applicant_data"], state["profile_output"])
        logger.info(f"[{applicant_id}] Risk Agent completed successfully")
        return {
            "risk_output": result,
            "current_agent": "risk_agent",
            "workflow_status": "RUNNING"
        }
    except LoanManagementException as e:
        logger.error(f"[{applicant_id}] Risk Agent error: {e.error_code} - {e.message}", exc_info=True)
        return {
            "risk_output": {"error": e.message, "error_code": e.error_code},
            "workflow_status": "ERROR",
            "error_message": f"Risk Agent failed: {e.message}",
            "error_agent": "risk_agent"
        }
    except Exception as e:
        logger.error(f"[{applicant_id}] Risk Agent unexpected error", exc_info=True)
        return {
            "risk_output": {"error": str(e)},
            "workflow_status": "ERROR",
            "error_message": f"Risk Agent failed: {str(e)}",
            "error_agent": "risk_agent"
        }


def decision_node(state: LoanApplicationState) -> dict:
    """Node 3: Loan Decision (Sonnet)"""
    applicant_id = state["applicant_data"].get("applicant_id", "UNKNOWN")

    # Skip if upstream failed
    if state.get("workflow_status") == "ERROR":
        logger.warning(f"[{applicant_id}] Decision Agent skipped due to upstream error")
        return {
            "decision_output": {"skipped": True, "reason": "Upstream agent failed"},
            "current_agent": "decision_agent",
            "workflow_status": "ERROR"
        }

    logger.info(f"[{applicant_id}] Decision Agent (Sonnet) - Making decision")
    try:
        result = run_decision_agent(
            state["applicant_data"],
            state["profile_output"],
            state["risk_output"]
        )
        logger.info(f"[{applicant_id}] Decision Agent completed: {result.get('classification', 'UNKNOWN')}")
        return {
            "decision_output": result,
            "current_agent": "decision_agent",
            "workflow_status": "RUNNING"
        }
    except LoanManagementException as e:
        logger.error(f"[{applicant_id}] Decision Agent error: {e.error_code} - {e.message}", exc_info=True)
        return {
            "decision_output": {"error": e.message, "error_code": e.error_code},
            "workflow_status": "ERROR",
            "error_message": f"Decision Agent failed: {e.message}",
            "error_agent": "decision_agent"
        }
    except Exception as e:
        logger.error(f"[{applicant_id}] Decision Agent unexpected error", exc_info=True)
        return {
            "decision_output": {"error": str(e)},
            "workflow_status": "ERROR",
            "error_message": f"Decision Agent failed: {str(e)}",
            "error_agent": "decision_agent"
        }


def compliance_node(state: LoanApplicationState) -> dict:
    """Node 4: Compliance & Actions (Haiku)"""
    applicant_id = state["applicant_data"].get("applicant_id", "UNKNOWN")

    # Skip if upstream failed, but still try compliance for error logging
    if state.get("workflow_status") == "ERROR":
        logger.warning(f"[{applicant_id}] Compliance Agent skipped due to upstream error")
        return {
            "compliance_output": {"skipped": True, "reason": "Upstream agent failed"},
            "current_agent": "compliance_agent",
            "workflow_status": "ERROR"
        }

    logger.info(f"[{applicant_id}] Compliance Agent (Haiku) - Processing compliance")
    try:
        result = run_compliance_agent(state["applicant_data"], state["decision_output"])
        logger.info(f"[{applicant_id}] Compliance Agent completed: {result.get('action_taken', 'UNKNOWN')}")
        return {
            "compliance_output": result,
            "current_agent": "compliance_agent",
            "workflow_status": "RUNNING"
        }
    except LoanManagementException as e:
        logger.error(f"[{applicant_id}] Compliance Agent error: {e.error_code} - {e.message}", exc_info=True)
        return {
            "compliance_output": {"error": e.message, "error_code": e.error_code},
            "workflow_status": "ERROR",
            "error_message": f"Compliance Agent failed: {e.message}",
            "error_agent": "compliance_agent"
        }
    except Exception as e:
        logger.error(f"[{applicant_id}] Compliance Agent unexpected error", exc_info=True)
        return {
            "compliance_output": {"error": str(e)},
            "workflow_status": "ERROR",
            "error_message": f"Compliance Agent failed: {str(e)}",
            "error_agent": "compliance_agent"
        }


def aggregate_node(state: LoanApplicationState) -> dict:
    """Final Node: Aggregate all results into final output."""
    applicant_id = state["applicant_data"].get("applicant_id", "UNKNOWN")
    logger.info(f"[{applicant_id}] Aggregating workflow results")

    # Handle partial results if workflow had errors
    profile_output = state["profile_output"] or {"error": "Not executed"}
    risk_output = state["risk_output"] or {"error": "Not executed"}
    decision_output = state["decision_output"] or {"error": "Not executed", "classification": "MANUAL_REVIEW"}
    compliance_output = state["compliance_output"] or {"error": "Not executed"}

    final_result = {
        "applicant_id": applicant_id,
        "decision": decision_output.get("classification", "MANUAL_REVIEW"),
        "risk_score": decision_output.get("risk_score", 50),
        "confidence": decision_output.get("confidence_level", 50),
        "explanation": decision_output.get("explanation", ""),
        "key_factors": decision_output.get("key_decision_factors", []),
        "case_id": compliance_output.get("case_id", ""),
        "notification_sent": compliance_output.get("notification_sent", False),
        "summary": compliance_output.get("summary", ""),
        "workflow_error": state.get("error_message"),
        "failed_agent": state.get("error_agent"),
        "agent_details": {
            "profile": profile_output,
            "risk": risk_output,
            "decision": decision_output,
            "compliance": compliance_output
        }
    }

    if state.get("workflow_status") == "ERROR":
        logger.warning(f"[{applicant_id}] Workflow completed with errors. Failed agent: {state.get('error_agent')}")
    else:
        logger.info(f"[{applicant_id}] Workflow completed successfully")

    return {
        "final_result": final_result,
        "workflow_status": "COMPLETED",
        "current_agent": "orchestrator"
    }


def should_continue(state: LoanApplicationState) -> str:
    """
    Edge condition: Check if workflow should continue or go to aggregate on error.

    Args:
        state: Current workflow state

    Returns:
        "continue" to proceed to next agent, "aggregate" to skip to results
    """
    if state.get("workflow_status") == "ERROR":
        applicant_id = state["applicant_data"].get("applicant_id", "UNKNOWN")
        logger.debug(f"[{applicant_id}] Conditional edge routing to aggregate due to error")
        return "aggregate"
    return "continue"


def build_loan_approval_graph():
    """
    Construct the LangGraph StateGraph with conditional edges.

    Graph Structure (with error handling):
        profile_node --[continue]--> risk_node --[continue]--> decision_node --[continue]--> compliance_node --[continue]--> aggregate_node --> END
                  \                            \                        \                            \
                   [ERROR]--[aggregate]-->[aggregate_node]              [aggregate]->[aggregate_node]
    """
    workflow = StateGraph(LoanApplicationState)

    # Add nodes
    workflow.add_node("profile", profile_node)
    workflow.add_node("risk", risk_node)
    workflow.add_node("decision", decision_node)
    workflow.add_node("compliance", compliance_node)
    workflow.add_node("aggregate", aggregate_node)

    # Set entry point
    workflow.set_entry_point("profile")

    # Add conditional edges (error handling)
    workflow.add_conditional_edges(
        "profile",
        should_continue,
        {
            "continue": "risk",
            "aggregate": "aggregate"
        }
    )

    workflow.add_conditional_edges(
        "risk",
        should_continue,
        {
            "continue": "decision",
            "aggregate": "aggregate"
        }
    )

    workflow.add_conditional_edges(
        "decision",
        should_continue,
        {
            "continue": "compliance",
            "aggregate": "aggregate"
        }
    )

    workflow.add_conditional_edges(
        "compliance",
        should_continue,
        {
            "continue": "aggregate",
            "aggregate": "aggregate"
        }
    )

    # Final edge
    workflow.add_edge("aggregate", END)

    # Compile the graph
    logger.debug("LangGraph workflow compiled with conditional edge routing")
    return workflow.compile()


def run_loan_approval(applicant_data: dict) -> dict:
    """
    Main entry point: Run the full loan approval workflow.

    Args:
        applicant_data: Dict with loan application fields

    Returns:
        Dict with final decision and all agent outputs
    """
    applicant_id = applicant_data.get("applicant_id", "UNKNOWN")
    logger.info(f"[{applicant_id}] Loan approval workflow starting")
    logger.debug(f"[{applicant_id}] Application data: {applicant_data}")

    graph = build_loan_approval_graph()

    # Initialize state
    initial_state = {
        "applicant_data": applicant_data,
        "profile_output": None,
        "risk_output": None,
        "decision_output": None,
        "compliance_output": None,
        "current_agent": None,
        "workflow_status": "RUNNING",
        "error_message": None,
        "error_agent": None,
        "final_result": None
    }

    # Execute the graph
    final_state = graph.invoke(initial_state)

    decision = final_state["final_result"]["decision"]
    logger.info(f"[{applicant_id}] Loan approval workflow completed with decision: {decision}")

    return final_state["final_result"]


if __name__ == "__main__":
    test_application = {
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

    result = run_loan_approval(test_application)
    import json
    print(json.dumps(result, indent=2))
