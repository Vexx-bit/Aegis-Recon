# Post-Installation Testing Guide

## 🎉 **Great! You've Installed All Tools!**

Now let's verify everything is working and run a test scan to see the **FULL intelligence** in action!

---

## ⚠️ **IMPORTANT: Restart Your Terminal First!**

Ruby and Perl won't be recognized until you restart PowerShell/Terminal:

```bash
# Close current PowerShell window
# Open NEW PowerShell window
# Navigate back to project
cd E:\Xampp\htdocs\Aegis Recon
```

---

## ✅ **Step 1: Verify All Tools**

Run these commands in your **NEW terminal**:

### **Check Nmap:**
```bash
nmap --version
```
**Expected:** `Nmap version 7.95` ✅ (Already working!)

### **Check Ruby:**
```bash
ruby --version
```
**Expected:** `ruby 3.2.x` or `ruby 3.3.x`

### **Check Perl:**
```bash
perl --version
```
**Expected:** `This is perl 5, version 38`

### **Check Python:**
```bash
python --version
```
**Expected:** `Python 3.12.x` ✅ (Already working!)

---

## 🔧 **Step 2: Install Tool Dependencies**

### **For WhatWeb (Ruby):**
```bash
cd tools\WhatWeb
gem install bundler
bundle install
```

### **For Nikto (Perl):**
```bash
# Nikto usually works out of the box with Strawberry Perl
# If you get SSL errors later, run:
cpan install Net::SSLeay
cpan install LWP::Protocol::https
```

### **For theHarvester (Python):**
```bash
cd tools\theHarvester
pip install -r requirements.txt
```

---

## 🧪 **Step 3: Test Each Tool Individually**

### **Test WhatWeb:**
```bash
cd E:\Xampp\htdocs\Aegis Recon\tools\WhatWeb
ruby whatweb https://example.com
```
**Expected:** Should show technologies detected (nginx, etc.)

### **Test Nikto:**
```bash
cd E:\Xampp\htdocs\Aegis Recon\tools\nikto\program
perl nikto.pl -h example.com -Tuning 1 -timeout 10
```
**Expected:** Should start scanning and show findings

### **Test theHarvester:**
```bash
cd E:\Xampp\htdocs\Aegis Recon\tools\theHarvester
python theHarvester.py -d example.com -b google
```
**Expected:** Should search for emails and hosts

### **Test Sublist3r:**
```bash
cd E:\Xampp\htdocs\Aegis Recon\tools\Sublist3r
python sublist3r.py -d example.com
```
**Expected:** Should enumerate subdomains

---

## 🚀 **Step 4: Run a Test Scan**

Now let's run a **REAL scan** to see the full intelligence!

### **Option 1: Quick Test (Mock Mode)**
```bash
cd E:\Xampp\htdocs\Aegis Recon
python ai_services/scan_worker_enhanced.py 127.0.0.1 --job-id=test_full_001 --mock
```
**Expected:** Completes in < 5 seconds with mock data

### **Option 2: Real Scan (Your Site)**
**Via Dashboard:**
1. Open: `http://localhost/Aegis%20Recon/frontend/dashboard_enhanced.html`
2. Enter: `rapidwebke.vercel.app`
3. Click: **Start Comprehensive Scan**
4. Watch: Real-time progress tracking!

**Expected Results:**
```
✅ Subdomains: 1 found
✅ Ports: 2 open (80, 443)
✅ Technologies: Vercel, Next.js, React, Golang
✅ Vulnerabilities: 5-10 findings
✅ OSINT: Emails, DNS records
```

---

## 📊 **What You Should See Now**

### **Before (Only Nmap):**
```
rapidwebke.vercel.app
├─ Port 80: http (Vercel)
└─ Port 443: http (Golang)
```

### **After (Full Intelligence):**
```
rapidwebke.vercel.app

🔌 PORTS & SERVICES
├─ Port 80: Vercel HTTP
└─ Port 443: Golang net/http server

💻 TECHNOLOGY STACK
├─ Hosting: Vercel
├─ Framework: Next.js
├─ Runtime: Node.js / Golang
├─ CDN: Vercel Edge Network
├─ SSL: Let's Encrypt
└─ JavaScript: React libraries

🐛 VULNERABILITIES
├─ Missing X-Frame-Options header
├─ Missing Content-Security-Policy
├─ Server version disclosure
├─ No HSTS header
└─ Missing security headers (5 total)

📧 OSINT INTELLIGENCE
├─ DNS Records: A, AAAA, MX, TXT
├─ SSL Certificate: Let's Encrypt
└─ Hosting: Vercel (US)
```

---

## 🐛 **Troubleshooting**

### **Issue: "ruby: command not found"**
**Solution:** 
```bash
# Restart PowerShell/Terminal
# Check Ruby installation path
where ruby
# Should show: C:\Ruby32-x64\bin\ruby.exe
```

