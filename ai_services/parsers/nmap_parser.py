#!/usr/bin/env python3
"""
Nmap XML Parser Module
Parses Nmap XML output files into normalized JSON format.
"""

import xml.etree.ElementTree as ET
import json
import os
import tempfile
from typing import Dict, List, Any, Optional
from pathlib import Path


class NmapParserError(Exception):
    """Custom exception for Nmap parsing errors."""
    pass


def parse_nmap_xml(xml_path: str) -> Dict[str, Any]:
    """
    Parse Nmap XML output file into normalized JSON format.
    
    Args:
        xml_path: Path to the Nmap XML output file
        
    Returns:
        Dictionary containing parsed scan results with the following structure:
        {
            "host": "192.168.1.1",
            "hostname": "example.com",
            "state": "up",
            "ports": [
                {
                    "port": 80,
                    "protocol": "tcp",
                    "state": "open",
                    "service": "http",
                    "version": "nginx 1.14.0"
                }
            ],
            "os": "Linux 3.X|4.X",
            "scan_info": {
                "start_time": "1698577200",
                "end_time": "1698577300",
                "scan_type": "syn"
            }
        }
        
    Raises:
        NmapParserError: If the XML file cannot be parsed or is invalid
        FileNotFoundError: If the XML file does not exist
    """
    # Validate file exists
    xml_file = Path(xml_path)
    if not xml_file.exists():
        raise FileNotFoundError(f"Nmap XML file not found: {xml_path}")
    
    try:
        # Parse XML file
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Initialize result structure
        result = {
            "host": None,
            "hostname": None,
            "state": "unknown",
            "ports": [],
            "os": None,
            "scan_info": {}
        }
        
        # Extract scan information
        scan_info_elem = root.find('scaninfo')
        if scan_info_elem is not None:
            result["scan_info"] = {
                "scan_type": scan_info_elem.get('type', 'unknown'),
                "protocol": scan_info_elem.get('protocol', 'tcp'),
                "num_services": scan_info_elem.get('numservices', '0')
            }
        
        # Extract run stats for timing
        runstats = root.find('runstats')
        if runstats is not None:
            finished = runstats.find('finished')
            if finished is not None:
                result["scan_info"]["start_time"] = root.get('start', '')
                result["scan_info"]["end_time"] = finished.get('time', '')
                result["scan_info"]["elapsed"] = finished.get('elapsed', '')
        
        # Find host element
        host_elem = root.find('host')
        if host_elem is None:
            raise NmapParserError("No host element found in Nmap XML")
        
        # Extract host state
        status_elem = host_elem.find('status')
        if status_elem is not None:
            result["state"] = status_elem.get('state', 'unknown')
        
        # Extract IP address
        address_elem = host_elem.find('address')
        if address_elem is not None:
            result["host"] = address_elem.get('addr', 'unknown')
        
        # Extract hostname(s)
        hostnames_elem = host_elem.find('hostnames')
        if hostnames_elem is not None:
            hostname_elem = hostnames_elem.find('hostname')
            if hostname_elem is not None:
                result["hostname"] = hostname_elem.get('name')
        
        # Extract OS information
        os_elem = host_elem.find('os')
        if os_elem is not None:
            osmatch_elem = os_elem.find('osmatch')
            if osmatch_elem is not None:
                os_name = osmatch_elem.get('name', '')
                os_accuracy = osmatch_elem.get('accuracy', '')
                result["os"] = f"{os_name} (accuracy: {os_accuracy}%)" if os_accuracy else os_name
        
        # Extract port information
        ports_elem = host_elem.find('ports')
        if ports_elem is not None:
            for port_elem in ports_elem.findall('port'):
                port_data = parse_port_element(port_elem)
                if port_data:
                    result["ports"].append(port_data)
        
        return result
        
    except ET.ParseError as e:
        raise NmapParserError(f"Failed to parse XML: {str(e)}")
    except Exception as e:
        raise NmapParserError(f"Unexpected error parsing Nmap XML: {str(e)}")


