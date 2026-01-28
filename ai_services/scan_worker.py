#!/usr/bin/env python3
"""
Aegis Recon - Automated Security Scanning Worker
Production-ready script for subdomain enumeration, port scanning, and vulnerability detection.
"""

import sys
import os
import json
import logging
import subprocess
import argparse
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import tempfile

# Get cross-platform temp directory
TEMP_DIR = tempfile.gettempdir()
LOG_FILE = os.path.join(TEMP_DIR, 'scan_worker.log')

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


class ScanWorkerError(Exception):
    """Custom exception for scan worker errors."""
    pass


class EthicsCheckError(ScanWorkerError):
    """Exception raised when ethics checks fail."""
    pass


def ethics_check(target: str) -> None:
    """
    Perform ethics and safety checks before scanning.
    
    Args:
        target: The domain or IP to scan
        
    Raises:
        EthicsCheckError: If ethics checks fail
    """
    logger.info("Performing ethics and safety checks...")
    
    # Check if target is provided
    if not target or target.strip() == "":
        raise EthicsCheckError("Target domain/IP is missing or empty")
    
    # Check ALLOW_SCANS environment variable
    allow_scans = os.environ.get('ALLOW_SCANS', '0')
    if allow_scans != '1':
        raise EthicsCheckError(
            "ALLOW_SCANS environment variable is not set to '1'. "
            "Set ALLOW_SCANS=1 to authorize scanning operations."
        )
    
    logger.info(f"Ethics check passed for target: {target}")


