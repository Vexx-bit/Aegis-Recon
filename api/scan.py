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

from http.server import BaseHTTPRequestHandler
import json
import os
import socket
import re
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from concurrent.futures import ThreadPoolExecutor, as_completed


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler for scanning"""
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """Handle scan requests"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}
            
            domain = data.get('domain', '').strip()
            
            if not domain:
                self._send_json({'success': False, 'error': 'Domain is required'}, 400)
                return
            
            # Clean domain
            domain = re.sub(r'^https?://', '', domain).rstrip('/')
            
            # Run the scan
            scanner = AegisScanner(domain)
            results = scanner.run()
            
            self._send_json({
                'success': True,
                'results': results,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            self._send_json({'success': False, 'error': str(e)}, 500)
    
    def do_GET(self):
        """Handle GET requests (health check)"""
        self._send_json({
            'status': 'ok',
            'service': 'Aegis Recon Scanner',
            'author': 'VexSpitta',
            'github': 'https://github.com/Vexx-bit'
        })
    
    def _send_json(self, data, status=200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))


class AegisScanner:
    """Lightweight scanner for Vercel serverless"""
    
    def __init__(self, target: str):
        self.target = target
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
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
    
    def _fetch(self, url, timeout=10):
        """Make HTTP request using urllib"""
        try:
            req = Request(url, headers=self.headers)
            with urlopen(req, timeout=timeout) as response:
                return response.read().decode('utf-8'), dict(response.headers)
        except:
            return None, {}
    
    def run(self):
        """Execute all scan phases"""
        self.scan_subdomains()
        self.probe_hosts()
        self.fingerprint_tech()
        self.scan_osint()
        self.enrich_hosts()
        self.calculate_score()
        return self.results
    
    def scan_subdomains(self):
        """Query crt.sh for certificate transparency logs"""
        try:
            url = f"https://crt.sh/?q=%.{self.target}&output=json"
            content, _ = self._fetch(url, timeout=15)
            
            if content:
                data = json.loads(content)
                subdomains = set()
                for entry in data:
                    name = entry.get('name_value', '')
                    for sub in name.split('\n'):
                        sub = sub.strip().lower()
                        if sub.endswith(self.target) and '*' not in sub:
                            subdomains.add(sub)
                
                self.results['phases']['subdomains'] = list(subdomains)[:50]
        except:
            self.results['phases']['subdomains'] = [self.target]
    
    def probe_hosts(self):
        """Resolve subdomains and check basic connectivity"""
        hosts = []
        domains_to_check = self.results['phases']['subdomains'][:15] or [self.target]
        common_ports = [80, 443, 22, 21, 8080]
        
        for domain in domains_to_check:
            try:
                ip = socket.gethostbyname(domain)
                open_ports = []
                
                for port in common_ports:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        if sock.connect_ex((ip, port)) == 0:
                            open_ports.append(port)
                        sock.close()
                    except:
                        pass
                
                hosts.append({
                    'hostname': domain,
                    'ip': ip,
                    'ports': open_ports,
                    'status': 'up' if open_ports else 'filtered'
                })
            except:
                pass
        
        self.results['phases']['hosts'] = hosts
    
    def fingerprint_tech(self):
        """Detect technologies from HTTP headers and HTML"""
        tech_found = []
        
        try:
            url = f"https://{self.target}"
            content, headers = self._fetch(url)
            
            if content:
                html = content.lower()
                
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
            content, _ = self._fetch(url)
            
            if content:
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                found = re.findall(email_pattern, content)
                
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
                    url = f"https://ipinfo.io/{ip}?token={token}"
                    content, _ = self._fetch(url, timeout=5)
                    if content:
                        data = json.loads(content)
                        host['geo'] = {
                            'city': data.get('city'),
                            'country': data.get('country'),
                            'org': data.get('org')
                        }
            except:
                pass
    
    def calculate_score(self):
        """Calculate a comprehensive security score based on reconnaissance findings
        
        IMPORTANT: This is a PASSIVE reconnaissance score, not a vulnerability assessment.
        A high score means low VISIBLE exposure, not necessarily secure infrastructure.
        True security requires active vulnerability scanning and penetration testing.
        """
        # Start at 70 - baseline for unknown (not 100, as we can't verify security)
        score = 70
        phases = self.results['phases']
        findings = []  # Track what affected the score
        
        # ========== POSITIVE FACTORS (add points) ==========
        
        # HTTPS enabled (+10)
        if any(443 in host.get('ports', []) for host in phases['hosts']):
            score += 10
            findings.append('+10: HTTPS enabled')
        
        # Modern security headers detected via technologies
        tech_names = [t.get('name', '').lower() for t in phases.get('technologies', [])]
        if any('cloudflare' in t or 'akamai' in t or 'fastly' in t for t in tech_names):
            score += 5
            findings.append('+5: CDN/WAF detected')
        
        # Limited attack surface (few subdomains)
        subdomain_count = len(phases.get('subdomains', []))
        if subdomain_count <= 3:
            score += 5
            findings.append('+5: Minimal subdomain exposure')
        
        # No exposed emails
        if not phases['osint']['emails']:
            score += 5
            findings.append('+5: No exposed email addresses')
        
        # ========== NEGATIVE FACTORS (deduct points) ==========
        
        # Exposed email addresses (-5 each, max -15)
        email_count = len(phases['osint']['emails'])
        if email_count > 0:
            deduction = min(email_count * 5, 15)
            score -= deduction
            findings.append(f'-{deduction}: {email_count} exposed emails')
        
        # Risky open ports
        risky_ports = {
            21: (15, 'FTP - cleartext credentials'),
            22: (5, 'SSH - potential brute-force target'),
            23: (20, 'Telnet - critical, cleartext protocol'),
            25: (5, 'SMTP - potential spam relay'),
            3306: (15, 'MySQL - database exposed'),
            5432: (15, 'PostgreSQL - database exposed'),
            1433: (15, 'MSSQL - database exposed'),
            3389: (15, 'RDP - ransomware target'),
            5900: (10, 'VNC - screen sharing exposed'),
            6379: (15, 'Redis - database exposed'),
            27017: (15, 'MongoDB - database exposed'),
        }
        
        for host in phases['hosts']:
            for port in host.get('ports', []):
                if port in risky_ports:
                    deduction, reason = risky_ports[port]
                    score -= deduction
                    findings.append(f'-{deduction}: Port {port} ({reason})')
        
        # HTTP without HTTPS (-10)
        has_http = any(80 in host.get('ports', []) for host in phases['hosts'])
        has_https = any(443 in host.get('ports', []) for host in phases['hosts'])
        if has_http and not has_https:
            score -= 10
            findings.append('-10: HTTP only, no HTTPS detected')
        
        # Outdated software detection
        outdated_indicators = ['openssl/1.0', 'php/5.', 'php/7.0', 'php/7.1', 'php/7.2', 
                               'apache/2.2', 'nginx/1.1', 'jquery/1.', 'jquery/2.']
        for tech in phases.get('technologies', []):
            tech_name = tech.get('name', '').lower()
            for indicator in outdated_indicators:
                if indicator in tech_name:
                    score -= 10
                    findings.append(f'-10: Outdated software ({tech.get("name")})')
                    break
        
        # Large subdomain footprint increases attack surface
        if subdomain_count > 10:
            deduction = min((subdomain_count - 10) * 2, 15)
            score -= deduction
            findings.append(f'-{deduction}: Large attack surface ({subdomain_count} subdomains)')
        
        # ========== UNCERTAINTY PENALTY ==========
        # If we detected very little, we can't give a high score
        tech_count = len(phases.get('technologies', []))
        host_count = len(phases.get('hosts', []))
        
        if tech_count == 0 and host_count <= 1:
            # Limited visibility - reduce score as we can't verify security
            score = min(score, 75)
            findings.append('Cap at 75: Limited reconnaissance data')
        
        # Store findings for potential use in reports
        self.results['score_factors'] = findings
        self.results['security_score'] = max(0, min(100, score))
        
        # Add disclaimer
        self.results['score_disclaimer'] = (
            "This score reflects VISIBLE exposure from passive reconnaissance only. "
            "It does not detect application-level vulnerabilities (SQLi, XSS, etc.). "
            "A comprehensive security assessment requires active vulnerability scanning."
        )

