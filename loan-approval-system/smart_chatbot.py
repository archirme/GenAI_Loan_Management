"""
Smart Context-Aware Chatbot Engine
Uses Claude Haiku to handle both loan-related and general conversations.
Automatically extracts applicant information and guides form completion.
"""
import re
import json
from typing import Dict, Tuple, Any
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from config import LLMGW_API_KEY, LLMGW_BASE_URL, AGENT_MODELS
from logging_config import get_logger

logger = get_logger(__name__)

# Initialize Haiku for fast general conversation
llm_haiku = ChatAnthropic(
    model=AGENT_MODELS.get("profile_agent", "claude-3-5-haiku-20241022"),
    api_key=LLMGW_API_KEY,
    base_url=LLMGW_BASE_URL,
    max_tokens=500,
    temperature=0.7  # Slightly higher temp for natural conversation
)


def classify_message(user_input: str) -> str:
    """
    Classify user message as 'loan' or 'general'.

    Args:
        user_input: User's message

    Returns:
        "loan" if message is about loan, "general" otherwise
    """
    loan_keywords = [
        "loan", "borrow", "credit", "age", "income", "salary", "employment",
        "credit score", "eligibility", "approval", "interest", "rate", "tenure",
        "amount", "form", "application", "financial", "debt", "liabilities",
        "emi", "repayment", "process", "decision", "documents", "requirements",
        "document", "years", "monthly", "cost", "fee", "salaried", "employed",
        "self-employed", "earning", "earning", "freelance", "business", "₹"
    ]

    user_lower = user_input.lower()

    # Check for explicit loan keywords
    if any(keyword in user_lower for keyword in loan_keywords):
        return "loan"

    # Check for questions about the system/process
    if any(phrase in user_lower for phrase in ["how does", "what is", "tell me about", "explain", "how can"]):
        if any(keyword in user_lower for keyword in ["loan", "process", "eligibility", "application", "work", "this"]):
            return "loan"

    # Short messages are often greetings/general chat
    if len(user_lower) < 20 and user_input.strip().endswith("?"):
        return "general"

    return "loan"


