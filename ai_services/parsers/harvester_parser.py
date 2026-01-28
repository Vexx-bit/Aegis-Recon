#!/usr/bin/env python3
"""
theHarvester Parser - Parse theHarvester output for OSINT data
"""

import json
import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Any, Set
import os

logger = logging.getLogger(__name__)


def parse_harvester_output(base_filename: str) -> Dict[str, Any]:
    """
    Parse theHarvester output files (JSON and XML formats).
    
    Args:
        base_filename: Base filename without extension (e.g., '/tmp/harvester-job123')
        
    Returns:
        Dictionary containing parsed OSINT data
    """
    results = {
        'emails': set(),
        'hosts': set(),
        'ips': set(),
        'urls': set(),
        'asns': set(),
        'interesting_urls': [],
        'social_media': [],
        'metadata': {}
    }
    
    # Try JSON format first
    json_file = f"{base_filename}.json"
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Parse JSON structure
            results['emails'] = set(data.get('emails', []))
            results['hosts'] = set(data.get('hosts', []))
            results['ips'] = set(data.get('ips', []))
            results['urls'] = set(data.get('urls', []))
            results['asns'] = set(data.get('asns', []))
            results['interesting_urls'] = data.get('interesting_urls', [])
            
            # Shodan data if available
            if 'shodan' in data:
                results['shodan'] = parse_shodan_data(data['shodan'])
            
            logger.info(f"Parsed theHarvester JSON: {len(results['emails'])} emails, {len(results['hosts'])} hosts")
            
        except Exception as e:
            logger.error(f"Error parsing theHarvester JSON: {str(e)}")
    
    # Try XML format as fallback
    xml_file = f"{base_filename}.xml"
    if os.path.exists(xml_file):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Parse XML structure
            for email in root.findall('.//email'):
                if email.text:
                    results['emails'].add(email.text.strip())
            
            for host in root.findall('.//host'):
                if host.text:
                    results['hosts'].add(host.text.strip())
            
            for ip in root.findall('.//ip'):
                if ip.text:
                    results['ips'].add(ip.text.strip())
            
            logger.info(f"Parsed theHarvester XML: {len(results['emails'])} emails, {len(results['hosts'])} hosts")
            
        except Exception as e:
            logger.error(f"Error parsing theHarvester XML: {str(e)}")
    
    # Convert sets to sorted lists for JSON serialization
    results['emails'] = sorted(list(results['emails']))
    results['hosts'] = sorted(list(results['hosts']))
    results['ips'] = sorted(list(results['ips']))
    results['urls'] = sorted(list(results['urls']))
    results['asns'] = sorted(list(results['asns']))
    
    return results


