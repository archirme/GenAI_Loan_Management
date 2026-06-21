"""
🏦 Agentic AI Intelligent Loan Approval System - Enhanced UI v3.0

Smart conversational chatbot with intelligent form extraction:
- Extract applicant info from chat conversation
- Answer loan eligibility questions
- Guided step-by-step form completion
- Real-time loan processing with multi-agent analysis
- Professional decision cards with animations
- Complete visual overhaul with modern design

Built with: LangGraph + FastAPI + Streamlit + Anthropic Claude
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests
import json
from datetime import datetime
from typing import Dict, Any
import re

# ============================================================================
# CONFIGURATION & ENHANCED STYLING
# ============================================================================

FASTAPI_URL = "http://localhost:8000"

# Page Configuration
st.set_page_config(
    page_title="AI Loan Approval System",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS with vibrant colors, proper fonts, and modern design
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&family=Montserrat:wght@600;700&display=swap');

    /* Global Styles */
    :root {
        --primary: #1e3a8a;
        --success: #10b981;
        --danger: #ef4444;
        --warning: #f59e0b;
    }

    * {
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }

    /* Animations */
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 5px rgba(255, 255, 255, 0.3); }
        50% { box-shadow: 0 0 15px rgba(255, 255, 255, 0.6); }
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    /* Decision Cards with animations - VIBRANT COLORS */
    .decision-card-approved {
        background: linear-gradient(135deg, #00d084 0%, #00a86b 100%);
        padding: 30px;
        border-radius: 18px;
        color: white;
        font-weight: 700;
        font-size: 24px;
        margin: 20px 0;
        text-align: center;
        box-shadow: 0 15px 40px rgba(0, 208, 132, 0.4);
        animation: slideIn 0.6s ease-out;
        border: 3px solid rgba(255, 255, 255, 0.25);
        font-family: 'Montserrat', sans-serif;
    }
    .decision-card-rejected {
        background: linear-gradient(135deg, #ff4757 0%, #ee5a6f 100%);
        padding: 30px;
        border-radius: 18px;
        color: white;
        font-weight: 700;
        font-size: 24px;
        margin: 20px 0;
        text-align: center;
        box-shadow: 0 15px 40px rgba(255, 71, 87, 0.4);
        animation: slideIn 0.6s ease-out;
        border: 3px solid rgba(255, 255, 255, 0.25);
        font-family: 'Montserrat', sans-serif;
    }
    .decision-card-review {
        background: linear-gradient(135deg, #ffa502 0%, #ff8c00 100%);
        padding: 30px;
        border-radius: 18px;
        color: white;
        font-weight: 700;
        font-size: 24px;
        margin: 20px 0;
        text-align: center;
        box-shadow: 0 15px 40px rgba(255, 165, 2, 0.4);
        animation: slideIn 0.6s ease-out;
        border: 3px solid rgba(255, 255, 255, 0.25);
        font-family: 'Montserrat', sans-serif;
    }

    /* Chat Section - COOL BLUES & PURPLES */
    .chat-section-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin-bottom: 15px;
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        font-size: 18px;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
    }

    .chat-container {
        height: 550px;
        overflow-y: auto;
        padding: 18px;
        background: linear-gradient(to bottom, #f5f7ff 0%, #f8f5ff 100%);
        border-radius: 15px;
        margin-bottom: 15px;
        border: 2px solid #e8e4ff;
        box-shadow: inset 0 2px 8px rgba(102, 126, 234, 0.1);
    }

    .chat-message-user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 14px 18px;
        border-radius: 14px;
        color: white;
        margin: 10px 0;
        max-width: 85%;
        margin-left: auto;
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.3);
        animation: slideInRight 0.4s ease-out;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
    }

    .chat-message-bot {
        background: linear-gradient(135deg, #f0f0ff 0%, #e8f0ff 100%);
        padding: 14px 18px;
        border-radius: 14px;
        color: #2d3748;
        margin: 10px 0;
        max-width: 85%;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        animation: slideInLeft 0.4s ease-out;
        border: 1px solid #d8e4ff;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
    }

    /* Form Section - WARM GRADIENTS */
    .form-section-header {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 18px;
        border-radius: 14px;
        color: white;
        margin-bottom: 15px;
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        font-size: 16px;
        box-shadow: 0 8px 20px rgba(245, 87, 108, 0.25);
    }

    .form-section {
        background: linear-gradient(135deg, #fff5f7 0%, #ffe5ec 100%);
        padding: 18px;
        border-radius: 14px;
        margin: 15px 0;
        border: 2px solid #ffcce0;
        animation: slideIn 0.5s ease-out;
        box-shadow: 0 4px 12px rgba(245, 87, 108, 0.1);
    }

    .form-section b {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        color: #d81b60;
    }

    /* Results Section - TEAL & CYAN */
    .results-section-header {
        background: linear-gradient(135deg, #06d6a0 0%, #118ab2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin-bottom: 15px;
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        font-size: 18px;
        box-shadow: 0 8px 20px rgba(6, 214, 160, 0.3);
    }

    .metric-card {
        background: linear-gradient(135deg, #06d6a0 0%, #118ab2 100%);
        padding: 24px;
        border-radius: 14px;
        color: white;
        text-align: center;
        box-shadow: 0 10px 25px rgba(6, 214, 160, 0.3);
        animation: slideIn 0.5s ease-out;
        transition: all 0.3s ease;
        border: 2px solid rgba(255, 255, 255, 0.2);
        font-family: 'Inter', sans-serif;
    }

    .metric-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 15px 35px rgba(6, 214, 160, 0.4);
    }

    .factor-item {
        background: linear-gradient(135deg, #d4f1f4 0%, #a8dadc 100%);
        padding: 14px 18px;
        margin: 12px 0;
        border-radius: 10px;
        border-left: 5px solid #118ab2;
        animation: slideIn 0.4s ease-out;
        font-family: 'Inter', sans-serif;
        color: #0b4f8c;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(17, 138, 178, 0.15);
    }

    /* Agent Badges - DISTINCT COLORS */
    .agent-badge {
        display: inline-block;
        padding: 10px 16px;
        margin: 6px;
        border-radius: 25px;
        font-size: 12px;
        font-weight: 700;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        font-family: 'Poppins', sans-serif;
        animation: slideIn 0.5s ease-out;
    }

    .agent-haiku {
        background: linear-gradient(135deg, #a8e6cf 0%, #56ab2f 100%);
        color: white;
        box-shadow: 0 6px 16px rgba(86, 171, 47, 0.3);
    }

    .agent-sonnet {
        background: linear-gradient(135deg, #ffd89b 0%, #ff9a76 100%);
        color: white;
        box-shadow: 0 6px 16px rgba(255, 154, 118, 0.3);
    }

    /* Info Boxes - VIBRANT GRADIENT */
    .info-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 18px;
        border-radius: 12px;
        border-left: 5px solid #ffffff;
        margin: 15px 0;
        color: white;
        font-family: 'Inter', sans-serif;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.25);
    }

    /* Sidebar */
    .sidebar-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin: 15px 0;
        font-family: 'Poppins', sans-serif;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.2);
    }

    /* Subheader styling */
    h2 {
        font-family: 'Montserrat', sans-serif;
        font-weight: 700;
        color: #1a202c;
        font-size: 22px;
        margin-top: 20px;
        margin-bottom: 15px;
    }

    h3 {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        color: #2d3748;
        font-size: 16px;
    }

    /* Button styling */
    .button-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 14px 28px !important;
        font-weight: 700 !important;
        font-family: 'Poppins', sans-serif !important;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3) !important;
        border: none !important;
        transition: all 0.3s ease !important;
    }

    .button-primary:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 28px rgba(102, 126, 234, 0.4) !important;
    }

    /* Metric Grid */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 18px;
        margin: 25px 0;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background: linear-gradient(90deg, #f5f7ff 0%, #f8f5ff 100%);
        border-radius: 12px;
        padding: 8px;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border-radius: 10px;
        font-weight: 600;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .metric-grid {
            grid-template-columns: 1fr;
        }
        .chat-container {
            height: 400px;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# SMART CHATBOT ENGINE
# ============================================================================

def extract_applicant_info(user_input: str, current_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract applicant information from user input"""
    data = current_data.copy()
    text = user_input.lower()

    # Age extraction
    age_match = re.search(r'(?:age|i\'?m|years old?)\s*(?:is\s+)?(\d+)', text)
    if age_match:
        data['age'] = int(min(70, max(18, int(age_match.group(1)))))

    # Income extraction - handle both k/K suffix and regular numbers
    income_match = re.search(r'(?:earning|income|₹|rupees?)\s*(?:is\s+)?(?:₹)?\s*(\d+[,\d]*)\s*(?:k|K)?', text)
    if income_match:
        income_str = income_match.group(1).replace(',', '')
        income_val = int(float(income_str))
        # Check if followed by 'k' or 'K' to multiply by 1000
        if re.search(r'(?:earning|income|₹|rupees?)\s*(?:is\s+)?(?:₹)?\s*\d+[,\d]*\s*[kK]', text):
            income_val *= 1000
        data['income'] = income_val

    # Employment type extraction
    if any(word in text for word in ['salaried', 'employee', 'job']):
        data['employment_type'] = 'Salaried'
    elif any(word in text for word in ['self-employed', 'business', 'freelance']):
        data['employment_type'] = 'Self-Employed'
    elif any(word in text for word in ['unemployed', 'jobless']):
        data['employment_type'] = 'Unemployed'

    # Credit score extraction
    credit_match = re.search(r'(?:credit\s+score|cibil)\s*(?:is\s+)?(\d{3})', text)
    if credit_match:
        data['credit_score'] = int(credit_match.group(1))

    # Loan amount extraction - handle both k/K suffix and regular numbers
    loan_match = re.search(r'(?:loan\s+amount|need|borrow)\s*(?:is\s+)?(?:₹)?\s*(\d+[,\d]*)\s*(?:k|K)?', text)
    if loan_match:
        loan_str = loan_match.group(1).replace(',', '')
        loan_val = int(float(loan_str))
        # Check if followed by 'k' or 'K' to multiply by 1000
        if re.search(r'(?:loan\s+amount|need|borrow)\s*(?:is\s+)?(?:₹)?\s*\d+[,\d]*\s*[kK]', text):
            loan_val *= 1000
        data['loan_amount'] = loan_val

    # Location extraction
    if any(word in text for word in ['mumbai', 'delhi', 'bangalore', 'hyderabad', 'pune', 'ahmedabad']):
        for city in ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Pune', 'Ahmedabad']:
            if city.lower() in text:
                data['location'] = city
                break

    return data

