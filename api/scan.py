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
    
    def _fetch_with_headers(self, url, timeout=10):
        """Make HTTP request and return response with full headers"""
        try:
            req = Request(url, headers=self.headers)
            with urlopen(req, timeout=timeout) as response:
                return response.read().decode('utf-8'), dict(response.headers), response.status
        except HTTPError as e:
            return None, dict(e.headers) if e.headers else {}, e.code
        except:
            return None, {}, 0
    
    def run(self):
        """Execute all scan phases"""
        self.scan_subdomains()
        self.probe_hosts()
        self.fingerprint_tech()
        self.scan_osint()
        self.enrich_hosts()
        
        # Security checks
        self.check_security_headers()
        self.check_ssl_certificate()
        self.check_robots_txt()
        self.check_admin_panels()
        self.check_directory_listing()
        self.check_cms_cves()
        
        # NEW OSINT modules
        self.enumerate_dns_records()
        self.lookup_whois()
        self.check_cookie_security()
        self.check_http_methods()
        self.check_cors_policy()
        
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
    
    def check_security_headers(self):
        """Check for important security headers"""
        self.results['security_headers'] = {
            'headers_found': [],
            'headers_missing': [],
            'grade': 'F',
            'details': []
        }
        
        try:
            url = f"https://{self.target}"
            _, headers, status = self._fetch_with_headers(url, timeout=10)
            
            if not headers:
                # Try HTTP if HTTPS fails
                url = f"http://{self.target}"
                _, headers, status = self._fetch_with_headers(url, timeout=10)
            
            if not headers:
                return
            
            # Important security headers to check
            security_headers = {
                'Strict-Transport-Security': {
                    'importance': 'critical',
                    'description': 'Enforces HTTPS connections'
                },
                'Content-Security-Policy': {
                    'importance': 'high',
                    'description': 'Prevents XSS and injection attacks'
                },
                'X-Frame-Options': {
                    'importance': 'medium',
                    'description': 'Prevents clickjacking attacks'
                },
                'X-Content-Type-Options': {
                    'importance': 'medium',
                    'description': 'Prevents MIME type sniffing'
                },
                'X-XSS-Protection': {
                    'importance': 'low',
                    'description': 'Legacy XSS filter (deprecated but still useful)'
                },
                'Referrer-Policy': {
                    'importance': 'medium',
                    'description': 'Controls referrer information leakage'
                },
                'Permissions-Policy': {
                    'importance': 'medium',
                    'description': 'Controls browser feature permissions'
                }
            }
            
            found = []
            missing = []
            score = 0
            max_score = 0
            
            importance_weights = {'critical': 30, 'high': 20, 'medium': 15, 'low': 10}
            
            for header, info in security_headers.items():
                weight = importance_weights[info['importance']]
                max_score += weight
                
                # Check case-insensitively
                header_value = None
                for h, v in headers.items():
                    if h.lower() == header.lower():
                        header_value = v
                        break
                
                if header_value:
                    found.append({
                        'name': header,
                        'value': header_value[:100],  # Truncate long values
                        'importance': info['importance']
                    })
                    score += weight
                else:
                    missing.append({
                        'name': header,
                        'description': info['description'],
                        'importance': info['importance']
                    })
            
            # Calculate grade
            percentage = (score / max_score) * 100 if max_score > 0 else 0
            if percentage >= 90:
                grade = 'A'
            elif percentage >= 75:
                grade = 'B'
            elif percentage >= 50:
                grade = 'C'
            elif percentage >= 25:
                grade = 'D'
            else:
                grade = 'F'
            
            self.results['security_headers'] = {
                'headers_found': found,
                'headers_missing': missing,
                'grade': grade,
                'score_percentage': round(percentage)
            }
            
        except Exception as e:
            self.results['security_headers']['error'] = str(e)
    
    def check_ssl_certificate(self):
        """Check SSL/TLS certificate information"""
        self.results['ssl_info'] = {
            'valid': False,
            'details': {}
        }
        
        try:
            import ssl
            import socket
            
            context = ssl.create_default_context()
            
            with socket.create_connection((self.target, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=self.target) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Parse certificate info
                    subject = dict(x[0] for x in cert.get('subject', []))
                    issuer = dict(x[0] for x in cert.get('issuer', []))
                    
                    # Parse dates
                    not_before = cert.get('notBefore', '')
                    not_after = cert.get('notAfter', '')
                    
                    # Check TLS version
                    tls_version = ssock.version()
                    
                    self.results['ssl_info'] = {
                        'valid': True,
                        'subject': subject.get('commonName', self.target),
                        'issuer': issuer.get('organizationName', 'Unknown'),
                        'not_before': not_before,
                        'not_after': not_after,
                        'tls_version': tls_version,
                        'is_expired': False  # Will be updated below
                    }
                    
                    # Check if expired
                    try:
                        from datetime import datetime
                        exp_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                        self.results['ssl_info']['is_expired'] = exp_date < datetime.now()
                        self.results['ssl_info']['days_until_expiry'] = (exp_date - datetime.now()).days
                    except:
                        pass
                    
        except Exception as e:
            self.results['ssl_info']['error'] = str(e)
    
    def check_robots_txt(self):
        """Parse robots.txt for sensitive paths"""
        self.results['robots_txt'] = {
            'found': False,
            'sensitive_paths': [],
            'all_disallowed': []
        }
        
        try:
            url = f"https://{self.target}/robots.txt"
            content, _, status = self._fetch_with_headers(url, timeout=5)
            
            if not content:
                url = f"http://{self.target}/robots.txt"
                content, _, status = self._fetch_with_headers(url, timeout=5)
            
            if content and status == 200:
                self.results['robots_txt']['found'] = True
                
                # Parse disallowed paths
                disallowed = []
                sensitive_keywords = ['admin', 'backup', 'config', 'database', 'db', 
                                      'private', 'secret', 'test', 'dev', 'staging',
                                      'old', 'temp', 'tmp', 'log', 'logs', 'sql',
                                      'dump', 'api', 'internal', 'manage', 'panel']
                
                sensitive_found = []
                
                for line in content.split('\n'):
                    line = line.strip().lower()
                    if line.startswith('disallow:'):
                        path = line.replace('disallow:', '').strip()
                        if path and path != '/':
                            disallowed.append(path)
                            
                            # Check if path contains sensitive keywords
                            for keyword in sensitive_keywords:
                                if keyword in path:
                                    sensitive_found.append({
                                        'path': path,
                                        'keyword': keyword
                                    })
                                    break
                
                self.results['robots_txt']['all_disallowed'] = disallowed[:20]
                self.results['robots_txt']['sensitive_paths'] = sensitive_found[:10]
                
        except:
            pass
    
    def check_admin_panels(self):
        """Check for exposed admin panels"""
        self.results['admin_panels'] = {
            'found': [],
            'checked': 0
        }
        
        common_admin_paths = [
            '/admin', '/administrator', '/admin.php', '/wp-admin', '/wp-login.php',
            '/login', '/signin', '/auth', '/panel', '/dashboard',
            '/manage', '/management', '/backend', '/cpanel', '/phpmyadmin',
            '/adminer', '/webadmin', '/.git', '/.env', '/config.php'
        ]
        
        base_urls = [f"https://{self.target}", f"http://{self.target}"]
        found_panels = []
        checked = 0
        
        try:
            for base in base_urls:
                for path in common_admin_paths[:15]:  # Limit to avoid timeout
                    checked += 1
                    try:
                        url = base + path
                        _, headers, status = self._fetch_with_headers(url, timeout=3)
                        
                        # Check if accessible (200, 301, 302, 401, 403 indicate existence)
                        if status in [200, 301, 302, 401, 403]:
                            found_panels.append({
                                'path': path,
                                'status': status,
                                'accessible': status == 200
                            })
                    except:
                        pass
                
                if found_panels:
                    break  # Found some, no need to try HTTP
            
            self.results['admin_panels'] = {
                'found': found_panels,
                'checked': checked
            }
            
        except:
            pass
    
    def check_directory_listing(self):
        """Check for directory listing vulnerabilities"""
        self.results['directory_listing'] = {
            'vulnerable': False,
            'exposed_dirs': []
        }
        
        test_dirs = ['/images/', '/assets/', '/uploads/', '/files/', 
                     '/css/', '/js/', '/media/', '/static/']
        
        try:
            for dir_path in test_dirs:
                for protocol in ['https', 'http']:
                    try:
                        url = f"{protocol}://{self.target}{dir_path}"
                        content, _, status = self._fetch_with_headers(url, timeout=3)
                        
                        if status == 200 and content:
                            # Check for directory listing indicators
                            listing_indicators = [
                                'Index of', 'Directory listing', '<title>Index of',
                                'Parent Directory', '[DIR]', '[To Parent Directory]'
                            ]
                            
                            if any(indicator in content for indicator in listing_indicators):
                                self.results['directory_listing']['vulnerable'] = True
                                self.results['directory_listing']['exposed_dirs'].append(dir_path)
                                break
                    except:
                        pass
                        
        except:
            pass
    
    def check_cms_cves(self):
        """Check for known CVEs in detected CMS versions"""
        cves = []
        
        tech_names = [t.get('name', '').lower() for t in self.results['phases'].get('technologies', [])]
        
        # Known vulnerable versions (simplified - in production, use a CVE database)
        vulnerable_versions = {
            'joomla': [
                {'version': '3.', 'cve': 'CVE-2023-23752', 'severity': 'Critical', 'desc': 'Unauthorized access to webservice endpoints'},
                {'version': '4.0', 'cve': 'CVE-2023-23752', 'severity': 'Critical', 'desc': 'Information disclosure vulnerability'}
            ],
            'wordpress': [
                {'version': '5.', 'cve': 'CVE-2022-21661', 'severity': 'High', 'desc': 'SQL injection in WP_Query'},
                {'version': '4.', 'cve': 'Multiple', 'severity': 'Critical', 'desc': 'Multiple unpatched vulnerabilities'}
            ],
            'drupal': [
                {'version': '7.', 'cve': 'CVE-2018-7600', 'severity': 'Critical', 'desc': 'Drupalgeddon2 RCE'},
                {'version': '8.', 'cve': 'CVE-2019-6340', 'severity': 'High', 'desc': 'Remote code execution'}
            ],
            'php/5.': [
                {'version': '5.', 'cve': 'Multiple', 'severity': 'Critical', 'desc': 'End of life - no security updates'}
            ],
            'php/7.0': [
                {'version': '7.0', 'cve': 'Multiple', 'severity': 'High', 'desc': 'End of life since 2019'}
            ],
            'php/7.1': [
                {'version': '7.1', 'cve': 'Multiple', 'severity': 'High', 'desc': 'End of life since 2019'}
            ],
            'php/7.2': [
                {'version': '7.2', 'cve': 'Multiple', 'severity': 'Medium', 'desc': 'End of life since 2020'}
            ],
            'openssl/1.0': [
                {'version': '1.0', 'cve': 'CVE-2020-1971', 'severity': 'High', 'desc': 'Null pointer dereference DoS'}
            ],
            'apache/2.2': [
                {'version': '2.2', 'cve': 'Multiple', 'severity': 'High', 'desc': 'End of life - multiple vulnerabilities'}
            ],
            'jquery/1.': [
                {'version': '1.', 'cve': 'CVE-2020-11022', 'severity': 'Medium', 'desc': 'XSS vulnerability in jQuery < 3.5.0'}
            ],
            'jquery/2.': [
                {'version': '2.', 'cve': 'CVE-2020-11022', 'severity': 'Medium', 'desc': 'XSS vulnerability in jQuery < 3.5.0'}
            ]
        }
        
        for tech_name in tech_names:
            for vuln_key, vuln_list in vulnerable_versions.items():
                if vuln_key in tech_name:
                    for vuln in vuln_list:
                        cves.append({
                            'technology': tech_name,
                            'cve': vuln['cve'],
                            'severity': vuln['severity'],
                            'description': vuln['desc']
                        })
        
        self.results['known_cves'] = cves

    # ==================================================================
    # NEW OSINT MODULES
    # ==================================================================

    def enumerate_dns_records(self):
        """Enumerate DNS records using Google & Cloudflare DNS-over-HTTPS"""
        records = []
        record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA']
        
        for rtype in record_types:
            try:
                url = f"https://dns.google/resolve?name={self.target}&type={rtype}"
                content, _ = self._fetch(url, timeout=5)
                if content:
                    data = json.loads(content)
                    for answer in data.get('Answer', []):
                        value = answer.get('data', '').strip('"')
                        if value:
                            records.append({
                                'type': rtype,
                                'name': answer.get('name', self.target).rstrip('.'),
                                'value': value,
                                'ttl': answer.get('TTL', 0)
                            })
            except:
                pass
        
        self.results['dns_records'] = records

    def lookup_whois(self):
        """Lightweight WHOIS lookup via RDAP (public, no API key needed)"""
        self.results['whois_info'] = {}
        
        try:
            # Use RDAP (Registration Data Access Protocol) - the modern WHOIS
            url = f"https://rdap.org/domain/{self.target}"
            content, _ = self._fetch(url, timeout=8)
            
            if content:
                data = json.loads(content)
                
                whois = {}
                
                # Registrar
                entities = data.get('entities', [])
                for entity in entities:
                    roles = entity.get('roles', [])
                    if 'registrar' in roles:
                        vcard = entity.get('vcardArray', [None, []])
                        if len(vcard) > 1:
                            for item in vcard[1]:
                                if item[0] == 'fn':
                                    whois['registrar'] = item[3]
                                    break
                        # Fallback to publicIds
                        if 'registrar' not in whois:
                            pub_ids = entity.get('publicIds', [])
                            if pub_ids:
                                whois['registrar'] = pub_ids[0].get('identifier', '')
                
                # Dates
                events = data.get('events', [])
                for event in events:
                    action = event.get('eventAction', '')
                    date_val = event.get('eventDate', '')
                    if date_val:
                        # Format date nicely
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                            date_str = dt.strftime('%Y-%m-%d')
                        except:
                            date_str = date_val[:10]
                        
                        if action == 'registration':
                            whois['creation_date'] = date_str
                        elif action == 'expiration':
                            whois['expiry_date'] = date_str
                        elif action == 'last changed':
                            whois['updated_date'] = date_str
                
                # Name servers
                nameservers = data.get('nameservers', [])
                if nameservers:
                    ns_list = [ns.get('ldhName', '') for ns in nameservers if ns.get('ldhName')]
                    if ns_list:
                        whois['name_servers'] = ', '.join(ns_list[:4])
                
                # Status / DNSSEC
                dnssec = data.get('secureDNS', {})
                if dnssec.get('delegationSigned'):
                    whois['dnssec'] = 'Signed'
                else:
                    whois['dnssec'] = 'Unsigned'
                
                # Status flags
                status = data.get('status', [])
                if status:
                    whois['status'] = ', '.join(status[:3])
                
                self.results['whois_info'] = whois
                
        except Exception as e:
            self.results['whois_info'] = {'error': str(e)}

    def check_cookie_security(self):
        """Analyze cookie security attributes"""
        self.results['cookie_security'] = {'cookies': []}
        
        try:
            url = f"https://{self.target}"
            _, headers, status = self._fetch_with_headers(url, timeout=8)
            
            if not headers:
                url = f"http://{self.target}"
                _, headers, status = self._fetch_with_headers(url, timeout=8)
            
            if not headers:
                return
            
            # Collect all Set-Cookie headers
            cookies = []
            for header_name, header_value in headers.items():
                if header_name.lower() == 'set-cookie':
                    # Parse cookie
                    parts = header_value.split(';')
                    if parts:
                        cookie_name = parts[0].split('=')[0].strip()
                        flags = header_value.lower()
                        
                        cookies.append({
                            'name': cookie_name,
                            'secure': 'secure' in flags,
                            'httponly': 'httponly' in flags,
                            'samesite': self._extract_samesite(flags),
                            'raw': header_value[:150]
                        })
            
            self.results['cookie_security'] = {'cookies': cookies}
            
        except:
            pass
    
    def _extract_samesite(self, cookie_str):
        """Extract SameSite value from cookie string"""
        lower = cookie_str.lower()
        if 'samesite=strict' in lower:
            return 'Strict'
        elif 'samesite=lax' in lower:
            return 'Lax'
        elif 'samesite=none' in lower:
            return 'None'
        return None

    def check_http_methods(self):
        """Test which HTTP methods the server allows"""
        self.results['http_methods'] = {'methods': [], 'risky_methods': []}
        
        try:
            # First try OPTIONS request
            url = f"https://{self.target}"
            
            try:
                req = Request(url, headers=self.headers, method='OPTIONS')
                with urlopen(req, timeout=5) as response:
                    allow = response.headers.get('Allow', '')
                    if allow:
                        methods = [m.strip().upper() for m in allow.split(',')]
                        risky = [m for m in methods if m in ['PUT', 'DELETE', 'TRACE', 'CONNECT']]
                        self.results['http_methods'] = {
                            'methods': methods,
                            'risky_methods': risky
                        }
                        return
            except:
                pass
            
            # Fallback: test common methods individually
            test_methods = ['GET', 'POST', 'HEAD', 'OPTIONS', 'PUT', 'DELETE', 'TRACE', 'PATCH']
            allowed = []
            risky = []
            
            for method in test_methods:
                try:
                    req = Request(url, headers=self.headers, method=method)
                    with urlopen(req, timeout=3) as response:
                        if response.status < 500:
                            allowed.append(method)
                            if method in ['PUT', 'DELETE', 'TRACE', 'CONNECT']:
                                risky.append(method)
                except HTTPError as e:
                    # 405 Method Not Allowed = method exists but blocked
                    # 400, 401, 403 = method potentially available
                    if e.code in [400, 401, 403]:
                        allowed.append(method)
                        if method in ['PUT', 'DELETE', 'TRACE', 'CONNECT']:
                            risky.append(method)
                except:
                    pass
            
            self.results['http_methods'] = {
                'methods': allowed if allowed else ['GET'],
                'risky_methods': risky
            }
            
        except:
            pass

    def check_cors_policy(self):
        """Check for CORS misconfigurations"""
        self.results['cors_check'] = {
            'cors_enabled': False,
            'wildcard_origin': False,
            'reflects_origin': False
        }
        
        try:
            url = f"https://{self.target}"
            
            # Test 1: Check for wildcard origin
            test_headers = dict(self.headers)
            test_headers['Origin'] = 'https://evil-attacker.com'
            
            try:
                req = Request(url, headers=test_headers)
                with urlopen(req, timeout=5) as response:
                    acao = response.headers.get('Access-Control-Allow-Origin', '')
                    
                    if acao == '*':
                        self.results['cors_check'] = {
                            'cors_enabled': True,
                            'wildcard_origin': True,
                            'reflects_origin': False,
                            'allow_origin': '*'
                        }
                    elif acao == 'https://evil-attacker.com':
                        self.results['cors_check'] = {
                            'cors_enabled': True,
                            'wildcard_origin': False,
                            'reflects_origin': True,
                            'allow_origin': acao
                        }
                    elif acao:
                        self.results['cors_check'] = {
                            'cors_enabled': True,
                            'wildcard_origin': False,
                            'reflects_origin': False,
                            'allow_origin': acao
                        }
            except:
                pass
                
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
            deduction = min(email_count * 3, 10)
            score -= deduction
            findings.append(f'-{deduction}: {email_count} exposed emails')
        
        # Risky open ports (reduced penalties)
        risky_ports = {
            21: (8, 'FTP - cleartext credentials'),
            22: (3, 'SSH - potential brute-force target'),
            23: (15, 'Telnet - critical, cleartext protocol'),
            25: (3, 'SMTP - potential spam relay'),
            3306: (10, 'MySQL - database exposed'),
            5432: (10, 'PostgreSQL - database exposed'),
            1433: (10, 'MSSQL - database exposed'),
            3389: (10, 'RDP - ransomware target'),
            5900: (8, 'VNC - screen sharing exposed'),
            6379: (10, 'Redis - database exposed'),
            27017: (10, 'MongoDB - database exposed'),
        }
        
        for host in phases['hosts']:
            for port in host.get('ports', []):
                if port in risky_ports:
                    deduction, reason = risky_ports[port]
                    score -= deduction
                    findings.append(f'-{deduction}: Port {port} ({reason})')
        
        # HTTP without HTTPS (-8)
        has_http = any(80 in host.get('ports', []) for host in phases['hosts'])
        has_https = any(443 in host.get('ports', []) for host in phases['hosts'])
        if has_http and not has_https:
            score -= 8
            findings.append('-8: HTTP only, no HTTPS detected')
        
        # Outdated software detection (reduced to -5)
        outdated_indicators = ['openssl/1.0', 'php/5.', 'php/7.0', 'php/7.1', 'php/7.2', 
                               'apache/2.2', 'nginx/1.1', 'jquery/1.', 'jquery/2.']
        outdated_found = 0
        for tech in phases.get('technologies', []):
            tech_name = tech.get('name', '').lower()
            for indicator in outdated_indicators:
                if indicator in tech_name and outdated_found < 2:  # Max 2 outdated penalties
                    score -= 5
                    outdated_found += 1
                    findings.append(f'-5: Outdated software ({tech.get("name")})')
                    break
        
        # Large subdomain footprint increases attack surface
        if subdomain_count > 10:
            deduction = min((subdomain_count - 10) * 1, 10)
            score -= deduction
            findings.append(f'-{deduction}: Large attack surface ({subdomain_count} subdomains)')
        
        # ========== NEW SECURITY CHECK FACTORS ==========
        
        # Security Headers Grade (reduced penalties)
        headers_grade = self.results.get('security_headers', {}).get('grade', 'F')
        if headers_grade == 'A':
            score += 10
            findings.append('+10: Excellent security headers (Grade A)')
        elif headers_grade == 'B':
            score += 5
            findings.append('+5: Good security headers (Grade B)')
        elif headers_grade == 'C':
            pass  # Neutral
        elif headers_grade in ['D', 'F']:
            score -= 5
            findings.append(f'-5: Poor security headers (Grade {headers_grade})')
        
        # SSL Certificate
        ssl_info = self.results.get('ssl_info', {})
        if ssl_info.get('valid'):
            if ssl_info.get('is_expired'):
                score -= 15
                findings.append('-15: SSL certificate is expired')
            elif ssl_info.get('days_until_expiry', 999) < 30:
                score -= 3
                findings.append('-3: SSL certificate expiring soon')
            else:
                score += 5
                findings.append('+5: Valid SSL certificate')
            
            # Check TLS version
            tls_version = ssl_info.get('tls_version', '')
            if 'TLSv1.0' in tls_version or 'TLSv1.1' in tls_version:
                score -= 5
                findings.append(f'-5: Outdated TLS version ({tls_version})')
        
        # Admin Panels Exposed (reduced)
        admin_panels = self.results.get('admin_panels', {}).get('found', [])
        accessible_panels = [p for p in admin_panels if p.get('accessible')]
        if accessible_panels:
            deduction = min(len(accessible_panels) * 5, 10)
            score -= deduction
            findings.append(f'-{deduction}: {len(accessible_panels)} admin panel(s) accessible')
        
        # Directory Listing (reduced)
        if self.results.get('directory_listing', {}).get('vulnerable'):
            exposed_count = len(self.results['directory_listing'].get('exposed_dirs', []))
            score -= 8
            findings.append(f'-8: Directory listing enabled ({exposed_count} dirs exposed)')
        
        # Known CVEs (reduced and deduplicated)
        cves = self.results.get('known_cves', [])
        # Deduplicate by CVE ID
        seen_cves = set()
        unique_cves = []
        for c in cves:
            if c.get('cve') not in seen_cves:
                seen_cves.add(c.get('cve'))
                unique_cves.append(c)
        
        critical_cves = [c for c in unique_cves if c.get('severity') == 'Critical']
        high_cves = [c for c in unique_cves if c.get('severity') == 'High']
        
        if critical_cves:
            deduction = min(len(critical_cves) * 8, 15)
            score -= deduction
            findings.append(f'-{deduction}: {len(critical_cves)} critical CVE(s) detected')
        if high_cves:
            deduction = min(len(high_cves) * 5, 10)
            score -= deduction
            findings.append(f'-{deduction}: {len(high_cves)} high severity CVE(s) detected')
        
        # Robots.txt sensitive paths (minor penalty)
        sensitive_paths = self.results.get('robots_txt', {}).get('sensitive_paths', [])
        if len(sensitive_paths) > 5:
            score -= 3
            findings.append('-3: Many sensitive paths in robots.txt')
        
        # ========== NEW MODULE FACTORS ==========
        
        # Cookie security
        cookies = self.results.get('cookie_security', {}).get('cookies', [])
        insecure_cookies = [c for c in cookies if not c.get('secure') or not c.get('httponly')]
        if insecure_cookies:
            deduction = min(len(insecure_cookies) * 2, 6)
            score -= deduction
            findings.append(f'-{deduction}: {len(insecure_cookies)} cookie(s) missing security flags')
        
        # HTTP risky methods
        risky_methods = self.results.get('http_methods', {}).get('risky_methods', [])
        if risky_methods:
            score -= 4
            findings.append(f'-4: Risky HTTP methods enabled ({", ".join(risky_methods)})')
        
        # CORS misconfiguration
        cors = self.results.get('cors_check', {})
        if cors.get('wildcard_origin'):
            score -= 6
            findings.append('-6: Wildcard CORS policy (Access-Control-Allow-Origin: *)')
        elif cors.get('reflects_origin'):
            score -= 8
            findings.append('-8: CORS reflects arbitrary origins (critical misconfiguration)')
        
        # WHOIS: domain expiry warning
        whois = self.results.get('whois_info', {})
        if whois.get('expiry_date'):
            try:
                from datetime import datetime
                exp = datetime.strptime(whois['expiry_date'], '%Y-%m-%d')
                days_left = (exp - datetime.now()).days
                if days_left < 30:
                    score -= 3
                    findings.append(f'-3: Domain expires in {days_left} days')
            except:
                pass
        
        # DNSSEC bonus
        if whois.get('dnssec') == 'Signed':
            score += 3
            findings.append('+3: DNSSEC enabled')
        
        # DNS: SPF/DMARC check
        dns_records = self.results.get('dns_records', [])
        has_spf = any('spf' in r.get('value', '').lower() for r in dns_records if r.get('type') == 'TXT')
        has_dmarc = any('dmarc' in r.get('value', '').lower() for r in dns_records if r.get('type') == 'TXT')
        if has_spf:
            score += 3
            findings.append('+3: SPF record present')
        if has_dmarc:
            score += 3
            findings.append('+3: DMARC record present')
        if not has_spf and not has_dmarc:
            score -= 4
            findings.append('-4: No SPF/DMARC email security records')
        
        # ========== MINIMUM SCORE ==========
        # Don't go below 15 - that's critical exposure
        score = max(15, score)
        
        # ========== UNCERTAINTY PENALTY ==========
        # If we detected very little, cap at 75
        tech_count = len(phases.get('technologies', []))
        host_count = len(phases.get('hosts', []))
        
        if tech_count == 0 and host_count <= 1:
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
