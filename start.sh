#!/bin/bash

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOAN_SYS_DIR="$PROJECT_ROOT/loan-approval-system"

# Activate virtual environment
if [ ! -d "$PROJECT_ROOT/csvenv" ]; then
    echo -e "${RED}❌ Virtual environment not found at $PROJECT_ROOT/csvenv${NC}"
    echo "Please create it first with: python3 -m venv csvenv"
    exit 1
fi

source "$PROJECT_ROOT/csvenv/bin/activate"

# Change to the loan-approval-system directory
cd "$LOAN_SYS_DIR" || exit 1

# Export environment variables from .env
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(cat "$PROJECT_ROOT/.env" | grep -v '#' | xargs)
fi

echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  🚀 LOAN MANAGEMENT SYSTEM - STARTUP${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════${NC}\n"

# Function to handle cleanup on exit
cleanup() {
    echo -e "\n${CYAN}════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════${NC}\n"

    if [ ! -z "$FASTAPI_PID" ] && kill -0 $FASTAPI_PID 2>/dev/null; then
        echo -e "${YELLOW}Stopping FastAPI (PID: $FASTAPI_PID)...${NC}"
        kill $FASTAPI_PID 2>/dev/null
        wait $FASTAPI_PID 2>/dev/null
    fi

    if [ ! -z "$STREAMLIT_PID" ] && kill -0 $STREAMLIT_PID 2>/dev/null; then
        echo -e "${YELLOW}Stopping Streamlit (PID: $STREAMLIT_PID)...${NC}"
        kill $STREAMLIT_PID 2>/dev/null
        wait $STREAMLIT_PID 2>/dev/null
    fi

    if [ ! -z "$ORCHESTRATOR_PID" ] && kill -0 $ORCHESTRATOR_PID 2>/dev/null; then
        echo -e "${YELLOW}Stopping Orchestrator (PID: $ORCHESTRATOR_PID)...${NC}"
        kill $ORCHESTRATOR_PID 2>/dev/null
        wait $ORCHESTRATOR_PID 2>/dev/null
    fi

    echo -e "\n${GREEN}✅ All services stopped${NC}\n"
}

# Set trap to cleanup on exit
trap cleanup EXIT INT TERM

# Start services
echo -e "${BLUE}[1/3] Starting FastAPI service on http://localhost:8000/docs${NC}"
python -m fastapi_service.main > /tmp/fastapi.log 2>&1 &
FASTAPI_PID=$!
sleep 2
if kill -0 $FASTAPI_PID 2>/dev/null; then
    echo -e "${GREEN}✅ FastAPI started (PID: $FASTAPI_PID)${NC}"
else
    echo -e "${RED}❌ FastAPI failed to start${NC}"
    cat /tmp/fastapi.log
    exit 1
fi

echo -e "${BLUE}[2/3] Starting Streamlit app on http://localhost:8501${NC}"
streamlit run streamlit_app/app.py --logger.level=warning > /tmp/streamlit.log 2>&1 &
STREAMLIT_PID=$!
sleep 3
if kill -0 $STREAMLIT_PID 2>/dev/null; then
    echo -e "${GREEN}✅ Streamlit started (PID: $STREAMLIT_PID)${NC}"
else
    echo -e "${RED}❌ Streamlit failed to start${NC}"
    cat /tmp/streamlit.log
    exit 1
fi

echo -e "${BLUE}[3/3] Starting Orchestrator${NC}"
python -m orchestrator.graph > /tmp/orchestrator.log 2>&1 &
ORCHESTRATOR_PID=$!
sleep 1
if kill -0 $ORCHESTRATOR_PID 2>/dev/null; then
    echo -e "${GREEN}✅ Orchestrator started (PID: $ORCHESTRATOR_PID)${NC}"
else
    echo -e "${RED}❌ Orchestrator failed to start${NC}"
    cat /tmp/orchestrator.log
    exit 1
fi

# Display summary
echo -e "\n${CYAN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ ALL SERVICES STARTED SUCCESSFULLY${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════${NC}\n"

echo -e "${CYAN}📊 LOAN MANAGEMENT SYSTEM${NC}"
echo -e "${CYAN}────────────────────────────────────────────────────────${NC}"
echo -e "🔗  ${YELLOW}API (FastAPI):${NC}     http://localhost:8000/docs"
echo -e "🔗  ${YELLOW}API Redoc:${NC}         http://localhost:8000/redoc"
echo -e "🎨  ${YELLOW}Web UI (Streamlit):${NC} http://localhost:8501"
echo -e "⚙️   ${YELLOW}Orchestrator:${NC}      Running in background"
echo -e "${CYAN}────────────────────────────────────────────────────────${NC}"
echo -e "\n📋  ${YELLOW}Process IDs:${NC}"
echo -e "    FastAPI:      $FASTAPI_PID"
echo -e "    Streamlit:    $STREAMLIT_PID"
echo -e "    Orchestrator: $ORCHESTRATOR_PID"
echo -e "\n📝  ${YELLOW}Logs:${NC}"
echo -e "    /tmp/fastapi.log"
echo -e "    /tmp/streamlit.log"
echo -e "    /tmp/orchestrator.log"
echo -e "\n🛑  ${YELLOW}To stop all services:${NC} Press Ctrl+C or run:"
echo -e "    kill $FASTAPI_PID $STREAMLIT_PID $ORCHESTRATOR_PID"
echo -e "\n${CYAN}════════════════════════════════════════════════════════${NC}\n"

# Wait for all background processes
wait
