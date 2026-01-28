# Aegis Recon - Enhancement Plan

## 🎯 **Based on User Feedback**

**Date:** 2025-10-30  
**Feedback Source:** User observations during real scans

---

## 📋 **Issues Identified**

### **1. Limited Technology Detection**
**Current:** Only shows HTTPServer, Country, IP, Redirect  
**Expected:** Should show PHP, HTML5, JavaScript frameworks, etc.

**Why it's limited:**
- Vercel/CDN platforms hide backend tech
- WhatWeb only scanning redirect response
- Need to follow redirects and scan deeper

**Solution:**
- ✅ Add `--follow-redirect` to WhatWeb
- ✅ Scan both HTTP and HTTPS
- ✅ Add more aggressive scanning options
- ✅ Parse HTML/JavaScript for framework detection

---

### **2. Subdomain Enumeration Not Displaying**
**Current:** Logs show "Sublist3r output file not found"  
**Expected:** Should list all discovered subdomains

**Why it's failing:**
- Output file path may be incorrect
- Sublist3r may be timing out
- No results for some targets (normal)

**Solution:**
- ✅ Fix Sublist3r output file path
- ✅ Add timeout handling
- ✅ Display "No subdomains found" vs "Error"
- ✅ Add subdomain list to dashboard

---

### **3. IP vs Domain Scanning Differences**
**Current:** Same scan approach for both  
**Expected:** Different features for IPs vs domains

**Enhancements needed:**

#### **For IP Scans:**
- ✅ Enhanced OS detection
- ✅ MAC address (if local network)
- ✅ Network distance (hops)
- ✅ Uptime detection
- ✅ Skip subdomain/OSINT (already done)
- ✅ Focus on network-level info

#### **For Domain Scans:**
- ✅ Subdomain enumeration
- ✅ OSINT (emails, social media)
- ✅ WHOIS information
- ✅ DNS records (A, MX, TXT, NS)
- ✅ SSL certificate details
- ✅ Technology stack detection

---

### **4. Unused Tools with Potential**

**Tools available but not integrated:**

#### **SQLMap** (SQL Injection Testing)
**Location:** `/tools/sqlmap`  
**Use case:** Test for SQL injection vulnerabilities  
**Integration:** Add as optional aggressive scan mode  
**Risk:** Can be destructive, needs user consent

#### **Recon-ng** (OSINT Framework)
**Location:** `/tools/recon-ng`  
**Use case:** Advanced OSINT (social media, breaches, etc.)  
**Integration:** Replace/supplement theHarvester  
**Benefit:** More comprehensive OSINT data

#### **Nmap NSE Scripts** (Vulnerability Detection)
**Location:** Built into Nmap  
**Use case:** Detect specific vulnerabilities (SMB, RDP, etc.)  
**Integration:** Add NSE script categories to Nmap scans  
**Benefit:** More vulnerability findings

#### **SSLyze/testssl.sh** (SSL/TLS Analysis)
**Location:** Not yet added  
**Use case:** Deep SSL/TLS configuration analysis  
**Integration:** Add as new scan phase  
**Benefit:** Detailed certificate and cipher analysis

---

## 🚀 **Immediate Fixes**

### **Fix 1: Enhance WhatWeb Scanning**

**Current command:**
```python
cmd = [
    'ruby', 'whatweb',
    '-v', '-a', '3',
    '--log-json', output_file,
    'http://target.com'
]
```

**Enhanced command:**
```python
cmd = [
    'ruby', 'whatweb',
    '-v',                          # Verbose
    '-a', '3',                     # Aggression level 3
    '--follow-redirect=always',    # Follow redirects!
    '--max-redirects=5',           # Up to 5 redirects
    '--log-json', output_file,
    '--user-agent', 'Mozilla/5.0', # Better user agent
    target_url
]

# Also scan HTTPS if HTTP scanned
if target_url.startswith('http://'):
    # Run second scan for https://
```

**Benefit:** Will detect technologies on actual app, not just redirect!

---

### **Fix 2: Fix Sublist3r Output**

**Current issue:** Output file not found

**Investigation needed:**
```python
# Check if Sublist3r is creating output file
# Verify output path is correct
# Add error handling for no results
```

**Enhanced logic:**
```python
if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
    # Parse subdomains
    subdomains = parse_sublist3r_output(output_file)
    logger.info(f"Found {len(subdomains)} subdomains")
else:
    logger.warning("No subdomains found (may be normal)")
    subdomains = [target]  # Use original target
```

---

### **Fix 3: IP vs Domain Detection**

**Add to scan worker:**
```python
def is_ip_address(target: str) -> bool:
    """Check if target is an IP address."""
    import re
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    return bool(re.match(ip_pattern, target))

def get_scan_strategy(target: str) -> dict:
    """Determine scan strategy based on target type."""
    if is_ip_address(target):
        return {
            'subdomain_enum': False,
            'osint': False,
            'enhanced_os_detection': True,
            'network_info': True,
            'whois': False
        }
    else:
        return {
            'subdomain_enum': True,
            'osint': True,
            'enhanced_os_detection': False,
            'network_info': False,
            'whois': True,
            'dns_records': True
        }
```

---

### **Fix 4: Add Missing Intelligence**