def get_chatbot_response(user_input: str, form_data: Dict[str, Any]) -> str:
    """Generate intelligent chatbot responses"""
    text = user_input.lower()

    # FAQ Responses
    faq_responses = {
        'eligibility': "✅ **Eligibility Requirements:**\n- Age: 18-70 years\n- Income: ₹10,000+/month\n- Credit Score: 580+\n- Employment: Salaried/Self-Employed",

        'process': "📋 **Loan Approval Process:**\n1. Fill your details\n2. AI agents analyze:\n   - 👤 Profile (Income stability, employment)\n   - 📊 Risk (Debt ratio, credit score)\n   - ⚖️ Decision (Approval logic)\n   - ✅ Compliance (Documentation)\n3. Get instant decision!",

        'documents': "📄 **Required Documents:**\n- ID proof (Aadhar/PAN)\n- Income proof (Salary slip/ITR)\n- Bank statements (Last 6 months)\n- Address proof",

        'timeline': "⏱️ **Processing Timeline:**\n- Application: Instant\n- AI Analysis: 2-5 minutes\n- Decision: Within 24 hours\n- Disbursement: 2-3 business days",

        'rates': "💰 **Interest Rates:**\n- Approved: 8-12% p.a.\n- Based on credit score\n- Tenure: 12-360 months",
    }

    # Check for FAQ keywords
    for keyword, response in faq_responses.items():
        if keyword in text:
            return response

    # If they provided info, acknowledge it
    extracted = extract_applicant_info(user_input, {})
    if extracted:
        msg = "✅ **Got it!**\n"
        if 'age' in extracted and extracted['age'] != form_data.get('age'):
            msg += f"- Age: {extracted['age']} ✓\n"
        if 'income' in extracted and extracted['income'] != form_data.get('income'):
            msg += f"- Income: ₹{extracted['income']:,.0f}/month ✓\n"
        if 'employment_type' in extracted and extracted['employment_type'] != form_data.get('employment_type'):
            msg += f"- Employment: {extracted['employment_type']} ✓\n"
        if msg != "✅ **Got it!**\n":
            msg += "\n📝 **Please fill in the remaining details on the right to submit your application!**"
            return msg

    # Default response
    return """💬 **How can I help?**\n
You can:
- 📝 Tell me your details (e.g., "I'm 30, earning ₹100k, salaried")
- ❓ Ask about eligibility, rates, or process
- 📋 Ask about required documents
- ⏱️ Ask about processing timeline
- 🎯 Or just fill the form and submit!"""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_currency(value: float) -> str:
    """Format number as currency"""
    return f"₹{value:,.2f}"

