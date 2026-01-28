#!/usr/bin/env python3
"""
Aegis Recon - Risk Scoring and Normalization Module
Analyzes scan results and calculates deterministic risk scores.
"""

import json
import sys
import re
from typing import Dict, List, Any, Tuple
from datetime import datetime


# Database ports that should not be exposed to the internet
DATABASE_PORTS = {
    3306: 'MySQL',
    5432: 'PostgreSQL',
    1433: 'MS SQL Server',
    1521: 'Oracle',
    27017: 'MongoDB',
    6379: 'Redis',
    5984: 'CouchDB',
    9200: 'Elasticsearch',
    7000: 'Cassandra',
    8086: 'InfluxDB'
}

# Known vulnerable/outdated service versions
OUTDATED_SERVICES = {
    'apache': {
        'pattern': r'Apache/(\d+\.\d+)',
        'vulnerable_versions': ['2.2', '2.0', '1.3'],
        'description': 'Apache HTTP Server'
    },
    'nginx': {
        'pattern': r'nginx[/ ](\d+\.\d+)',
        'vulnerable_versions': ['1.0', '1.1', '1.2', '1.3', '1.4', '1.5', '1.6', '1.7', '1.8', '1.9', '1.10'],
        'description': 'Nginx Web Server'
    },
    'openssh': {
        'pattern': r'OpenSSH[_ ](\d+\.\d+)',
        'vulnerable_versions': ['5.0', '5.1', '5.2', '5.3', '5.4', '5.5', '5.6', '5.7', '5.8', '5.9', '6.0', '6.1', '6.2', '6.3', '6.4', '6.5', '6.6'],
        'description': 'OpenSSH'
    },
    'mysql': {
        'pattern': r'MySQL[/ ](\d+\.\d+)',
        'vulnerable_versions': ['5.0', '5.1', '5.5'],
        'description': 'MySQL Database'
    },
    'php': {
        'pattern': r'PHP[/ ](\d+\.\d+)',
        'vulnerable_versions': ['5.0', '5.1', '5.2', '5.3', '5.4', '5.5', '5.6', '7.0', '7.1'],
        'description': 'PHP'
    }
}

# High severity vulnerability keywords
HIGH_SEVERITY_KEYWORDS = [
    'sql injection',
    'remote code execution',
    'rce',
    'authentication bypass',
    'privilege escalation',
    'arbitrary file upload',
    'directory traversal',
    'command injection',
    'xxe',
    'xml external entity',
    'deserialization',
    'buffer overflow'
]


