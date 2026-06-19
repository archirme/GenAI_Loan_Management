"""
LangGraph Orchestration Engine
Coordinates the multi-agent workflow for loan approval.
Implements: Profile → Risk → Decision → Compliance pipeline.
"""
from langgraph.graph import StateGraph, END
from orchestrator.state import LoanApplicationState
from agents.profile_agent import run_profile_agent
from agents.risk_agent import run_risk_agent
from agents.decision_agent import run_decision_agent
from agents.compliance_agent import run_compliance_agent

def profile_node(state: LoanApplicationState) -> dict:
    """Node 1: Applicant Profile Analysis (Haiku)"""
    print("\n[Agent 1] Applicant Profile Agent (Haiku) - Analyzing profile...")
    try:
        result = run_profile_agent(state["applicant_data"])
        return {
            "profile_output": result,
            "current_agent": "profile_agent",
            "workflow_status": "RUNNING"
        }
    except Exception as e:
        return {
            "profile_output": {"error": str(e)},
            "workflow_status": "ERROR",
            "error_message": f"Profile Agent failed: {str(e)}"
        }

def risk_node(state: LoanApplicationState) -> dict:
    """Node 2: Financial Risk Analysis (Sonnet)"""
    print("[Agent 2] Financial Risk Agent (Sonnet) - Calculating risk...")
    try:
        result = run_risk_agent(state["applicant_data"], state["profile_output"])
        return {
            "risk_output": result,
            "current_agent": "risk_agent",
            "workflow_status": "RUNNING"
        }
    except Exception as e:
        return {
            "risk_output": {"error": str(e)},
            "workflow_status": "ERROR",
            "error_message": f"Risk Agent failed: {str(e)}"
        }


def decision_node(state: LoanApplicationState) -> dict:
    """Node 3: Loan Decision (Sonnet)"""
    print(" [Agent 3] Loan Decision Agent (Sonnet) - Making decision...")
    try:
        result = run_decision_agent(
            state["applicant_data"],
            state["profile_output"],
            state["risk_output"]
        )
        return {
            "decision_output": result,
            "current_agent": "decision_agent",
            "workflow_status": "RUNNING"
        }
    except Exception as e:
        return {
            "decision_output": {"error": str(e)},
            "workflow_status": "ERROR",
            "error_message": f"Decision Agent failed: {str(e)}"
        }


def compliance_node(state: LoanApplicationState) -> dict:
    """Node 4: Compliance & Actions (Haiku)"""
    print("[Agent 4] Compliance Agent (Haiku) - Processing actions...")
    try:
        result = run_compliance_agent(state["applicant_data"], state["decision_output"])
        return {
            "compliance_output": result,
            "current_agent": "compliance_agent",
            "workflow_status": "RUNNING"
        }
    except Exception as e:
        return {
            "compliance_output": {"error": str(e)},
            "workflow_status": "ERROR",
            "error_message": f"Compliance Agent failed: {str(e)}"
        }

def aggregate_node(state: LoanApplicationState) -> dict:
    """Final Node: Aggregate all results into final output."""
    print("✅ [Orchestrator] Aggregating final results...")
    
    final_result = {
        "applicant_id": state["applicant_data"].get("applicant_id"),
        "decision": state["decision_output"].get("classification", "MANUAL_REVIEW"),
        "risk_score": state["decision_output"].get("risk_score", 50),
        "confidence": state["decision_output"].get("confidence_level", 50),
        "explanation": state["decision_output"].get("explanation", ""),
        "key_factors": state["decision_output"].get("key_decision_factors", []),
        "case_id": state["compliance_output"].get("case_id", ""),
        "notification_sent": state["compliance_output"].get("notification_sent", False),
        "summary": state["compliance_output"].get("summary", ""),
        "agent_details": {
            "profile": state["profile_output"],
            "risk": state["risk_output"],
            "decision": state["decision_output"],
            "compliance": state["compliance_output"]
        }
    }
    
    return {
        "final_result": final_result,
        "workflow_status": "COMPLETED",
        "current_agent": "orchestrator"
    }

def should_continue(state: LoanApplicationState) -> str:
    """Edge condition: Check if workflow should continue or stop on error."""
    if state.get("workflow_status") == "ERROR":
        return "aggregate"  # Go to aggregate even on error for partial results
    return "continue"



# Build the LangGraph workflow
def build_loan_approval_graph():
    """
    Construct the LangGraph StateGraph for loan approval workflow.
    
    Graph Structure:
        profile_node → risk_node → decision_node → compliance_node → aggregate_node → END
    """
    workflow = StateGraph(LoanApplicationState)
    
    # Add nodes
    workflow.add_node("profile", profile_node)
    workflow.add_node("risk", risk_node)
    workflow.add_node("decision", decision_node)
    workflow.add_node("compliance", compliance_node)
    workflow.add_node("aggregate", aggregate_node)
    
    # Add edges (sequential pipeline)
    workflow.set_entry_point("profile")
    workflow.add_edge("profile", "risk")
    workflow.add_edge("risk", "decision")
    workflow.add_edge("decision", "compliance")
    workflow.add_edge("compliance", "aggregate")
    workflow.add_edge("aggregate", END)
    
    # Compile the graph
    graph = workflow.compile()
    return graph



def run_loan_approval(applicant_data: dict) -> dict:
    """
    Main entry point: Run the full loan approval workflow.
    
    Args:
        applicant_data: Dict with loan application fields
        
    Returns:
        Dict with final decision and all agent outputs
    """
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
        "final_result": None
    }
    
    print("\n" + "="*60)
    print("LOAN APPROVAL WORKFLOW STARTED")
    print("="*60)
    print(f"Applicant ID: {applicant_data.get('applicant_id')}")
    print(f"Loan Amount: ₹{applicant_data.get('loan_amount', 0):,}")
    print("="*60)
    
    # Execute the graph
    final_state = graph.invoke(initial_state)
    
    print("\n" + "="*60)
    print("LOAN APPROVAL WORKFLOW COMPLETED")
    print(f"Decision: {final_state['final_result']['decision']}")
    print("="*60 + "\n")
    
    return final_state["final_result"]


if __name__ == "__main__":
    # Test the orchestrator
    test_application = {
        "applicant_id": "APP001",
        "age": 32,
        "income": 85000,
        "employment_type": "Salaried",
        "credit_score": 720,
        "loan_amount": 500000,
        "loan_tenure": 60,
        "existing_liabilities": 15000,
        "location": "Mumbai",
        "timestamp": "2025-01-15T10:30:00Z"
    }
    
    import json
    result = run_loan_approval(test_application)
    print(json.dumps(result, indent=2))