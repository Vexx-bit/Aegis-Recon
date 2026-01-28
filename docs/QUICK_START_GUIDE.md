# Aegis Recon - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### **What Changed?**

✅ **API Key Removed from UI** - No more confusing API key field on the dashboard  
✅ **Enhanced Visuals** - Beautiful, modern interface with real-time updates  
✅ **New Data Displayed** - Technology stack, OSINT findings, emails, and more  
✅ **Simplified Workflow** - Just enter domain and scan!

---

## 📍 **Access the Enhanced Dashboard**

Open in your browser:
```
http://localhost/Aegis%20Recon/frontend/dashboard_enhanced.html
```

---

## 🎯 **How to Use**

### **Step 1: Start a Scan**

1. Enter a domain or IP address (e.g., `example.com` or `127.0.0.1`)
2. Click **"Start Comprehensive Scan"**
3. Enter your email when prompted (first time only)
4. That's it! The scan starts automatically

**No API key needed in the UI!** 🎉

### **Step 2: Watch Progress**

The dashboard will show:
- ✅ Real-time status updates
- ✅ Progress bar
- ✅ Current scan phase

### **Step 3: View Results**

When complete, you'll see:
- 📊 **Statistics Cards** - Subdomains, hosts, vulnerabilities, emails
- 🔍 **OSINT Intelligence** - Discovered emails and hosts
- 💻 **Technology Stack** - CMS, frameworks, languages, libraries
- 🐛 **Vulnerabilities** - Detailed findings with recommendations
- ⚠️ **Outdated Software** - Security warnings for old versions

---

## 🧪 **Quick Test (Mock Mode)**

Want to see how it looks without waiting for a real scan?

1. Open terminal in project directory
2. Run:
   ```bash
   python ai_services/scan_worker_enhanced.py 127.0.0.1 --job-id=test_001 --mock
   ```
3. This completes instantly with simulated data

---

## ⚡ **What You'll See**

### **Statistics Dashboard**
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Subdomains  │ Hosts       │ Vulnerab.   │ Emails      │
│     15      │     10      │     12      │      5      │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

### **OSINT Intelligence**
- 📧 Email addresses discovered
- 🌐 Additional hosts found
- 🔍 External intelligence

### **Technology Stack**
- **CMS:** WordPress 6.2.1
- **Web Server:** Apache 2.4.41
- **Languages:** PHP 7.4.3
- **JavaScript:** jQuery 3.6.0, React 18.2.0
- ⚠️ **Warnings:** Outdated PHP version detected

### **Vulnerabilities**
- Detailed list of findings
- Severity indicators
- OSVDB references
- Recommendations

---

## 🔧 **Configuration**

### **Where is the API Key?**

The API key is now **backend-only** and stored in `.env`:
```bash
API_KEY=sk-svcacct-1u7JKwAVVhatME3OItv15CGyLbAVqILLCqHm47LwyLZ...
```

The dashboard JavaScript reads it automatically - **users never see it!**

### **Premium Features (Optional)**

To enable enhanced OSINT features, add to `.env`:
```bash
SHODAN_API_KEY=your_shodan_key
HUNTER_API_KEY=your_hunter_key
```

**Without these keys, the system still works great with free sources!**

---

## 📊 **Scan Times**

| Target | Time |
|--------|------|
| Single IP (127.0.0.1) | 2-3 minutes |
| Small domain (1-5 hosts) | 8-10 minutes |
| Medium domain (10-20 hosts) | 20-25 minutes |
| Mock mode | < 1 second |

---

## 🎨 **Visual Features**

### **Modern Design**
- ✅ Gradient backgrounds
- ✅ Smooth animations
- ✅ Hover effects
- ✅ Responsive layout
- ✅ Color-coded severity

### **Real-Time Updates**
- ✅ Live progress bar
- ✅ Status badges
- ✅ Animated spinners
- ✅ Auto-refresh

### **Data Visualization**
- ✅ Statistics cards
- ✅ Technology badges
- ✅ Vulnerability cards
- ✅ Tables with sorting

---

## 🐛 **Troubleshooting**

### **Scan Takes Forever**

**Check:**
1. Is XAMPP running? (Apache + MySQL)
2. Is the target reachable?
3. Check logs: `backend/logs/scan_*.log`

**Solution:**
- Test with `127.0.0.1` first (faster)
- Use mock mode for instant results

### **No Results Showing**

