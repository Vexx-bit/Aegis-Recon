# Installing Scanning Tools - Get Full Intelligence

## 🎯 **Current Problem**

Your scan of `rapidwebke.vercel.app` only shows:
```
✅ Open Ports (Nmap working)
❌ No Technologies (WhatWeb not installed)
❌ No Vulnerabilities (Nikto not installed)
❌ No OSINT (theHarvester not installed)
```

**Scan logs show:**
```
ERROR - Error running WhatWeb: [WinError 2] The system cannot find the file specified
ERROR - Error running Nikto: [WinError 2] The system cannot find the file specified
ERROR - Error running theHarvester: [WinError 2] The system cannot find the file specified
```

---

## 🚀 **Solution: Install All Tools**

### **Step 1: Install Ruby (for WhatWeb)**

**Download & Install:**
```
1. Go to: https://rubyinstaller.org/downloads/
2. Download: Ruby+Devkit 3.2.X (x64)
3. Run installer
4. Check "Add Ruby to PATH"
5. Install MSYS2 when prompted
```

**Verify:**
```bash
ruby --version
# Should show: ruby 3.2.x
```

**Install WhatWeb:**
```bash
cd E:\Xampp\htdocs\Aegis Recon\tools\WhatWeb
gem install bundler
bundle install
```

**Test:**
```bash
ruby whatweb --version
```

---

### **Step 2: Install Perl (for Nikto)**

**Download & Install:**
```
1. Go to: https://strawberryperl.com/
2. Download: Strawberry Perl (64-bit)
3. Run installer
4. Default installation is fine
```

**Verify:**
```bash
perl --version
# Should show: This is perl 5.x
```

**Install Nikto Dependencies:**
```bash
cd E:\Xampp\htdocs\Aegis Recon\tools\nikto\program
cpan install LWP::UserAgent
cpan install Net::SSLeay
```

**Test:**
```bash
perl nikto.pl -Version
```

---

### **Step 3: Fix theHarvester Path**

**Check if theHarvester exists:**
```bash
cd E:\Xampp\htdocs\Aegis Recon\tools\theHarvester
dir
```

**If missing, download:**
```bash
cd E:\Xampp\htdocs\Aegis Recon\tools
git clone https://github.com/laramies/theHarvester.git
cd theHarvester
pip install -r requirements.txt
```

**Test:**
```bash
python theHarvester.py -h
```

---

### **Step 4: Verify Nmap (Already Working)**

**Check version:**
```bash
nmap --version
# Should show: Nmap version 7.x
```

✅ **Nmap is already working!** (Your scan found ports successfully)

---

## 🔧 **Quick Installation Script**

Create this PowerShell script to check everything:

**File: `check_tools.ps1`**
```powershell
# Aegis Recon - Tool Installation Checker

Write-Host "=== Aegis Recon Tool Checker ===" -ForegroundColor Cyan
Write-Host ""

# Check Nmap
Write-Host "Checking Nmap..." -ForegroundColor Yellow
try {
    $nmap = nmap --version 2>&1 | Select-String "Nmap version"
    Write-Host "✓ Nmap: $nmap" -ForegroundColor Green
} catch {
    Write-Host "✗ Nmap: NOT FOUND" -ForegroundColor Red
    Write-Host "  Install from: https://nmap.org/download.html" -ForegroundColor Gray
}

# Check Ruby
Write-Host "Checking Ruby..." -ForegroundColor Yellow
try {
    $ruby = ruby --version 2>&1
    Write-Host "✓ Ruby: $ruby" -ForegroundColor Green
} catch {
    Write-Host "✗ Ruby: NOT FOUND" -ForegroundColor Red
    Write-Host "  Install from: https://rubyinstaller.org/" -ForegroundColor Gray
}

# Check Perl
Write-Host "Checking Perl..." -ForegroundColor Yellow
try {
    $perl = perl --version 2>&1 | Select-String "This is perl"
    Write-Host "✓ Perl: $perl" -ForegroundColor Green
} catch {
    Write-Host "✗ Perl: NOT FOUND" -ForegroundColor Red
    Write-Host "  Install from: https://strawberryperl.com/" -ForegroundColor Gray
}

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $python = python --version 2>&1
    Write-Host "✓ Python: $python" -ForegroundColor Green
} catch {
    Write-Host "✗ Python: NOT FOUND" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Tool Files ===" -ForegroundColor Cyan

# Check WhatWeb
$whatweb = "E:\Xampp\htdocs\Aegis Recon\tools\WhatWeb\whatweb"
if (Test-Path $whatweb) {
    Write-Host "✓ WhatWeb: Found" -ForegroundColor Green
} else {
    Write-Host "✗ WhatWeb: NOT FOUND at $whatweb" -ForegroundColor Red
}

# Check Nikto
$nikto = "E:\Xampp\htdocs\Aegis Recon\tools\nikto\program\nikto.pl"
if (Test-Path $nikto) {
    Write-Host "✓ Nikto: Found" -ForegroundColor Green
} else {
    Write-Host "✗ Nikto: NOT FOUND at $nikto" -ForegroundColor Red
}

# Check theHarvester
$harvester = "E:\Xampp\htdocs\Aegis Recon\tools\theHarvester\theHarvester.py"
if (Test-Path $harvester) {
    Write-Host "✓ theHarvester: Found" -ForegroundColor Green
} else {
    Write-Host "✗ theHarvester: NOT FOUND at $harvester" -ForegroundColor Red
}

# Check Sublist3r
$sublist3r = "E:\Xampp\htdocs\Aegis Recon\tools\Sublist3r\sublist3r.py"
if (Test-Path $sublist3r) {
    Write-Host "✓ Sublist3r: Found" -ForegroundColor Green
} else {
    Write-Host "✗ Sublist3r: NOT FOUND at $sublist3r" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Install missing tools to get full scan capabilities!" -ForegroundColor Yellow
```

