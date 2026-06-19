# Loan Management System - Launch Guide

This document describes three ways to launch the Loan Management System with all three services (FastAPI, Streamlit, Orchestrator).

---

## 📋 Prerequisites

### System Requirements
- Python 3.12+
- 4GB RAM minimum
- 2GB disk space
- Internet connection (for LLM Gateway API)

### Required Environment Variables
Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
LLMGW_API_KEY=your_api_key_here
LLMGW_BASE_URL=https://llmgw-wp.tekstac.com
LLMGW_MODEL=global.anthropic.claude-haiku-4-5-20251001-v1:0
```

---

## 🚀 Option 1: Python Script (Recommended for Development)

**Best for:** Development, debugging, and local testing

### Setup
```bash
# Navigate to project root
cd /home/ubuntu/Documents/LoanManagement

# Ensure virtual environment is active (optional)
source csvenv/bin/activate
```

### Launch All Services
```bash
python start.py
```

### What It Does
✅ Validates environment variables  
✅ Starts FastAPI on `http://localhost:8000`  
✅ Starts Streamlit on `http://localhost:8501`  
✅ Starts Orchestrator in background  
✅ Displays real-time logs from all services  
✅ Graceful shutdown on Ctrl+C  

### Access Points
- **API Documentation:** http://localhost:8000/docs
- **API ReDoc:** http://localhost:8000/redoc
- **Web UI:** http://localhost:8501
- **Health Check:** http://localhost:8000/health

### Example Output
```
✅ FastAPI service started
✅ Streamlit app started
✅ Orchestrator started

╔════════════════════════════════════════════════════════════════╗
║                    LOAN MANAGEMENT SYSTEM                      ║
╠════════════════════════════════════════════════════════════════╣
║  🔗 API Documentation: http://localhost:8000/docs             ║
║  🎨 Web Interface: http://localhost:8501                      ║
║  🛑 To stop: Press Ctrl+C                                      ║
╚════════════════════════════════════════════════════════════════╝
```

### Stopping Services
Press `Ctrl+C` to gracefully stop all services.

---

## 🛠️ Option 2: Shell Script (Lightweight)

**Best for:** Quick launches from terminal

### Launch All Services
```bash
cd /home/ubuntu/Documents/LoanManagement
./start.sh
```

### Features
✅ Lightweight bash script  
✅ Log output to `/tmp/*.log` files  
✅ Process IDs displayed for reference  
✅ Color-coded output  
✅ Automatic cleanup on exit  

### View Logs
```bash
# FastAPI logs
tail -f /tmp/fastapi.log

# Streamlit logs
tail -f /tmp/streamlit.log

# Orchestrator logs
tail -f /tmp/orchestrator.log
```

### Manually Stop Services
```bash
# Get the process IDs (shown at startup)
kill <FASTAPI_PID> <STREAMLIT_PID> <ORCHESTRATOR_PID>

# Or use killall
killall python
```

---

## 🐳 Option 3: Docker Compose (Production)

**Best for:** Production deployment, isolated environments, CI/CD

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Setup
```bash
cd /home/ubuntu/Documents/LoanManagement

# Build images
docker-compose build
```

### Launch All Services
```bash
docker-compose up
```

### Launch in Background
```bash
docker-compose up -d
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f fastapi
docker-compose logs -f streamlit
docker-compose logs -f orchestrator
docker-compose logs -f mysql
```

### Access Points (Same as Option 1)
- **API Documentation:** http://localhost:8000/docs
- **Web UI:** http://localhost:8501

### Common Commands

#### Stop All Services
```bash
docker-compose down
```

#### Stop and Remove Volumes (Clean)
```bash
docker-compose down -v
```

#### Rebuild After Code Changes
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

#### Scale Services (if needed)
```bash
docker-compose up -d --scale orchestrator=2
```

#### Check Service Health
```bash
docker-compose ps
docker-compose exec fastapi curl http://localhost:8000/health
```

---

## 📊 API Endpoints

### Health & Info
- `GET /health` - Health check
- `GET /api/agents/info` - Agent information

### Loan Applications
- `POST /api/loan/apply` - Submit loan application