def run_sublist3r(domain: str, mock: bool = False) -> List[str]:
    """
    Run Sublist3r to enumerate subdomains.
    
    Args:
        domain: The domain to enumerate
        mock: If True, return mock data
        
    Returns:
        List of discovered subdomains
    """
    logger.info(f"Running Sublist3r on domain: {domain}")
    
    if mock:
        logger.info("Mock mode: returning simulated subdomains")
        return [domain, f"www.{domain}", f"mail.{domain}", f"api.{domain}"]
    
    try:
        # Check if sublist3r is available
        result = subprocess.run(
            ['python', '-m', 'sublist3r', '-d', domain, '-o', '/tmp/sublist3r_output.txt'],
            check=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Read the output file
        output_file = Path('/tmp/sublist3r_output.txt')
        if output_file.exists():
            with open(output_file, 'r') as f:
                subdomains = [line.strip() for line in f if line.strip()]
            output_file.unlink()  # Clean up
            logger.info(f"Found {len(subdomains)} subdomains")
            return subdomains if subdomains else [domain]
        else:
            logger.warning("Sublist3r output file not found, using target domain only")
            return [domain]
            
    except subprocess.TimeoutExpired:
        logger.error("Sublist3r timed out")
        return [domain]
    except subprocess.CalledProcessError as e:
        logger.error(f"Sublist3r failed: {e.stderr}")
        return [domain]
    except Exception as e:
        logger.error(f"Error running Sublist3r: {str(e)}")
        return [domain]


def run_nmap(host: str, job_id: str, mock: bool = False) -> Dict[str, Any]:
    """
    Run Nmap port scan on a host.
    
    Args:
        host: The host to scan
        job_id: Job identifier
        mock: If True, return mock data
        
    Returns:
        Dictionary with port scan results
    """
    logger.info(f"Running Nmap on host: {host}")
    
    if mock:
        logger.info("Mock mode: returning simulated Nmap results")
        return {
            "host": host,
            "ports": [
                {"port": 22, "service": "ssh", "version": "OpenSSH 7.4"},
                {"port": 80, "service": "http", "version": "nginx 1.14.0"},
                {"port": 443, "service": "https", "version": "nginx 1.14.0"}
            ]
        }
    
    output_file = f"/tmp/scan-{job_id}-{host.replace('.', '_')}.xml"
    
    try:
        # Run nmap with service version detection
        subprocess.run(
            ['nmap', '-sV', '-oX', output_file, host],
            check=True,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        # Parse XML output
        return parse_nmap_xml(output_file, host)
        
    except subprocess.TimeoutExpired:
        logger.error(f"Nmap scan timed out for {host}")
        return {"host": host, "ports": [], "error": "Scan timeout"}
    except subprocess.CalledProcessError as e:
        logger.error(f"Nmap scan failed for {host}: {e.stderr}")
        return {"host": host, "ports": [], "error": str(e)}
    except Exception as e:
        logger.error(f"Error running Nmap on {host}: {str(e)}")
        return {"host": host, "ports": [], "error": str(e)}


def parse_nmap_xml(xml_file: str, host: str) -> Dict[str, Any]:
    """
    Parse Nmap XML output into JSON format.
    
    Args:
        xml_file: Path to Nmap XML output file
        host: The scanned host
        
    Returns:
        Dictionary with parsed port information
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        ports = []
        for port_elem in root.findall(".//port"):
            port_id = port_elem.get('portid')
            protocol = port_elem.get('protocol')
            
            state_elem = port_elem.find('state')
            state = state_elem.get('state') if state_elem is not None else 'unknown'
            
            if state == 'open':
                service_elem = port_elem.find('service')
                service_name = service_elem.get('name', 'unknown') if service_elem is not None else 'unknown'
                service_version = service_elem.get('version', '') if service_elem is not None else ''
                service_product = service_elem.get('product', '') if service_elem is not None else ''
                
                version_str = f"{service_product} {service_version}".strip() if service_product or service_version else ''
                
                ports.append({
                    "port": int(port_id),
                    "protocol": protocol,
                    "service": service_name,
                    "version": version_str
                })
        
        logger.info(f"Parsed {len(ports)} open ports for {host}")
        return {"host": host, "ports": ports}
        
    except Exception as e:
        logger.error(f"Error parsing Nmap XML for {host}: {str(e)}")
        return {"host": host, "ports": [], "error": str(e)}


def has_web_service(ports: List[Dict[str, Any]]) -> bool:
    """
    Check if host has HTTP/HTTPS services.
    
    Args:
        ports: List of port dictionaries
        
    Returns:
        True if web service is detected
    """
    web_ports = {80, 443, 8080, 8443}
    for port_info in ports:
        if port_info.get('port') in web_ports:
            return True
        if 'http' in port_info.get('service', '').lower():
            return True
    return False


def run_nikto(host: str, job_id: str, mock: bool = False) -> List[Dict[str, Any]]:
    """
    Run Nikto web vulnerability scanner.
    
    Args:
        host: The host to scan
        job_id: Job identifier
        mock: If True, return mock data
        
    Returns:
        List of vulnerability findings
    """
    logger.info(f"Running Nikto on host: {host}")
    
    if mock:
        logger.info("Mock mode: returning simulated Nikto results")
        return [
            {
                "id": "000001",
                "method": "GET",
                "url": f"http://{host}/",
                "msg": "Server leaks inodes via ETags",
                "osvdb": "3233"
            },
            {
                "id": "000002",
                "method": "GET",
                "url": f"http://{host}/",
                "msg": "The anti-clickjacking X-Frame-Options header is not present.",
                "osvdb": "0"
            }
        ]
    
    output_file = f"/tmp/nikto-{job_id}-{host.replace('.', '_')}.json"
    nikto_path = "tools/nikto/nikto.pl"
    
    # Check if Nikto exists
    if not Path(nikto_path).exists():
        logger.warning(f"Nikto not found at {nikto_path}, skipping web vulnerability scan")
        return []
    
    try:
        # Run Nikto
        subprocess.run(
            ['perl', nikto_path, '-h', host, '-o', output_file, '-Format', 'json'],
            check=True,
            capture_output=True,
            text=True,
            timeout=900  # 15 minute timeout
        )
        
        # Parse JSON output
        return parse_nikto_json(output_file)
        
    except subprocess.TimeoutExpired:
        logger.error(f"Nikto scan timed out for {host}")
        return []
    except subprocess.CalledProcessError as e:
        logger.error(f"Nikto scan failed for {host}: {e.stderr}")
        return []
    except Exception as e:
        logger.error(f"Error running Nikto on {host}: {str(e)}")
        return []


def parse_nikto_json(json_file: str) -> List[Dict[str, Any]]:
    """
    Parse Nikto JSON output.
    
    Args:
        json_file: Path to Nikto JSON output file
        
    Returns:
        List of vulnerability findings
    """
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        vulnerabilities = []
        
        # Nikto JSON structure can vary, handle common formats
        if isinstance(data, dict):
            # Extract vulnerabilities from various possible locations
            vulns = data.get('vulnerabilities', [])
            if not vulns and 'host' in data:
                vulns = data.get('host', {}).get('vulnerabilities', [])
            
            for vuln in vulns:
                vulnerabilities.append({
                    "id": vuln.get('id', ''),
                    "method": vuln.get('method', 'GET'),
                    "url": vuln.get('url', ''),
                    "msg": vuln.get('msg', ''),
                    "osvdb": vuln.get('OSVDB', '')
                })
        
        logger.info(f"Parsed {len(vulnerabilities)} vulnerabilities from Nikto output")
        return vulnerabilities
        
    except Exception as e:
        logger.error(f"Error parsing Nikto JSON: {str(e)}")
        return []


def combine_results(job_id: str, target: str, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Combine all scan results into normalized JSON format.
    
    Args:
        job_id: Job identifier
        target: Original target domain/IP
        scan_results: List of scan results for each host
        
    Returns:
        Combined results dictionary
    """
    logger.info("Combining scan results into normalized format")
    
    combined = {
        "job_id": job_id,
        "target": target,
        "hosts": scan_results,
        "metadata": {
            "scan_date": datetime.utcnow().isoformat() + "Z",
            "total_hosts": len(scan_results),
            "total_ports": sum(len(h.get('ports', [])) for h in scan_results),
            "total_vulnerabilities": sum(len(h.get('web_vulns', [])) for h in scan_results),
            "scanner_version": "1.0.0"
        }
    }
    
    return combined


def save_results(job_id: str, results: Dict[str, Any]) -> str:
    """
    Save results to JSON file.
    
    Args:
        job_id: Job identifier
        results: Results dictionary
        
    Returns:
        Path to saved results file
    """
    # Use cross-platform temp directory
    output_path = os.path.join(TEMP_DIR, f"results-{job_id}.json")
    
    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error saving results: {str(e)}")
        raise ScanWorkerError(f"Failed to save results: {str(e)}")


def main(target: str, job_id: Optional[str] = None, mock: bool = False) -> int:
    """
    Main scanning workflow.
    
    Args:
        target: Domain or IP to scan
        job_id: Optional job identifier
        mock: If True, run in mock mode
        
    Returns:
        Exit code (0 for success)
    """
    try:
        # Generate job ID if not provided
        if not job_id:
            job_id = str(uuid.uuid4())
        
        logger.info(f"Starting scan job {job_id} for target: {target}")
        
        # Perform ethics checks (skip in mock mode)
        if not mock:
            ethics_check(target)
        else:
            logger.info("Mock mode: skipping ethics checks")
        
        # Step 1: Run Sublist3r
        subdomains = run_sublist3r(target, mock=mock)
        logger.info(f"Discovered {len(subdomains)} subdomains/hosts")
        
        # Step 2-4: Scan each subdomain
        scan_results = []
        
        for subdomain in subdomains:
            logger.info(f"Processing host: {subdomain}")
            
            # Run Nmap
            nmap_result = run_nmap(subdomain, job_id, mock=mock)
            
            host_data = {
                "host": subdomain,
                "ports": nmap_result.get('ports', []),
                "web_vulns": []
            }
            
            # Run Nikto if web service detected
            if has_web_service(host_data['ports']):
                logger.info(f"Web service detected on {subdomain}, running Nikto")
                host_data['web_vulns'] = run_nikto(subdomain, job_id, mock=mock)
            
            scan_results.append(host_data)
        
        # Combine results
        combined_results = combine_results(job_id, target, scan_results)
        
        # Save results
        output_path = save_results(job_id, combined_results)
        
        # Print output path to stdout
        print(output_path)
        
        logger.info(f"Scan job {job_id} completed successfully")
        return 0
        
    except EthicsCheckError as e:
        logger.error(f"Ethics check failed: {str(e)}")
        print(f"ERROR: {str(e)}", file=sys.stderr)
        return 1
        
    except ScanWorkerError as e:
        logger.error(f"Scan worker error: {str(e)}")
        print(f"ERROR: {str(e)}", file=sys.stderr)
        return 1
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        print(f"ERROR: {str(e)}", file=sys.stderr)
        return 1


def test_mock_mode():
    """
    Unit test function for mock mode.
    Runs a simulated scan on 127.0.0.1.
    """
    logger.info("=" * 60)
    logger.info("Running unit test in mock mode")
    logger.info("=" * 60)
    
    test_target = "127.0.0.1"
    test_job_id = "test-" + str(uuid.uuid4())[:8]
    
    try:
        exit_code = main(test_target, test_job_id, mock=True)
        
        if exit_code == 0:
            # Verify output file exists
            output_file = f"/tmp/results-{test_job_id}.json"
            if Path(output_file).exists():
                with open(output_file, 'r') as f:
                    results = json.load(f)
                
                logger.info("Mock test PASSED")
                logger.info(f"Results file: {output_file}")
                logger.info(f"Hosts scanned: {results['metadata']['total_hosts']}")
                logger.info(f"Total ports: {results['metadata']['total_ports']}")
                logger.info(f"Total vulnerabilities: {results['metadata']['total_vulnerabilities']}")
                
                # Clean up test file
                Path(output_file).unlink()
                
                return True
            else:
                logger.error("Mock test FAILED: Output file not created")
                return False
        else:
            logger.error(f"Mock test FAILED: Exit code {exit_code}")
            return False
            
    except Exception as e:
        logger.error(f"Mock test FAILED with exception: {str(e)}")
        return False


if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Aegis Recon - Automated Security Scanning Worker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scan_worker.py example.com --job-id scan-001
  python scan_worker.py 192.168.1.1
  python scan_worker.py --mock  # Run unit test
  
Environment Variables:
  ALLOW_SCANS=1  # Must be set to authorize scanning operations
        """
    )
    
    parser.add_argument(
        'target',
        nargs='?',
        help='Domain or IP address to scan'
    )
    
    parser.add_argument(
        '--job-id',
        type=str,
        help='Optional job identifier'
    )
    
    parser.add_argument(
        '--mock',
        action='store_true',
        help='Run in mock mode for testing (uses 127.0.0.1)'
    )
    
    args = parser.parse_args()
    
    # Handle mock mode
    if args.mock:
        success = test_mock_mode()
        sys.exit(0 if success else 1)
    
    # Validate target argument
    if not args.target:
        parser.print_help()
        print("\nERROR: Target domain/IP is required", file=sys.stderr)
        sys.exit(1)
    
    # Run main workflow
    exit_code = main(args.target, args.job_id)
    sys.exit(exit_code)