**Run it:**
```bash
powershell -ExecutionPolicy Bypass -File check_tools.ps1
```

---

## 📊 **What You'll Get After Installation**

### **Before (Current):**
```
rapidwebke.vercel.app
├─ Port 80: http (Vercel)
├─ Port 443: http (Golang)
└─ No other data
```

### **After (Full Intelligence):**
```
rapidwebke.vercel.app
├─ 🔌 PORTS
│   ├─ 80: http (Vercel)
│   └─ 443: https (Golang net/http)
│
├─ 💻 TECHNOLOGIES
│   ├─ Hosting: Vercel
│   ├─ Framework: Next.js / React
│   ├─ CDN: Vercel Edge Network
│   ├─ SSL: Let's Encrypt
│   └─ JavaScript: React, Next.js
│
├─ 🐛 VULNERABILITIES
│   ├─ Missing security headers
│   ├─ Server version disclosure
│   └─ SSL/TLS configuration
│
└─ 📧 OSINT
    ├─ Emails discovered
    ├─ Related subdomains
    └─ DNS records
```

---

## 🎯 **Installation Priority**

### **Priority 1: Ruby (WhatWeb)**
**Impact:** Technology detection
**Time:** 10 minutes
**Benefit:** See CMS, frameworks, languages, CDN, etc.

### **Priority 2: Perl (Nikto)**
**Impact:** Vulnerability scanning
**Time:** 10 minutes
**Benefit:** See security issues, misconfigurations, CVEs

### **Priority 3: theHarvester**
**Impact:** OSINT intelligence
**Time:** 5 minutes
**Benefit:** See emails, subdomains, DNS records

---

## ✅ **Quick Start (30 Minutes)**

```bash
# 1. Install Ruby
# Download from: https://rubyinstaller.org/
# Run installer, check "Add to PATH"

# 2. Install Perl
# Download from: https://strawberryperl.com/
# Run installer

# 3. Verify installations
ruby --version
perl --version

# 4. Test WhatWeb
cd E:\Xampp\htdocs\Aegis Recon\tools\WhatWeb
ruby whatweb https://example.com

# 5. Test Nikto
cd E:\Xampp\htdocs\Aegis Recon\tools\nikto\program
perl nikto.pl -h example.com

# 6. Run a new scan!
# Go to dashboard, scan rapidwebke.vercel.app again
# You'll see FULL intelligence this time!
```

---

## 🚨 **Common Issues**

### **Issue: "ruby: command not found"**
**Solution:** Restart terminal after installing Ruby

### **Issue: "WhatWeb gems missing"**
**Solution:**
```bash
cd tools\WhatWeb
gem install bundler
bundle install
```

### **Issue: "Nikto SSL errors"**
**Solution:**
```bash
cpan install Net::SSLeay
cpan install LWP::Protocol::https
```

### **Issue: "theHarvester not found"**
**Solution:**
```bash
cd tools
git clone https://github.com/laramies/theHarvester.git
cd theHarvester
pip install -r requirements.txt
```

---

## 📋 **Verification Checklist**

After installation, verify each tool:

```bash
# Nmap
nmap --version
✓ Should show version 7.x or higher

# Ruby
ruby --version
✓ Should show ruby 3.x

# Perl
perl --version
✓ Should show perl 5.x

# WhatWeb
cd tools\WhatWeb
ruby whatweb --version
✓ Should show WhatWeb version

# Nikto
cd tools\nikto\program
perl nikto.pl -Version
✓ Should show Nikto version

# theHarvester
cd tools\theHarvester
python theHarvester.py -h
✓ Should show help menu

# Sublist3r
cd tools\Sublist3r
python sublist3r.py -h
✓ Should show help menu
```

---

## 🎉 **After Installation**

**Scan `rapidwebke.vercel.app` again and you'll see:**

✅ **Technology Stack:**
- Vercel hosting
- Next.js framework
- React library
- Golang backend
- CDN details
- SSL/TLS info

✅ **Vulnerabilities:**
- Missing headers
- Security misconfigurations
- SSL/TLS issues
- Version disclosures

✅ **OSINT:**
- Email addresses
- Subdomains
- DNS records
- Certificate details

**From just 2 ports to 50+ data points!** 🚀

---

## 📞 **Need Help?**

If you encounter issues:
1. Check the scan logs: `backend\logs\scan_*.log`
2. Run the tool checker script
3. Verify PATH variables
4. Restart terminal/PowerShell

**The difference will be HUGE once tools are installed!**
