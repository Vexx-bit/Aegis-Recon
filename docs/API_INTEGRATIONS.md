# Aegis Recon - API Integrations & Features

## 🟢 Features Implemented (Plan B - Pure Python)

We have successfully replaced the heavy tools with generic Python logic.

- **Subdomain Enumeration**: Replaced `Sublist3r` with **crt.sh** Public API.
- **Port Scanning**: Replaced `Nmap` with **Python Sockets**.
- **Header Analysis**: Replaced `WhatWeb` with **Requests & BeautifulSoup**.

## 🟡 Missing / Enhancements (The "Left Out" Features)

To make this truly "Professional Grade" without installing binaries, you should integrate these APIs.

### 1. Advanced Vulnerability Data (CVEs)

Currently, we only check for missing headers. To find _real_ CVEs (e.g., "Log4j" or "Outdated Apache"):

- **Tool**: [Vulners API](https://vulners.com/api/v3/search/lucene/)
- **Cost**: Free Tier (Limited requests)
- **Key Needed**: Yes
- **Why**: You send a software string "Apache 2.4.49" and it returns "CVE-2021-41773 (High Severity)".

### 2. IP Reputation / Geolocation

- **Tool**: [IPinfo.io](https://ipinfo.io/)
- **Cost**: Free (50k req/month)
- **Key Needed**: Optional (but recommended)
- **Why**: Tells you if the IP is hosted on AWS, DigitalOcean, or a residential proxy, and its physical location.

### 3. Google Safe Browsing

- **Tool**: [Google Safe Browsing API](https://developers.google.com/safe-browsing/v4)
- **Cost**: Free
- **Key Needed**: Yes (Google Cloud Console)
- **Why**: Instantly checks if the domain is already flagged as a phishing/malware site by Chrome.

### 4. CMS specific Deep Scans (WPScan)

- **Tool**: [WPSec API](https://wpscan.com/api)
- **Cost**: Free (25 req/day)
- **Key Needed**: Yes
- **Why**: If we detect WordPress, we query this API to see if the installed version has hacks.

---

## 🔑 Recommended .env Updates

To activate these future features, your `.env` should eventually look like this:

```bash
# Core
API_KEY=xxx
GROQ_API_KEY=xxx

# Intelligence APIs
VULNERS_API_KEY=   # https://vulners.com/
IPINFO_TOKEN=      # https://ipinfo.io/signup
GOOGLE_SAFE_KEY=   # https://console.cloud.google.com/
WPSCAN_API_KEY=    # https://wpscan.com/
```