### **Issue: "perl: command not found"**
**Solution:**
```bash
# Restart PowerShell/Terminal
# Check Perl installation path
where perl
# Should show: C:\Strawberry\perl\bin\perl.exe
```

### **Issue: WhatWeb "bundler not found"**
**Solution:**
```bash
gem install bundler
cd tools\WhatWeb
bundle install
```

### **Issue: Nikto SSL errors**
**Solution:**
```bash
cpan install Net::SSLeay
cpan install LWP::Protocol::https
```

### **Issue: theHarvester "No module named 'requests'"**
**Solution:**
```bash
cd tools\theHarvester
pip install -r requirements.txt
```

---

## ✅ **Verification Checklist**

Run this checklist after restarting terminal:

```bash
# 1. Check all tools are in PATH
nmap --version          # ✓ Should work
ruby --version          # ✓ Should work after restart
perl --version          # ✓ Should work after restart
python --version        # ✓ Should work

# 2. Test WhatWeb
cd tools\WhatWeb
ruby whatweb --version  # ✓ Should show version

# 3. Test Nikto
cd ..\nikto\program
perl nikto.pl -Version  # ✓ Should show version

# 4. Test theHarvester
cd ..\..\theHarvester
python theHarvester.py -h  # ✓ Should show help

# 5. Test Sublist3r
cd ..\Sublist3r
python sublist3r.py -h  # ✓ Should show help
```

---

## 🎯 **Quick Test Command**

After restarting terminal and verifying tools, run this:

```bash
cd E:\Xampp\htdocs\Aegis Recon

# Test with mock data (instant)
python ai_services/scan_worker_enhanced.py 127.0.0.1 --job-id=test_tools_001 --mock

# Check the log for errors
type C:\Users\ADMINI~1\AppData\Local\Temp\scan_worker_enhanced.log
```

**Look for:**
```
✅ "Running WhatWeb on host" (no errors)
✅ "Running Nikto on host" (no errors)
✅ "Running theHarvester" (no errors)
✅ "Enhanced scan completed successfully"
```

**If you see errors:**
```
❌ "Error running WhatWeb: [WinError 2]" → Ruby not in PATH
❌ "Error running Nikto: [WinError 2]" → Perl not in PATH
```
**Solution:** Restart terminal!

---

## 🚀 **Next Steps**

### **1. Restart Terminal** ⚠️
```bash
# Close current PowerShell
# Open NEW PowerShell
cd E:\Xampp\htdocs\Aegis Recon
```

### **2. Verify Tools**
```bash
ruby --version
perl --version
```

### **3. Install Dependencies**
```bash
# WhatWeb
cd tools\WhatWeb
gem install bundler
bundle install

# theHarvester
cd ..\theHarvester
pip install -r requirements.txt
```

### **4. Run Test Scan**
```bash
cd E:\Xampp\htdocs\Aegis Recon
python ai_services/scan_worker_enhanced.py 127.0.0.1 --job-id=test_001 --mock
```

### **5. Scan Real Target via Dashboard**
```
http://localhost/Aegis%20Recon/frontend/dashboard_enhanced.html
Enter: rapidwebke.vercel.app
Watch: Full intelligence gathering!
```

---

## 🎉 **Expected Results**

Once everything is working, you'll see:

### **Statistics:**
- ✅ 1-5 Subdomains
- ✅ 1-5 Hosts scanned
- ✅ 5-15 Vulnerabilities
- ✅ 0-10 Emails found

### **Technology Stack:**
- ✅ CMS/Framework detected
- ✅ Web server version
- ✅ Programming languages
- ✅ JavaScript libraries
- ✅ CDN/Hosting provider

### **Vulnerabilities:**
- ✅ Missing security headers
- ✅ Server version disclosure
- ✅ SSL/TLS issues
- ✅ Configuration problems

### **OSINT:**
- ✅ Email addresses
- ✅ DNS records
- ✅ Subdomains
- ✅ Certificate details

---

## 📞 **Need Help?**

If you encounter issues:

1. **Check scan logs:**
   ```bash
   type backend\logs\scan_*.log
   ```

2. **Check tool logs:**
   ```bash
   type C:\Users\ADMINI~1\AppData\Local\Temp\scan_worker_enhanced.log
   ```

3. **Verify PATH:**
   ```bash
   echo $env:PATH
   # Should include Ruby, Perl paths
   ```

4. **Restart everything:**
   - Close terminal
   - Close browser
   - Restart XAMPP
   - Open new terminal
   - Try again

---

## 🎯 **Summary**

**Current Status:**
- ✅ Nmap: Installed and working
- ⏳ Ruby: Installed, needs terminal restart
- ⏳ Perl: Installed, needs terminal restart
- ✅ Python: Already working

**Next Actions:**
1. **Restart terminal** (most important!)
2. Verify `ruby --version` and `perl --version`
3. Install tool dependencies
4. Run test scan
5. See FULL intelligence! 🚀

**The difference will be HUGE!** From 2 data points to 50+ intelligence findings!
