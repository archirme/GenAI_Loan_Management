## Streamlit Chatbot UI

### File: `streamlit_app/app.py`
"""
Streamlit Chatbot UI for Loan Approval System.
Provides conversational interface for loan application submission and status display.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests
import json
from datetime import datetime

# Configuration
FASTAPI_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title=" AI Loan Approval System",
    page_icon="",
    layout="wide"
)

st.title("Agentic AI Loan Approval System")
st.caption("Multi-Agent AI system with Split Model Strategy (Haiku + Sonnet)")

# Sidebar - System Info
with st.sidebar:
    st.header("System Architecture")
    st.markdown("""
    **Split Model Strategy:**
    - Profile Agent → Haiku (fast/cheap)
    - Risk Agent → Sonnet (powerful)
    - Decision Agent → Sonnet (powerful)
    - Compliance Agent → Haiku (fast/cheap)
    """)
    
    st.divider()
    st.header("Agent Workflow")
    st.markdown("""
    1. Profile Analysis
    2. Risk Assessment
    3. Decision Making
    4. Compliance & Actions
    """)
    
    st.divider()
    # API Health Check
    if st.button("Check API Health"):
        try:
            resp = requests.get(f"{FASTAPI_URL}/health", timeout=5)
            if resp.status_code == 200:
                st.success("✅ API is healthy!")
                st.json(resp.json())
            else:
                st.error(f"❌ API returned {resp.status_code}")
        except Exception as e:
            st.error(f"❌ Cannot connect to API: {e}")


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Initial greeting
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Welcome to the AI Loan Approval System! I can help you submit a loan application and get an instant AI-powered decision.\n\nYou can either:\n1. **Fill the form** on the right side, or\n2. **Chat with me** and provide your details conversationally.\n\nThe system uses 4 specialized AI agents to analyze your application."
    })

# Two-column layout
col1, col2 = st.columns([1, 1])

# Left column - Chat Interface
with col1:
    st.subheader(" Chat Interface")
    
    # Display chat history
    chat_container = st.container(height=400)
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about loan approval or provide details..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Simple conversational response
        response = "I've noted your input. Please fill in the application form on the right and click 'Submit Application' to get your AI-powered decision. All 4 agents will analyze your application using the Split Model Strategy."
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

# Right column - Application Form
with col2:
    st.subheader("Loan Application Form")
    
    with st.form("loan_application_form"):
        applicant_id = st.text_input("Applicant ID", value="APP001")
        
        col_a, col_b = st.columns(2)
        with col_a:
            age = st.number_input("Age", min_value=18, max_value=70, value=32)
            income = st.number_input("Monthly Income (₹)", min_value=1000, value=85000)
            employment_type = st.selectbox("Employment Type", 
                                           ["Salaried", "Self-Employed", "Unemployed"])
        with col_b:
            credit_score = st.number_input("Credit Score", min_value=300, max_value=900, value=720)
            loan_amount = st.number_input("Loan Amount (₹)", min_value=10000, value=500000)
            loan_tenure = st.number_input("Loan Tenure (months)", min_value=6, max_value=360, value=60)
        
        existing_liabilities = st.number_input("Existing Monthly Liabilities (₹)", min_value=0, value=15000)
        location = st.text_input("Location", value="Mumbai")
        
        submitted = st.form_submit_button(" Submit Application", use_container_width=True)
    
    if submitted:
        # Build application payload
        application = {
            "applicant_id": applicant_id,
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
        
        st.session_state.messages.append({
            "role": "user",
            "content": f"Submitted loan application:\n```json\n{json.dumps(application, indent=2)}\n```"
        })
        
        # Call FastAPI
        with st.spinner("Processing through 4 AI agents..."):
            try:
                response = requests.post(
                    f"{FASTAPI_URL}/api/loan/apply",
                    json=application,
                    timeout=120
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Format decision display
                    decision_emoji = {
                        "APPROVED": "✅",
                        "REJECTED": "❌",
                        "MANUAL_REVIEW": "Manual Review"
                    }
                    emoji = decision_emoji.get(result["decision"], "❓")
                    
                    # Display result
                    st.divider()
                    st.subheader(f"{emoji} Decision: {result['decision']}")
                    
                    # Metrics row
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Risk Score", f"{result['risk_score']}/100")
                    m2.metric("Confidence", f"{result['confidence']}%")
                    m3.metric("Case ID", result.get('case_id', 'N/A'))
                    
                    # Explanation
                    st.markdown("### Explanation")
                    st.info(result.get("explanation", "No explanation provided"))
                    
                    # Key Factors
                    st.markdown("### Key Decision Factors")
                    for factor in result.get("key_factors", []):
                        st.markdown(f"- {factor}")
                    
                    # Detailed Agent Outputs (expandable)
                    with st.expander(" Detailed Agent Outputs"):
                        st.json(result.get("agent_details", {}))
                    
                    # Add to chat
                    chat_response = f"{emoji} **Decision: {result['decision']}**\n\n"
                    chat_response += f"**Risk Score:** {result['risk_score']}/100\n"
                    chat_response += f"**Confidence:** {result['confidence']}%\n\n"
                    chat_response += f"**Explanation:** {result.get('explanation', '')}\n\n"
                    chat_response += f"**Case ID:** {result.get('case_id', 'N/A')}"
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": chat_response
                    })
                    
                else:
                    st.error(f"❌ API Error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to the API server. Make sure FastAPI is running on port 8000.")
                st.code("python fastapi_service/main.py", language="bash")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


# Footer
st.divider()
st.caption("Agentic AI Loan Approval System | Split Model Strategy: Haiku (simple) + Sonnet (complex) | Built with LangGraph + FastAPI + Streamlit + Anthropic Claude")
