"""
Applicant Profile Agent with Logging, Timeouts, and Caching
Model: Claude Haiku (Split Model Strategy - simple extraction task)
MCP Server: ApplicantDB
Output: Income Stability Score, Employment Risk, Credit History Summary, Completeness Flags
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

# Import MCP tools directly (in-process for simplicity)
from mcp_servers.applicant_db import (
    get_applicant_profile,
    get_credit_history,
    check_application_completeness
)

llm = ChatAnthropic(
    model=AGENT_MODELS["profile_agent"],
    api_key=LLMGW_API_KEY,
    base_url=LLMGW_BASE_URL,
    max_tokens=MAX_TOKENS["profile_agent"],
    temperature=0,
    timeout=30  # 30 second timeout
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
- income_stability_score: Salaried = 70-85, Self-Employed = 50-70, Based on provided income and stability
- employment_risk: Salaried = LOW, Self-Employed = MEDIUM, Freelance = HIGH
- credit_history_summary: Summarize credit score and any risk factors
- completeness_flags: List only ACTUAL missing fields, not database lookup failures

**IMPORTANT:** Ignore "not_found" messages from the database. These are normal when applicants are new.
Focus on analyzing the actual application data provided. If the database is unavailable, use the form data.
Only flag fields if they're missing from the APPLICATION itself, not from the database.

Be concise. Return ONLY the JSON object, no other text."""


def run_profile_agent(applicant_data: dict) -> dict:
    """
    Execute the Applicant Profile Agent with logging and error handling.
    Uses Haiku model for cost efficiency (simple extraction task).
    """
    applicant_id = applicant_data.get("applicant_id", "UNKNOWN")
    logger.info(f"[{applicant_id}] Profile Agent starting analysis")

    # Check cache first
    cache_key_str = cache_key(applicant_id, "profile")
    cached_result = get_cache(cache_key_str)
    if cached_result:
        logger.info(f"[{applicant_id}] Profile Agent cache hit")
        return cached_result

    try:
        # Fetch context from MCP Server (ApplicantDB)
        logger.debug(f"[{applicant_id}] Fetching profile and credit history from MCP")
        profile_context = get_applicant_profile(applicant_id)
        credit_context = get_credit_history(applicant_id)
        completeness = check_application_completeness(applicant_data)
        logger.debug(f"[{applicant_id}] MCP data fetched successfully")

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

        logger.debug(f"[{applicant_id}] Invoking Claude Haiku for profile analysis")
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_message)
        ])

        response_text = response.content.strip()
        logger.debug(f"[{applicant_id}] LLM response received ({len(response_text)} chars)")

        # Parse response with fallback strategies
        result = _parse_json_response(response_text, applicant_id)

        # Add metadata
        result["agent"] = "profile_agent"
        result["model_used"] = AGENT_MODELS["profile_agent"]
        result["applicant_id"] = applicant_id

        # Cache result
        set_cache(cache_key_str, result)
        logger.info(f"[{applicant_id}] Profile Agent analysis complete")

        return result

    except Exception as e:
        logger.error(f"[{applicant_id}] Profile Agent failed", exc_info=True)
        raise LLMCallError(f"Profile Agent analysis failed: {str(e)}", agent_name="profile_agent") from e


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
        "income_stability_score": 50,
        "employment_risk": "MEDIUM",
        "credit_history_summary": "Unable to parse - manual review needed",
        "completeness_flags": ["LLM_RESPONSE_PARSE_ERROR"]
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
    result = run_profile_agent(test_data)
    print(json.dumps(result, indent=2))
