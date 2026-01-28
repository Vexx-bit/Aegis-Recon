"""
Intelligence Helpers - Additional data collection utilities
Provides DNS, WHOIS, SSL certificate analysis, and other intelligence gathering functions.
"""

import logging
import socket
import ssl
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


def get_dns_records(domain: str) -> Dict[str, List[str]]:
    """
    Get comprehensive DNS records for a domain.
    
    Args:
        domain: Target domain
        
    Returns:
        Dictionary of DNS record types and their values
    """
    try:
        import dns.resolver
    except ImportError:
        logger.warning("dnspython not installed, skipping DNS records")
        return {}
    
    records = {}
    record_types = ['A', 'AAAA', 'MX', 'TXT', 'NS', 'SOA', 'CNAME']
    
    for rtype in record_types:
        try:
            answers = dns.resolver.resolve(domain, rtype, lifetime=10)
            records[rtype] = [str(rdata) for rdata in answers]
            logger.info(f"DNS {rtype}: Found {len(records[rtype])} records")
        except dns.resolver.NXDOMAIN:
            logger.debug(f"DNS {rtype}: Domain does not exist")
            records[rtype] = []
        except dns.resolver.NoAnswer:
            logger.debug(f"DNS {rtype}: No records found")
            records[rtype] = []
        except dns.resolver.Timeout:
            logger.warning(f"DNS {rtype}: Query timeout")
            records[rtype] = []
        except Exception as e:
            logger.debug(f"DNS {rtype}: Error - {str(e)}")
            records[rtype] = []
    
    return records


def get_whois_info(domain: str) -> Dict[str, Any]:
    """
    Get WHOIS registration information for a domain.
    
    Args:
        domain: Target domain
        
    Returns:
        Dictionary of WHOIS information
    """
    try:
        import whois
    except ImportError:
        logger.warning("python-whois not installed, skipping WHOIS lookup")
        return {}
    
    try:
        w = whois.whois(domain)
        
        # Handle dates which might be lists or single values
        creation_date = w.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0] if creation_date else None
        
        expiration_date = w.expiration_date
        if isinstance(expiration_date, list):
            expiration_date = expiration_date[0] if expiration_date else None
        
        return {
            'registrar': w.registrar,
            'creation_date': str(creation_date) if creation_date else None,
            'expiration_date': str(expiration_date) if expiration_date else None,
            'name_servers': w.name_servers if w.name_servers else [],
            'emails': w.emails if w.emails else [],
            'status': w.status if hasattr(w, 'status') else None
        }
    except Exception as e:
        logger.warning(f"WHOIS lookup failed: {str(e)}")
        return {}


def analyze_ssl_certificate(host: str, port: int = 443) -> Dict[str, Any]:
    """
    Analyze SSL/TLS certificate for a host.
    
    Args:
        host: Target hostname
        port: SSL port (default 443)
        
    Returns:
        Dictionary of certificate information
    """
    try:
        context = ssl.create_default_context()
        
        with socket.create_connection((host, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                
                # Extract subject and issuer
                subject = dict(x[0] for x in cert.get('subject', []))
                issuer = dict(x[0] for x in cert.get('issuer', []))
                
                # Extract SAN (Subject Alternative Names)
                san = []
                for item in cert.get('subjectAltName', []):
                    if item[0] == 'DNS':
                        san.append(item[1])
                
                return {
                    'subject': subject,
                    'issuer': issuer,
                    'version': cert.get('version'),
                    'serial_number': cert.get('serialNumber'),
                    'not_before': cert.get('notBefore'),
                    'not_after': cert.get('notAfter'),
                    'subject_alt_names': san,
                    'common_name': subject.get('commonName'),
                    'organization': subject.get('organizationName'),
                    'issuer_name': issuer.get('commonName')
                }
    except socket.timeout:
        logger.warning(f"SSL certificate analysis timeout for {host}:{port}")
        return {}
    except ssl.SSLError as e:
        logger.warning(f"SSL error for {host}:{port}: {str(e)}")
        return {}
    except Exception as e:
        logger.debug(f"SSL certificate analysis failed: {str(e)}")
        return {}


def is_ip_address(target: str) -> bool:
    """
    Check if target is an IP address.
    
    Args:
        target: Target string to check
        
    Returns:
        True if target is an IP address, False otherwise
    """
    import re
    
    # IPv4 pattern
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if re.match(ipv4_pattern, target):
        # Validate octets are 0-255
        octets = target.split('.')
        return all(0 <= int(octet) <= 255 for octet in octets)
    
    # IPv6 pattern (simplified)
    ipv6_pattern = r'^([0-9a-fA-F]{0,4}:){7}[0-9a-fA-F]{0,4}$'
    if re.match(ipv6_pattern, target):
        return True
    
    return False


def get_scan_strategy(target: str) -> Dict[str, bool]:
    """
    Determine scan strategy based on target type (IP vs domain).
    
    Args:
        target: Target to scan
        
    Returns:
        Dictionary of features to enable/disable
    """
    if is_ip_address(target):
        return {
            'subdomain_enum': False,
            'osint': False,
            'whois': False,
            'dns_records': False,
            'ssl_cert_analysis': True,
            'enhanced_os_detection': True,
            'network_info': True,
            'service_detection': True
        }
    else:
        return {
            'subdomain_enum': True,
            'osint': True,
            'whois': True,
            'dns_records': True,
            'ssl_cert_analysis': True,
            'enhanced_os_detection': False,
            'network_info': False,
            'service_detection': True
        }


def extract_domain_from_url(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: URL string
        
    Returns:
        Domain name
    """
    from urllib.parse import urlparse
    
    parsed = urlparse(url if '://' in url else f'http://{url}')
    return parsed.netloc or parsed.path


def get_reverse_dns(ip: str) -> Optional[str]:
    """
    Get reverse DNS (PTR record) for an IP address.
    
    Args:
        ip: IP address
        
    Returns:
        Hostname or None
    """
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except (socket.herror, socket.gaierror):
        return None
    except Exception as e:
        logger.debug(f"Reverse DNS lookup failed: {str(e)}")
        return None


def get_geolocation(ip: str) -> Dict[str, Any]:
    """
    Get geolocation information for an IP address.
    Note: Requires external API or GeoIP database.
    
    Args:
        ip: IP address
        
    Returns:
        Dictionary of geolocation data
    """
    # Placeholder for future implementation
    # Could integrate with MaxMind GeoIP, ip-api.com, etc.
    logger.debug(f"Geolocation lookup not yet implemented for {ip}")
    return {}
