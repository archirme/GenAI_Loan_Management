# 🎯 START HERE - Loan Management System Launch Guide

Welcome! This guide will help you launch the Loan Management System in seconds.

---

## ⚡ Quick Decision Tree

**Pick your situation:**

### 👨‍💻 I'm a Developer (Want to debug/develop)
→ **Use [Python Script](#-option-1-python-script)** with `python start.py`  
→ Then read [QUICK_START.md](QUICK_START.md) (3 min)

### 🚀 I want to Deploy to Production
→ **Use [Docker Compose](#-option-3-docker-compose)** with `docker-compose up`  
→ Then read [LAUNCH.md](LAUNCH.md) (15 min)

### ⚙️ I'm Setting up in CI/CD Pipeline
→ **Use [Shell Script](#-option-2-shell-script)** with `./start.sh`  
→ Then read [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) (10 min)

### 🤔 I Just Want to Try It
→ **Run `python start.py`** right now!  
→ Then open http://localhost:8501

---

## 🚀 Three Options (Pick One)

### 🐍 Option 1: Python Script
```bash
python start.py
```
✅ Best for development  
✅ Real-time logs  
✅ Easy debugging  
**[Learn more](README_LAUNCH.md#1️⃣-python-script---python-startpy)**

### 🐚 Option 2: Shell Script
```bash
./start.sh
```
✅ Quick & lightweight  
✅ Good for CI/CD  
✅ Automatic logging  
**[Learn more](README_LAUNCH.md#2️⃣-shell-script---./start.sh)**

### 🐳 Option 3: Docker Compose
```bash
docker-compose up
```
✅ Production-ready  
✅ Full isolation  
✅ Includes database  
**[Learn more](README_LAUNCH.md#3️⃣-docker-compose---docker-composeup)**

---

## ✨ What You Get

After launching, you'll have:

| Service | URL | Purpose |
|---------|-----|---------|
| **Web UI** | http://localhost:8501 | Interactive dashboard |
| **API Docs** | http://localhost:8000/docs | Interactive API |
| **API ReDoc** | http://localhost:8000/redoc | Alternative API docs |
| **Health** | http://localhost:8000/health | Status check |

---

## 📚 Documentation Map

### Quick Reads (Start Here)
- **[QUICK_START.md](QUICK_START.md)** - 3 minutes  
  One-command startup, basic troubleshooting

### Comprehensive Guides
- **[README_LAUNCH.md](README_LAUNCH.md)** - 10 minutes  
  Complete overview with examples
  
- **[LAUNCH.md](LAUNCH.md)** - 15 minutes  
  Detailed setup, all three methods, troubleshooting

### Technical Details
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - 10 minutes  
  What was built, testing results

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Optional deep dive  
  System architecture, data flow, deployment patterns

---

## 🎯 Try It Now (2 minutes)

### Step 1: Start Services
```bash
python start.py
```

### Step 2: Open Web UI
Open in browser: **http://localhost:8501**

### Step 3: Submit Test Application
Fill in the form and click "Process Application"

### Step 4: View Results
See the multi-agent decision making in action!

---

## 🛑 Stop Services

**Python Script:** Press `Ctrl+C`

**Shell Script:** Press `Ctrl+C`

**Docker Compose:** Press `Ctrl+C` or run `docker-compose down`

---

## 📊 Services Overview

### FastAPI (Port 8000)
- REST API backend
- Loan application endpoint
- Health checks
- API documentation

### Streamlit (Port 8501)
- Web UI dashboard
- Submit applications
- View results
- Interactive forms

### Orchestrator
- 4-agent pipeline
- Multi-agent decision making
- Background processing
- Real-time results

### MySQL (Docker only)
- Persistent database
- Application records
- Audit logging

---

## ⚙️ Configuration

Everything is pre-configured in `.env`

To change settings:
```bash
# Edit the configuration
nano .env

# Or copy template
cp .env.example .env
```

**Key settings:**
- `LLMGW_API_KEY` - LLM Gateway API key (required)
- `LLMGW_BASE_URL` - LLM endpoint (already fixed ✅)
- `DATA_SOURCE` - mock (default) or mysql

---

## 🔗 API Quick Test

### Health Check
```bash
curl http://localhost:8000/health
```

### Submit Loan Application
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

## 🐛 Troubleshooting

### "Port already in use"
```bash
# Kill process using port
lsof -i :8000
kill -9 <PID>
```

### "ModuleNotFoundError"
```bash
# Activate virtual environment
source csvenv/bin/activate
pip install -r requirements.txt
```

### "404 from LLM Gateway"
✅ Already fixed in `.env`  
Check: `LLMGW_BASE_URL` should NOT end with `/v1/messages`

**More help:** See [LAUNCH.md#-troubleshooting](LAUNCH.md#-troubleshooting)

---

## 💡 Tips & Tricks

### Use Makefile (if installed)
```bash
make help          # Show all commands
make start         # Start (Python)
make health        # Check health
make test          # Test API
make logs          # View logs (Docker)
```

### View Logs
```bash
# Python/Docker: Shown in terminal

# Shell script:
tail -f /tmp/fastapi.log
tail -f /tmp/streamlit.log
tail -f /tmp/orchestrator.log
```

### Check Service Status
```bash
# Python/Shell
pgrep -f fastapi && echo "Running"

# Docker
docker-compose ps
```

---

## 📖 Next Steps

1. ✅ **Choose Your Method**  
   Python (recommended), Shell, or Docker

2. ✅ **Run It**  
   `python start.py` (or alternatives above)

3. ✅ **Try It**  
   Open http://localhost:8501

4. ✅ **Read Documentation**  
   [QUICK_START.md](QUICK_START.md) (3 min)

5. ✅ **Explore Features**  
   Use the API or web UI

---

## 🎓 Learn More

### For Development Setup
→ [README_LAUNCH.md](README_LAUNCH.md)

### For Production Deployment
→ [LAUNCH.md](LAUNCH.md)

### For Understanding Architecture
→ [ARCHITECTURE.md](ARCHITECTURE.md)

### For Implementation Details
→ [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

---

## 🆘 Need Help?

1. **Quick issue?**  
   → Read [QUICK_START.md](QUICK_START.md)

2. **Setup problem?**  
   → Check [LAUNCH.md#-troubleshooting](LAUNCH.md#-troubleshooting)

3. **Want technical details?**  
   → See [ARCHITECTURE.md](ARCHITECTURE.md)

4. **Still stuck?**  
   → Check logs:
   ```bash
   # Python/Docker: Console output
   # Shell: /tmp/*.log files
   ```

---

## 🎉 You're Ready!

All three launch methods are:
- ✅ Fully implemented
- ✅ Tested and working
- ✅ Documented
- ✅ Production-ready

**Choose one and get started:**

```bash
python start.py          # Recommended for development
```

Then open: **http://localhost:8501**

---

## 📞 Support Matrix

| Need | File | Time |
|------|------|------|
| Quick start | [QUICK_START.md](QUICK_START.md) | 3 min |
| Complete guide | [README_LAUNCH.md](README_LAUNCH.md) | 10 min |
| Troubleshooting | [LAUNCH.md](LAUNCH.md) | Check section |
| Technical details | [ARCHITECTURE.md](ARCHITECTURE.md) | 15 min |
| What was built | [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | 10 min |

---

## ✅ Verification Checklist

After launching, verify:

- [ ] FastAPI started without errors
- [ ] Streamlit started without errors
- [ ] Orchestrator started without errors
- [ ] Can access http://localhost:8501
- [ ] Can access http://localhost:8000/docs
- [ ] Health check responds: `curl http://localhost:8000/health`
- [ ] Can submit test application
- [ ] Decision is returned correctly

---

**Version:** 1.0  
**Status:** Production Ready  
**Last Updated:** June 19, 2026

---

🚀 **Ready? Let's go!**

```bash
cd /home/ubuntu/Documents/LoanManagement
python start.py
```

Then open: http://localhost:8501 🎉
