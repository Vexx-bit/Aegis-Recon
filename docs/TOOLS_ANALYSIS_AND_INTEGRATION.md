# Aegis Recon - Tools Analysis & Integration Plan

## 📋 Available Tools Analysis

Based on the tools in your `tools/` directory, here's what we have and how we can integrate them:

---

## 🔍 Tool #1: Sublist3r (Subdomain Enumeration)

### **What It Does**
- **Primary Function:** Subdomain enumeration using OSINT
- **Data Sources:** 
  - Google, Yahoo, Bing, Ask, Baidu (search engines)
  - Netcraft, DNSdumpster, VirusTotal
  - ThreatCrowd, CRT.sh (SSL certificates)
  - PassiveDNS
- **Features:**
  - Multi-threaded enumeration
  - Brute-force capability (with subbrute)
  - Port scanning of discovered subdomains
  - Multiple search engine support

### **Current Status in Aegis Recon**
✅ **Already Integrated** - Called in `scan_worker.py` line ~100

### **Available Features We Can Adopt**

#### **1. Multi-Source Enumeration** ⭐⭐⭐
**What:** Query 10+ different sources for subdomains
**Benefit:** More comprehensive subdomain discovery
**Implementation:**
```python
# Currently we just call sublist3r.py
# We can enable specific engines:
engines = [
    GoogleEnum, YahooEnum, BingEnum, 
    Virustotal, DNSdumpster, CrtSearch,
    ThreatCrowd, Netcraft
]
```

#### **2. Brute-Force Mode** ⭐⭐
**What:** Dictionary-based subdomain brute-forcing
**Benefit:** Discover subdomains not indexed by search engines
**Implementation:**
```python
# Enable brute-force with wordlist
python sublist3r.py -d example.com -b -t 50
```

#### **3. Port Scanning Integration** ⭐
**What:** Built-in port scanner for discovered subdomains
**Benefit:** Quick port check without separate Nmap call
**Implementation:**
```python
# Scan common ports on discovered subdomains
python sublist3r.py -d example.com -p 80,443,8080,8443
```

### **Recommended Integration**
```python
def run_sublist3r_enhanced(domain: str, job_id: str, enable_bruteforce: bool = False):
    """Enhanced Sublist3r with multiple engines."""
    
    cmd = [
        'python', 
        'tools/Sublist3r-master/sublist3r.py',
        '-d', domain,
        '-o', f'/tmp/subdomains-{job_id}.txt',
        '-t', '50',  # 50 threads for faster enumeration
        '-v'  # Verbose output
    ]
    
    if enable_bruteforce:
        cmd.extend(['-b'])  # Enable brute-force
    
    # Optional: Enable specific engines
    # cmd.extend(['-e', 'google,virustotal,dnsdumpster,crtsh'])
    
    subprocess.run(cmd, capture_output=True, text=True)
```

---

## 🔍 Tool #2: theHarvester (OSINT & Email Harvesting)

### **What It Does**
- **Primary Function:** OSINT data gathering
- **Collects:**
  - Email addresses
  - Subdomains
  - Hosts
  - Employee names
  - Open ports
  - Banners
- **Data Sources:**
  - Google, Bing, Yahoo
  - Shodan, Censys
  - LinkedIn, Twitter
  - Hunter.io, SecurityTrails
  - And 30+ more sources

### **Current Status in Aegis Recon**
❌ **Not Integrated** - Available but not used

### **Available Features We Can Adopt**

#### **1. Email Address Discovery** ⭐⭐⭐
**What:** Find email addresses associated with domain
**Benefit:** Identify potential targets for social engineering awareness
**Use Case:** Security awareness training, phishing simulation prep
**Implementation:**
```bash
python theHarvester.py -d example.com -b google,bing,hunter -l 500
```

#### **2. Employee Name Enumeration** ⭐⭐
**What:** Discover employee names from LinkedIn, social media
**Benefit:** Understand organizational structure, identify key personnel
**Use Case:** Red team assessments, social engineering awareness
**Implementation:**
```bash
python theHarvester.py -d example.com -b linkedin,twitter
```

#### **3. Shodan/Censys Integration** ⭐⭐⭐
**What:** Query Shodan/Censys for exposed services
**Benefit:** Discover internet-facing assets, open ports, banners
**Use Case:** External attack surface mapping
**Implementation:**
```bash
python theHarvester.py -d example.com -b shodan,censys
```

#### **4. Virtual Host Discovery** ⭐⭐
**What:** Find virtual hosts on same IP
**Benefit:** Discover related domains/services
**Implementation:**
```bash
python theHarvester.py -d example.com -v
```

