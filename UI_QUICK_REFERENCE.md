# 🎨 Streamlit UI - Quick Reference Guide

## 🚀 Quick Start

```bash
# Navigate to project
cd /home/ubuntu/Documents/LoanManagement

# Start the app
streamlit run loan-approval-system/streamlit_app/app.py

# Access in browser
http://localhost:8501
```

---

## 📱 Interface Overview

### Main Screen Layout

```
┌─────────────────────────────────────────────────────────┐
│ Sidebar         │ Left Column  │ Middle Column │ Right  │
│ • Navigation    │ • Chat       │ • Form        │ Column │
│ • Status        │ • Messages   │ • Input       │ •      │
│ • Links         │ • Input      │ • Validation  │ Result │
│                 │              │ • Submit      │        │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Three Main Pages

### 1. 💬 Chat & Apply (Default)
**Purpose:** Submit loan applications and get instant decisions

**Features:**
- Live chat with AI assistant
- Application form with validation
- Real-time decision display
- Gradient decision cards

**How to use:**
1. Read welcome message in chat
2. Fill form: Personal → Financial → Credit & Loan
3. Click "🚀 Submit Application"
4. View decision on right column
5. Chat updates with summary

**Form Sections:**
```
Personal Information
├─ Applicant ID (auto-generated if blank)
├─ Age (18-70 years)
└─ Location

Financial Information
├─ Monthly Income (₹)
├─ Employment Type (dropdown)
└─ Monthly Liabilities (₹)

Credit & Loan Details
├─ Credit Score (300-900)
├─ Loan Amount (₹)
└─ Tenure (6-360 months)
```

---

### 2. 📊 Dashboard (Analysis)
**Purpose:** Detailed analysis and agent outputs

**Sections:**
1. **Applicant Summary** - Complete profile
2. **Agent Analysis Tabs** - 4 detailed tabs
3. **Raw JSON** - Complete response
4. **Export** - Download report

**Agent Tabs:**
```
Tab 1: Profile Agent (Haiku - Fast)
  ├─ Income Stability Score
  ├─ Employment Risk
  ├─ Credit History Summary
  └─ Completeness Status

Tab 2: Risk Agent (Sonnet - Powerful)
  ├─ DTI Ratio
  ├─ Credit Risk Level
  ├─ Loan Amount Risk
  ├─ Anomalies
  └─ Detailed Reasoning

Tab 3: Decision Agent (Sonnet - Powerful)
  ├─ Classification
  ├─ Risk Score
  ├─ Confidence Level
  ├─ Key Factors
  └─ Full Explanation

Tab 4: Compliance Agent (Haiku - Fast)
  ├─ Action Taken
  ├─ Case ID
  ├─ Notification Status
  ├─ Checklist
  └─ Summary
```

---

### 3. ℹ️ System Info (Help)
**Purpose:** Documentation and system information

**Content:**
- Architecture overview
- Supported operations
- API endpoints
- Documentation links

---

## 🎨 Color Coding

### Decision Cards

| Decision | Color | Emoji | Meaning |
|----------|-------|-------|---------|
| APPROVED | Green Gradient | ✅ | Loan approved automatically |
| REJECTED | Red Gradient | ❌ | Loan rejected automatically |
| MANUAL_REVIEW | Orange Gradient | ⏳ | Requires manual review |

### Credit Score Indicators

| Score | Indicator | Color | Status |
|-------|-----------|-------|--------|
| 750+ | 🟢 Excellent | Green | Very Good |
| 700-749 | 🟢 Good | Green | Good |
| 650-699 | 🟡 Fair | Yellow | Average |
| 580-649 | 🔴 Poor | Red | Below Average |
| <580 | 🔴 Very Poor | Red | Bad |

### Risk Level Indicators

| Score | Indicator | Color | Status |
|-------|-----------|-------|--------|
| 0-25 | 🟢 Low Risk | Green | Safe |
| 25-50 | 🟡 Medium Risk | Yellow | Moderate |
| 50-75 | 🟠 High Risk | Orange | Risky |
| 75+ | 🔴 Critical Risk | Red | Very Risky |

---

## 📊 Key Metrics Display

### Decision Card Metrics

```
┌──────────────┬────────────┬──────────┬──────────────┐
│ Risk Score   │ Confidence │ Case ID  │ Notification │
│ 0-100        │ 0-100%     │ ID-XXXX  │ Sent/Pending │
└──────────────┴────────────┴──────────┴──────────────┘
```

### Applicant Summary (4 Columns)

```
Column 1: Basic Info
├─ Applicant ID
├─ Age
└─ Location

