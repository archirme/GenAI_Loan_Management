"""
Loan Decision Agent
Model: Claude Sonnet (Split Model Strategy - complex synthesis & explainability)
MCP Server: DecisionSynthesis
Output: Classification, Risk Score, Confidence Level, Key Decision Factors, Explanation
"""
import json
#from anthropic import Anthropic
#from config import ANTHROPIC_API_KEY, AGENT_MODELS, MAX_TOKENS
from langchain_anthropic import ChatAnthropic
from config import LLMGW_API_KEY, LLMGW_BASE_URL, AGENT_MODELS, MAX_TOKENS
from langchain_core.messages import SystemMessage, HumanMessage

from mcp_servers.decision_synthesis import (
    get_decision_rules,
    get_decision_precedents,
    log_decision
)

#client = Anthropic(api_key=ANTHROPIC_API_KEY)

llm = ChatAnthropic(
    model=AGENT_MODELS["decision_agent"],      # e.g., "profile_agent"
    api_key=LLMGW_API_KEY,
    base_url=LLMGW_BASE_URL,                 # Routes through LLMGW gateway
    max_tokens=MAX_TOKENS["decision_agent"],
    temperature=0
)

SYSTEM_PROMPT = """You are the Chief Loan Decision Officer. You synthesize all prior analysis to make a final, explainable loan decision.

You MUST return ONLY valid JSON with these exact fields:
{
    "classification": "<APPROVED|REJECTED|MANUAL_REVIEW>",
    "risk_score": <0-100 integer, higher = riskier>,
    "confidence_level": <0-100 integer, your confidence in this decision>,
    "key_decision_factors": ["<factor 1>", "<factor 2>", "<factor 3>"],
    "explanation": "<detailed human-readable paragraph explaining why this decision was made, suitable for an auditor>"
}

Decision Rules:
- APPROVE: credit_score_risk ≤ MEDIUM AND dti_ratio < 0.4 AND no HIGH/CRITICAL anomalies AND income_stability >= 60
- REJECT: credit_score_risk = CRITICAL OR dti_ratio > 0.6 OR multiple HIGH anomalies OR income_stability < 30
- MANUAL_REVIEW: All other cases that don't clearly fit APPROVE or REJECT

Your explanation must be:
1. Clear and professional
2. Reference specific data points
3. Suitable for regulatory audit
4. Explainable to the applicant

Return ONLY the JSON object."""


def run_decision_agent(applicant_data: dict, profile_output: dict, risk_output: dict) -> dict:
    """
    Execute the Loan Decision Agent.
    Uses Sonnet model for complex synthesis (Split Model Strategy).
    """
    applicant_id = applicant_data.get("applicant_id", "UNKNOWN")
    
    # Fetch context from MCP Server (DecisionSynthesis)
    decision_rules = get_decision_rules()
    precedents = get_decision_precedents()
    
    user_message = f"""Make the final loan decision based on all analysis:

**Original Application:**
{json.dumps(applicant_data, indent=2)}

**Profile Agent Output:**
{json.dumps(profile_output, indent=2)}

**Risk Analysis Output:**
{json.dumps(risk_output, indent=2)}

**Decision Matrix Rules:**
{json.dumps(decision_rules, indent=2)}

**Historical Precedents:**
{json.dumps(precedents, indent=2)}

Synthesize all information, apply the decision rules, and return your final decision as JSON with full explanation."""

    # Call Claude Sonnet (Split Model Strategy - complex reasoning + explainability)
    """
    response = client.messages.create(
        model=AGENT_MODELS["decision_agent"],
        max_tokens=MAX_TOKENS["decision_agent"],
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )
    
    response_text = response.content[0].text.strip()
    """
    response = llm.invoke([
    SystemMessage(content=SYSTEM_PROMPT),     # system is now a message in the list
    HumanMessage(content=user_message)
    ])

    # ChatAnthropic (LangChain) returns an AIMessage with content as a string
    response_text = response.content.strip()     # .content is directly a string
    #                        ^^^^^^^
    #                        directly a string, no indexing needed

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {
                "classification": "MANUAL_REVIEW",
                "risk_score": 50,
                "confidence_level": 30,
                "key_decision_factors": ["Error in processing"],
                "explanation": "System was unable to make automated decision. Forwarding to manual review."
            }
    
    # Log the decision via MCP server
    log_decision(
        applicant_id=applicant_id,
        classification=result.get("classification", "MANUAL_REVIEW"),
        risk_score=result.get("risk_score", 50),
        confidence=result.get("confidence_level", 50),
        factors=result.get("key_decision_factors", []),
        explanation=result.get("explanation", "")
    )
    
    # Add metadata
    result["agent"] = "decision_agent"
    result["model_used"] = AGENT_MODELS["decision_agent"]
    result["applicant_id"] = applicant_id
    
    return result


if __name__ == "__main__":
    test_data = {
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
    test_profile = {
        "income_stability_score": 85,
        "employment_risk": "LOW",
        "credit_history_summary": "Good credit with score 720",
        "completeness_flags": []
    }
    test_risk = {
        "debt_to_income_ratio": 0.27,
        "credit_score_risk_level": "LOW",
        "loan_amount_risk": "LOW",
        "anomaly_flags": [],
        "reasoning": "All metrics within safe range"
    }
    result = run_decision_agent(test_data, test_profile, test_risk)
    print(json.dumps(result, indent=2))