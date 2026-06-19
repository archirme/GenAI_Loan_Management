"""
Applicant Profile Agent
Model: Claude Haiku (Split Model Strategy - simple extraction task)
MCP Server: ApplicantDB
Output: Income Stability Score, Employment Risk, Credit History Summary, Completeness Flags
"""
import json
#from anthropic import Anthropic
#from config import ANTHROPIC_API_KEY, AGENT_MODELS, MAX_TOKENS
from langchain_anthropic import ChatAnthropic
from config import LLMGW_API_KEY, LLMGW_BASE_URL, AGENT_MODELS, MAX_TOKENS
from langchain_core.messages import SystemMessage, HumanMessage

# Import MCP tools directly (in-process for simplicity)
from mcp_servers.applicant_db import (
    get_applicant_profile,
    get_credit_history,
    check_application_completeness
)

#client = Anthropic(api_key=ANTHROPIC_API_KEY)

llm = ChatAnthropic(
    model=AGENT_MODELS["<agent_name>"],      # e.g., "profile_agent"
    api_key=LLMGW_API_KEY,
    base_url=LLMGW_BASE_URL,                 # Routes through LLMGW gateway
    max_tokens=MAX_TOKENS["<agent_name>"],
    temperature=0
)

SYSTEM_PROMPT = """You are a Loan Applicant Profile Analyst. Your job is to analyze applicant data and produce a structured assessment.

You MUST return ONLY valid JSON with these exact fields:
{
    "income_stability_score": <0-100 integer>,
    "employment_risk": "<LOW|MEDIUM|HIGH>",
    "credit_history_summary": "<brief 1-2 sentence summary>",
    "completeness_flags": ["<list of any issues or empty list>"]
}

Scoring Rules:
- income_stability_score: Salaried with 5+ years = 80-100, Salaried <5 years = 60-79, Self-Employed profitable = 50-70, Unemployed = 0-30
- employment_risk: Salaried = LOW, Self-Employed with 3+ years = MEDIUM, Self-Employed <3 years or Unemployed = HIGH
- credit_history_summary: Interpret the credit score and history concisely
- completeness_flags: List any missing fields or data quality issues

Be concise. Return ONLY the JSON object, no other text."""


def run_profile_agent(applicant_data: dict) -> dict:
    """
    Execute the Applicant Profile Agent.
    Uses Haiku model for cost efficiency (simple extraction task).
    """
    applicant_id = applicant_data.get("applicant_id", "UNKNOWN")
    
    # Fetch context from MCP Server (ApplicantDB)
    profile_context = get_applicant_profile(applicant_id)
    credit_context = get_credit_history(applicant_id)
    completeness = check_application_completeness(applicant_data)
    
    # Build the user message with all context
    user_message = f"""Analyze this loan applicant:

**Application Data:**
{json.dumps(applicant_data, indent=2)}

**Profile Database Context:**
{json.dumps(profile_context, indent=2)}

**Credit History Context:**
{json.dumps(credit_context, indent=2)}

**Application Completeness Check:**
{json.dumps(completeness, indent=2)}

Return your analysis as JSON."""

    # Call Claude Haiku (Split Model Strategy)
    """
    response = client.messages.create(
        model=AGENT_MODELS["profile_agent"],
        max_tokens=MAX_TOKENS["profile_agent"],
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )
    
    # Parse response
    response_text = response.content[0].text.strip()
    """
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ])
    
    # Parse response
    response_text = response.content.strip()
    
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {
                "income_stability_score": 50,
                "employment_risk": "MEDIUM",
                "credit_history_summary": "Unable to parse - manual review needed",
                "completeness_flags": ["PARSE_ERROR"]
            }
    
    # Add metadata
    result["agent"] = "profile_agent"
    result["model_used"] = AGENT_MODELS["profile_agent"]
    result["applicant_id"] = applicant_id
    
    return result


if __name__ == "__main__":
    # Test the agent
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
    result = run_profile_agent(test_data)
    print(json.dumps(result, indent=2))