def get_credit_color(score: int) -> str:
    """Get color based on credit score"""
    if score >= 750:
        return "🟢 Excellent"
    elif score >= 700:
        return "🟢 Good"
    elif score >= 650:
        return "🟡 Fair"
    elif score >= 580:
        return "🔴 Poor"
    else:
        return "🔴 Very Poor"

def get_risk_color(score: int) -> str:
    """Get color based on risk score"""
    if score <= 25:
        return "🟢 Low Risk"
    elif score <= 50:
        return "🟡 Medium Risk"
    elif score <= 75:
        return "🟠 High Risk"
    else:
        return "🔴 Critical Risk"

def display_decision_card(result: Dict[str, Any]):
    """Display professional decision card"""
    decision = result["decision"]
    risk_score = result["risk_score"]
    confidence = result["confidence"]

    # Decision styling
    if decision == "APPROVED":
        card_class = "decision-card-approved"
        emoji = "✅ APPROVED"
        color = "green"
    elif decision == "REJECTED":
        card_class = "decision-card-rejected"
        emoji = "❌ REJECTED"
        color = "red"
    else:
        card_class = "decision-card-review"
        emoji = "⏳ REQUIRES MANUAL REVIEW"
        color = "orange"

    st.markdown(f'<div class="{card_class}">{emoji}</div>', unsafe_allow_html=True)

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Risk Score", f"{risk_score}/100", delta=None)

    with col2:
        st.metric("Confidence", f"{confidence}%", delta=None)

    with col3:
        st.metric("Case ID", result.get("case_id", "N/A")[:15])

    with col4:
        status = "Sent" if result.get("notification_sent") else "Pending"
        st.metric("Notification", status)

    # Add Dashboard Link Button
    st.markdown("---")
    col_dashboard, col_spacer = st.columns([2, 3])
    with col_dashboard:
        if st.button("📊 View Full Analysis Dashboard", use_container_width=True, key="dashboard_btn"):
            st.session_state.page = "📊 Dashboard"
            st.rerun()

