"""
Loan Decision Agent with Logging, Timeouts, and Caching
Model: Claude Sonnet (Split Model Strategy - complex synthesis & explainability)
MCP Server: DecisionSynthesis
Output: Classification, Risk Score, Confidence Level, Key Decision Factors, Explanation
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

from mcp_servers.decision_synthesis import (
    get_decision_rules,
    get_decision_precedents,
    log_decision
)

llm = ChatAnthropic(
    model=AGENT_MODELS["decision_agent"],
    api_key=LLMGW_API_KEY,
    base_url=LLMGW_BASE_URL,
    max_tokens=MAX_TOKENS["decision_agent"],
    temperature=0,
    timeout=30  # 30 second timeout
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
    Execute the Loan Decision Agent with logging and error handling.
    Uses Sonnet model for complex synthesis (Split Model Strategy).
    """
    applicant_id = applicant_data.get("applicant_id", "UNKNOWN")
    logger.info(f"[{applicant_id}] Decision Agent starting decision synthesis")

    # Check cache first
    cache_key_str = cache_key(applicant_id, "decision")
    cached_result = get_cache(cache_key_str)
    if cached_result:
        logger.info(f"[{applicant_id}] Decision Agent cache hit")
        return cached_result

    try:
        # Fetch context from MCP Server (DecisionSynthesis)
        logger.debug(f"[{applicant_id}] Fetching decision rules and precedents from MCP")
        decision_rules = get_decision_rules()
        precedents = get_decision_precedents()
        logger.debug(f"[{applicant_id}] Decision context fetched successfully")

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

        logger.debug(f"[{applicant_id}] Invoking Claude Sonnet for decision synthesis")
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_message)
        ])

        response_text = response.content.strip()
        logger.debug(f"[{applicant_id}] LLM response received ({len(response_text)} chars)")

        # Parse response with fallback strategies
        result = _parse_json_response(response_text, applicant_id)

        # Log the decision via MCP server
        logger.debug(f"[{applicant_id}] Logging decision to MCP server")
        try:
            log_decision(
                applicant_id=applicant_id,
                classification=result.get("classification", "MANUAL_REVIEW"),
                risk_score=result.get("risk_score", 50),
                confidence=result.get("confidence_level", 50),
                factors=result.get("key_decision_factors", []),
                explanation=result.get("explanation", "")
            )
        except Exception as e:
            logger.warning(f"[{applicant_id}] Failed to log decision to database: {e}")

        # Add metadata
        result["agent"] = "decision_agent"
        result["model_used"] = AGENT_MODELS["decision_agent"]
        result["applicant_id"] = applicant_id

        # Cache result
        set_cache(cache_key_str, result)
        logger.info(f"[{applicant_id}] Decision Agent synthesis complete: {result.get('classification')}")

        return result

    except Exception as e:
        logger.error(f"[{applicant_id}] Decision Agent failed", exc_info=True)
        raise LLMCallError(f"Decision Agent synthesis failed: {str(e)}", agent_name="decision_agent") from e


def _parse_json_response(response_text: str, applicant_id: str) -> dict:
    """
    Try to parse JSON response with fallback strategies.

    Args:
        response_text: Raw LLM response
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

    # Strategy 2: Extract JSON from markdown
    try:
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(1))
            logger.info(f"[{applicant_id}] Extracted JSON from markdown code block")
            return result
    except (json.JSONDecodeError, AttributeError) as e:
        logger.debug(f"[{applicant_id}] Markdown extraction failed: {e}")

    # Strategy 3: Find largest JSON object
    try:
        json_matches = list(re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL))
        if json_matches:
            largest_match = max(json_matches, key=lambda m: len(m.group(0)))
            result = json.loads(largest_match.group(0))
            logger.info(f"[{applicant_id}] Extracted largest JSON object from response")
            return result
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        logger.debug(f"[{applicant_id}] Largest JSON extraction failed: {e}")

    # Strategy 4: Fallback with defaults
    logger.warning(f"[{applicant_id}] All JSON extraction strategies failed. Using defaults.")
    result = {
        "classification": "MANUAL_REVIEW",
        "risk_score": 50,
        "confidence_level": 30,
        "key_decision_factors": ["Error in processing"],
        "explanation": "System was unable to make automated decision. Forwarding to manual review."
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
    test_risk = {
        "debt_to_income_ratio": 0.32,
        "credit_score_risk_level": "LOW",
        "loan_amount_risk": "MEDIUM",
        "anomaly_flags": [],
        "reasoning": "Good profile with acceptable DTI ratio"
    }
    result = run_decision_agent(test_data, test_profile, test_risk)
    print(json.dumps(result, indent=2))
