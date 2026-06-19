"""
LangGraph State Definitions
Defines the shared state that flows through the agent workflow graph.
"""
from typing import TypedDict, Optional, Any


class LoanApplicationState(TypedDict):
    """State object that flows through the LangGraph workflow."""
    
    # Input
    applicant_data: dict                    # Original loan application data
    
    # Agent Outputs (populated as workflow progresses)
    profile_output: Optional[dict]          # From Applicant Profile Agent
    risk_output: Optional[dict]             # From Financial Risk Agent
    decision_output: Optional[dict]         # From Loan Decision Agent
    compliance_output: Optional[dict]       # From Compliance Agent
    
    # Workflow Metadata
    current_agent: Optional[str]            # Which agent is currently executing
    workflow_status: Optional[str]          # RUNNING, COMPLETED, ERROR
    error_message: Optional[str]           # Error details if any
    
    # Final Result
    final_result: Optional[dict]           # Aggregated final output