#!/usr/bin/env python3
"""
Aegis Recon - Enhanced Security Scanning Worker
Complete integration with WhatWeb, theHarvester, enhanced Sublist3r, and Nikto
"""

import sys
import os
import json
import logging
import subprocess
import argparse
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import existing parsers
from parsers.nmap_parser import parse_nmap_xml
from parsers.whatweb_parser import parse_whatweb_json, get_technology_summary, check_outdated_versions
from parsers.harvester_parser import parse_harvester_output, get_osint_summary, prioritize_findings
import progress_tracker

# Get cross-platform temp directory
TEMP_DIR = tempfile.gettempdir()
LOG_FILE = os.path.join(TEMP_DIR, 'scan_worker_enhanced.log')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE)
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Logging to: {LOG_FILE}")


class EnhancedScanWorker:
    """Enhanced scan worker with full tool integration."""
    
    def __init__(self, target: str, job_id: str, mock: bool = False):
        """
        Initialize enhanced scan worker.
        
        Args:
            target: Target domain or IP
            job_id: Unique job identifier
            mock: If True, use mock data for testing
        """
        self.target = target
        self.job_id = job_id
        self.mock = mock
        self.tools_dir = Path(__file__).parent.parent / 'tools'
        self.results = {
            'job_id': job_id,
            'target': target,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'phases': {}
        }
    
    def run_sublist3r_enhanced(self) -> List[str]:
        """
        Run enhanced Sublist3r with multiple engines.
        
        Returns:
            List of discovered subdomains
        """
        logger.info("Phase 1: Enhanced subdomain enumeration")
        
        # Check if target is an IP address - skip subdomain enumeration for IPs
        import re
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ip_pattern, self.target):
            logger.info(f"Target is an IP address ({self.target}), skipping subdomain enumeration")
            return [self.target]
        
        if self.mock:
            logger.info("Mock mode: returning simulated subdomains")
            return [self.target, f"www.{self.target}", f"mail.{self.target}", f"api.{self.target}"]
        
        output_file = os.path.join(TEMP_DIR, f"subdomains-{self.job_id}.txt")
        
        # Get configuration from environment
        threads = os.getenv('SUBLIST3R_THREADS', '50')
        enable_bruteforce = os.getenv('SUBLIST3R_BRUTEFORCE', 'false').lower() == 'true'
        
        cmd = [
            'python',
            str(self.tools_dir / 'Sublist3r-master' / 'sublist3r.py'),
            '-d', self.target,
            '-o', output_file,
            '-t', threads,
            '-v'
        ]
        
        if enable_bruteforce:
            cmd.append('-b')
            logger.info("Brute-force mode enabled")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            # Parse output file
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    subdomains = [line.strip() for line in f if line.strip()]
                logger.info(f"Discovered {len(subdomains)} subdomains")
                return subdomains
            else:
                logger.warning("Sublist3r output file not found")
                return [self.target]
                
        except subprocess.TimeoutExpired:
            logger.error("Sublist3r timed out")
            return [self.target]
        except Exception as e:
            logger.error(f"Error running Sublist3r: {str(e)}")
            return [self.target]
    
    def run_theharvester(self) -> Dict[str, Any]:
        """
        Run theHarvester for OSINT gathering.
        
        Returns:
            Dictionary of OSINT data
        """
        logger.info("Phase 2: OSINT data gathering with theHarvester")
        
        if self.mock:
            logger.info("Mock mode: returning simulated OSINT data")
            return {
                'emails': [f'admin@{self.target}', f'info@{self.target}'],
                'hosts': [self.target, f'www.{self.target}'],
                'ips': ['192.168.1.1'],
                'urls': [],
                'asns': []
            }
        
        output_base = os.path.join(TEMP_DIR, f"harvester-{self.job_id}")
        
        # Build command with free sources
        sources = ['google', 'bing', 'dnsdumpster', 'crtsh', 'virustotal']
        
        # Add premium sources if API keys available
        if os.getenv('SHODAN_API_KEY'):
            sources.append('shodan')
        if os.getenv('HUNTER_API_KEY'):
            sources.append('hunter')
        
        cmd = [
            'python',
            str(self.tools_dir / 'theHarvester' / 'theHarvester-master' / 'theHarvester.py'),
            '-d', self.target,
            '-b', ','.join(sources),
            '-f', output_base,
            '-l', '500'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            osint_data = parse_harvester_output(output_base)
            logger.info(f"OSINT: {get_osint_summary(osint_data)}")
            return osint_data
            
        except subprocess.TimeoutExpired:
            logger.error("theHarvester timed out")
            return {}
        except Exception as e:
            logger.error(f"Error running theHarvester: {str(e)}")
            return {}
    
    def run_nmap(self, host: str) -> Dict[str, Any]:
        """
        Run Nmap port scan on host.
        
        Args:
            host: Target host
            
        Returns:
            Parsed Nmap results
        """
        logger.info(f"Running Nmap on host: {host}")
        
        if self.mock:
            logger.info("Mock mode: returning simulated Nmap results")
            return {
                'host': host,
                'ports': [
                    {'port': 80, 'state': 'open', 'service': 'http', 'version': 'Apache 2.4.41'},
                    {'port': 443, 'state': 'open', 'service': 'https', 'version': 'Apache 2.4.41'}
                ],
                'os': 'Linux'
            }
        
        output_file = os.path.join(TEMP_DIR, f"nmap-{self.job_id}-{host}.xml")
        
        cmd = [
            'nmap',
            '-sV',  # Service version detection
            '-O',   # OS detection
            '--top-ports', '1000',
            '-oX', output_file,
            host
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return parse_nmap_xml(output_file)
        except Exception as e:
            logger.error(f"Error running Nmap: {str(e)}")
            return {'host': host, 'ports': [], 'error': str(e)}
    
    def run_whatweb(self, host: str) -> Dict[str, Any]:
        """
        Run WhatWeb for technology fingerprinting.
        
        Args:
            host: Target host
            
        Returns:
            Parsed technology data
        """
        logger.info(f"Running WhatWeb on host: {host}")
        
        if self.mock:
            logger.info("Mock mode: returning simulated WhatWeb results")
            return {
                'target': host,
                'summary': {
                    'cms': ['WordPress 6.2.1'],
                    'web_servers': ['Apache 2.4.41'],
                    'programming_languages': ['PHP 7.4.3'],
                    'javascript_libraries': ['jQuery 3.6.0'],
                    'frameworks': [],
                    'analytics': ['Google Analytics'],
                    'security': ['HSTS'],
                    'other': []
                }
            }
        
        output_file = os.path.join(TEMP_DIR, f"whatweb-{self.job_id}-{host}.json")
        aggression = os.getenv('WHATWEB_AGGRESSION', '3')
        
        # Ensure host has protocol
        if not host.startswith('http'):
            host = f'http://{host}'
        
        cmd = [
            'ruby',
            str(self.tools_dir / 'WhatWeb' / 'WhatWeb-master' / 'whatweb'),
            '-v',
            '-a', aggression,
            '--follow-redirect=always',  # Follow redirects to scan actual app
            '--max-redirects=5',          # Up to 5 redirects
            '--log-json', output_file,
            '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            host
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            tech_data = parse_whatweb_json(output_file)
            logger.info(f"Technologies: {get_technology_summary(tech_data)}")
            return tech_data
        except Exception as e:
            logger.error(f"Error running WhatWeb: {str(e)}")
            return {}
    
    def run_nikto_enhanced(self, host: str) -> List[Dict[str, Any]]:
        """
        Run enhanced Nikto with tuning options.
        
        Args:
            host: Target host
            
        Returns:
            List of vulnerabilities
        """
        logger.info(f"Running enhanced Nikto on host: {host}")
        
        if self.mock:
            logger.info("Mock mode: returning simulated Nikto results")
            return [
                {
                    'id': '000001',
                    'method': 'GET',
                    'url': f'http://{host}/',
                    'msg': 'Server leaks inodes via ETags',
                    'osvdb': '3233'
                }
            ]
        
        output_file = os.path.join(TEMP_DIR, f"nikto-{self.job_id}-{host}.json")
        tuning = os.getenv('NIKTO_TUNING', '478')  # High-severity only by default
        
        # Try both HTTP and HTTPS
        protocols_to_try = []
        if host.startswith('http://') or host.startswith('https://'):
            protocols_to_try.append(host)
        else:
            # Try HTTPS first (more common), then HTTP
            protocols_to_try = [f'https://{host}', f'http://{host}']
        
        all_vulnerabilities = []
        
        for target_url in protocols_to_try:
            logger.info(f"Nikto scanning: {target_url}")
            
            cmd = [
                'perl',
                str(self.tools_dir / 'Nikto' / 'nikto-master' / 'program' / 'nikto.pl'),
                '-h', target_url,
                '-o', output_file,
                '-Format', 'json',
                '-Tuning', tuning,
                '-timeout', '20',  # Increased timeout
                '-ask', 'no',
                '-nointeractive'
            ]
            
            # Add SSL check for HTTPS
            if target_url.startswith('https'):
                cmd.extend(['-ssl', '-nossl'])  # Try with and without SSL verification
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                
                # Parse Nikto JSON
                if os.path.exists(output_file):
                    with open(output_file, 'r') as f:
                        data = json.load(f)
                    
                    # Check if connection was successful
                    if isinstance(data, dict):
                        if 'vulnerabilities' in data:
                            vulns = data['vulnerabilities']
                            # Filter out connection errors
                            real_vulns = [v for v in vulns if 'Unable to connect' not in v.get('msg', '')]
                            
                            if real_vulns:
                                logger.info(f"Found {len(real_vulns)} vulnerabilities on {target_url}")
                                all_vulnerabilities.extend(real_vulns)
                                break  # Success! No need to try other protocol
                            else:
                                logger.warning(f"Nikto could not connect to {target_url}")
                        elif 'value' in data and isinstance(data['value'], list):
                            # Alternative JSON format
                            for item in data['value']:
                                if 'vulnerabilities' in item:
                                    vulns = item['vulnerabilities']
                                    real_vulns = [v for v in vulns if 'Unable to connect' not in v.get('msg', '')]
                                    if real_vulns:
                                        logger.info(f"Found {len(real_vulns)} vulnerabilities on {target_url}")
                                        all_vulnerabilities.extend(real_vulns)
                                        break
                    
                    # Clean up output file for next attempt
                    if os.path.exists(output_file):
                        os.remove(output_file)
                        
            except subprocess.TimeoutExpired:
                logger.warning(f"Nikto timeout scanning {target_url}")
            except Exception as e:
                logger.warning(f"Nikto error scanning {target_url}: {str(e)}")
        
        if all_vulnerabilities:
            logger.info(f"Total vulnerabilities found: {len(all_vulnerabilities)}")
        else:
            logger.info("No vulnerabilities detected (site may be secure or unreachable)")
        
        return all_vulnerabilities
    
    def scan(self) -> Dict[str, Any]:
        """
        Execute complete enhanced scan workflow with progress tracking.
        
        Returns:
            Complete scan results
        """
        logger.info(f"Starting enhanced scan for {self.target}")
        
        # Initialize progress tracker
        progress_tracker.init_tracker(self.job_id)
        
        # Phase 1: Subdomain Enumeration
        progress_tracker.start_phase(1, f"Enumerating subdomains for {self.target}")
        subdomains = self.run_sublist3r_enhanced()
        self.results['phases']['subdomains'] = subdomains
        progress_tracker.complete_phase(1, f"Found {len(subdomains)} subdomain(s)")
        
        # Phase 2: OSINT Gathering
        progress_tracker.start_phase(2, "Gathering OSINT intelligence")
        osint_data = self.run_theharvester()
        self.results['phases']['osint'] = osint_data
        
        # Add OSINT findings to results
        if osint_data:
            self.results['phases']['osint_findings'] = prioritize_findings(osint_data)
        
        email_count = len(osint_data.get('emails', []))
        progress_tracker.complete_phase(2, f"Discovered {email_count} email(s)")
        
        # Phase 3-5: Scan each discovered host
        host_results = []
        total_hosts = min(len(subdomains), 10)  # Limit to first 10 hosts
        
        for idx, host in enumerate(subdomains[:10], 1):
            logger.info(f"Scanning host: {host}")
            
            # Update progress for current host
            sub_progress = int((idx - 1) / total_hosts * 100)
            progress_tracker.update_activity(f"Scanning host {idx}/{total_hosts}: {host}", sub_progress)
            
            host_data = {
                'host': host,
                'nmap': {},
                'technologies': {},
                'vulnerabilities': []
            }
            
            # Phase 3: Port Scanning
            progress_tracker.start_phase(3, f"Port scanning {host}")
            nmap_results = self.run_nmap(host)
            host_data['nmap'] = nmap_results
            
            open_ports = len(nmap_results.get('ports', []))
            progress_tracker.update_activity(f"Found {open_ports} open port(s) on {host}")
            
            # Check if web service is running
            has_web = any(
                p.get('service', '').lower() in ['http', 'https', 'ssl/http']
                for p in nmap_results.get('ports', [])
            )
            
            if has_web:
                # Phase 4: Technology Fingerprinting
                progress_tracker.start_phase(4, f"Detecting technologies on {host}")
                tech_data = self.run_whatweb(host)
                host_data['technologies'] = tech_data
                
                if tech_data and tech_data.get('summary'):
                    tech_summary = get_technology_summary(tech_data)
                    progress_tracker.update_activity(f"Detected: {tech_summary}")
                
                # Check for outdated versions
                if tech_data:
                    outdated = check_outdated_versions(tech_data)
                    if outdated:
                        host_data['outdated_technologies'] = outdated
                
                # Phase 5: Web Vulnerability Scanning
                progress_tracker.start_phase(5, f"Scanning vulnerabilities on {host}")
                vulns = self.run_nikto_enhanced(host)
                host_data['vulnerabilities'] = vulns
                
                progress_tracker.update_activity(f"Found {len(vulns)} vulnerability/vulnerabilities on {host}")
            
            host_results.append(host_data)
        
        self.results['phases']['hosts'] = host_results
        
        # Generate metadata
        total_vulns = sum(len(h.get('vulnerabilities', [])) for h in host_results)
        self.results['metadata'] = {
            'total_subdomains': len(subdomains),
            'total_hosts_scanned': len(host_results),
            'total_emails_found': len(osint_data.get('emails', [])),
            'total_vulnerabilities': total_vulns,
            'scan_duration': 'N/A',  # Calculate if needed
            'scanner_version': '2.0.0-enhanced'
        }
        
        # Complete progress tracking
        summary = f"Scan complete: {len(host_results)} host(s), {total_vulns} vulnerability/vulnerabilities"
        progress_tracker.complete_scan(summary)
        progress_tracker.close_tracker()
        
        logger.info("Enhanced scan completed successfully")
        return self.results
    
    def save_results(self) -> str:
        """
        Save scan results to JSON file and update database.
        
        Returns:
            Path to results file
        """
        output_path = os.path.join(TEMP_DIR, f"results-enhanced-{self.job_id}.json")
        
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        print(output_path)  # Print for PHP to capture
        
        # Update database status
        self.update_database_status('done', output_path)
        
        return output_path
    
    def update_database_status(self, status: str, results_path: Optional[str] = None, error_msg: Optional[str] = None):
        """
        Update scan status in database.
        
        Args:
            status: Status to set ('done' or 'error')
            results_path: Path to results file
            error_msg: Error message if status is error
        """
        try:
            import mysql.connector
            from pathlib import Path
            
            # Load environment variables
            env_path = Path(__file__).parent.parent / '.env'
            env_vars = {}
            
            if env_path.exists():
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
            
            # Connect to database
            db = mysql.connector.connect(
                host=env_vars.get('DB_HOST', 'localhost'),
                port=int(env_vars.get('DB_PORT', 3306)),
                user=env_vars.get('DB_USER', 'root'),
                password=env_vars.get('DB_PASS', ''),
                database=env_vars.get('DB_NAME', 'aegis_recon')
            )
            
            cursor = db.cursor()
            
            # Load results if available
            results_json = None
            if results_path and os.path.exists(results_path):
                with open(results_path, 'r') as f:
                    results_json = json.dumps(json.load(f))
            
            # Update scan record
            if status == 'done':
                cursor.execute("""
                    UPDATE scans 
                    SET status = 'done',
                        results = %s,
                        completed_at = NOW(),
                        updated_at = NOW()
                    WHERE job_id = %s
                """, (results_json, self.job_id))
            else:
                cursor.execute("""
                    UPDATE scans 
                    SET status = 'error',
                        error_message = %s,
                        completed_at = NOW(),
                        updated_at = NOW()
                    WHERE job_id = %s
                """, (error_msg, self.job_id))
            
            db.commit()
            logger.info(f"Database updated: {self.job_id} -> {status}")
            
            cursor.close()
            db.close()
            
        except Exception as e:
            logger.error(f"Failed to update database: {str(e)}")
            # Don't fail the scan if database update fails


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Aegis Recon - Enhanced Scan Worker')
    parser.add_argument('target', help='Target domain or IP address')
    parser.add_argument('--job-id', required=True, help='Unique job identifier')
    parser.add_argument('--mock', action='store_true', help='Use mock data for testing')
    
    args = parser.parse_args()
    
    # Check environment
    if not args.mock and os.getenv('ALLOW_SCANS') != '1':
        logger.error("ALLOW_SCANS environment variable must be set to '1'")
        sys.exit(1)
    
    try:
        # Create worker and run scan
        worker = EnhancedScanWorker(args.target, args.job_id, args.mock)
        worker.scan()
        worker.save_results()
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
