"""
FastAPI Microservice for Loan Approval System.
Receives loan applications, triggers the LangGraph orchestrator, returns decisions.
"""
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_service.models import (
    LoanApplicationRequest, 
    LoanDecisionResponse, 
    HealthResponse
)
from orchestrator.graph import run_loan_approval
from config import AGENT_MODELS, FASTAPI_HOST, FASTAPI_PORT

app = FastAPI(
    title="Agentic AI Loan Approval System",
    description="Multi-Agent AI system for intelligent loan approval using Split Model Strategy",
    version="1.0.0"
)

# CORS middleware for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="loan-approval-system",
        version="1.0.0",
        models_configured=AGENT_MODELS
    )


@app.post("/api/loan/apply", response_model=LoanDecisionResponse)
async def process_loan_application(application: LoanApplicationRequest):
    """
    Process a loan application through the multi-agent AI system.
    
    Flow: Validate → Orchestrate (4 agents) → Return Decision
    """
    try:
        # Add timestamp if not provided
        applicant_data = application.model_dump()
        if not applicant_data.get("timestamp"):
            applicant_data["timestamp"] = datetime.utcnow().isoformat()
        
        # Run the LangGraph orchestrator
        result = run_loan_approval(applicant_data)
        
        # Return structured response
        return LoanDecisionResponse(
            applicant_id=result.get("applicant_id", application.applicant_id),
            decision=result.get("decision", "MANUAL_REVIEW"),
            risk_score=result.get("risk_score", 50),
            confidence=result.get("confidence", 50),
            explanation=result.get("explanation", ""),
            key_factors=result.get("key_factors", []),
            case_id=result.get("case_id", ""),
            notification_sent=result.get("notification_sent", False),
            summary=result.get("summary", ""),
            agent_details=result.get("agent_details")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing loan application: {str(e)}"
        )


@app.get("/api/agents/info")
async def get_agent_info():
    """Get information about agents and their model assignments (Split Model Strategy)."""
    return {
        "strategy": "Split Model Strategy",
        "description": "Haiku for simple tasks, Sonnet for complex reasoning",
        "agents": {
            "Applicant Profile Agent": {
                "model": AGENT_MODELS["profile_agent"],
                "tier": "LOW_COST",
                "role": "Data extraction and simple scoring"
            },
            "Financial Risk Agent": {
                "model": AGENT_MODELS["risk_agent"],
                "tier": "HIGH_COST",
                "role": "Complex risk analysis and anomaly detection"
            },
            "Loan Decision Agent": {
                "model": AGENT_MODELS["decision_agent"],
                "tier": "HIGH_COST",
                "role": "Decision synthesis with explainability"
            },
            "Compliance Agent": {
                "model": AGENT_MODELS["compliance_agent"],
                "tier": "LOW_COST",
                "role": "Notification and case management"
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=FASTAPI_HOST, port=FASTAPI_PORT)