"""
Pydantic Output Schemas for Agent Validation
Ensures all agent outputs conform to expected structure.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level enum."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EmploymentRisk(str, Enum):
    """Employment risk enum."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DecisionClassification(str, Enum):
    """Loan decision classification."""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class ActionTaken(str, Enum):
    """Compliance action taken."""
    CASE_CREATED = "CASE_CREATED"
    FLAGGED_FOR_REVIEW = "FLAGGED_FOR_REVIEW"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"


class ProfileAgentOutput(BaseModel):
    """Output schema for Profile Agent (Haiku)."""
    income_stability_score: int = Field(..., ge=0, le=100, description="Score 0-100")
    employment_risk: EmploymentRisk
    credit_history_summary: str = Field(..., min_length=1, max_length=500)
    completeness_flags: List[str] = Field(default_factory=list)
    agent: str = "profile_agent"
    model_used: str = ""
    applicant_id: str = ""

    @field_validator('income_stability_score')
    def validate_score(cls, v):
        if not isinstance(v, int):
            raise ValueError("Score must be integer")
        return v


class RiskAgentOutput(BaseModel):
    """Output schema for Risk Agent (Sonnet)."""
    debt_to_income_ratio: float = Field(..., ge=0, le=10, description="DTI ratio 0-10")
    credit_score_risk_level: RiskLevel
    loan_amount_risk_level: RiskLevel
    anomalies_detected: List[str] = Field(default_factory=list)
    detailed_reasoning: str = Field(..., min_length=1)
    agent: str = "risk_agent"
    model_used: str = ""
    applicant_id: str = ""

    @field_validator('debt_to_income_ratio')
    def validate_dti(cls, v):
        if v < 0:
            raise ValueError("DTI cannot be negative")
        return v


class DecisionAgentOutput(BaseModel):
    """Output schema for Decision Agent (Sonnet)."""
    classification: DecisionClassification
    risk_score: int = Field(..., ge=0, le=100)
    confidence_level: int = Field(..., ge=0, le=100)
    key_decision_factors: List[str] = Field(default_factory=list)
    explanation: str = Field(..., min_length=1)
    agent: str = "decision_agent"
    model_used: str = ""
    applicant_id: str = ""


class ComplianceAgentOutput(BaseModel):
    """Output schema for Compliance Agent (Haiku)."""
    action_taken: ActionTaken
    case_id: str = ""
    notification_sent: bool = False
    notification_status: str = ""
    compliance_checklist: List[str] = Field(default_factory=list)
    summary: str = ""
    agent: str = "compliance_agent"
    model_used: str = ""
    applicant_id: str = ""


class AggregatedResult(BaseModel):
    """Final aggregated result from orchestrator."""
    applicant_id: str
    decision: DecisionClassification
    risk_score: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)
    explanation: str = ""
    key_factors: List[str] = Field(default_factory=list)
    case_id: str = ""
    notification_sent: bool = False
    summary: str = ""
    agent_details: Dict[str, Any] = Field(default_factory=dict)
    workflow_status: str = "COMPLETED"