def extract_applicant_info(user_input: str, current_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract applicant information from user input using regex patterns.

    Args:
        user_input: User's message
        current_data: Current form data

    Returns:
        Updated form data with extracted information
    """
    extracted = current_data.copy()

    # Age patterns: "I'm 30", "28 years old", "age 35"
    age_match = re.search(r'(?:i\'?m|am|age|aged?)\s+(\d{1,3})(?:\s+(?:year|yr))?', user_input, re.IGNORECASE)
    if age_match:
        age = int(age_match.group(1))
        if 18 <= age <= 80:
            extracted["age"] = age
            logger.debug(f"Extracted age: {age}")

    # Income patterns: "₹100k", "100000", "earning 100k/month"
    income_match = re.search(r'(?:₹|earning|income|salary|earn|get)[\s:]*(?:₹\s*)?(\d{1,3}(?:[.,]\d{3})*(?:\.\d+)?)\s*(?:k|K)?', user_input, re.IGNORECASE)
    if income_match:
        income_str = income_match.group(1).replace(',', '').replace('.', '')
        has_k_suffix = 'k' in user_input[max(0, income_match.end()-5):income_match.end()].lower()
        try:
            income = int(float(income_str))
            if has_k_suffix:
                income = income * 1000
            if income > 0 and income < 10000000:
                extracted["income"] = income
                logger.debug(f"Extracted income: {income}")
        except (ValueError, AttributeError):
            pass

    # Employment type patterns
    employment_match = re.search(r'\b(salaried|self[\s-]employed|freelance|business|contractor|employee|job|work)\b', user_input, re.IGNORECASE)
    if employment_match:
        emp_type = employment_match.group(1).lower()
        if "salaried" in emp_type or "employee" in emp_type or "job" in emp_type:
            extracted["employment_type"] = "Salaried"
        elif "self" in emp_type or "business" in emp_type:
            extracted["employment_type"] = "Self-Employed"
        elif "freelance" in emp_type or "contractor" in emp_type:
            extracted["employment_type"] = "Freelance"
        logger.debug(f"Extracted employment: {extracted.get('employment_type')}")

    # Credit score patterns: "750", "credit score 750"
    credit_match = re.search(r'(?:credit\s+score|score|cibil)[\s:]*(\d{3})\b', user_input, re.IGNORECASE)
    if credit_match:
        score = int(credit_match.group(1))
        if 300 <= score <= 900:
            extracted["credit_score"] = score
            logger.debug(f"Extracted credit score: {score}")

    # Loan amount patterns: "₹500k", "500000", "want 500k"
    loan_match = re.search(r'(?:loan|amount|need|want)[\s:]*(?:₹\s*)?(\d{1,3}(?:[.,]\d{3})*(?:\.\d+)?)\s*(?:k|K)?', user_input, re.IGNORECASE)
    if loan_match:
        loan_str = loan_match.group(1).replace(',', '').replace('.', '')
        try:
            loan = int(float(loan_str))
            if 'k' in user_input[max(0, loan_match.end()-5):loan_match.end()].lower():
                loan = loan * 1000
            if loan > 0 and loan < 100000000:
                extracted["loan_amount"] = loan
                logger.debug(f"Extracted loan amount: {loan}")
        except (ValueError, AttributeError):
            pass

    # Tenure patterns: "60 months", "5 years"
    tenure_match = re.search(r'(\d{1,3})\s*(?:months?|years?|yrs?)\b', user_input, re.IGNORECASE)
    if tenure_match:
        tenure_str = tenure_match.group(1)
        if 'year' in user_input[tenure_match.start():tenure_match.end()].lower():
            tenure = int(tenure_str) * 12
        else:
            tenure = int(tenure_str)
        if 6 <= tenure <= 360:
            extracted["loan_tenure"] = tenure
            logger.debug(f"Extracted tenure: {tenure} months")

    return extracted


def get_missing_fields(form_data: Dict[str, Any]) -> list:
    """
    Identify missing required form fields.

    Args:
        form_data: Current form data

    Returns:
        List of missing field names
    """
    required_fields = ["age", "income", "employment_type", "credit_score", "loan_amount", "loan_tenure"]
    missing = [f for f in required_fields if f not in form_data or form_data[f] is None]
    return missing


def get_loan_faq_response(user_input: str) -> str:
    """
    Provide FAQ responses for common loan-related questions.

    Args:
        user_input: User's question

    Returns:
        FAQ response or None if not a FAQ question
    """
    user_lower = user_input.lower()

    # Eligibility questions
    if any(word in user_lower for word in ["eligible", "eligibility", "qualify", "requirements"]):
        return """✅ **Eligibility Requirements:**
• Age: 18-70 years
• Monthly Income: ₹10,000+
• Credit Score: 580+
• Employment: Salaried, Self-Employed, or Freelance
• Location: All India

You can apply even if you don't meet all criteria - we'll review your complete profile."""

    # Process questions
    if any(word in user_lower for word in ["how does", "process", "how it works", "workflow", "steps"]):
        return """✅ **Loan Approval Process:**
1. **Profile Analysis** - We evaluate your background and income stability
2. **Risk Assessment** - We calculate financial risk based on your profile
3. **Decision Making** - Our system makes a decision: Approved, Rejected, or Manual Review
4. **Compliance Check** - We verify regulatory requirements
5. **Result** - You get your decision instantly!

⏱️ Total time: Usually less than 2 minutes"""

    # Document questions
    if any(word in user_lower for word in ["document", "require", "proof", "submit", "papers"]):
        return """📄 **Required Documents:**
• Identity Proof (PAN, Aadhar, Passport)
• Address Proof (Utility bill, Lease agreement)
• Income Proof (Salary slip, ITR, Bank statement)
• Employment Proof (Appointment letter, Business registration)
• Bank Statements (Last 6 months)

*For now, just fill the form - documents are collected after approval.*"""

    # Timeline questions
    if any(word in user_lower for word in ["timeline", "how long", "duration", "minutes", "hours", "days"]):
        return """⏰ **Processing Timeline:**
• Form Filling: 2-5 minutes
• AI Analysis: <2 minutes
• Decision: Instant
• Manual Review (if needed): 24-48 hours

✅ Most decisions are instant after form submission!"""

    # Interest rate questions
    if any(word in user_lower for word in ["interest", "rate", "emi", "cost", "charges"]):
        return """💰 **Interest Rates & EMI:**
Interest rates depend on:
• Your Credit Score (higher = better rate)
• Risk Assessment Score (lower risk = better rate)
• Loan Amount & Tenure

📊 **Rate Range:** 8% - 16% per annum (typical)

*Exact rate will be calculated based on your complete profile. Fill the form to get your personalized offer!*"""

    return None


def get_intelligent_chatbot_response(user_input: str, form_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Get intelligent response based on message classification and context.

    Args:
        user_input: User's message
        form_data: Current form data

    Returns:
        Tuple of (response_text, updated_form_data)
    """
    message_type = classify_message(user_input)

    updated_data = form_data.copy()
    response = ""

    if message_type == "loan":
        # Extract any information from the message
        updated_data = extract_applicant_info(user_input, form_data)

        # Get extracted fields
        new_extractions = [k for k in updated_data if updated_data.get(k) != form_data.get(k)]

        if new_extractions:
            response = "✅ **Got it!**\n"
            field_names = {
                "age": "Age",
                "income": "Income",
                "employment_type": "Employment",
                "credit_score": "Credit Score",
                "loan_amount": "Loan Amount",
                "loan_tenure": "Tenure"
            }
            for field in new_extractions:
                if field in field_names:
                    value = updated_data[field]
                    if field == "income":
                        value = f"₹{value:,}/month"
                    elif field == "loan_amount":
                        value = f"₹{value:,}"
                    elif field == "loan_tenure":
                        value = f"{value} months"
                    response += f"• {field_names[field]}: {value} ✓\n"

            response += "\n"

            # Show summary of all collected details
            response += "**📋 Summary of your details:**\n"
            collected_fields = []
            for key in ["age", "income", "employment_type", "credit_score", "loan_amount", "loan_tenure"]:
                if key in updated_data and updated_data[key] is not None:
                    if key == "age":
                        collected_fields.append(f"Age: {updated_data[key]}")
                    elif key == "income":
                        collected_fields.append(f"Income: ₹{updated_data[key]:,}")
                    elif key == "employment_type":
                        collected_fields.append(f"Employment: {updated_data[key]}")
                    elif key == "credit_score":
                        collected_fields.append(f"Credit: {updated_data[key]}")
                    elif key == "loan_amount":
                        collected_fields.append(f"Loan: ₹{updated_data[key]:,}")
                    elif key == "loan_tenure":
                        collected_fields.append(f"Tenure: {updated_data[key]} months")

            if collected_fields:
                response += " | ".join(collected_fields) + "\n"

        # Check for FAQ questions
        faq_response = get_loan_faq_response(user_input)
        if faq_response:
            response += faq_response + "\n"

        # If no FAQ match and no extraction, ask for specific info
        if not faq_response and not new_extractions:
            response = "I'm here to help with your loan application! You can tell me about yourself, and I'll extract the information to fill your form.\n\n"
            response += "For example, you could say: *'I'm 30 years old, earning ₹120k monthly as a salaried employee'*"

        # Suggest next steps
        missing = get_missing_fields(updated_data)
        if missing:
            response += f"\n\n📝 **Still need:** {', '.join([f.replace('_', ' ') for f in missing[:2]])}"

    else:  # general message
        # Build context from current form data for conversational awareness
        context_info = []
        if form_data.get('age'):
            context_info.append(f"Age: {form_data['age']}")
        if form_data.get('employment_type'):
            context_info.append(f"Employment: {form_data['employment_type']}")
        if form_data.get('income'):
            context_info.append(f"Income: ₹{form_data['income']:,}")

        context_str = ""
        if context_info:
            context_str = f"\n\nApplicant context: {', '.join(context_info)}"

        system_prompt = f"""You are a friendly and helpful loan application assistant. Answer the user's question or respond to their message in a natural, conversational way.
Keep responses VERY BRIEF - maximum 2 sentences, under 150 words.
You can discuss topics outside of loans too - be helpful and friendly.
If appropriate, gently mention how your service can help with loan applications.{context_str}"""

        try:
            llm_response = llm_haiku.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input)
            ])
            response = llm_response.content.strip()

            # Truncate to 200 characters for display
            if len(response) > 200:
                response = response[:197] + "..."

            # Add a gentle redirect for non-loan topics (brief)
            if not any(keyword in user_input.lower() for keyword in ["loan", "application", "eligibility", "process", "form"]):
                response += " 💡 Need help with loans?"

        except Exception as e:
            logger.error(f"General chat error: {e}")
            response = "Happy to help! Chat or ask about loans."

    logger.info(f"Chatbot response generated - Type: {message_type}, Extracted: {len(get_missing_fields(updated_data))} fields still needed")
    return response, updated_data
