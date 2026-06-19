"""
Configuration for the Loan Approval System.
Split Model Strategy: Haiku for simple agents, Sonnet for complex reasoning.
"""
"""import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic API Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Split Model Strategy - Model Assignment
MODELS = {
    "haiku": "claude-haiku-3-5-20241022",    # Cheap, fast - for simple tasks
    "sonnet": "claude-sonnet-4-20250514",    # Powerful - for complex reasoning
}

"""

#import requests
#import json
import os
from dotenv import load_dotenv
# ─── Load environment variables from .env file ────────────────────────────────
load_dotenv(override=True)  # override=True allows .env values to overwrite existing env vars

# ─── Configuration ────────────────────────────────────────────────────────────
LLMGW_API_KEY = os.getenv("LLMGW_API_KEY")
LLMGW_BASE_URL =os.getenv("LLMGW_BASE_URL")
LLMGW_MODEL = os.getenv("LLMGW_MODEL")

print (f"API KEY {LLMGW_API_KEY}")
print (f"ENDPOINT {LLMGW_BASE_URL}")
print (f"MODEL {LLMGW_MODEL}")
"""
# ─── Headers (same as Postman Headers tab) ────────────────────────────────────
headers = {
    "x-api-key": API_KEY,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json"
}
# ─── Request Body (same as Postman Body → raw → JSON) ─────────────────────────
payload = {
    "model": MODEL,
    "max_tokens": 256,
    "temperature": 0.5,
    "system": "You are a helpful assistant.",
    "messages": [
        {
            "role": "user",
            "content": "What is the capital of France?"
        }
    ]
}

# ─── Send POST Request ─────────────────────────────────────────────────────────
response = requests.post(ENDPOINT, headers=headers, json=payload, verify=False)
# ─── Display Response ──────────────────────────────────────────────────────────
print(f"Status Code : {response.status_code}")
print(f"Response    :\n{json.dumps(response.json(), indent=2)}")
"""

# Split Model Strategy - Model Assignment
MODELS = {
    "haiku": "global.anthropic.claude-haiku-4-5-20251001-v1:0",    # Cheap, fast - for simple tasks
    "sonnet": "global.anthropic.claude-sonnet-4-6",    # Powerful - for complex reasoning
    "opus": "global.anthropic.claude-opus-4-5-20251101-v1:0",    # MOST Powerful - for complex reasoning
}


# Agent-to-Model Mapping (Split Model Strategy)
AGENT_MODELS = {
    "profile_agent": MODELS["haiku"],       # Simple extraction → Haiku
    "risk_agent": MODELS["sonnet"],         # Complex analysis → Sonnet
    "decision_agent": MODELS["sonnet"],     # Reasoning + explanation → Sonnet
    "compliance_agent": MODELS["haiku"],    # Template actions → Haiku
}

# Token Limits (cost control)
MAX_TOKENS = {
    "profile_agent": 500,       # Short structured output
    "risk_agent": 1000,         # Detailed analysis
    "decision_agent": 1000,     # Decision + explanation
    "compliance_agent": 500,    # Short action record
}

# MCP Server URLs (when running locally)
MCP_SERVERS = {
    "applicant_db": "http://localhost:8001",
    "risk_rules_db": "http://localhost:8002",
    "decision_synthesis": "http://localhost:8003",
    "notification_system": "http://localhost:8004",
}

# FastAPI Service
FASTAPI_HOST = "localhost"
FASTAPI_PORT = 8000


# ============================================================
# NEW: DATA SOURCE CONFIGURATION
# ============================================================

# Toggle between "mock" (in-memory data) and "mysql" (real database)
# Change this in .env to switch without modifying any code
DATA_SOURCE = os.getenv("DATA_SOURCE", "mock")  # "mock" or "mysql"

# MySQL Configuration (used only when DATA_SOURCE = "mysql")
MYSQL_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "loan_approval_db"),
}