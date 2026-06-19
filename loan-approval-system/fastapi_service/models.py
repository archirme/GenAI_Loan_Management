"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class LoanApplicationRequest(BaseModel):
    """Input model for loan application submission."""
    applicant_id: str = Field(..., description="Unique applicant identifier")
    age: int = Field(..., ge=18, le=70, description="Applicant age")
    income: float = Field(..., gt=0, description="Monthly income")
    employment_type: str = Field(..., description="Salaried/Self-Employed/Unemployed")
    credit_score: int = Field(..., ge=300, le=900, description="Credit score")
    loan_amount: float = Field(..., gt=0, description="Requested loan amount")
    loan_tenure: int = Field(..., ge=6, le=360, description="Loan tenure in months")
    existing_liabilities: float = Field(default=0, ge=0, description="Monthly existing liabilities")
    location: str = Field(..., description="Applicant location/city")
    timestamp: Optional[str] = Field(default=None, description="Application timestamp")

    class Config:
        json_schema_extra = {
            "example": {
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
        }


class AgentOutput(BaseModel):
    """Individual agent output."""
    agent: str
    model_used: str
    output: dict


class LoanDecisionResponse(BaseModel):
    """Response model for loan decision."""
    applicant_id: str
    decision: str = Field(..., description="APPROVED / REJECTED / MANUAL_REVIEW")
    risk_score: int = Field(..., description="0-100, higher = riskier")
    confidence: int = Field(..., description="0-100, decision confidence")
    explanation: str = Field(..., description="Human-readable explanation")
    key_factors: List[str] = Field(..., description="Key decision factors")
    case_id: str
    notification_sent: bool
    summary: str
    agent_details: Optional[dict] = Field(default=None, description="Detailed outputs from each agent")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    models_configured: dict