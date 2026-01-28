#!/usr/bin/env python3
"""
Aegis Recon - "Pure" Python Scanner
Zero external binary dependencies (No Nmap, No Ruby, No Perl).
Relying on socket calls, HTTP headers, and public APIs.
"""

import sys
import os
import json
import logging
import socket
import requests
import concurrent.futures
import re
from datetime import datetime
from urllib.parse import urlparse
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PureScanner:
    def __init__(self, target: str, job_id: str):
        self.target = target
        self.job_id = job_id
        self.results = {
            'job_id': job_id,
            'target': target,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'phases': {}
        }
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Security-Research)'})

    # -------------------------------------------------------------------------
    # Phase 1: Subdomain Enumeration (crt.sh API) - Replaces Sublist3r
    # -------------------------------------------------------------------------
    def scan_subdomains(self) -> List[str]:
        logger.info("Phase 1: Querying crt.sh for subdomains...")
        url = f"https://crt.sh/?q=%.{self.target}&output=json"
        
        try:
            response = self.session.get(url, timeout=20)
            if response.status_code == 200:
                data = response.json()
                # Extract and clean subdomains
                subs = set()
                for entry in data:
                    name_value = entry.get('name_value', '')
                    for sub in name_value.split('\n'):
                        if self.target in sub and '*' not in sub:
                            subs.add(sub.lower())
                
                results = list(subs)
                logger.info(f"crt.sh found {len(results)} subdomains")
                return results[:50] # Limit to top 50 to save time
        except Exception as e:
            logger.error(f"CRT.sh API failed: {e}")
            
        return [self.target] # Fallback to target only

    # -------------------------------------------------------------------------
    # Phase 2: Port Scanning (Python Socket) - Replaces Nmap
    # -------------------------------------------------------------------------
    def check_port(self, host: str, port: int) -> int:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1.0) # Fast timeout
                if s.connect_ex((host, port)) == 0:
                    return port
        except:
            pass
        return None

    def scan_ports(self, host: str) -> List[Dict]:
        logger.info(f"Phase 2: Scanning ports for {host}")
        # Top 20 Common Ports
        ports_to_scan = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 3306, 3389, 5900, 8080, 8443]
        open_ports = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_port = {executor.submit(self.check_port, host, port): port for port in ports_to_scan}
            for future in concurrent.futures.as_completed(future_to_port):
                port = future.result()
                if port:
                    service_name = socket.getservbyport(port) if port else "unknown"
                    open_ports.append({
                        "port": port,
                        "state": "open",
                        "service": service_name,
                        "version": "" # Passive scan can't easily get version without banners
                    })
        
        return open_ports

    # -------------------------------------------------------------------------
    # Phase 3: Tech Detection (Headers & Source) - Replaces WhatWeb
    # -------------------------------------------------------------------------
    def detect_tech(self, host: str) -> Dict[str, Any]:
        logger.info(f"Phase 3: Detecting technologies on {host}")
        summary = {
            "web_servers": [],
            "cms": [],
            "security": [],
            "languages": []
        }
        
        protocols = ['https', 'http']
        for proto in protocols:
            try:
                target_url = f"{proto}://{host}"
                resp = self.session.get(target_url, timeout=5)
                
                # Check Headers
                server = resp.headers.get('Server')
                if server: summary['web_servers'].append(server)
                
                powered_by = resp.headers.get('X-Powered-By')
                if powered_by: summary['languages'].append(powered_by)
                
                # Simple Body Checks (Naive Wappalyzer)
                html = resp.text.lower()
                if 'wp-content' in html: summary['cms'].append("WordPress")
                if 'drupal' in html: summary['cms'].append("Drupal")
                if 'laravel' in html: summary['languages'].append("Laravel (PHP)")
                if 'react' in html: summary['languages'].append("React")
                if 'bootstrap' in html: summary['web_servers'].append("Bootstrap UI")
                
                # Check Security Headers
                if 'strict-transport-security' in resp.headers: summary['security'].append("HSTS Enabled")
                else: summary['security'].append("Missing HSTS")
                
                if 'x-frame-options' not in resp.headers: summary['security'].append("Missing Clickjack Protection")
                
                break # If successful, stop trying
            except:
                continue
                
        return {"summary": summary}
        
    def run(self):
        # 1. Subdomains
        subdomains = self.scan_subdomains()
        self.results['phases']['subdomains'] = subdomains
        
        # 2. Host Analysis
        valid_hosts = []
        hosts_data = []
        
        # Only scan first 5 subdomains to be fast/demo-friendly
        for host in subdomains[:5]: 
            host_info = {
                'host': host,
                'ports': [],
                'technologies': {},
                'vulnerabilities': []
            }
            
            # Port Scan
            ports = self.scan_ports(host)
            host_info['ports'] = ports
            
            if ports: # If host is alive
                # Tech Detect
                host_info['technologies'] = self.detect_tech(host)
                
                # Simple Vuln Logic (e.g. Missing Headers)
                sec_issues = host_info['technologies']['summary'].get('security', [])
                for issue in sec_issues:
                    if "Missing" in issue:
                        host_info['vulnerabilities'].append({
                            "id": "HEADER_MISSING",
                            "msg": f"Security Header Issue: {issue}",
                            "severity": "Low"
                        })
            
            hosts_data.append(host_info)
            
        self.results['phases']['hosts'] = hosts_data
        
        # Metadata
        self.results['metadata'] = {
            'total_subdomains': len(subdomains),
            'total_hosts_scanned': len(hosts_data),
            'total_vulnerabilities': sum(len(h['vulnerabilities']) for h in hosts_data),
            'scan_duration': 'N/A'
        }
        
        return self.results

    def save_results(self):
        temp_dir = os.environ.get('TEMP', '/tmp')
        output_file = os.path.join(temp_dir, f"results-enhanced-{self.job_id}.json")
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        print(output_file) # For PHP to read
        
        # Database Update Mock (Since we are pure python, we assume the caller handles DB or we use basic SQL)
        # In a real deployed pure script, we'd add mysql-connector here.
        # For now, we print the path successfully.

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('target')
    parser.add_argument('--job-id', required=True)
    args = parser.parse_args()
    
    scanner = PureScanner(args.target, args.job_id)
    scanner.run()
    scanner.save_results()