class RiskScorer:
    """Calculate risk scores for scan results."""
    
    def __init__(self):
        self.findings = []
        self.total_score = 0
    
    def analyze_scan_results(self, scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze scan results and calculate risk score.
        
        Args:
            scan_data: Normalized scan results from scan_worker
            
        Returns:
            Dictionary with risk_score and finding_scores
        """
        self.findings = []
        self.total_score = 0
        
        # Analyze each host
        for host in scan_data.get('hosts', []):
            self._analyze_host(host)
        
        # Cap score at 100
        final_score = min(self.total_score, 100)
        
        return {
            'risk_score': final_score,
            'risk_level': self._get_risk_level(final_score),
            'finding_scores': self.findings,
            'metadata': {
                'total_findings': len(self.findings),
                'analyzed_at': datetime.utcnow().isoformat() + 'Z',
                'target': scan_data.get('target', 'unknown'),
                'job_id': scan_data.get('job_id', 'unknown')
            }
        }
    
    def _analyze_host(self, host: Dict[str, Any]) -> None:
        """Analyze a single host for security issues."""
        hostname = host.get('host', 'unknown')
        
        # Check for exposed database ports
        self._check_database_ports(hostname, host.get('ports', []))
        
        # Check for outdated services
        self._check_outdated_services(hostname, host.get('ports', []))
        
        # Check for web vulnerabilities
        self._check_web_vulnerabilities(hostname, host.get('web_vulns', []))
    
    def _check_database_ports(self, hostname: str, ports: List[Dict[str, Any]]) -> None:
        """Check for exposed database ports."""
        for port_info in ports:
            port = port_info.get('port')
            state = port_info.get('state', 'unknown')
            
            if port in DATABASE_PORTS and state == 'open':
                points = 30
                self.total_score += points
                
                self.findings.append({
                    'type': 'exposed_database_port',
                    'severity': 'HIGH',
                    'points': points,
                    'host': hostname,
                    'port': port,
                    'service': DATABASE_PORTS[port],
                    'rationale': f'{DATABASE_PORTS[port]} (port {port}) is exposed to the internet. '
                                f'Database services should not be directly accessible from external networks.',
                    'recommendation': f'Restrict access to port {port} using firewall rules. '
                                    f'Only allow connections from trusted IP addresses.'
                })
    
    def _check_outdated_services(self, hostname: str, ports: List[Dict[str, Any]]) -> None:
        """Check for outdated or vulnerable service versions."""
        for port_info in ports:
            service = port_info.get('service', '').lower()
            version = port_info.get('version', '')
            port = port_info.get('port')
            
            if not version:
                continue
            
            # Check against known outdated services
            for service_key, service_config in OUTDATED_SERVICES.items():
                if service_key in service.lower() or service_key in version.lower():
                    # Extract version number
                    match = re.search(service_config['pattern'], version, re.IGNORECASE)
                    if match:
                        detected_version = match.group(1)
                        
                        # Check if version is in vulnerable list
                        if any(vuln_ver in detected_version for vuln_ver in service_config['vulnerable_versions']):
                            points = 10
                            self.total_score += points
                            
                            self.findings.append({
                                'type': 'outdated_service',
                                'severity': 'MEDIUM',
                                'points': points,
                                'host': hostname,
                                'port': port,
                                'service': service_config['description'],
                                'version': detected_version,
                                'rationale': f'{service_config["description"]} version {detected_version} is outdated '
                                           f'and may contain known security vulnerabilities.',
                                'recommendation': f'Update {service_config["description"]} to the latest stable version.'
                            })
    
    def _check_web_vulnerabilities(self, hostname: str, vulnerabilities: List[Dict[str, Any]]) -> None:
        """Check for web vulnerabilities from Nikto or similar scanners."""
        for vuln in vulnerabilities:
            msg = vuln.get('msg', '').lower()
            vuln_id = vuln.get('id', 'unknown')
            url = vuln.get('url', '')
            
            # Determine severity based on keywords
            is_high_severity = any(keyword in msg for keyword in HIGH_SEVERITY_KEYWORDS)
            
            if is_high_severity:
                points = 50
                severity = 'CRITICAL'
            else:
                points = 15
                severity = 'MEDIUM'
            
            self.total_score += points
            
            self.findings.append({
                'type': 'web_vulnerability',
                'severity': severity,
                'points': points,
                'host': hostname,
                'url': url,
                'vulnerability_id': vuln_id,
                'description': vuln.get('msg', 'Unknown vulnerability'),
                'rationale': f'Web vulnerability detected: {vuln.get("msg", "Unknown")}. '
                           f'{"This is a critical security issue that could lead to system compromise." if is_high_severity else "This vulnerability should be addressed to improve security posture."}',
                'recommendation': 'Review and remediate the identified vulnerability. '
                                'Consult security advisories for specific mitigation steps.'
            })
    
    def _get_risk_level(self, score: int) -> str:
        """Get risk level based on score."""
        if score >= 70:
            return 'CRITICAL'
        elif score >= 50:
            return 'HIGH'
        elif score >= 30:
            return 'MEDIUM'
        else:
            return 'LOW'


def normalize_and_score(scan_results_path: str, output_path: str = None) -> Dict[str, Any]:
    """
    Load scan results, calculate risk score, and save output.
    
    Args:
        scan_results_path: Path to scan results JSON file
        output_path: Optional path to save scored results
        
    Returns:
        Dictionary with risk scoring results
    """
    # Load scan results
    try:
        with open(scan_results_path, 'r') as f:
            scan_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Scan results file not found: {scan_results_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in scan results: {str(e)}")
    
    # Calculate risk score
    scorer = RiskScorer()
    results = scorer.analyze_scan_results(scan_data)
    
    # Save output if path provided
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Risk scoring results saved to: {output_path}")
    
    return results


# ============================================================================
# UNIT TESTS
# ============================================================================

def create_test_case_1() -> Dict[str, Any]:
    """
    Test Case 1: Low Risk - Clean scan with no major issues
    Expected Score: ~0-20
    """
    return {
        "job_id": "test_001",
        "target": "secure-example.com",
        "hosts": [
            {
                "host": "secure-example.com",
                "ports": [
                    {"port": 443, "protocol": "tcp", "service": "https", "version": "nginx 1.20.0", "state": "open"},
                    {"port": 22, "protocol": "tcp", "service": "ssh", "version": "OpenSSH 8.2", "state": "open"}
                ],
                "web_vulns": []
            }
        ],
        "metadata": {
            "scan_date": "2025-10-29T10:00:00Z",
            "total_hosts": 1,
            "total_ports": 2,
            "total_vulnerabilities": 0
        }
    }


def create_test_case_2() -> Dict[str, Any]:
    """
    Test Case 2: Medium Risk - Exposed database + outdated service
    Expected Score: ~40-50
    """
    return {
        "job_id": "test_002",
        "target": "vulnerable-site.com",
        "hosts": [
            {
                "host": "vulnerable-site.com",
                "ports": [
                    {"port": 80, "protocol": "tcp", "service": "http", "version": "Apache 2.2.15", "state": "open"},
                    {"port": 3306, "protocol": "tcp", "service": "mysql", "version": "MySQL 5.5.62", "state": "open"},
                    {"port": 22, "protocol": "tcp", "service": "ssh", "version": "OpenSSH 6.6", "state": "open"}
                ],
                "web_vulns": [
                    {
                        "id": "000123",
                        "method": "GET",
                        "url": "http://vulnerable-site.com/",
                        "msg": "Server leaks inodes via ETags"
                    }
                ]
            }
        ],
        "metadata": {
            "scan_date": "2025-10-29T10:00:00Z",
            "total_hosts": 1,
            "total_ports": 3,
            "total_vulnerabilities": 1
        }
    }


def create_test_case_3() -> Dict[str, Any]:
    """
    Test Case 3: Critical Risk - Multiple exposed databases + high severity vulns
    Expected Score: 100 (capped)
    """
    return {
        "job_id": "test_003",
        "target": "critical-risk.com",
        "hosts": [
            {
                "host": "critical-risk.com",
                "ports": [
                    {"port": 3306, "protocol": "tcp", "service": "mysql", "version": "MySQL 5.0", "state": "open"},
                    {"port": 5432, "protocol": "tcp", "service": "postgresql", "version": "PostgreSQL 9.0", "state": "open"},
                    {"port": 27017, "protocol": "tcp", "service": "mongodb", "version": "MongoDB 2.4", "state": "open"},
                    {"port": 80, "protocol": "tcp", "service": "http", "version": "Apache 2.0", "state": "open"}
                ],
                "web_vulns": [
                    {
                        "id": "000456",
                        "method": "POST",
                        "url": "http://critical-risk.com/login",
                        "msg": "SQL injection vulnerability detected in login form"
                    },
                    {
                        "id": "000789",
                        "method": "GET",
                        "url": "http://critical-risk.com/upload",
                        "msg": "Remote code execution possible via file upload"
                    }
                ]
            }
        ],
        "metadata": {
            "scan_date": "2025-10-29T10:00:00Z",
            "total_hosts": 1,
            "total_ports": 4,
            "total_vulnerabilities": 2
        }
    }


def run_unit_tests():
    """Run unit tests with sample cases."""
    print("=" * 70)
    print("RISK SCORING MODULE - UNIT TESTS")
    print("=" * 70)
    
    test_cases = [
        ("Test Case 1: Low Risk (Clean Scan)", create_test_case_1(), 0, 20),
        ("Test Case 2: Medium Risk (Exposed DB + Outdated)", create_test_case_2(), 40, 70),
        ("Test Case 3: Critical Risk (Multiple Issues)", create_test_case_3(), 90, 100)
    ]
    
    scorer = RiskScorer()
    all_passed = True
    
    for i, (name, test_data, min_score, max_score) in enumerate(test_cases, 1):
        print(f"\n[{i}] {name}")
        print("-" * 70)
        
        try:
            results = scorer.analyze_scan_results(test_data)
            
            score = results['risk_score']
            level = results['risk_level']
            findings = results['finding_scores']
            
            print(f"Target: {test_data['target']}")
            print(f"Risk Score: {score}/100")
            print(f"Risk Level: {level}")
            print(f"Total Findings: {len(findings)}")
            
            # Validate score is in expected range
            if min_score <= score <= max_score:
                print(f"✓ Score in expected range ({min_score}-{max_score})")
            else:
                print(f"✗ Score outside expected range ({min_score}-{max_score})")
                all_passed = False
            
            # Display findings
            print("\nFindings Breakdown:")
            for finding in findings:
                print(f"  - [{finding['severity']}] {finding['type']}: +{finding['points']} points")
                print(f"    {finding['rationale']}")
            
            # Display full JSON
            print("\nFull Results JSON:")
            print(json.dumps(results, indent=2))
            
        except Exception as e:
            print(f"✗ Test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("ALL TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ✗")
    print("=" * 70)
    
    return all_passed


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            # Run unit tests
            success = run_unit_tests()
            sys.exit(0 if success else 1)
        else:
            # Process scan results file
            input_file = sys.argv[1]
            output_file = sys.argv[2] if len(sys.argv) > 2 else None
            
            try:
                results = normalize_and_score(input_file, output_file)
                print(json.dumps(results, indent=2))
                sys.exit(0)
            except Exception as e:
                print(f"Error: {str(e)}", file=sys.stderr)
                sys.exit(1)
    else:
        # Run unit tests by default
        print("Usage:")
        print("  python normalize_and_score.py --test                    # Run unit tests")
        print("  python normalize_and_score.py <input.json> [output.json] # Score scan results")
        print("\nRunning unit tests...\n")
        run_unit_tests()