### **Recommended Integration**
```python
def run_theharvester(domain: str, job_id: str, api_keys: dict = None):
    """
    Run theHarvester for OSINT gathering.
    
    Args:
        domain: Target domain
        job_id: Job identifier
        api_keys: Dict of API keys for premium sources (Shodan, Hunter, etc.)
    """
    
    output_file = f'/tmp/harvester-{job_id}'
    
    cmd = [
        'python3',
        'tools/theHarvester/theHarvester-master/theHarvester.py',
        '-d', domain,
        '-b', 'google,bing,dnsdumpster,crtsh,virustotal',  # Free sources
        '-f', output_file,  # Output file
        '-l', '500'  # Limit results
    ]
    
    # Add premium sources if API keys provided
    if api_keys:
        if api_keys.get('shodan'):
            cmd.extend(['-s', api_keys['shodan']])
        if api_keys.get('hunter'):
            cmd.extend(['-h', api_keys['hunter']])
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    
    return {
        'emails': parse_emails(output_file),
        'hosts': parse_hosts(output_file),
        'ips': parse_ips(output_file)
    }
```

---

## 🔍 Tool #3: Nikto (Web Vulnerability Scanner)

### **What It Does**
- **Primary Function:** Web server vulnerability scanning
- **Checks For:**
  - Outdated server versions
  - Dangerous files/programs
  - Server configuration issues
  - Default files and programs
  - Insecure files
  - Server options (HTTP methods)
  - 6700+ known vulnerabilities

### **Current Status in Aegis Recon**
✅ **Already Integrated** - Called in `scan_worker.py` line ~240

### **Available Features We Can Adopt**

#### **1. Comprehensive Vulnerability Database** ⭐⭐⭐
**What:** 6700+ vulnerability checks
**Benefit:** Already using this!
**Status:** ✅ Implemented

#### **2. SSL/TLS Testing** ⭐⭐
**What:** Check SSL certificate validity, cipher strength
**Benefit:** Identify weak SSL/TLS configurations
**Implementation:**
```bash
perl nikto.pl -h https://example.com -ssl -Tuning 2
```

#### **3. Tuning Options** ⭐⭐
**What:** Focus on specific vulnerability types
**Benefit:** Faster, targeted scans
**Options:**
- `1` - Interesting files
- `2` - Misconfiguration
- `3` - Information disclosure
- `4` - Injection (XSS/SQL)
- `5` - Remote file retrieval
- `6` - Denial of service
- `7` - Remote command execution
- `8` - SQL injection
- `9` - File upload
- `x` - Reverse tuning (exclude)

**Implementation:**
```bash
# Focus on high-severity issues only
perl nikto.pl -h example.com -Tuning 478  # Injection, RCE, SQLi
```

#### **4. Authentication Support** ⭐
**What:** Scan authenticated areas
**Benefit:** Test protected sections of web apps
**Implementation:**
```bash
perl nikto.pl -h example.com -id username:password
```

### **Recommended Enhancement**
```python
def run_nikto_enhanced(host: str, job_id: str, tuning: str = None, ssl_check: bool = True):
    """
    Enhanced Nikto scanning with tuning options.
    
    Args:
        host: Target host
        job_id: Job identifier
        tuning: Tuning string (e.g., '478' for high-severity only)
        ssl_check: Enable SSL/TLS checks
    """
    
    output_file = f'/tmp/nikto-{job_id}-{host}.json'
    
    cmd = [
        'perl',
        'tools/Nikto/program/nikto.pl',
        '-h', host,
        '-o', output_file,
        '-Format', 'json',
        '-timeout', '10'
    ]
    
    if tuning:
        cmd.extend(['-Tuning', tuning])
    
    if ssl_check and host.startswith('https'):
        cmd.extend(['-ssl'])
    
    # Disable interactive prompts
    cmd.extend(['-ask', 'no'])
    
    subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    
    return parse_nikto_json(output_file)
```

---

## 🔍 Tool #4: WhatWeb (Web Technology Fingerprinting)

### **What It Does**
- **Primary Function:** Web technology identification
- **Identifies:**
  - CMS (WordPress, Joomla, Drupal)
  - Web frameworks (Laravel, Django, Rails)
  - JavaScript libraries (jQuery, React, Angular)
  - Web servers (Apache, Nginx, IIS)
  - Programming languages (PHP, Python, Ruby)
  - Analytics (Google Analytics, etc.)
  - 1900+ plugins for detection

### **Current Status in Aegis Recon**
❌ **Not Integrated** - Available but not used

### **Available Features We Can Adopt**

#### **1. Technology Stack Detection** ⭐⭐⭐
**What:** Identify all technologies used by a website
**Benefit:** Understand attack surface, find version-specific vulnerabilities
**Implementation:**
```bash
whatweb -v -a 3 example.com --log-json=output.json
```