def display_applicant_summary(applicant_data: Dict[str, Any], result: Dict[str, Any]):
    """Display applicant details summary"""
    st.subheader("📋 Applicant Summary")

    # Create summary card
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        **Applicant ID:** {applicant_data['applicant_id']}
        **Age:** {applicant_data['age']} years
        **Location:** {applicant_data['location']}
        """)

    with col2:
        st.markdown(f"""
        **Income:** {format_currency(applicant_data['income'])}/month
        **Employment:** {applicant_data['employment_type']}
        **Credit Score:** {applicant_data['credit_score']} {get_credit_color(applicant_data['credit_score'])}
        """)

    with col3:
        st.markdown(f"""
        **Loan Amount:** {format_currency(applicant_data['loan_amount'])}
        **Tenure:** {applicant_data['loan_tenure']} months
        **Monthly EMI:** {format_currency(applicant_data['loan_amount'] / applicant_data['loan_tenure'])}
        """)

    with col4:
        monthly_debt = applicant_data['existing_liabilities'] + (applicant_data['loan_amount'] / applicant_data['loan_tenure'])
        dti = monthly_debt / applicant_data['income']
        st.markdown(f"""
        **Existing Liabilities:** {format_currency(applicant_data['existing_liabilities'])}/month
        **Total Monthly Debt:** {format_currency(monthly_debt)}
        **DTI Ratio:** {dti:.2%} {get_risk_color(int(dti*100))}
        """)

def display_agent_analysis(agent_details: Dict[str, Any]):
    """Display detailed agent analysis"""
    st.subheader("🤖 Agent Analysis Pipeline")

    # Create tabs for each agent
    tab1, tab2, tab3, tab4 = st.tabs([
        "👤 Profile Agent",
        "📊 Risk Agent",
        "⚖️ Decision Agent",
        "✅ Compliance Agent"
    ])

    # Profile Agent
    with tab1:
        st.markdown('<span class="agent-badge agent-haiku">Claude Haiku (Fast)</span>', unsafe_allow_html=True)
        profile = agent_details.get("profile", {})

        if "error" not in profile:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Income Stability Score", f"{profile.get('income_stability_score', 'N/A')}/100")
                st.metric("Employment Risk", profile.get('employment_risk', 'N/A'))
            with col2:
                st.success(profile.get('credit_history_summary', 'N/A'))
                flags = profile.get('completeness_flags', [])
                if flags:
                    st.warning(f"Issues: {', '.join(flags)}")
                else:
                    st.success("✅ Application Complete")
        else:
            st.error(profile.get("error"))

    # Risk Agent
    with tab2:
        st.markdown('<span class="agent-badge agent-sonnet">Claude Sonnet (Powerful)</span>', unsafe_allow_html=True)
        risk = agent_details.get("risk", {})

        if "error" not in risk:
            col1, col2, col3 = st.columns(3)
            with col1:
                dti = risk.get('debt_to_income_ratio', 0)
                st.metric("Debt-to-Income", f"{dti:.2%}")
            with col2:
                st.metric("Credit Risk Level", risk.get('credit_score_risk_level', 'N/A'))
            with col3:
                st.metric("Loan Amount Risk", risk.get('loan_amount_risk', 'N/A'))

            # Anomalies
            anomalies = risk.get('anomaly_flags', [])
            if anomalies:
                st.warning(f"⚠️ Detected Anomalies: {', '.join(anomalies)}")
            else:
                st.success("✅ No anomalies detected")

            # Reasoning
            with st.expander("📝 Detailed Risk Analysis"):
                st.write(risk.get('reasoning', 'No reasoning provided'))
        else:
            st.error(risk.get("error"))

    # Decision Agent
    with tab3:
        st.markdown('<span class="agent-badge agent-sonnet">Claude Sonnet (Powerful)</span>', unsafe_allow_html=True)
        decision = agent_details.get("decision", {})

        if "error" not in decision:
            st.subheader(decision.get('classification', 'N/A'))
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Risk Score", decision.get('risk_score', 'N/A'))
            with col2:
                st.metric("Confidence Level", f"{decision.get('confidence_level', 'N/A')}%")

            # Key Factors
            st.markdown("**Key Decision Factors:**")
            for factor in decision.get('key_decision_factors', []):
                st.markdown(f'<div class="factor-item">• {factor}</div>', unsafe_allow_html=True)

            # Full Explanation
            with st.expander("📖 Full Decision Explanation"):
                st.write(decision.get('explanation', 'No explanation provided'))
        else:
            st.error(decision.get("error"))

    # Compliance Agent
    with tab4:
        st.markdown('<span class="agent-badge agent-haiku">Claude Haiku (Fast)</span>', unsafe_allow_html=True)
        compliance = agent_details.get("compliance", {})

        if "error" not in compliance:
            st.success(f"✅ {compliance.get('action_taken', 'No action')}")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Case ID", compliance.get('case_id', 'N/A'))
            with col2:
                st.metric("Notification Sent", "✅ Yes" if compliance.get('notification_sent') else "❌ No")

            st.info(f"**Channel:** {compliance.get('notification_channel', 'N/A')}")

            # Compliance Checklist
            checklist = compliance.get('compliance_checklist', {})
            if checklist.get('actions'):
                st.markdown("**Compliance Checklist:**")
                for action in checklist['actions']:
                    st.markdown(f"- ✅ {action}")

            # Full Summary
            with st.expander("📋 Full Compliance Summary"):
                st.write(compliance.get('summary', 'No summary provided'))
        else:
            st.error(compliance.get("error"))

# ============================================================================
# SIDEBAR - NAVIGATION & SYSTEM INFO
# ============================================================================

with st.sidebar:
    st.image("https://via.placeholder.com/200x50?text=AI+Loan+System", width=300)
    st.divider()

    page = st.radio(
        "Navigation",
        ["💬 Chat & Apply", "📊 Dashboard", "ℹ️ System Info"],
        label_visibility="collapsed"
    )

    st.divider()

    # System Status
    st.subheader("🔧 System Status")
    try:
        resp = requests.get(f"{FASTAPI_URL}/health", timeout=5)
        if resp.status_code == 200:
            st.success("✅ API Healthy")
            health_data = resp.json()
            st.caption(f"v{health_data.get('version', '1.0')}")
        else:
            st.error("❌ API Down")
    except:
        st.error("❌ Cannot Connect")

    st.divider()

    # Architecture Info
    st.subheader("🏗️ Architecture")
    st.markdown("""
    **Split Model Strategy:**
    - 👤 Profile → Claude Haiku
    - 📊 Risk → Claude Sonnet
    - ⚖️ Decision → Claude Sonnet
    - ✅ Compliance → Claude Haiku

    **Technology Stack:**
    - LangGraph Orchestration
    - FastAPI Backend
    - 4 MCP Servers
    - MySQL Support
    """)

    st.divider()

    # Quick Links
    st.subheader("🔗 Quick Links")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📖 API Docs", use_container_width=True):
            st.info("Open: http://localhost:8000/docs")
    with col2:
        if st.button("🏥 Health Check", use_container_width=True):
            try:
                resp = requests.get(f"{FASTAPI_URL}/health", timeout=5)
                st.json(resp.json())
            except Exception as e:
                st.error(str(e))

# ============================================================================
# MAIN CONTENT - PAGE ROUTING
# ============================================================================

if page == "💬 Chat & Apply":
    # Initialize chat history and form data
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.current_application = None
        st.session_state.form_data = {}
        st.session_state.messages.append({
            "role": "assistant",
            "content": "👋 **Welcome to the AI Loan Approval System!** 🏦\n\nI'm your intelligent assistant with 4 specialized AI agents. You can:\n\n1. 💬 **Chat with me** - Tell your details or ask about loans\n2. 📝 **Fill the form** - Use the fields on the right\n3. 🚀 **Get instant decision** - AI analyzes in seconds\n\n**Try telling me:**\n- \"I'm 30, earning ₹100k, salaried\"\n- \"What's the eligibility?\"\n- \"How long does it take?\"\n\nLet's get started! 🎯"
        })

    # Three-column layout with vertical scroll for better responsiveness
    col_chat, col_form, col_result = st.columns([1.2, 1, 1.2], gap="medium")

    # ===== LEFT COLUMN: CHAT =====
    with col_chat:
        st.markdown('<div class="chat-section-header">💬 Smart Loan Assistant 🤖</div>', unsafe_allow_html=True)

        # Chat display styling - handled by Streamlit container
        st.markdown("""
            <style>
            .chat-message-user {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 12px 16px;
                border-radius: 12px;
                color: white;
                margin: 8px 0;
                max-width: 85%;
                margin-left: auto;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            }

            .chat-message-bot {
                background: #f3f4f6;
                padding: 12px 16px;
                border-radius: 12px;
                color: #1f2937;
                margin: 8px 0;
                max-width: 85%;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }
            </style>
        """, unsafe_allow_html=True)

        # Chat display using Streamlit container (better scroll behavior)
        chat_container = st.container(height=500, border=True)

        with chat_container:
            # Display messages in REVERSE order (latest at top)
            for message in reversed(st.session_state.messages):
                if message["role"] == "user":
                    st.markdown(f'<div class="chat-message-user">👤 {message["content"]}</div>', unsafe_allow_html=True)
                else:
                    # Truncate bot message to 200 chars if general response
                    content = message["content"]
                    if len(content) > 200 and "✅ **Got it!**" not in content and "💬" not in content:
                        content = content[:200] + "..."
                    st.markdown(f'<div class="chat-message-bot">🤖 {content}</div>', unsafe_allow_html=True)

        # Chat input with auto-fill capability
        if prompt := st.chat_input("Tell me your details or ask about the loan..."):
            st.session_state.messages.append({"role": "user", "content": prompt})

            try:
                # Extract info from chat with type safety
                extracted_data = extract_applicant_info(prompt, st.session_state.form_data)

                # Ensure all numeric values are proper types
                if 'age' in extracted_data:
                    extracted_data['age'] = int(extracted_data['age'])
                if 'income' in extracted_data:
                    extracted_data['income'] = int(float(extracted_data['income']))
                if 'credit_score' in extracted_data:
                    extracted_data['credit_score'] = int(extracted_data['credit_score'])
                if 'loan_amount' in extracted_data:
                    extracted_data['loan_amount'] = int(float(extracted_data['loan_amount']))
                if 'loan_tenure' in extracted_data:
                    extracted_data['loan_tenure'] = int(extracted_data['loan_tenure'])
                if 'existing_liabilities' in extracted_data:
                    extracted_data['existing_liabilities'] = int(float(extracted_data['existing_liabilities']))

                st.session_state.form_data.update(extracted_data)

                # Smart bot response
                response = get_chatbot_response(prompt, st.session_state.form_data)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"⚠️ I had trouble processing that message. Please try: 'I'm 30, earning ₹100k, salaried'"
                })

            st.rerun()

    # ===== MIDDLE COLUMN: FORM =====
    with col_form:
        st.markdown('<div class="form-section-header">📝 Application Form</div>', unsafe_allow_html=True)

        with st.form("loan_application_form", border=False):
            col_id, col_help = st.columns([3, 1])
            with col_id:
                applicant_id = st.text_input(
                    "👤 Applicant ID",
                    value=st.session_state.form_data.get('applicant_id', "APP"),
                    placeholder="e.g., APP001"
                )
            with col_help:
                with st.popover("❓ Help", use_container_width=True):
                    st.write("**Applicant ID** is your unique identifier in our system. Auto-generated if left blank. Example: APP001, APP002")

            # Section: Personal Info
            st.markdown("<div class='form-section'><b>👤 Personal Information</b></div>", unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            with col_a:
                age = st.slider(
                    "🎂 Age",
                    18, 70,
                    st.session_state.form_data.get('age', 32),
                    help="Your current age (18-70 years). Example: 30, 45, 65"
                )
            with col_b:
                location = st.text_input(
                    "📍 Location",
                    value=st.session_state.form_data.get('location', "Mumbai"),
                    help="Your city of residence. Example: Mumbai, Delhi, Bangalore",
                    placeholder="e.g., Mumbai"
                )

            # Section: Financial Info
            st.markdown("<div class='form-section'><b>💰 Financial Information</b></div>", unsafe_allow_html=True)
            income = st.number_input(
                "💵 Monthly Income (₹)",
                min_value=1000,
                value=int(st.session_state.form_data.get('income', 85000)),
                step=1000,
                help="Your total monthly income after taxes. Include salary, business income, etc. Example: ₹50,000, ₹100,000, ₹150,000"
            )
            employment_type = st.selectbox(
                "💼 Employment Type",
                ["Salaried", "Self-Employed", "Unemployed"],
                index=0 if st.session_state.form_data.get('employment_type') is None else
                      (0 if st.session_state.form_data.get('employment_type') == 'Salaried' else
                       1 if st.session_state.form_data.get('employment_type') == 'Self-Employed' else 2),
                help="Your employment status. Salaried: Regular job, Self-Employed: Business/Freelance, Unemployed: No current employment"
            )
            existing_liabilities = st.number_input(
                "📊 Monthly Liabilities (₹)",
                min_value=0,
                value=int(st.session_state.form_data.get('existing_liabilities', 15000)),
                step=1000,
                help="Your monthly debt payments (car loan, other loans, credit card). Example: ₹10,000, ₹25,000"
            )

            # Section: Credit & Loan
            st.markdown("<div class='form-section'><b>💳 Credit & Loan Details</b></div>", unsafe_allow_html=True)
            credit_score = st.slider(
                "📈 Credit Score",
                300, 900,
                int(st.session_state.form_data.get('credit_score', 720)),
                help="Your CIBIL/credit score (300-900). Higher is better. Example: 580 (Poor), 700 (Good), 750+ (Excellent)"
            )
            loan_amount = st.number_input(
                "💰 Loan Amount (₹)",
                min_value=10000,
                value=int(st.session_state.form_data.get('loan_amount', 500000)),
                step=10000,
                help="Amount you want to borrow. Example: ₹200,000, ₹500,000, ₹1,000,000"
            )
            loan_tenure = st.slider(
                "⏳ Tenure (months)",
                6, 360,
                int(st.session_state.form_data.get('loan_tenure', 60)),
                help="Loan repayment period in months. Example: 12 months (1 yr), 60 months (5 yrs), 120 months (10 yrs)"
            )

            # Review button first
            col1, col2 = st.columns(2)
            with col1:
                review_clicked = st.form_submit_button(
                    "👁️ REVIEW APPLICATION",
                    use_container_width=True,
                    type="secondary"
                )
            with col2:
                submitted = st.form_submit_button(
                    "🚀 SUBMIT APPLICATION",
                    use_container_width=True,
                    type="primary"
                )

    # ===== RIGHT COLUMN: RESULTS =====
    with col_result:
        st.markdown('<div class="results-section-header">📊 Decision Results</div>', unsafe_allow_html=True)

        if review_clicked:
            # Build application payload for review
            application = {
                "applicant_id": applicant_id or f"APP{int(datetime.now().timestamp())}",
                "age": age,
                "income": float(income),
                "employment_type": employment_type,
                "credit_score": credit_score,
                "loan_amount": float(loan_amount),
                "loan_tenure": loan_tenure,
                "existing_liabilities": float(existing_liabilities),
                "location": location,
                "timestamp": datetime.utcnow().isoformat()
            }

            st.session_state.current_application = application
            st.session_state.show_review = True

        # ===== REVIEW SECTION (shows when review clicked) =====
        if st.session_state.get('show_review') and st.session_state.get('current_application'):
            st.markdown("---")
            st.markdown("### 📋 Review Your Application Details")

            app = st.session_state.current_application
            review_col1, review_col2 = st.columns(2)

            with review_col1:
                st.write("**Personal Information**")
                st.write(f"👤 Applicant ID: `{app['applicant_id']}`")
                st.write(f"🎂 Age: `{app['age']} years`")
                st.write(f"📍 Location: `{app['location']}`")

            with review_col2:
                st.write("**Financial Information**")
                st.write(f"💵 Monthly Income: `₹{app['income']:,.0f}`")
                st.write(f"💼 Employment: `{app['employment_type']}`")
                st.write(f"📊 Monthly Liabilities: `₹{app['existing_liabilities']:,.0f}`")

            review_col3, review_col4 = st.columns(2)

            with review_col3:
                st.write("**Credit & Loan Details**")
                st.write(f"📈 Credit Score: `{app['credit_score']}`")
                st.write(f"💰 Loan Amount: `₹{app['loan_amount']:,.0f}`")

            with review_col4:
                st.write("**Loan Terms**")
                st.write(f"⏳ Tenure: `{app['loan_tenure']} months`")
                monthly_emi = app['loan_amount'] / app['loan_tenure']
                st.write(f"📌 Estimated EMI: `₹{monthly_emi:,.0f}/month`")

            st.info("✅ All details look correct? Click 'SUBMIT APPLICATION' below to proceed!")

        if submitted and st.session_state.get('current_application'):
            application = st.session_state.current_application

            # Add to chat
            st.session_state.messages.append({
                "role": "user",
                "content": f"📤 Application submitted: {application['applicant_id']}"
            })

            # Processing
            with st.spinner("⏳ Processing through 4 AI agents..."):
                try:
                    response = requests.post(
                        f"{FASTAPI_URL}/api/loan/apply",
                        json=application,
                        timeout=120
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.last_result = result

                        # Display decision card
                        display_decision_card(result)

                        # Add to chat
                        decision_msg = f"✅ **Decision: {result['decision']}**\n\nRisk Score: {result['risk_score']}/100 | Confidence: {result['confidence']}%\n\nCase ID: {result.get('case_id', 'N/A')}"
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": decision_msg
                        })

                        st.rerun()
                    else:
                        # Try to get error details from response
                        error_detail = "Unknown error"
                        try:
                            error_response = response.json()
                            error_detail = error_response.get("detail", f"HTTP {response.status_code}")
                        except:
                            error_detail = f"HTTP {response.status_code}: {response.text[:200]}"

                        st.error(f"❌ Error: {error_detail}")
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"❌ Error processing application: {error_detail}"
                        })

                except requests.exceptions.Timeout:
                    st.error("⏱️ Request timed out. Please try again.")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to API server.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

        elif "last_result" in st.session_state:
            display_decision_card(st.session_state.last_result)

elif page == "📊 Dashboard":
    st.title("📊 Detailed Analysis Dashboard")

    if "last_result" in st.session_state and "current_application" in st.session_state:
        result = st.session_state.last_result
        application = st.session_state.current_application

        # Display applicant summary
        display_applicant_summary(application, result)

        st.divider()

        # Display agent analysis
        display_agent_analysis(result.get("agent_details", {}))

        st.divider()

        # Full Result JSON
        with st.expander("📋 Raw JSON Response"):
            st.json(result)

        # Export options
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📥 Download Report", use_container_width=True):
                report = json.dumps(result, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=report,
                    file_name=f"loan_decision_{application['applicant_id']}.json",
                    mime="application/json"
                )
        with col2:
            if st.button("🔄 New Application", use_container_width=True):
                st.session_state.pop("last_result", None)
                st.session_state.pop("current_application", None)
                st.rerun()
    else:
        st.info("💡 No application processed yet. Submit an application from the Chat & Apply tab first!")

elif page == "ℹ️ System Info":
    st.title("ℹ️ System Information")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏗️ Architecture")
        st.markdown("""
        **Multi-Agent System:**
        - Orchestration Engine: LangGraph
        - Framework: LangChain + FastAPI
        - UI: Streamlit

        **Agent Pipeline:**
        1. Profile Analysis (Haiku)
        2. Risk Assessment (Sonnet)
        3. Decision Making (Sonnet)
        4. Compliance & Actions (Haiku)

        **Data Processing:**
        - Input: Applicant details
        - Processing: 4 MCP servers
        - Output: Decision + Analysis
        """)

    with col2:
        st.subheader("📋 Supported Operations")
        st.markdown("""
        **Loan Analysis:**
        - ✅ Credit Score Analysis
        - ✅ Income Verification
        - ✅ Risk Assessment
        - ✅ DTI Ratio Calculation
        - ✅ Anomaly Detection

        **Decision Classification:**
        - ✅ APPROVED
        - ✅ REJECTED
        - ✅ MANUAL REVIEW
        """)

    st.divider()
    st.subheader("🔧 API Endpoints")
    st.markdown("""
    - `POST /api/loan/apply` - Submit application
    - `GET /health` - Health check
    - `GET /api/agents/info` - Agent information
    """)

    st.divider()
    st.subheader("📚 Documentation")
    st.markdown("""
    - [START_HERE.md](http://localhost:8501) - Quick start guide
    - [QUICK_START.md](http://localhost:8501) - Fast setup
    - [README_LAUNCH.md](http://localhost:8501) - Launch guide
    - [ARCHITECTURE.md](http://localhost:8501) - System design
    """)

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
<div style='text-align: center; color: #666; font-size: 12px;'>
    <p>🏦 Agentic AI Intelligent Loan Approval System | Split Model Strategy</p>
    <p>Powered by LangGraph + FastAPI + Streamlit + Anthropic Claude</p>
    <p>Built for the AI Loan Approval Case Study</p>
</div>
""", unsafe_allow_html=True)
