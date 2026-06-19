#!/usr/bin/env python3
"""
Launch all three services for the Loan Management System
- FastAPI service (API backend)
- Streamlit app (Web UI)
- Orchestrator (Loan processing engine)
"""
import subprocess
import signal
import os
import sys
import time
from pathlib import Path
from threading import Thread

# Get the project root
PROJECT_ROOT = Path(__file__).parent
LOAN_SYS_DIR = PROJECT_ROOT / "loan-approval-system"

# Change to loan-approval-system directory
os.chdir(LOAN_SYS_DIR)
sys.path.insert(0, str(LOAN_SYS_DIR))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

processes = []
process_names = {
    "fastapi": "FastAPI Service",
    "streamlit": "Streamlit UI",
    "orchestrator": "Orchestrator"
}

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_success(text):
    """Print success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print error message"""
    print(f"❌ {text}")

def print_warning(text):
    """Print warning message"""
    print(f"⚠️  {text}")

def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")

def read_output(process, name):
    """Read process output in a separate thread"""
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"[{name}] {line.rstrip()}")
    except:
        pass

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print_header("SHUTTING DOWN SERVICES")

    for i, p in enumerate(processes):
        if p.poll() is None:  # Process is still running
            service_name = list(process_names.values())[i]
            print_info(f"Stopping {service_name}...")
            p.terminate()
            try:
                p.wait(timeout=5)
                print_success(f"{service_name} stopped")
            except subprocess.TimeoutExpired:
                print_warning(f"{service_name} did not stop gracefully, killing...")
                p.kill()
                p.wait()
                print_success(f"{service_name} killed")

    print_header("ALL SERVICES STOPPED")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main launcher function"""
    print_header("LOAN MANAGEMENT SYSTEM - STARTUP")

    # Verify environment
    print_info("Checking environment...")
    api_key = os.getenv("LLMGW_API_KEY")
    base_url = os.getenv("LLMGW_BASE_URL")

    if not api_key or not base_url:
        print_error("Missing LLMGW_API_KEY or LLMGW_BASE_URL in .env")
        sys.exit(1)

    print_success("Environment variables loaded")

    # 1. Start FastAPI service
    print_info("Starting FastAPI service on http://localhost:8000/docs")
    try:
        fastapi_process = subprocess.Popen(
            [sys.executable, "-m", "fastapi_service.main"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(fastapi_process)

        # Start thread to read output
        Thread(target=read_output, args=(fastapi_process, "FastAPI"), daemon=True).start()

        time.sleep(2)  # Give FastAPI time to start
        print_success("FastAPI service started")
    except Exception as e:
        print_error(f"Failed to start FastAPI: {e}")
        signal_handler(signal.SIGINT, None)

    # 2. Start Streamlit app
    print_info("Starting Streamlit app on http://localhost:8501")
    try:
        streamlit_process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "streamlit_app/app.py", "--logger.level=warning"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(streamlit_process)

        # Start thread to read output
        Thread(target=read_output, args=(streamlit_process, "Streamlit"), daemon=True).start()

        time.sleep(3)  # Give Streamlit time to start
        print_success("Streamlit app started")
    except Exception as e:
        print_error(f"Failed to start Streamlit: {e}")
        signal_handler(signal.SIGINT, None)

    # 3. Start Orchestrator
    print_info("Starting Orchestrator...")
    try:
        orchestrator_process = subprocess.Popen(
            [sys.executable, "-m", "orchestrator.graph"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(orchestrator_process)

        # Start thread to read output
        Thread(target=read_output, args=(orchestrator_process, "Orchestrator"), daemon=True).start()

        time.sleep(1)
        print_success("Orchestrator started")
    except Exception as e:
        print_error(f"Failed to start Orchestrator: {e}")
        signal_handler(signal.SIGINT, None)

    # Summary
    print_header("ALL SERVICES STARTED SUCCESSFULLY")
    print("""
╔════════════════════════════════════════════════════════════════╗
║                    LOAN MANAGEMENT SYSTEM                      ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  🔗 API Documentation:                                        ║
║     http://localhost:8000/docs                               ║
║     http://localhost:8000/redoc                              ║
║                                                                ║
║  🎨 Web Interface:                                            ║
║     http://localhost:8501                                    ║
║                                                                ║
║  ⚙️  Orchestrator:                                             ║
║     Running in background (see logs above)                   ║
║                                                                ║
║  📊 API Endpoints:                                             ║
║     POST   /api/loan/apply       - Submit loan application   ║
║     GET    /health              - Health check              ║
║     GET    /api/agents/info      - Agent information         ║
║                                                                ║
║  🛑 To stop all services: Press Ctrl+C                         ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
    """)

    # Keep the script running and monitor processes
    try:
        while True:
            # Check if any process has died
            for i, p in enumerate(processes):
                if p.poll() is not None:
                    service_name = list(process_names.values())[i]
                    print_error(f"{service_name} has stopped (exit code: {p.returncode})")
            time.sleep(2)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()
