"""
Compliance & Action Orchestrator Agent
Model: Claude Haiku (Split Model Strategy - template-based actions)
MCP Server: NotificationSystem
Output: Action Taken, Notification Sent, Case ID, Timestamp, Summary
"""
import json
from datetime import datetime
#from anthropic import Anthropic
#from config import ANTHROPIC_API_KEY, AGENT_MODELS, MAX_TOKENS
from langchain_anthropic import ChatAnthropic
from config import LLMGW_API_KEY, LLMGW_BASE_URL, AGENT_MODELS, MAX_TOKENS
from langchain_core.messages import SystemMessage, HumanMessage

from mcp_servers.notification_system import (
    send_notification,
    create_case,
    get_compliance_checklist
)

#client = Anthropic(api_key=ANTHROPIC_API_KEY)

llm = ChatAnthropic(
    model=AGENT_MODELS["<agent_name>"],      # e.g., "profile_agent"
    api_key=LLMGW_API_KEY,
    base_url=LLMGW_BASE_URL,                 # Routes through LLMGW gateway
    max_tokens=MAX_TOKENS["<agent_name>"],
    temperature=0
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
    Execute the Compliance & Action Orchestrator Agent.
    Uses Haiku model for cost efficiency (template-based task).
    """
    applicant_id = applicant_data.get("applicant_id", "UNKNOWN")
    classification = decision_output.get("classification", "MANUAL_REVIEW")
    
    # Execute MCP actions
    # 1. Get compliance checklist
    checklist = get_compliance_checklist(classification)
    
    # 2. Create case record
    case_record = create_case(
        applicant_id=applicant_id,
        classification=classification,
        summary=decision_output.get("explanation", ""),
        priority="HIGH" if classification == "MANUAL_REVIEW" else "NORMAL"
    )
    
    # 3. Send notification
    notification_messages = {
        "APPROVED": f"Congratulations! Your loan application {applicant_id} has been approved.",
        "REJECTED": f"We regret to inform you that your loan application {applicant_id} has not been approved at this time.",
        "MANUAL_REVIEW": f"Your loan application {applicant_id} is under review. A representative will contact you within 72 hours."
    }
    
    notification = send_notification(
        applicant_id=applicant_id,
        notification_type=f"LOAN_{classification}",
        message=notification_messages.get(classification, "Application update"),
        channel="email"
    )
    
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

    # Call Claude Haiku (Split Model Strategy - simple template task)
    """
    response = client.messages.create(
        model=AGENT_MODELS["compliance_agent"],
        max_tokens=MAX_TOKENS["compliance_agent"],
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
                "action_taken": f"Loan {classification.lower()} - automated processing",
                "notification_sent": True,
                "notification_channel": "email",
                "notification_message": notification_messages.get(classification, ""),
                "case_id": case_record.get("case_id", "UNKNOWN"),
                "timestamp": datetime.utcnow().isoformat(),
                "summary": f"Application {applicant_id} processed with result: {classification}"
            }
    
    # Add metadata
    result["agent"] = "compliance_agent"
    result["model_used"] = AGENT_MODELS["compliance_agent"]
    result["compliance_checklist"] = checklist
    
    return result


if __name__ == "__main__":
    test_data = {"applicant_id": "APP001", "age": 32, "income": 85000}
    test_decision = {
        "classification": "APPROVED",
        "risk_score": 25,
        "confidence_level": 90,
        "key_decision_factors": ["Good credit", "Low DTI", "Stable employment"],
        "explanation": "Application approved based on strong financial profile."
    }
    result = run_compliance_agent(test_data, test_decision)
    print(json.dumps(result, indent=2))