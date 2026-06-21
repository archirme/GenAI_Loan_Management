"""
Financial Risk Analysis Agent
Model: Claude Sonnet (Split Model Strategy - complex reasoning task)
MCP Server: RiskRulesDB
Output: Debt-to-Income Ratio, Credit Score Risk Level, Loan Amount Risk, Anomaly Detection, Reasoning
"""
import json
import re
from langchain_anthropic import ChatAnthropic
from config import LLMGW_API_KEY, LLMGW_BASE_URL, AGENT_MODELS, MAX_TOKENS
from langchain_core.messages import SystemMessage, HumanMessage
from logging_config import get_logger
from exceptions import JSONParseError, LLMCallError
from cache import get_cache, set_cache, cache_key

logger = get_logger(__name__)

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
    Execute the Financial Risk Analysis Agent with improved error handling.
    Uses Sonnet model for complex reasoning (Split Model Strategy).
    """
    applicant_id = applicant_data.get("applicant_id", "UNKNOWN")
    logger.info(f"[{applicant_id}] Risk Agent starting analysis")

    # Check cache first
    cache_key_str = cache_key(applicant_id, "risk")
    cached_result = get_cache(cache_key_str)
    if cached_result:
        logger.info(f"[{applicant_id}] Risk Agent cache hit")
        return cached_result

    try:
        # Fetch context from MCP Server (RiskRulesDB)
        logger.debug(f"[{applicant_id}] Fetching risk rules and credit data")
        risk_rules = get_risk_rules()
        credit_risk = get_credit_score_risk_level(applicant_data.get("credit_score", 0))

        # Calculate proposed EMI
        loan_amount = applicant_data.get("loan_amount", 0)
        tenure_months = applicant_data.get("loan_tenure", 12)
        proposed_emi = loan_amount / tenure_months if tenure_months > 0 else 0

        dti_data = calculate_dti_ratio(
            monthly_income=applicant_data.get("income", 0),
            existing_liabilities=applicant_data.get("existing_liabilities", 0),
            proposed_emi=proposed_emi
        )

        anomaly_data = detect_anomalies(applicant_data)
        logger.debug(f"[{applicant_id}] MCP data calculated: DTI={dti_data.get('dti_ratio', 'N/A')}, Anomalies={len(anomaly_data.get('anomalies', []))}")

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

        logger.debug(f"[{applicant_id}] Invoking Claude Sonnet for risk analysis")
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_message)
        ])

        response_text = response.content.strip()
        logger.debug(f"[{applicant_id}] LLM response received ({len(response_text)} chars)")

        # Try to parse JSON with multiple fallback strategies
        result = _parse_json_response(response_text, dti_data, credit_risk, anomaly_data, applicant_id)

        # Add metadata
        result["agent"] = "risk_agent"
        result["model_used"] = AGENT_MODELS["risk_agent"]
        result["applicant_id"] = applicant_id
        result["mcp_data"] = {
            "dti_calculated": dti_data,
            "anomalies_detected": anomaly_data
        }

        # Cache result
        set_cache(cache_key_str, result)
        logger.info(f"[{applicant_id}] Risk Agent analysis complete")

        return result

    except Exception as e:
        logger.error(f"[{applicant_id}] Risk Agent failed", exc_info=True)
        raise LLMCallError(f"Risk Agent analysis failed: {str(e)}", agent_name="risk_agent") from e


def _parse_json_response(response_text: str, dti_data: dict, credit_risk: dict, anomaly_data: dict, applicant_id: str) -> dict:
    """
    Try to parse JSON response with multiple fallback strategies.

    Args:
        response_text: Raw LLM response
        dti_data: Pre-calculated DTI data (fallback)
        credit_risk: Pre-calculated credit risk (fallback)
        anomaly_data: Pre-calculated anomalies (fallback)
        applicant_id: Applicant ID for logging

    Returns:
        Parsed result dictionary
    """
    # Strategy 1: Direct JSON parse
    try:
        result = json.loads(response_text)
        logger.debug(f"[{applicant_id}] Direct JSON parsing successful")
        return result
    except json.JSONDecodeError as e:
        logger.debug(f"[{applicant_id}] Direct JSON parsing failed: {e}")

    # Strategy 2: Extract JSON from markdown code blocks
    try:
        # Find content between ``` markers
        code_block_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
        if code_block_match:
            code_content = code_block_match.group(1).strip()
            # Try to parse as JSON
            result = json.loads(code_content)
            logger.info(f"[{applicant_id}] Extracted JSON from markdown code block")
            return result
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        logger.debug(f"[{applicant_id}] Markdown extraction failed: {e}")

    # Strategy 2b: Extract JSON directly from response (greedy approach)
    try:
        # Find first { and match all the way to the last }
        start_idx = response_text.find('{')
        if start_idx != -1:
            # Count braces to find matching close brace
            brace_count = 0
            for i in range(start_idx, len(response_text)):
                if response_text[i] == '{':
                    brace_count += 1
                elif response_text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        potential_json = response_text[start_idx:i+1]
                        result = json.loads(potential_json)
                        # Verify it has required fields
                        if all(k in result for k in ["debt_to_income_ratio", "credit_score_risk_level"]):
                            logger.info(f"[{applicant_id}] Extracted JSON using brace matching")
                            return result
    except (json.JSONDecodeError, ValueError) as e:
        logger.debug(f"[{applicant_id}] Brace matching extraction failed: {e}")

    # Strategy 3: Find largest JSON object in response (improved regex)
    try:
        # Better regex to find JSON objects with nested braces
        json_pattern = r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}'
        json_matches = list(re.finditer(json_pattern, response_text, re.DOTALL))
        if json_matches:
            # Try each match from largest to smallest
            for match in sorted(json_matches, key=lambda m: len(m.group(0)), reverse=True):
                try:
                    result = json.loads(match.group(0))
                    # Verify it has required fields
                    if all(k in result for k in ["debt_to_income_ratio", "credit_score_risk_level"]):
                        logger.info(f"[{applicant_id}] Extracted valid JSON object from response")
                        return result
                except json.JSONDecodeError:
                    continue
    except (AttributeError, ValueError) as e:
        logger.debug(f"[{applicant_id}] JSON extraction failed: {e}")

    # Strategy 4: Build result from MCP data (fallback with logging)
    logger.warning(f"[{applicant_id}] All JSON extraction strategies failed. Using MCP-calculated values with partial reasoning.")

    # Get anomalies without adding parse error
    anomalies = anomaly_data.get("anomalies", [])
    if not anomalies:
        anomalies = []

    result = {
        "debt_to_income_ratio": dti_data.get("dti_ratio", 0),
        "credit_score_risk_level": credit_risk.get("risk_level", "MEDIUM"),
        "loan_amount_risk": _estimate_loan_amount_risk(dti_data),
        "anomaly_flags": anomalies,  # Only include actual anomalies, not parse error
        "reasoning": f"Risk assessment completed using standard MCP calculations. DTI: {dti_data.get('dti_ratio', 0):.2%}, Credit Risk: {credit_risk.get('risk_level', 'MEDIUM')}"
    }

    logger.info(f"[{applicant_id}] Fallback result generated with {len(result['anomaly_flags'])} anomalies")
    return result


def _estimate_loan_amount_risk(dti_data: dict) -> str:
    """Estimate loan amount risk based on DTI."""
    dti = dti_data.get("dti_ratio", 0)
    if dti <= 0.35:
        return "LOW"
    elif dti <= 0.45:
        return "MEDIUM"
    else:
        return "HIGH"


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