def parse_port_element(port_elem: ET.Element) -> Optional[Dict[str, Any]]:
    """
    Parse a single port element from Nmap XML.
    
    Args:
        port_elem: XML Element representing a port
        
    Returns:
        Dictionary with port information or None if port should be skipped
    """
    try:
        port_id = port_elem.get('portid')
        protocol = port_elem.get('protocol', 'tcp')
        
        # Get port state
        state_elem = port_elem.find('state')
        if state_elem is None:
            return None
        
        state = state_elem.get('state', 'unknown')
        
        # Initialize port data
        port_data = {
            "port": int(port_id),
            "protocol": protocol,
            "state": state,
            "service": "unknown",
            "version": ""
        }
        
        # Extract service information
        service_elem = port_elem.find('service')
        if service_elem is not None:
            service_name = service_elem.get('name', 'unknown')
            service_product = service_elem.get('product', '')
            service_version = service_elem.get('version', '')
            service_extrainfo = service_elem.get('extrainfo', '')
            
            port_data["service"] = service_name
            
            # Build version string
            version_parts = []
            if service_product:
                version_parts.append(service_product)
            if service_version:
                version_parts.append(service_version)
            if service_extrainfo:
                version_parts.append(f"({service_extrainfo})")
            
            port_data["version"] = " ".join(version_parts)
        
        return port_data
        
    except Exception as e:
        # Log error but don't fail entire parse
        print(f"Warning: Failed to parse port element: {str(e)}")
        return None


def parse_multiple_hosts(xml_path: str) -> List[Dict[str, Any]]:
    """
    Parse Nmap XML file that may contain multiple hosts.
    
    Args:
        xml_path: Path to the Nmap XML output file
        
    Returns:
        List of dictionaries, one for each host found
        
    Raises:
        NmapParserError: If the XML file cannot be parsed
        FileNotFoundError: If the XML file does not exist
    """
    xml_file = Path(xml_path)
    if not xml_file.exists():
        raise FileNotFoundError(f"Nmap XML file not found: {xml_path}")
    
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        results = []
        
        # Find all host elements
        for host_elem in root.findall('host'):
            host_result = {
                "host": None,
                "hostname": None,
                "state": "unknown",
                "ports": [],
                "os": None
            }
            
            # Extract host state
            status_elem = host_elem.find('status')
            if status_elem is not None:
                host_result["state"] = status_elem.get('state', 'unknown')
            
            # Extract IP address
            address_elem = host_elem.find('address')
            if address_elem is not None:
                host_result["host"] = address_elem.get('addr', 'unknown')
            
            # Extract hostname
            hostnames_elem = host_elem.find('hostnames')
            if hostnames_elem is not None:
                hostname_elem = hostnames_elem.find('hostname')
                if hostname_elem is not None:
                    host_result["hostname"] = hostname_elem.get('name')
            
            # Extract OS
            os_elem = host_elem.find('os')
            if os_elem is not None:
                osmatch_elem = os_elem.find('osmatch')
                if osmatch_elem is not None:
                    host_result["os"] = osmatch_elem.get('name', '')
            
            # Extract ports
            ports_elem = host_elem.find('ports')
            if ports_elem is not None:
                for port_elem in ports_elem.findall('port'):
                    port_data = parse_port_element(port_elem)
                    if port_data:
                        host_result["ports"].append(port_data)
            
            results.append(host_result)
        
        return results
        
    except ET.ParseError as e:
        raise NmapParserError(f"Failed to parse XML: {str(e)}")
    except Exception as e:
        raise NmapParserError(f"Unexpected error parsing Nmap XML: {str(e)}")


# ============================================================================
# TEST SECTION
# ============================================================================

