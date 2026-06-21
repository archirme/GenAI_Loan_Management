"""
Compliance & Action Orchestrator Agent with Logging, Timeouts, and Caching
Model: Claude Haiku (Split Model Strategy - template-based actions)
MCP Server: NotificationSystem
Output: Action Taken, Notification Sent, Case ID, Timestamp, Summary
"""
import json
import re
from datetime import datetime
from langchain_anthropic import ChatAnthropic
from config import LLMGW_API_KEY, LLMGW_BASE_URL, AGENT_MODELS, MAX_TOKENS
from langchain_core.messages import SystemMessage, HumanMessage
from logging_config import get_logger
from exceptions import JSONParseError, LLMCallError
from cache import get_cache, set_cache, cache_key

logger = get_logger(__name__)

from mcp_servers.notification_system import (
    send_notification,
    create_case,
    get_compliance_checklist
)

llm = ChatAnthropic(
    model=AGENT_MODELS["compliance_agent"],
    api_key=LLMGW_API_KEY,
    base_url=LLMGW_BASE_URL,
    max_tokens=MAX_TOKENS["compliance_agent"],
    temperature=0,
    timeout=30  # 30 second timeout
)

SYSTEM_PROMPT = """You are a Compliance and Notification Officer for a bank's loan department. Based on the loan decision, you generate formal action records.

You MUST return ONLY valid JSON with these exact fields:
{
    "action_taken": "<formal description of action performed>",
    "notification_sent": true,
    "notification_channel": "<email|sms|both>",
    "notification_message": "<brief formal message sent to applicant>",
    "case_id": "<use the case_id from the context>",
    "timestamp": "<current UTC timestamp>",
    "summary": "<one-paragraph formal summary of the entire loan application journey and final outcome>"
}

Be brief, formal, and professional. This is an official record.
Return ONLY the JSON object."""


def run_compliance_agent(applicant_data: dict, decision_output: dict) -> dict:
    """
    Execute the Compliance & Action Orchestrator Agent with logging and error handling.
    Uses Haiku model for cost efficiency (template-based task).
    """
    applicant_id = applicant_data.get("applicant_id", "UNKNOWN")
    classification = decision_output.get("classification", "MANUAL_REVIEW")
    logger.info(f"[{applicant_id}] Compliance Agent starting compliance processing for {classification}")

    # Check cache first
    cache_key_str = cache_key(applicant_id, "compliance")
    cached_result = get_cache(cache_key_str)
    if cached_result:
        logger.info(f"[{applicant_id}] Compliance Agent cache hit")
        return cached_result

    try:
        # Notification messages
        notification_messages = {
            "APPROVED": f"Congratulations! Your loan application {applicant_id} has been approved.",
            "REJECTED": f"We regret to inform you that your loan application {applicant_id} has not been approved at this time.",
            "MANUAL_REVIEW": f"Your loan application {applicant_id} is under review. A representative will contact you within 72 hours."
        }

        # Execute MCP actions
        logger.debug(f"[{applicant_id}] Fetching compliance checklist from MCP")
        checklist = get_compliance_checklist(classification)

        logger.debug(f"[{applicant_id}] Creating case record in MCP")
        case_record = create_case(
            applicant_id=applicant_id,
            classification=classification,
            summary=decision_output.get("explanation", ""),
            priority="HIGH" if classification == "MANUAL_REVIEW" else "NORMAL"
        )

        logger.debug(f"[{applicant_id}] Sending notification via MCP")
        notification = send_notification(
            applicant_id=applicant_id,
            notification_type=f"LOAN_{classification}",
            message=notification_messages.get(classification, "Application update"),
            channel="email"
        )
        logger.debug(f"[{applicant_id}] MCP actions completed. Case ID: {case_record.get('case_id')}")

        # Build user message for LLM to generate formal summary
        user_message = f"""Generate the compliance action record for this loan decision:

**Applicant Data:**
{json.dumps(applicant_data, indent=2)}

**Decision Output:**
{json.dumps(decision_output, indent=2)}

**Compliance Checklist:**
{json.dumps(checklist, indent=2)}

**Case Created:**
{json.dumps(case_record, indent=2)}

**Notification Sent:**
{json.dumps(notification, indent=2)}

Generate the formal action record as JSON."""

        logger.debug(f"[{applicant_id}] Invoking Claude Haiku for compliance summary")
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_message)
        ])

        response_text = response.content.strip()
        logger.debug(f"[{applicant_id}] LLM response received ({len(response_text)} chars)")

        # Parse response with fallback strategies
        result = _parse_json_response(response_text, applicant_id, case_record, classification, notification_messages)

        # Add metadata
        result["agent"] = "compliance_agent"
        result["model_used"] = AGENT_MODELS["compliance_agent"]
        result["applicant_id"] = applicant_id
        result["compliance_checklist"] = checklist

        # Cache result
        set_cache(cache_key_str, result)
        logger.info(f"[{applicant_id}] Compliance Agent processing complete. Case: {result.get('case_id')}")

        return result

    except Exception as e:
        logger.error(f"[{applicant_id}] Compliance Agent failed", exc_info=True)
        raise LLMCallError(f"Compliance Agent processing failed: {str(e)}", agent_name="compliance_agent") from e


def _parse_json_response(response_text: str, applicant_id: str, case_record: dict, classification: str, notification_messages: dict) -> dict:
    """
    Try to parse JSON response with fallback strategies.

    Args:
        response_text: Raw LLM response
        applicant_id: Applicant ID for logging
        case_record: Case record from MCP (fallback)
        classification: Loan decision classification (fallback)
        notification_messages: Messages dict (fallback)

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

    # Strategy 4: Fallback with MCP data
    logger.warning(f"[{applicant_id}] All JSON extraction strategies failed. Using MCP-calculated values.")
    result = {
        "action_taken": f"Loan {classification.lower()} - automated processing",
        "notification_sent": True,
        "notification_channel": "email",
        "notification_message": notification_messages.get(classification, ""),
        "case_id": case_record.get("case_id", "UNKNOWN"),
        "timestamp": datetime.utcnow().isoformat(),
        "summary": f"Application {applicant_id} processed with result: {classification}"
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
    test_decision = {
        "classification": "APPROVED",
        "risk_score": 35,
        "confidence_level": 95,
        "key_decision_factors": ["Good credit score", "Low DTI", "Stable employment"],
        "explanation": "Applicant meets all approval criteria with low risk profile"
    }
    result = run_compliance_agent(test_data, test_decision)
    print(json.dumps(result, indent=2))