#### **2. Aggressive Scanning** ⭐⭐
**What:** Deep inspection with multiple requests
**Benefit:** More accurate technology detection
**Levels:**
- `1` - Stealthy (1 HTTP request)
- `2` - Polite (2 requests)
- `3` - Aggressive (multiple requests, slower)
- `4` - Heavy (extensive testing)

#### **3. Plugin System** ⭐⭐⭐
**What:** 1900+ plugins for specific technologies
**Benefit:** Detect specific CMS, frameworks, versions
**Examples:**
- WordPress version detection
- Drupal module detection
- PHP version identification
- Server header analysis

#### **4. Version Detection** ⭐⭐⭐
**What:** Identify specific versions of detected technologies
**Benefit:** Match against CVE databases for known vulnerabilities
**Implementation:**
```bash
whatweb -v -a 3 --log-verbose example.com
```

### **Recommended Integration**
```python
def run_whatweb(host: str, job_id: str, aggression: int = 3):
    """
    Run WhatWeb for technology fingerprinting.
    
    Args:
        host: Target host
        job_id: Job identifier
        aggression: Aggression level (1-4)
    """
    
    output_file = f'/tmp/whatweb-{job_id}-{host}.json'
    
    cmd = [
        'ruby',  # WhatWeb is Ruby-based
        'tools/WhatWeb/whatweb',
        '-v',  # Verbose
        '-a', str(aggression),  # Aggression level
        '--log-json', output_file,
        host
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    
    return parse_whatweb_json(output_file)
```

---

## 🎯 Integration Priority & Recommendations

### **High Priority (Implement First)** ⭐⭐⭐

1. **WhatWeb Integration**
   - **Why:** Provides crucial technology stack information
   - **Benefit:** Helps identify version-specific vulnerabilities
   - **Effort:** Low (simple command execution)
   - **Impact:** High (better vulnerability correlation)

2. **theHarvester - Shodan/Censys Module**
   - **Why:** Discovers external attack surface
   - **Benefit:** Find exposed services, open ports
   - **Effort:** Medium (requires API keys)
   - **Impact:** High (comprehensive asset discovery)

3. **Sublist3r - Multi-Engine Enhancement**
   - **Why:** More comprehensive subdomain discovery
   - **Benefit:** Find more attack vectors
   - **Effort:** Low (already integrated, just enable more engines)
   - **Impact:** Medium-High

### **Medium Priority (Nice to Have)** ⭐⭐

4. **theHarvester - Email Discovery**
   - **Why:** Useful for social engineering awareness
   - **Benefit:** Identify potential phishing targets
   - **Effort:** Low
   - **Impact:** Medium (depends on use case)

5. **Nikto - Tuning Options**
   - **Why:** Faster, more focused scans
   - **Benefit:** Reduce scan time, focus on critical issues
   - **Effort:** Low (just add parameters)
   - **Impact:** Medium

6. **Sublist3r - Brute-Force Mode**
   - **Why:** Discover hidden subdomains
   - **Benefit:** More complete enumeration
   - **Effort:** Low
   - **Impact:** Medium (slower scans)

### **Low Priority (Optional)** ⭐

7. **theHarvester - Employee Names**
   - **Why:** Organizational intelligence
   - **Benefit:** Red team assessments
   - **Effort:** Low
   - **Impact:** Low (privacy concerns)

8. **Nikto - Authentication Support**
   - **Why:** Scan authenticated areas
   - **Benefit:** More comprehensive testing
   - **Effort:** Medium (requires credentials)
   - **Impact:** Low (specific use cases)

---

## 📦 Proposed Enhanced Scan Worker

Here's how we can integrate these tools into an enhanced scan worker:

```python
def enhanced_scan_workflow(domain: str, job_id: str, options: dict = None):
    """
    Enhanced scanning workflow with all tools integrated.
    
    Workflow:
    1. Subdomain enumeration (Sublist3r - multi-engine)
    2. OSINT gathering (theHarvester - emails, hosts, Shodan)
    3. Port scanning (Nmap - existing)
    4. Technology fingerprinting (WhatWeb - NEW)
    5. Web vulnerability scanning (Nikto - enhanced)
    6. Risk scoring (existing)
    7. Report generation (existing)
    """
    
    results = {
        'job_id': job_id,
        'target': domain,
        'timestamp': datetime.utcnow().isoformat(),
        'phases': {}
    }
    
    # Phase 1: Subdomain Enumeration (Enhanced)
    logger.info("Phase 1: Subdomain enumeration with multiple engines")
    subdomains = run_sublist3r_enhanced(
        domain, 
        job_id,
        enable_bruteforce=options.get('bruteforce', False)
    )
    results['phases']['subdomains'] = subdomains
    
    # Phase 2: OSINT Gathering (NEW)
    logger.info("Phase 2: OSINT data gathering")
    osint_data = run_theharvester(
        domain,
        job_id,
        api_keys=options.get('api_keys', {})
    )
    results['phases']['osint'] = osint_data
    
    # Phase 3: Port Scanning (Existing)
    logger.info("Phase 3: Port scanning")
    for host in subdomains:
        nmap_results = run_nmap(host, job_id)
        results['phases'].setdefault('nmap', []).append(nmap_results)
    
    # Phase 4: Technology Fingerprinting (NEW)
    logger.info("Phase 4: Technology fingerprinting")
    for host in subdomains:
        if is_web_service(host):
            whatweb_results = run_whatweb(host, job_id, aggression=3)
            results['phases'].setdefault('technologies', []).append(whatweb_results)
    
    # Phase 5: Web Vulnerability Scanning (Enhanced)
    logger.info("Phase 5: Web vulnerability scanning")
    for host in subdomains:
        if is_web_service(host):
            nikto_results = run_nikto_enhanced(
                host, 
                job_id,
                tuning='478',  # Focus on high-severity
                ssl_check=True
            )
            results['phases'].setdefault('vulnerabilities', []).append(nikto_results)
    
    # Phase 6: Risk Scoring (Existing)
    logger.info("Phase 6: Risk scoring")
    risk_score = calculate_risk_score(results)
    results['risk_score'] = risk_score
    
    # Phase 7: Save Results
    save_results(job_id, results)
    
    return results
```

---

## 🛠️ Implementation Steps

### **Step 1: Add WhatWeb Integration (Quick Win)**

1. Create `ai_services/parsers/whatweb_parser.py`
2. Add WhatWeb call to `scan_worker.py`
3. Parse JSON output
4. Display in dashboard

**Estimated Time:** 1-2 hours

### **Step 2: Enhance Sublist3r Usage**

1. Enable multiple engines
2. Add brute-force option (optional)
3. Update configuration

**Estimated Time:** 30 minutes

### **Step 3: Add theHarvester Integration**

1. Create `ai_services/parsers/harvester_parser.py`
2. Add theHarvester call to `scan_worker.py`
3. Handle API keys securely
4. Parse and display results

**Estimated Time:** 2-3 hours

### **Step 4: Enhance Nikto Usage**

1. Add tuning options
2. Add SSL/TLS checks
3. Update parser for additional fields

**Estimated Time:** 1 hour

---

## 📊 Expected Benefits

### **Before Integration**
- Subdomain enumeration: Basic
- Port scanning: Good
- Web vulnerabilities: Good
- Technology detection: None
- OSINT: None
- External asset discovery: None

### **After Integration**
- Subdomain enumeration: ⭐⭐⭐ Excellent (multi-source)
- Port scanning: ⭐⭐⭐ Good (existing)
- Web vulnerabilities: ⭐⭐⭐ Excellent (tuned)
- Technology detection: ⭐⭐⭐ Excellent (WhatWeb)
- OSINT: ⭐⭐⭐ Excellent (theHarvester)
- External asset discovery: ⭐⭐⭐ Excellent (Shodan/Censys)

---

## 🔒 Security & Legal Considerations

### **Important Notes:**

1. **Consent Required:** All tools should only be used on systems you own or have explicit permission to test

2. **API Keys:** Store securely in `.env` file:
   ```bash
   SHODAN_API_KEY=your_key_here
   HUNTER_API_KEY=your_key_here
   CENSYS_API_ID=your_id_here
   CENSYS_API_SECRET=your_secret_here
   ```

3. **Rate Limiting:** Implement delays between requests to avoid:
   - IP bans from search engines
   - API rate limit violations
   - Network flooding

4. **Data Privacy:** Email and employee name harvesting should be used responsibly:
   - Only for authorized security assessments
   - Comply with GDPR/data protection laws
   - Obtain proper consent

---

## 🎓 Summary

### **Tools You Have:**
1. ✅ **Sublist3r** - Subdomain enumeration (already integrated)
2. ✅ **Nikto** - Web vulnerability scanning (already integrated)
3. ❌ **theHarvester** - OSINT gathering (not integrated)
4. ❌ **WhatWeb** - Technology fingerprinting (not integrated)

### **Recommended Next Steps:**
1. **Integrate WhatWeb** for technology detection (HIGH PRIORITY)
2. **Enhance Sublist3r** with multi-engine support (MEDIUM PRIORITY)
3. **Add theHarvester** for OSINT and Shodan integration (HIGH PRIORITY)
4. **Enhance Nikto** with tuning options (LOW PRIORITY)

### **Estimated Total Implementation Time:**
- High Priority Items: 4-6 hours
- All Items: 8-10 hours

---

**Would you like me to start implementing any of these integrations?** I recommend starting with WhatWeb as it's a quick win with high impact! 🚀
