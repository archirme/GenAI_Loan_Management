.PHONY: help start start-python start-shell start-docker start-docker-bg stop logs logs-fastapi logs-streamlit logs-orchestrator logs-mysql clean test health requirements docker-build docker-down docker-clean

help:
	@echo "Loan Management System - Makefile Commands"
	@echo "=========================================="
	@echo ""
	@echo "Launch Methods:"
	@echo "  make start              Start all services (Python script - recommended)"
	@echo "  make start-python       Start all services (Python script)"
	@echo "  make start-shell        Start all services (Shell script)"
	@echo "  make start-docker       Start all services (Docker Compose, foreground)"
	@echo "  make start-docker-bg    Start all services (Docker Compose, background)"
	@echo ""
	@echo "Stop & Cleanup:"
	@echo "  make stop               Stop all services"
	@echo "  make clean              Clean up logs and temp files"
	@echo "  make docker-clean       Clean Docker containers and volumes"
	@echo ""
	@echo "Monitoring:"
	@echo "  make logs               Show all logs (Docker only)"
	@echo "  make logs-fastapi       Show FastAPI logs"
	@echo "  make logs-streamlit     Show Streamlit logs"
	@echo "  make logs-orchestrator  Show Orchestrator logs"
	@echo "  make logs-mysql         Show MySQL logs (Docker only)"
	@echo ""
	@echo "Utilities:"
	@echo "  make health             Check service health"
	@echo "  make test               Run test API call"
	@echo "  make requirements       Install dependencies"
	@echo "  make docker-build       Build Docker images"
	@echo ""

# Default target
.DEFAULT_GOAL := help

# Launch targets
start: start-python

start-python:
	@echo "Starting all services with Python script..."
	python start.py

start-shell:
	@echo "Starting all services with Shell script..."
	bash start.sh

start-docker:
	@echo "Starting all services with Docker Compose (foreground)..."
	docker-compose up

start-docker-bg:
	@echo "Starting all services with Docker Compose (background)..."
	docker-compose up -d
	@echo "✅ Services started in background"
	@echo "Use 'make logs' to view logs"

# Stop targets
stop:
	@echo "Stopping services..."
	@if command -v docker-compose &> /dev/null; then \
		docker-compose down; \
		echo "✅ Docker Compose services stopped"; \
	else \
		pkill -f "python -m fastapi_service"; \
		pkill -f "streamlit run"; \
		pkill -f "python -m orchestrator"; \
		echo "✅ Services stopped"; \
	fi

# Logs targets
logs:
	docker-compose logs -f

logs-fastapi:
	@if command -v docker-compose &> /dev/null; then \
		docker-compose logs -f fastapi; \
	else \
		tail -f /tmp/fastapi.log; \
	fi

logs-streamlit:
	@if command -v docker-compose &> /dev/null; then \
		docker-compose logs -f streamlit; \
	else \
		tail -f /tmp/streamlit.log; \
	fi

logs-orchestrator:
	@if command -v docker-compose &> /dev/null; then \
		docker-compose logs -f orchestrator; \
	else \
		tail -f /tmp/orchestrator.log; \
	fi

logs-mysql:
	docker-compose logs -f mysql

# Health & Testing
health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | python -m json.tool
	@echo ""
	@echo "✅ FastAPI is healthy!"

test:
	@echo "Testing API with sample loan application..."
	@curl -X POST http://localhost:8000/api/loan/apply \
		-H "Content-Type: application/json" \
		-d '{ \
			"applicant_id": "TEST_$(shell date +%s)", \
			"age": 30, \
			"income": 50000, \
			"employment_type": "Salaried", \
			"credit_score": 700, \
			"loan_amount": 200000, \
			"loan_tenure": 36, \
			"existing_liabilities": 10000, \
			"location": "Mumbai" \
		}' | python -m json.tool

# Cleanup targets
clean:
	@echo "Cleaning up logs and temp files..."
	rm -f /tmp/fastapi.log /tmp/streamlit.log /tmp/orchestrator.log
	rm -rf __pycache__ .pytest_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleanup complete"

docker-clean:
	@echo "Cleaning Docker containers and volumes..."
	docker-compose down -v
	docker system prune -f
	@echo "✅ Docker cleanup complete"

# Setup targets
requirements:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed"

docker-build:
	@echo "Building Docker images..."
	docker-compose build
	@echo "✅ Docker images built"

# Development utilities
venv:
	@echo "Creating virtual environment..."
	python3 -m venv csvenv
	source csvenv/bin/activate && pip install -r requirements.txt
	@echo "✅ Virtual environment created"

env-example:
	@echo "Creating .env from .env.example..."
	cp .env.example .env
	@echo "✅ .env created - edit it with your configuration"

# Status commands
status:
	@echo "Service Status:"
	@echo "==============="
	@if command -v docker-compose &> /dev/null; then \
		docker-compose ps; \
	else \
		echo "FastAPI:"; \
		pgrep -f "fastapi" > /dev/null && echo "  ✅ Running" || echo "  ❌ Stopped"; \
		echo "Streamlit:"; \
		pgrep -f "streamlit" > /dev/null && echo "  ✅ Running" || echo "  ❌ Stopped"; \
		echo "Orchestrator:"; \
		pgrep -f "orchestrator" > /dev/null && echo "  ✅ Running" || echo "  ❌ Stopped"; \
	fi

info:
	@echo "Loan Management System - Configuration"
	@echo "======================================="
	@echo ""
	@echo "Environment Configuration:"
	@grep -v '^#' .env | grep -v '^$$'
	@echo ""
	@echo "Access Points:"
	@echo "  API Docs:    http://localhost:8000/docs"
	@echo "  Web UI:      http://localhost:8501"
	@echo "  Health:      http://localhost:8000/health"

# Format code
format:
	@echo "Formatting Python code..."
	black loan-approval-system/ --quiet
	@echo "✅ Code formatted"

# Lint code
lint:
	@echo "Linting Python code..."
	flake8 loan-approval-system/ --count --show-source --statistics
	@echo "✅ Lint complete"