### Example: Submit Application
```bash
curl -X POST http://localhost:8000/api/loan/apply \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "TEST001",
    "age": 35,
    "income": 75000,
    "employment_type": "Salaried",
    "credit_score": 700,
    "loan_amount": 400000,
    "loan_tenure": 60,
    "existing_liabilities": 20000,
    "location": "Delhi"
  }'
```

---

## 🔍 Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000
kill -9 <PID>

# Same for other ports (8501, 3306)
```

### Environment Variables Not Loaded
```bash
# Verify .env exists
cat .env

# For shell script, manually export
export $(cat .env | grep -v '^#' | xargs)
```

### Docker Build Failures
```bash
# Clean rebuild
docker-compose build --no-cache

# Check Docker resources
docker system df

# Remove unused images
docker system prune -a
```

### Services Won't Start
```bash
# Check logs
docker-compose logs --tail=50 fastapi

# Check if ports are free
netstat -tuln | grep -E "8000|8501|3306"
```

### Database Connection Issues
```bash
# Test MySQL connection
docker-compose exec mysql mysql -uroot -p${DB_PASSWORD} -e "SELECT 1;"

# Reset database
docker-compose down -v
docker-compose up
```

---

## 📈 Performance Tuning

### For Python Script
- Adjust timeouts in `start.py` if services are slow
- Run on system with 8GB+ RAM for optimal performance

### For Docker
```bash
# Increase memory limits in docker-compose.yml
services:
  fastapi:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

---

## 🔒 Security Notes

### For Production
1. Change default database passwords in `.env`
2. Use strong API keys
3. Enable HTTPS for production endpoints
4. Use secrets management tools (e.g., HashiCorp Vault)
5. Implement rate limiting
6. Add authentication middleware

### Docker Security
```bash
# Run containers as non-root
# Already implemented in Dockerfile

# Scan images for vulnerabilities
docker scan loan-approval-fastapi
```

---

## 📝 Logs Location

| Method | Location |
|--------|----------|
| Python Script | Console output (real-time) |
| Shell Script | `/tmp/fastapi.log`, `/tmp/streamlit.log`, `/tmp/orchestrator.log` |
| Docker Compose | `docker-compose logs -f` |

---

## 🆘 Getting Help

### Check Logs First
```bash
# Python script
# Logs displayed in real-time in terminal

# Shell script
tail -50 /tmp/*.log

# Docker
docker-compose logs --tail=100 <service_name>
```

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| ModuleNotFoundError | Activate venv: `source csvenv/bin/activate` |
| 404 from LLM Gateway | Check `LLMGW_BASE_URL` in `.env` - remove `/v1/messages` |
| Port already in use | Kill process: `kill -9 $(lsof -ti:8000)` |
| Database errors | Reset: `docker-compose down -v && docker-compose up` |
| Slow startup | Increase timeouts in scripts or wait longer |

---

## ✅ Verification Checklist

After launching, verify everything is working:

- [ ] FastAPI starts without errors
- [ ] Streamlit starts without errors
- [ ] Orchestrator starts without errors
- [ ] FastAPI health check responds: `curl http://localhost:8000/health`
- [ ] Web UI loads: `http://localhost:8501`
- [ ] API docs available: `http://localhost:8000/docs`
- [ ] Can submit test loan application via API or UI

---

## 🎯 Next Steps

1. **Test the System**
   - Use Streamlit UI to submit applications
   - Or use curl to test API endpoints

2. **Monitor Logs**
   - Watch real-time logs during operation
   - Check for any errors or warnings

3. **Scale if Needed**
   - With Docker: `docker-compose up -d --scale service=N`
   - Adjust resource limits as needed

4. **Integrate with External Systems**
   - Configure database connection
   - Set up notification channels
   - Integrate with existing lending systems

---

## 📞 Support

For issues or questions:
1. Check logs (see above)
2. Review troubleshooting section
3. Check `.env.example` for correct configuration
4. Verify all prerequisites are installed

---

**Last Updated:** 2026-06-19  
**Version:** 1.0  
**Status:** Production Ready
