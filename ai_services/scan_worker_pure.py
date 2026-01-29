#!/usr/bin/env python3
"""
Aegis Recon - "Pure" Python Scanner (Pro Edition)
Integrates:
- Pure Python Port Scanning (Socket)
- crt.sh (Subdomains)
- IPInfo.io (Geolocation)
- Google Safe Browsing (Reputation)
- Vulners (CVE Search)
- Database Status Updates (Fixes "Forever Loading" bug)
"""

import sys
import os
import json
import logging
import socket
import requests
import concurrent.futures
import mysql.connector
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(LOG_DIR, 'scan_debug.log'))
    ]
)
logger = logging.getLogger(__name__)

class PureScanner:
    def __init__(self, target: str, job_id: str):
        self.target = target
        self.job_id = job_id
        self.results = {
            'job_id': job_id,
            'target': target,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'phases': {},
            'security_score': 100
        }
        self.session = requests.Session()
        # FIX: Spoof User-Agent to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        })
        self.session.headers.update({'User-Agent': 'AegisRecon/1.0 (Security-Research)'})
        
        # Load Env (Primitive)
        self.load_env()

    def load_env(self):
        """Manually load .env since we want zero dependencies like python-dotenv"""
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        k, v = line.split('=', 1)
                        os.environ[k] = v.strip('"').strip("'")

    def get_db_connection(self):
        return mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASS', ''),
            database=os.getenv('DB_NAME', 'aegis_recon')
        )

    def update_status(self, status: str, message: str = ""):
        """updates the database status so the frontend stops loading"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Update status
            sql = "UPDATE scans SET status = %s WHERE job_id = %s"
            cursor.execute(sql, (status, self.job_id))
            
            # If finished/done, save results too
            if status in ('done', 'finished', 'completed'):
                results_json = json.dumps(self.results)
                sql_res = "UPDATE scans SET results = %s, completed_at = NOW() WHERE job_id = %s"
                cursor.execute(sql_res, (results_json, self.job_id))
                logger.info(f"Results saved to database ({len(results_json)} bytes)")
                
            conn.commit()
            conn.close()
            logger.info(f"DB Status updated to: {status}")
        except Exception as e:
            logger.error(f"Failed to update DB status: {e}")

    # -------------------------------------------------------------------------
    # API INTEGRATIONS
    # -------------------------------------------------------------------------
    
    def check_ipinfo(self, ip: str) -> Dict:
        """Get location and ASN info"""
        token = os.getenv('IPINFO_TOKEN')
        if not token: return {}
        
        try:
            url = f"https://ipinfo.io/{ip}?token={token}"
            res = self.session.get(url, timeout=5).json()
            return {
                "country": res.get("country"),
                "city": res.get("city"),
                "org": res.get("org"),
                "loc": res.get("loc")
            }
        except:
            return {}

    def check_safebrowsing(self, domain: str) -> Dict:
        """Check Google Safe Browsing"""
        key = os.getenv('GOOGLE_SAFE_KEY')
        if not key: return {}
        
        try:
            url = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={key}"
            payload = {
                "client": {"clientId": "aegis-recon", "clientVersion": "1.0.0"},
                "threatInfo": {
                    "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING"],
                    "platformTypes": ["ANY_PLATFORM"],
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [{"url": f"http://{domain}"}, {"url": f"https://{domain}"}]
                }
            }
            res = self.session.post(url, json=payload, timeout=5).json()
            return {"safe": False if res else True, "matches": res}
        except Exception as e:
            logger.error(f"SafeBrowsing Error: {e}")
            return {}

    def search_vulners(self, software: str, version: str) -> List[Dict]:
        """Search Vulners for CVEs"""
        key = os.getenv('VULNERS_API_KEY')
        if not key or not software or not version: return []
        
        try:
            # Simple free text search (e.g., "nginx 1.18.0")
            query = f"{software} {version}"
            url = "https://vulners.com/api/v3/search/lucene/"
            payload = {
                "query": query,
                "apiKey": key,
                "limit": 3
            }
            res = self.session.post(url, json=payload, timeout=5).json()
            data = res.get('data', {}).get('search', [])
            
            cves = []
            for item in data:
                cves.append({
                    "id": item.get('id'),
                    "title": item.get('title'),
                    "score": item.get('cvss', {}).get('score', 0),
                    "link": item.get('href')
                })
            return cves
        except Exception as e:
            logger.error(f"Vulners Error: {e}")
            return []

    # -------------------------------------------------------------------------
    # CORE SCANNERS
    # -------------------------------------------------------------------------

    def scan_subdomains(self) -> List[str]:
        logger.info("Phase 1: Querying crt.sh for subdomains...")
        url = f"https://crt.sh/?q=%.{self.target}&output=json"
        try:
            response = self.session.get(url, timeout=10) # 10s timeout
            if response.status_code == 200:
                data = response.json()
                subs = set()
                for entry in data:
                    name_value = entry.get('name_value', '')
                    for sub in name_value.split('\n'):
                        if self.target in sub and '*' not in sub:
                            subs.add(sub.lower())
                return list(subs)[:50]
        except:
            pass
        return [self.target]

    def scan_ports(self, host: str) -> List[Dict]:
        ports_to_scan = [21, 22, 53, 80, 443, 3306, 8080]
        open_ports = []
        
        def check(p):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.5)
                    if s.connect_ex((host, p)) == 0:
                        return p
            except: pass
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            for port in executor.map(check, ports_to_scan):
                if port:
                    open_ports.append({"port": port, "state": "open", "service": socket.getservbyport(port, 'tcp')})
        return open_ports

    def scan_osint(self, domain: str) -> Dict:
        """Harverst emails/info from public main page"""
        emails = set()
        try:
             resp = self.session.get(f"http://{domain}", timeout=5)
             # Regex for emails
             import re
             found = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resp.text)
             for email in found:
                 # Filter out binary garbage or default placeholders
                 if len(email) < 50 and 'example.com' not in email:
                     emails.add(email)
        except: pass
        
        return {"emails": list(emails), "hosts": []}

    def detect_tech(self, host: str) -> Dict:
        summary = {"web_servers": [], "cms": [], "security": []}
        try:
            resp = self.session.get(f"http://{host}", timeout=3)
            
            # Extract headers
            server = resp.headers.get('Server')
            if server: summary['web_servers'].append(server)
            
            # Simple Technology checks
            html = resp.text.lower()
            if 'wp-' in html: summary['cms'].append("WordPress")
            
            # Vulners Check if software found
            if server:
                parts = server.split('/')
                if len(parts) == 2:
                    cves = self.search_vulners(parts[0], parts[1])
                    if cves:
                        summary['vulners_cves'] = cves
                        self.results['security_score'] -= (len(cves) * 10)

            # 2. Offline Intelligence (Fallback)
            if not summary.get('vulners_cves'):
                offline_cves = self.check_offline_db(server)
                if offline_cves:
                    summary['vulners_cves'] = offline_cves
                    self.results['security_score'] -= (len(offline_cves) * 15)

        except: pass
        return summary

    def check_offline_db(self, banner: str) -> List[Dict]:
        """Local fallback database for common vulnerable services"""
        if not banner: return []
        banner = banner.lower()
        cves = []
        
        # OFFLINE VULN LOGIC
        if 'nginx/1.19' in banner or 'nginx/1.18' in banner:
            cves.append({"id": "CVE-2021-23017", "title": "Nginx DNS Resolver Off-by-One Heap Write", "score": 9.8, "link": "https://nvd.nist.gov/vuln/detail/CVE-2021-23017"})
        
        if 'apache/2.4.49' in banner:
             cves.append({"id": "CVE-2021-41773", "title": "Apache Path Traversal (RCE)", "score": 10.0, "link": "https://nvd.nist.gov/vuln/detail/CVE-2021-41773"})
             
        if 'php/5.' in banner:
            cves.append({"id": "EOL-PHP5", "title": "PHP 5.x is End of Life (Critical Risk)", "score": 10.0, "link": "https://www.php.net/eol.php"})
            
        return cves

    def run(self):
        try:
            self.update_status('running')
            
            # 1. Location & Safety
            try:
                target_ip = socket.gethostbyname(self.target)
                self.results['phases']['geoip'] = self.check_ipinfo(target_ip)
                self.results['phases']['safebrowsing'] = self.check_safebrowsing(self.target)
            except: pass

            # 2. Subdomains
            subdomains = self.scan_subdomains()
            self.results['phases']['subdomains'] = subdomains
            
            # Ensure target itself is ALWAYS scanned (Fix for "No host data" bug)
            targets_to_scan = list(set([self.target] + subdomains))[:5] # Deduplicate and limit
            
            # 3. Hosts
            hosts_data = []
            for host in targets_to_scan: 
                host_info = {
                    'host': host,
                    'ports': self.scan_ports(host),
                    'technologies': self.detect_tech(host)
                }
                
                # Check for WordPress specific things
                if host_info['technologies'].get('cms') and 'WordPress' in host_info['technologies']['cms']:
                   # Pro-active WP user check (Example logic)
                   host_info['technologies']['other'] = host_info['technologies'].get('other', []) + ['WP-JSON API Exposed']
                   
                hosts_data.append(host_info)
            
            self.results['phases']['hosts'] = hosts_data
            
            # 4. OSINT
            try:
                self.update_status('gathering_osint')
                osint_data = self.scan_osint(self.target)
                self.results['phases']['osint'] = osint_data
                if osint_data.get('emails'):
                    self.results['metadata']['total_emails_found'] = len(osint_data['emails'])
            except: pass

            # Done
            self.update_status('finished')
            
        except Exception as e:
            logger.error(f"Global Scan Failure: {e}")
            self.update_status('failed')

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('target')
    parser.add_argument('--job-id', required=True)
    args = parser.parse_args()
    
    scanner = PureScanner(args.target, args.job_id)
    scanner.run()