def create_sample_xml() -> str:
    """
    Create a sample Nmap XML file for testing.
    
    Returns:
        Path to the created sample XML file
    """
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE nmaprun>
<nmaprun scanner="nmap" args="nmap -sV -oX sample.xml 192.168.1.100" start="1698577200" version="7.80">
<scaninfo type="syn" protocol="tcp" numservices="1000" services="1-1000"/>
<host starttime="1698577200" endtime="1698577300">
<status state="up" reason="echo-reply" reason_ttl="64"/>
<address addr="192.168.1.100" addrtype="ipv4"/>
<hostnames>
<hostname name="webserver.example.com" type="PTR"/>
</hostnames>
<ports>
<port protocol="tcp" portid="22">
<state state="open" reason="syn-ack" reason_ttl="64"/>
<service name="ssh" product="OpenSSH" version="7.4" extrainfo="protocol 2.0" method="probed" conf="10"/>
</port>
<port protocol="tcp" portid="80">
<state state="open" reason="syn-ack" reason_ttl="64"/>
<service name="http" product="nginx" version="1.14.0" method="probed" conf="10"/>
</port>
<port protocol="tcp" portid="443">
<state state="open" reason="syn-ack" reason_ttl="64"/>
<service name="https" product="nginx" version="1.14.0" method="probed" conf="10"/>
</port>
<port protocol="tcp" portid="3306">
<state state="open" reason="syn-ack" reason_ttl="64"/>
<service name="mysql" product="MySQL" version="5.7.30" method="probed" conf="10"/>
</port>
</ports>
<os>
<osmatch name="Linux 3.X|4.X" accuracy="95" line="12345"/>
</os>
</host>
<runstats>
<finished time="1698577300" timestr="Sun Oct 29 12:15:00 2023" elapsed="100.50" summary="Nmap done at Sun Oct 29 12:15:00 2023; 1 IP address (1 host up) scanned in 100.50 seconds" exit="success"/>
</runstats>
</nmaprun>
"""
    
    # Use cross-platform temporary directory
    temp_dir = tempfile.gettempdir()
    sample_path = os.path.join(temp_dir, "sample_nmap.xml")
    
    with open(sample_path, 'w') as f:
        f.write(sample_xml)
    
    return sample_path


def test_parser():
    """
    Test the Nmap parser with sample data.
    """
    print("=" * 70)
    print("NMAP PARSER TEST")
    print("=" * 70)
    
    try:
        # Create sample XML file
        print("\n[1] Creating sample Nmap XML file...")
        sample_path = create_sample_xml()
        print(f"    ✓ Sample file created: {sample_path}")
        
        # Parse the sample file
        print("\n[2] Parsing Nmap XML...")
        result = parse_nmap_xml(sample_path)
        print("    ✓ Parsing successful")
        
        # Display results
        print("\n[3] Parsed Results:")
        print("-" * 70)
        print(json.dumps(result, indent=2))
        print("-" * 70)
        
        # Validate key fields
        print("\n[4] Validation:")
        assert result["host"] == "192.168.1.100", "Host IP mismatch"
        print("    ✓ Host IP correct")
        
        assert result["hostname"] == "webserver.example.com", "Hostname mismatch"
        print("    ✓ Hostname correct")
        
        assert result["state"] == "up", "Host state mismatch"
        print("    ✓ Host state correct")
        
        assert len(result["ports"]) == 4, "Port count mismatch"
        print(f"    ✓ Found {len(result['ports'])} ports")
        
        assert result["os"] is not None, "OS detection failed"
        print(f"    ✓ OS detected: {result['os']}")
        
        # Check specific port
        http_port = next((p for p in result["ports"] if p["port"] == 80), None)
        assert http_port is not None, "HTTP port not found"
        assert http_port["service"] == "http", "HTTP service mismatch"
        assert "nginx" in http_port["version"], "HTTP version mismatch"
        print("    ✓ HTTP port (80) correctly parsed")
        
        print("\n" + "=" * 70)
        print("ALL TESTS PASSED ✓")
        print("=" * 70)
        
        # Clean up
        Path(sample_path).unlink()
        
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Run test when module is executed directly
    test_parser()
