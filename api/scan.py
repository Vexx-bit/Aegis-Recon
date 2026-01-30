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