def parse_shodan_data(shodan_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Shodan data from theHarvester output.
    
    Args:
        shodan_data: Raw Shodan data
        
    Returns:
        Parsed Shodan information
    """
    parsed = {
        'hosts': [],
        'total_results': 0,
        'vulnerabilities': [],
        'open_ports': set(),
        'services': set()
    }
    
    if not shodan_data:
        return parsed
    
    # Parse Shodan results
    results = shodan_data.get('results', [])
    parsed['total_results'] = len(results)
    
    for result in results:
        host_info = {
            'ip': result.get('ip_str', ''),
            'port': result.get('port', 0),
            'transport': result.get('transport', 'tcp'),
            'product': result.get('product', ''),
            'version': result.get('version', ''),
            'os': result.get('os', ''),
            'org': result.get('org', ''),
            'isp': result.get('isp', ''),
            'asn': result.get('asn', ''),
            'hostnames': result.get('hostnames', []),
            'domains': result.get('domains', []),
            'vulns': result.get('vulns', [])
        }
        
        parsed['hosts'].append(host_info)
        
        # Collect open ports
        if host_info['port']:
            parsed['open_ports'].add(host_info['port'])
        
        # Collect services
        if host_info['product']:
            service_str = f"{host_info['product']}"
            if host_info['version']:
                service_str += f" {host_info['version']}"
            parsed['services'].add(service_str)
        
        # Collect vulnerabilities
        if host_info['vulns']:
            for vuln in host_info['vulns']:
                parsed['vulnerabilities'].append({
                    'ip': host_info['ip'],
                    'port': host_info['port'],
                    'cve': vuln,
                    'service': host_info['product']
                })
    
    # Convert sets to sorted lists
    parsed['open_ports'] = sorted(list(parsed['open_ports']))
    parsed['services'] = sorted(list(parsed['services']))
    
    return parsed


def analyze_email_patterns(emails: List[str]) -> Dict[str, Any]:
    """
    Analyze email patterns to identify naming conventions.
    
    Args:
        emails: List of email addresses
        
    Returns:
        Analysis of email patterns
    """
    if not emails:
        return {}
    
    patterns = {
        'total': len(emails),
        'domains': {},
        'naming_conventions': {
            'firstname.lastname': 0,
            'firstnamelastname': 0,
            'first.last': 0,
            'flastname': 0,
            'firstnamel': 0,
            'other': 0
        }
    }
    
    for email in emails:
        if '@' not in email:
            continue
        
        local, domain = email.split('@', 1)
        
        # Count by domain
        patterns['domains'][domain] = patterns['domains'].get(domain, 0) + 1
        
        # Analyze naming convention
        if '.' in local:
            parts = local.split('.')
            if len(parts) == 2:
                patterns['naming_conventions']['firstname.lastname'] += 1
            else:
                patterns['naming_conventions']['other'] += 1
        elif len(local) > 1 and local[0].islower() and local[1:].islower():
            if len(local) > 10:
                patterns['naming_conventions']['firstnamelastname'] += 1
            else:
                patterns['naming_conventions']['other'] += 1
        else:
            patterns['naming_conventions']['other'] += 1
    
    # Determine most common pattern
    max_count = 0
    common_pattern = 'unknown'
    for pattern, count in patterns['naming_conventions'].items():
        if count > max_count:
            max_count = count
            common_pattern = pattern
    
    patterns['common_pattern'] = common_pattern
    
    return patterns


def get_osint_summary(osint_data: Dict[str, Any]) -> str:
    """
    Generate human-readable summary of OSINT data.
    
    Args:
        osint_data: Parsed OSINT data
        
    Returns:
        Summary string
    """
    parts = []
    
    if osint_data.get('emails'):
        parts.append(f"{len(osint_data['emails'])} emails")
    
    if osint_data.get('hosts'):
        parts.append(f"{len(osint_data['hosts'])} hosts")
    
    if osint_data.get('ips'):
        parts.append(f"{len(osint_data['ips'])} IPs")
    
    if osint_data.get('shodan'):
        shodan = osint_data['shodan']
        if shodan.get('open_ports'):
            parts.append(f"{len(shodan['open_ports'])} open ports (Shodan)")
        if shodan.get('vulnerabilities'):
            parts.append(f"{len(shodan['vulnerabilities'])} CVEs (Shodan)")
    
    return ", ".join(parts) if parts else "No OSINT data collected"


def prioritize_findings(osint_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Prioritize OSINT findings by risk/importance.
    
    Args:
        osint_data: Parsed OSINT data
        
    Returns:
        List of prioritized findings
    """
    findings = []
    
    # High priority: Shodan vulnerabilities
    if osint_data.get('shodan', {}).get('vulnerabilities'):
        for vuln in osint_data['shodan']['vulnerabilities']:
            findings.append({
                'priority': 'high',
                'type': 'vulnerability',
                'title': f"CVE {vuln['cve']} on {vuln['ip']}:{vuln['port']}",
                'description': f"Known vulnerability in {vuln['service']}",
                'data': vuln
            })
    
    # Medium priority: Exposed database ports
    if osint_data.get('shodan', {}).get('open_ports'):
        db_ports = {3306, 5432, 27017, 6379, 1433, 3389}
        exposed_db_ports = set(osint_data['shodan']['open_ports']) & db_ports
        if exposed_db_ports:
            findings.append({
                'priority': 'medium',
                'type': 'exposed_service',
                'title': f"Exposed database ports: {', '.join(map(str, exposed_db_ports))}",
                'description': "Database services accessible from internet",
                'data': {'ports': list(exposed_db_ports)}
            })
    
    # Low priority: Email addresses (for awareness)
    if osint_data.get('emails'):
        email_count = len(osint_data['emails'])
        if email_count > 10:
            findings.append({
                'priority': 'low',
                'type': 'information_disclosure',
                'title': f"{email_count} email addresses discovered",
                'description': "Email addresses may be used for social engineering",
                'data': {'count': email_count, 'sample': osint_data['emails'][:5]}
            })
    
    return findings


if __name__ == '__main__':
    # Test the parser
    import sys
    
    if len(sys.argv) > 1:
        result = parse_harvester_output(sys.argv[1])
        print(json.dumps(result, indent=2, default=str))
        print("\nSummary:", get_osint_summary(result))
        
        if result.get('emails'):
            patterns = analyze_email_patterns(result['emails'])
            print(f"\nEmail Pattern: {patterns.get('common_pattern', 'unknown')}")
        
        findings = prioritize_findings(result)
        if findings:
            print("\nPrioritized Findings:")
            for finding in findings:
                print(f"  [{finding['priority'].upper()}] {finding['title']}")
