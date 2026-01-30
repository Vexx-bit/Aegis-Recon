"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                            AEGIS RECON                                     ║
║              Advanced Threat Intelligence System                           ║
╠═══════════════════════════════════════════════════════════════════════════╣
║  Author: VexSpitta                                                         ║
║  GitHub: https://github.com/Vexx-bit                                       ║
║  Project: https://github.com/Vexx-bit/Aegis-Recon                         ║
║                                                                            ║
║  © 2024-2026 VexSpitta. All Rights Reserved.                              ║
║  Unauthorized copying, modification, or distribution is prohibited.       ║
╚═══════════════════════════════════════════════════════════════════════════╝

Aegis Recon - Vercel Serverless API
Main scan endpoint - triggers reconnaissance
"""

import json
import os
import socket
import requests
import re
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

def handler(request):
    """Vercel serverless handler for scanning"""
    
    # Handle CORS preflight
    if request.method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": ""
        }
    
    try:
        # Parse request body
        body = json.loads(request.body) if request.body else {}
        domain = body.get("domain", "").strip()
        
        if not domain:
            return error_response("Domain is required", 400)
        
        # Clean domain
        domain = re.sub(r'^https?://', '', domain).rstrip('/')
        
        # Run the scan
        scanner = AegisScanner(domain)
        results = scanner.run()
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "success": True,
                "results": results,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        }
        
    except Exception as e:
        return error_response(str(e), 500)


def error_response(message, status_code=400):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "success": False,
            "error": message
        })
    }


class AegisScanner:
    """Lightweight scanner for Vercel serverless (no MySQL dependency)"""
    
    def __init__(self, target: str):
        self.target = target
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        self.results = {
            'target': target,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'phases': {
                'subdomains': [],
                'hosts': [],
                'osint': {'emails': []},
                'technologies': []
            },
            'security_score': 100
        }
    
    def run(self):
        """Execute all scan phases"""
        
        # Phase 1: Subdomains from crt.sh
        self.scan_subdomains()
        
        # Phase 2: Resolve and probe hosts
        self.probe_hosts()
        
        # Phase 3: Technology fingerprinting
        self.fingerprint_tech()
        
        # Phase 4: OSINT (email harvesting)
        self.scan_osint()
        
        # Phase 5: IP enrichment
        self.enrich_hosts()
        
        # Calculate security score
        self.calculate_score()
        
        return self.results
    
    def scan_subdomains(self):
        """Query crt.sh for certificate transparency logs"""
        try:
            url = f"https://crt.sh/?q=%.{self.target}&output=json"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                subdomains = set()
                for entry in data:
                    name = entry.get('name_value', '')
                    for sub in name.split('\n'):
                        sub = sub.strip().lower()
                        if sub.endswith(self.target) and '*' not in sub:
                            subdomains.add(sub)
                
                self.results['phases']['subdomains'] = list(subdomains)[:50]
        except Exception as e:
            self.results['phases']['subdomains'] = [self.target]
    
    def probe_hosts(self):
        """Resolve subdomains and check basic connectivity"""
        hosts = []
        domains_to_check = self.results['phases']['subdomains'][:20] or [self.target]
        
        common_ports = [80, 443, 22, 21, 8080, 8443]
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {}
            for domain in domains_to_check:
                futures[executor.submit(self._probe_single_host, domain, common_ports)] = domain
            
            for future in as_completed(futures, timeout=30):
                try:
                    result = future.result(timeout=5)
                    if result:
                        hosts.append(result)
                except:
                    pass
        
        self.results['phases']['hosts'] = hosts
    
    def _probe_single_host(self, domain, ports):
        """Probe a single host"""
        try:
            ip = socket.gethostbyname(domain)
            open_ports = []
            
            for port in ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    if sock.connect_ex((ip, port)) == 0:
                        open_ports.append(port)
                    sock.close()
                except:
                    pass
            
            return {
                'hostname': domain,
                'ip': ip,
                'ports': open_ports,
                'status': 'up' if open_ports else 'filtered'
            }
        except:
            return None
    
    def fingerprint_tech(self):
        """Detect technologies from HTTP headers and HTML"""
        tech_found = []
        
        try:
            url = f"https://{self.target}"
            response = self.session.get(url, timeout=10, allow_redirects=True)
            headers = response.headers
            html = response.text.lower()
            
            # Header-based detection
            server = headers.get('Server', '')
            if server:
                tech_found.append({'name': server, 'category': 'Web Server', 'source': 'header'})
            
            powered_by = headers.get('X-Powered-By', '')
            if powered_by:
                tech_found.append({'name': powered_by, 'category': 'Framework', 'source': 'header'})
            
            # HTML-based detection
            tech_signatures = {
                'wordpress': 'WordPress',
                'wp-content': 'WordPress',
                'drupal': 'Drupal',
                'joomla': 'Joomla',
                'shopify': 'Shopify',
                'wix': 'Wix',
                'squarespace': 'Squarespace',
                'react': 'React',
                'angular': 'Angular',
                'vue': 'Vue.js',
                'bootstrap': 'Bootstrap',
                'tailwind': 'Tailwind CSS',
                'jquery': 'jQuery',
                'cloudflare': 'Cloudflare',
                'google-analytics': 'Google Analytics',
                'gtag': 'Google Tag Manager'
            }
            
            for sig, name in tech_signatures.items():
                if sig in html:
                    if not any(t['name'] == name for t in tech_found):
                        tech_found.append({'name': name, 'category': 'CMS/Framework', 'source': 'html'})
            
        except:
            pass
        
        self.results['phases']['technologies'] = tech_found
    
    def scan_osint(self):
        """Extract emails from the target page"""
        emails = set()
        
        try:
            url = f"https://{self.target}"
            response = self.session.get(url, timeout=10)
            
            # Regex for emails
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            found = re.findall(email_pattern, response.text)
            
            for email in found:
                if not any(x in email.lower() for x in ['example.com', 'domain.com', 'email.com', '.png', '.jpg', '.gif']):
                    emails.add(email.lower())
            
        except:
            pass
        
        self.results['phases']['osint']['emails'] = list(emails)[:20]
    
    def enrich_hosts(self):
        """Add geolocation data to hosts using IPInfo"""
        token = os.environ.get('IPINFO_TOKEN')
        if not token:
            return
        
        for host in self.results['phases']['hosts'][:5]:
            try:
                ip = host.get('ip')
                if ip:
                    response = self.session.get(f"https://ipinfo.io/{ip}?token={token}", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        host['geo'] = {
                            'city': data.get('city'),
                            'country': data.get('country'),
                            'org': data.get('org')
                        }
            except:
                pass
    
    def calculate_score(self):
        """Calculate a basic security score"""
        score = 100
        phases = self.results['phases']
        
        # Deduct for exposed emails
        if phases['osint']['emails']:
            score -= min(len(phases['osint']['emails']) * 5, 20)
        
        # Deduct for risky open ports
        risky_ports = {21: 10, 22: 5, 23: 15, 3389: 10, 5900: 10}
        for host in phases['hosts']:
            for port in host.get('ports', []):
                if port in risky_ports:
                    score -= risky_ports[port]
        
        # Bonus for HTTPS
        if any(443 in host.get('ports', []) for host in phases['hosts']):
            score += 5
        
        self.results['security_score'] = max(0, min(100, score))