Column 2: Income & Credit
├─ Income
├─ Employment
└─ Credit Score with indicator

Column 3: Loan Details
├─ Loan Amount
├─ Tenure
└─ Calculated EMI

Column 4: Debt Metrics
├─ Existing Liabilities
├─ Total Monthly Debt
└─ DTI Ratio with indicator
```

---

## 🤖 Agent Badges

```
Claude Haiku (Fast)     → Light Blue Badge
Claude Sonnet (Powerful) → Light Pink Badge
```

---

## 💬 Chat Interface

### Chat Features
- **Message History** - All messages persisted
- **User Messages** - Marked with 👤 avatar
- **Bot Messages** - Marked with 🤖 avatar
- **Chat Input** - Bottom input field
- **Markdown Support** - **bold**, *italic*, `code`, etc.

### Bot Response Types
1. **Welcome** - Initial greeting
2. **Instruction** - Guide user to form
3. **Submission Confirmation** - After form submit
4. **Decision Summary** - After getting result

---

## 📋 Application Form Tips

### Input Validation
```
Age:           18-70 years (slider)
Income:        ₹1,000+ (currency input)
Employment:    Dropdown selection
Credit Score:  300-900 (slider)
Loan Amount:   ₹10,000+ (currency)
Tenure:        6-360 months (slider)
```

### Smart Defaults
```
Applicant ID:  APP (auto-fills with timestamp)
Age:           32 years
Income:        ₹85,000/month
Employment:    Salaried
Credit Score:  720
Loan Amount:   ₹500,000
Tenure:        60 months
Liabilities:   ₹15,000/month
Location:      Mumbai
```

---

## 🚀 User Workflows

### Workflow 1: Quick Decision (5 min)
```
1. Open Streamlit (http://localhost:8501)
2. Read welcome message
3. Modify form values if needed
4. Click "Submit Application"
5. View decision card
6. Done! ✅
```

### Workflow 2: Full Analysis (10 min)
```
1. Complete Workflow 1
2. Switch to "Dashboard" tab
3. Review "Applicant Summary"
4. Click agent tabs to explore
5. Download report if needed
6. Done! ✅
```

### Workflow 3: System Check (3 min)
```
1. Check sidebar for API status
2. Click "Health Check" button
3. View system information
4. Switch to "System Info" tab
5. Review documentation
6. Done! ✅
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Enter | Submit form in chat |
| Tab | Navigate form fields |
| Ctrl+R | Refresh page |
| Escape | Close expandables |

---

## 📥 Export Features

### Download Report
```
File Name:     loan_decision_APP001.json
Location:      Downloads folder
Format:        JSON (machine-readable)
Contents:      Complete decision + all agent analysis
```

### New Application
```
Button Location: Dashboard tab
Action:         Clears form and resets chat
Result:         Ready for next applicant
```

---

## 🔧 Sidebar Functions

### Navigation
- **💬 Chat & Apply** - Go to main interface
- **📊 Dashboard** - Go to analysis view
- **ℹ️ System Info** - Go to documentation

### System Status
- **Green ✅** - API is healthy
- **Red ❌** - API is down

### Quick Links
- **📖 API Docs** - Opens http://localhost:8000/docs
- **🏥 Health Check** - Runs health check and shows result

---

## 🎨 Visual Elements

### Decision Cards
```
✅ APPROVED          ❌ REJECTED          ⏳ REQUIRES MANUAL REVIEW
[Green Gradient]     [Red Gradient]       [Orange Gradient]
100% confidence      5% chance            Will review in 24h
```

### Factor Items
```
┌──────────────────────────────────────────┐
│ • Strong credit profile with score 750   │
│ • Low DTI ratio at 27.45%                │
│ • Stable employment for 5+ years        │
└──────────────────────────────────────────┘
```

### Agent Tabs
```
╔═══════════╦═══════════╦═══════════╦═══════════╗
║ Profile   ║ Risk      ║ Decision  ║ Compliance║
║ Agent     ║ Agent     ║ Agent     ║ Agent     ║
╚═══════════╩═══════════╩═══════════╩═══════════╝
```

---

## 🐛 Troubleshooting

### Issue: Cannot connect to API
**Solution:** 
1. Check if FastAPI is running: `python start.py`
2. Verify port 8000 is available: `lsof -i :8000`
3. Restart Streamlit: `Ctrl+C` and run again

### Issue: Form not submitting
**Solution:**
1. Check input validation (green checkmarks on fields)
2. Fill all required fields
3. Check browser console for errors
4. Clear browser cache and refresh

### Issue: Decision card not appearing
**Solution:**
1. Check API response: Open browser dev tools (F12)
2. Check Network tab for /api/loan/apply call
3. Verify response status (should be 200)
4. Check for error message in red alert box

### Issue: Dashboard not loading
**Solution:**
1. Ensure you've submitted an application first
2. Check "Chat & Apply" tab first
3. Then switch to "Dashboard" tab
4. Use "New Application" button to reset if needed

### Issue: Download not working
**Solution:**
1. Check browser download settings
2. Allow downloads from localhost
3. Try different browser if issue persists
4. Check popup blocker is disabled

---

## 📞 Help Resources

| Topic | Location |
|-------|----------|
| Quick Start | START_HERE.md |
| Setup Help | README_LAUNCH.md |
| API Docs | http://localhost:8000/docs |
| Architecture | ARCHITECTURE.md |
| Improvements | IMPROVEMENTS_RECOMMENDED.md |
| UI Details | STREAMLIT_UI_IMPROVEMENTS.md |

---

## ✅ Feature Checklist

### Core Features
- [x] Multi-page navigation
- [x] Chat interface with history
- [x] Application form with validation
- [x] Decision display with cards
- [x] Applicant profile summary
- [x] Agent analysis tabs
- [x] Export/Download features
- [x] Responsive design

### Visual Features
- [x] Gradient decision cards
- [x] Color-coded indicators
- [x] Agent badges
- [x] Currency formatting
- [x] Emoji indicators
- [x] Professional layout

### Functional Features
- [x] Real-time processing
- [x] Error handling
- [x] Input validation
- [x] Session persistence
- [x] Page routing
- [x] API integration

---

## 🎯 Performance

| Metric | Value |
|--------|-------|
| Page Load | <1 second |
| Form Submit | <5 seconds |
| Decision Processing | <120 seconds |
| Chat Response | Instant |
| Export | <1 second |

---

## 📱 Browser Compatibility

| Browser | Status | Notes |
|---------|--------|-------|
| Chrome | ✅ Full support | Recommended |
| Firefox | ✅ Full support | Good |
| Safari | ✅ Full support | Good |
| Edge | ✅ Full support | Good |
| Mobile | ⚠️ Limited | Responsive but best on desktop |

---

## 🔐 Security Notes

- No sensitive data is stored locally
- All communication uses HTTP (upgrade to HTTPS for production)
- API key is secure in backend
- Chat history cleared on session end
- Download files are temporary

---

## 📚 Documentation Links

**In-App:**
- System Info tab → API Endpoints
- System Info tab → Documentation

**Project Files:**
- STREAMLIT_UI_IMPROVEMENTS.md - Detailed UI guide
- IMPROVEMENTS_RECOMMENDED.md - Enhancement roadmap
- ARCHITECTURE.md - System architecture
- README_LAUNCH.md - Complete launch guide

---

## 🎉 Summary

The Streamlit UI provides:
- ✨ Professional, modern appearance
- 🎨 Intuitive 3-page navigation
- 💬 Interactive chat interface
- 📋 Comprehensive form handling
- 📊 Detailed decision display
- 👤 Complete applicant analysis
- 🤖 Multi-agent insights
- 📥 Export capabilities
- 📱 Responsive design
- 🚀 Production-ready

**Version:** 2.0  
**Status:** Complete & Ready  
**Last Updated:** June 20, 2026

---

**Happy Loan Processing! 🏦**
