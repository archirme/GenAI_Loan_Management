# ⚡ Quick Start Guide

Get the Loan Management System running in seconds!

---

## 🚀 Fastest Way to Start (Recommended)

### Option 1: One Command (Python)
```bash
cd /home/ubuntu/Documents/LoanManagement
python start.py
```

**That's it!** All three services start automatically.

### Access Points
- 📊 **API Docs:** http://localhost:8000/docs
- 🎨 **Web UI:** http://localhost:8501
- ✅ **Health Check:** http://localhost:8000/health

---

## 🛠️ Alternative: Shell Script
```bash
./start.sh
```

View logs:
```bash
tail -f /tmp/fastapi.log
tail -f /tmp/streamlit.log
tail -f /tmp/orchestrator.log
```

---

## 🐳 Production: Docker Compose
```bash
docker-compose up
```

View logs:
```bash
docker-compose logs -f
```

---

## ✅ Verify It's Working

### Test the API
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "loan-approval-system",
  "version": "1.0.0"
}
```

### Submit a Test Loan Application
```bash
curl -X POST http://localhost:8000/api/loan/apply \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "TEST001",
    "age": 30,
    "income": 50000,
    "employment_type": "Salaried",
    "credit_score": 700,
    "loan_amount": 200000,
    "loan_tenure": 36,
    "existing_liabilities": 10000,
    "location": "Mumbai"
  }'
```

---

## 🛑 Stop All Services

**For Python script:** `Ctrl+C`

**For Shell script:** `Ctrl+C` or `kill <PID>`

**For Docker:** `docker-compose down`

---

## 📋 Configuration

Edit `.env` to customize:
```bash
# LLM Gateway (required)
LLMGW_API_KEY=your_key_here
LLMGW_BASE_URL=https://llmgw-wp.tekstac.com
LLMGW_MODEL=global.anthropic.claude-haiku-4-5-20251001-v1:0

# Database (optional)
DATA_SOURCE=mock  # or "mysql"
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=Tek@12345
```

---

## 🔍 Services Overview

| Service | Port | Purpose |
|---------|------|---------|
| **FastAPI** | 8000 | REST API backend |
| **Streamlit** | 8501 | Web UI dashboard |
| **Orchestrator** | - | Loan processing engine |
| **MySQL** | 3306 | Database (Docker only) |

---

## 📚 Full Documentation

For detailed information, see [LAUNCH.md](LAUNCH.md)

---

**Ready to go!** 🎉
