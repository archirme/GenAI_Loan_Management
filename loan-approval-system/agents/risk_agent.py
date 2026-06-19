"""
Financial Risk Analysis Agent
Model: Claude Sonnet (Split Model Strategy - complex reasoning task)
MCP Server: RiskRulesDB
Output: Debt-to-Income Ratio, Credit Score Risk Level, Loan Amount Risk, Anomaly Detection, Reasoning
"""
import json
#from anthropic import Anthropic
#from config import ANTHROPIC_API_KEY, AGENT_MODELS, MAX_TOKENS
from langchain_anthropic import ChatAnthropic
from config import LLMGW_API_KEY, LLMGW_BASE_URL, AGENT_MODELS, MAX_TOKENS
from langchain_core.messages import SystemMessage, HumanMessage

# Import MCP tools directly
from mcp_servers.risk_rules_db import (
    get_risk_rules,
    get_credit_score_risk_level,
    calculate_dti_ratio,
    detect_anomalies
)

#client = Anthropic(api_key=ANTHROPIC_API_KEY)


# ChatAnthropic client pointing to LLMGW (TekStac LLM Gateway)
llm = ChatAnthropic(
    model=AGENT_MODELS["risk_agent"],
    api_key=LLMGW_API_KEY,
    base_url=LLMGW_BASE_URL,
    max_tokens=MAX_TOKENS["risk_agent"],
    temperature=0
)

SYSTEM_PROMPT = """You are a Senior Financial Risk Analyst for a bank. You perform deep, quantitative risk analysis on loan applications.

You MUST return ONLY valid JSON with these exact fields:
{
    "debt_to_income_ratio": <float, calculated as (existing_liabilities + proposed_EMI) / monthly_income>,
    "credit_score_risk_level": "<LOW|MEDIUM|HIGH|CRITICAL>",
    "loan_amount_risk": "<LOW|MEDIUM|HIGH>",
    "anomaly_flags": ["<list of detected anomalies or empty list>"],
    "reasoning": "<detailed step-by-step explanation of your risk assessment, including calculations>"
}

Risk Assessment Rules:
- Credit Score: >=750=LOW, 700-749=LOW, 650-699=MEDIUM, 580-649=HIGH, <580=CRITICAL
- DTI: <=0.35=LOW, 0.35-0.45=MEDIUM, 0.45-0.55=HIGH, >0.55=CRITICAL
- Loan Amount Risk: Based on income multiplier (Salaried: safe if <20x monthly, Self-employed: safe if <12x monthly)
- Anomalies: Flag unusual patterns (income-loan mismatch, age risks, credit utilization >70%)

Think step-by-step. Show your calculations in the reasoning field. Return ONLY the JSON object."""


def run_risk_agent(applicant_data: dict, profile_output: dict) -> dict:
    """
    Execute the Financial Risk Analysis Agent.
    Uses Sonnet model for complex reasoning (Split Model Strategy).
    """
    # Fetch context from MCP Server (RiskRulesDB)
    risk_rules = get_risk_rules()
    credit_risk = get_credit_score_risk_level(applicant_data.get("credit_score", 0))
    
    # Calculate proposed EMI (simple formula: loan_amount / tenure_months)
    loan_amount = applicant_data.get("loan_amount", 0)
    tenure_months = applicant_data.get("loan_tenure", 12)
    # Simple EMI approximation (without interest for demo)
    proposed_emi = loan_amount / tenure_months if tenure_months > 0 else 0
    
    dti_data = calculate_dti_ratio(
        monthly_income=applicant_data.get("income", 0),
        existing_liabilities=applicant_data.get("existing_liabilities", 0),
        proposed_emi=proposed_emi
    )
    
    anomaly_data = detect_anomalies(applicant_data)
    
    # Build user message
    user_message = f"""Perform comprehensive risk analysis on this loan application:

**Application Data:**
{json.dumps(applicant_data, indent=2)}

**Profile Agent Analysis:**
{json.dumps(profile_output, indent=2)}

**Risk Rules & Thresholds:**
{json.dumps(risk_rules, indent=2)}

**Pre-calculated Credit Risk Level:**
{json.dumps(credit_risk, indent=2)}

**Pre-calculated DTI Data:**
{json.dumps(dti_data, indent=2)}

**Anomaly Detection Results:**
{json.dumps(anomaly_data, indent=2)}

Analyze all factors, show your reasoning with calculations, and return your risk assessment as JSON."""

    # Call Claude Sonnet (Split Model Strategy - complex reasoning)
    """
    response = client.messages.create(
        model=AGENT_MODELS["risk_agent"],
        max_tokens=MAX_TOKENS["risk_agent"],
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )
    
    response_text = response.content[0].text.strip()
    """
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ])
    
    response_text = response.content.strip()

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {
                "debt_to_income_ratio": dti_data.get("dti_ratio", 0),
                "credit_score_risk_level": credit_risk.get("risk_level", "MEDIUM"),
                "loan_amount_risk": "MEDIUM",
                "anomaly_flags": ["PARSE_ERROR"],
                "reasoning": "Error parsing LLM response - using pre-calculated values"
            }
    
    # Add metadata
    result["agent"] = "risk_agent"
    result["model_used"] = AGENT_MODELS["risk_agent"]
    result["mcp_data"] = {
        "dti_calculated": dti_data,
        "anomalies_detected": anomaly_data
    }
    
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
        "credit_history_summary": "Good credit history with score 720",
        "completeness_flags": []
    }
    result = run_risk_agent(test_data, test_profile)
    print(json.dumps(result, indent=2))