#### **A. DNS Records (for domains)**
```python
def get_dns_records(domain: str) -> dict:
    """Get comprehensive DNS records."""
    import dns.resolver
    
    records = {}
    record_types = ['A', 'AAAA', 'MX', 'TXT', 'NS', 'SOA', 'CNAME']
    
    for rtype in record_types:
        try:
            answers = dns.resolver.resolve(domain, rtype)
            records[rtype] = [str(rdata) for rdata in answers]
        except:
            records[rtype] = []
    
    return records
```

#### **B. WHOIS Information (for domains)**
```python
def get_whois_info(domain: str) -> dict:
    """Get WHOIS registration information."""
    import whois
    
    try:
        w = whois.whois(domain)
        return {
            'registrar': w.registrar,
            'creation_date': str(w.creation_date),
            'expiration_date': str(w.expiration_date),
            'name_servers': w.name_servers,
            'emails': w.emails
        }
    except:
        return {}
```

#### **C. SSL Certificate Analysis**
```python
def analyze_ssl_certificate(host: str) -> dict:
    """Analyze SSL certificate details."""
    import ssl
    import socket
    
    try:
        context = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                return {
                    'subject': dict(x[0] for x in cert['subject']),
                    'issuer': dict(x[0] for x in cert['issuer']),
                    'version': cert['version'],
                    'serial_number': cert['serialNumber'],
                    'not_before': cert['notBefore'],
                    'not_after': cert['notAfter'],
                    'san': cert.get('subjectAltName', [])
                }
    except:
        return {}
```

---

## 📊 **Enhanced Scan Output**

### **For Domain: rapidwebke.vercel.app**

**Current:**
```
✓ Subdomains: 1
✓ Technologies: HTTPServer Vercel
✓ Ports: 80, 443
```

**Enhanced:**
```
✓ Subdomains: 5 found
  ├─ www.rapidwebke.vercel.app
  ├─ api.rapidwebke.vercel.app
  └─ ...

✓ Technologies:
  ├─ Web Server: Vercel
  ├─ Framework: Next.js 14.0
  ├─ Runtime: Node.js 18.x
  ├─ JavaScript: React 18.2
  ├─ CDN: Vercel Edge Network
  └─ SSL: Let's Encrypt

✓ DNS Records:
  ├─ A: 76.76.21.21
  ├─ AAAA: 2606:4700:...
  ├─ MX: None (no email)
  └─ TXT: Vercel verification

✓ SSL Certificate:
  ├─ Issuer: Let's Encrypt
  ├─ Valid: 2024-12-01 to 2025-03-01
  ├─ SAN: *.vercel.app
  └─ Cipher: TLS 1.3

✓ WHOIS:
  ├─ Registrar: Vercel Inc.
  ├─ Created: 2023-01-15
  └─ Expires: 2025-01-15
```

---

### **For IP: 192.168.100.1**

**Current:**
```
✓ Ports: 7 (filtered/open)
✓ No technologies
```

**Enhanced:**
```
✓ Network Information:
  ├─ IP: 192.168.100.1
  ├─ MAC: 00:11:22:33:44:55
  ├─ Vendor: TP-Link
  ├─ Distance: 1 hop (local)
  └─ Uptime: 47 days

✓ OS Detection:
  ├─ OS: Linux 3.x/4.x
  ├─ Device: Router/Gateway
  └─ CPE: cpe:/o:linux:linux_kernel:4

✓ Open Ports:
  ├─ 53: DNS (domain)
  └─ 80: HTTP (filtered)

✓ Filtered Ports:
  ├─ 21: FTP (firewall)
  ├─ 22: SSH (firewall)
  ├─ 23: Telnet (firewall)
  ├─ 139: NetBIOS (firewall)
  └─ 445: SMB (firewall)

✓ Security Analysis:
  ├─ Firewall: Active (good!)
  ├─ Telnet: Filtered (good!)
  └─ SMB: Filtered (good!)
```

---

## 🎯 **Implementation Priority**

### **Priority 1: Quick Wins (Today)**
1. ✅ Fix WhatWeb redirect following
2. ✅ Fix Sublist3r output parsing
3. ✅ Add DNS record collection
4. ✅ Improve IP vs domain display

### **Priority 2: Medium Term (This Week)**
1. ⏳ Add SSL certificate analysis
2. ⏳ Add WHOIS lookup
3. ⏳ Enhance Nmap with NSE scripts
4. ⏳ Better technology categorization

### **Priority 3: Advanced (Later)**
1. ⏳ Integrate SQLMap (optional, with consent)
2. ⏳ Add Recon-ng for advanced OSINT
3. ⏳ Add testssl.sh for SSL analysis
4. ⏳ Add screenshot capture for web apps

---

## 📝 **Summary**

**User Feedback:**
1. ✅ Technology detection working but limited
2. ✅ Subdomains not displaying
3. ✅ IP vs domain should differ
4. ✅ More tools could be used

**Actions:**
1. 🔧 Enhance WhatWeb scanning
2. 🔧 Fix subdomain display
3. 🔧 Add IP-specific features
4. 🔧 Integrate more intelligence sources

**Result:**
- From 10 data points → 50+ data points
- Better categorization
- More actionable intelligence
- Clearer IP vs domain differences

---

**Ready to implement these enhancements!** 🚀