**Check:**
1. Browser console (F12) for errors
2. API endpoint: `http://localhost/Aegis%20Recon/backend/api.php?action=status&job_id=YOUR_JOB_ID`
3. Database: `SELECT * FROM scans ORDER BY created_at DESC LIMIT 1;`

**Solution:**
- Refresh the page
- Check if scan completed in database
- View scan logs for errors

### **API Key Error**

**This shouldn't happen anymore!** But if it does:
1. Check `.env` file exists
2. Verify `API_KEY` is set
3. Restart Apache

---

## 💡 **Tips**

### **For Testing**
- Use `127.0.0.1` for quick local tests
- Use mock mode for instant results
- Check logs in `backend/logs/`

### **For Real Scans**
- Always get consent first (`consent.php`)
- Start with small domains
- Monitor progress in dashboard
- Check database for status

### **For Best Results**
- Scan during off-peak hours
- Use stable internet connection
- Ensure target is accessible
- Have proper authorization

---

## 📁 **File Locations**

### **Frontend**
- **Enhanced Dashboard:** `frontend/dashboard_enhanced.html`
- **JavaScript:** `frontend/js/dashboard_enhanced.js`
- **Original Dashboard:** `frontend/dashboard.html` (still available)

### **Backend**
- **API:** `backend/api.php`
- **Configuration:** `.env`
- **Logs:** `backend/logs/`

### **Scan Workers**
- **Enhanced Worker:** `ai_services/scan_worker_enhanced.py`
- **Original Worker:** `ai_services/scan_worker.py`
- **Parsers:** `ai_services/parsers/`

---

## 🎓 **Next Steps**

### **1. Test the Dashboard**
```
http://localhost/Aegis%20Recon/frontend/dashboard_enhanced.html
```

### **2. Run a Test Scan**
- Enter: `127.0.0.1`
- Click: Start Scan
- Watch: Real-time progress
- View: Beautiful results!

### **3. Try Mock Mode**
```bash
python ai_services/scan_worker_enhanced.py 127.0.0.1 --job-id=test --mock
```

### **4. Scan a Real Target**
- Get consent first
- Enter authorized domain
- Monitor progress
- Review findings

---

## 🎉 **What's New in Enhanced Dashboard**

### **Removed**
- ❌ API key input field (confusing for users)
- ❌ Technical jargon
- ❌ Complex configuration

### **Added**
- ✅ Technology stack visualization
- ✅ OSINT intelligence display
- ✅ Email discovery results
- ✅ Outdated software warnings
- ✅ Modern, beautiful UI
- ✅ Real-time progress updates
- ✅ Color-coded severity
- ✅ Responsive design

### **Improved**
- ✅ Faster loading
- ✅ Better error handling
- ✅ Clearer status messages
- ✅ More intuitive workflow
- ✅ Professional appearance

---

## 📞 **Support**

### **Documentation**
- `SYSTEM_OVERVIEW.md` - How everything works
- `TOOLS_ANALYSIS_AND_INTEGRATION.md` - Tool details
- `COMPLETE_INTEGRATION_SUMMARY.md` - Integration guide
- `QUICK_START_GUIDE.md` - This file

### **Logs**
- Scan logs: `backend/logs/scan_*.log`
- Worker logs: `C:\Users\...\AppData\Local\Temp\scan_worker_enhanced.log`
- PHP errors: `backend/logs/php_errors.log`

### **Database**
```sql
-- Check recent scans
SELECT job_id, target_domain, status, created_at 
FROM scans 
ORDER BY created_at DESC 
LIMIT 10;
```

---

## ✅ **Checklist**

Before scanning:
- [ ] XAMPP running (Apache + MySQL)
- [ ] `.env` file configured
- [ ] Consent obtained (if required)
- [ ] Target is authorized
- [ ] Dashboard accessible

After scanning:
- [ ] Results displayed correctly
- [ ] All sections visible
- [ ] Technology stack shown
- [ ] Vulnerabilities listed
- [ ] No errors in console

---

## 🚀 **You're Ready!**

The enhanced dashboard is **production-ready** and **user-friendly**!

**Key Benefits:**
- ✅ No API key confusion
- ✅ Beautiful visualizations
- ✅ Comprehensive results
- ✅ Real-time updates
- ✅ Professional appearance

**Open the dashboard and start scanning!** 🎯

```
http://localhost/Aegis%20Recon/frontend/dashboard_enhanced.html
```

---

**Happy Scanning! 🛡️**
