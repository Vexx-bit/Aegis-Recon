#!/usr/bin/env python3
"""
WhatWeb Parser - Parse WhatWeb JSON output for technology fingerprinting
"""

import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def parse_whatweb_json(json_file: str) -> Dict[str, Any]:
    """
    Parse WhatWeb JSON output.
    
    Args:
        json_file: Path to WhatWeb JSON output file
        
    Returns:
        Dictionary containing parsed technology information
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            logger.warning("Empty WhatWeb output")
            return {}
        
        # WhatWeb returns a list of results (one per target)
        if isinstance(data, list) and len(data) > 0:
            result = data[0]  # Get first result
        else:
            result = data
        
        technologies = {
            'target': result.get('target', ''),
            'http_status': result.get('http_status', 0),
            'request_config': result.get('request_config', {}),
            'plugins': {},
            'summary': {
                'cms': [],
                'web_servers': [],
                'programming_languages': [],
                'javascript_libraries': [],
                'frameworks': [],
                'analytics': [],
                'security': [],
                'other': []
            }
        }
        
        # Parse plugins (detected technologies)
        plugins = result.get('plugins', {})
        
        for plugin_name, plugin_data in plugins.items():
            # Extract version if available
            version = None
            if isinstance(plugin_data, dict):
                version = plugin_data.get('version', [])
                if isinstance(version, list) and len(version) > 0:
                    version = version[0]
                elif not version:
                    version = plugin_data.get('string', [])
                    if isinstance(version, list) and len(version) > 0:
                        version = version[0]
            
            tech_info = {
                'name': plugin_name,
                'version': version,
                'data': plugin_data
            }
            
            technologies['plugins'][plugin_name] = tech_info
            
            # Categorize technologies
            categorize_technology(plugin_name, version, technologies['summary'])
        
        return technologies
        
    except FileNotFoundError:
        logger.error(f"WhatWeb output file not found: {json_file}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing WhatWeb JSON: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error parsing WhatWeb output: {str(e)}")
        return {}


def categorize_technology(name: str, version: Optional[str], summary: Dict[str, List]) -> None:
    """
    Categorize detected technology into appropriate category.
    
    Args:
        name: Technology name
        version: Technology version (if detected)
        summary: Summary dictionary to update
    """
    name_lower = name.lower()
    tech_string = f"{name} {version}" if version else name
    
    # CMS Detection
    cms_list = ['wordpress', 'joomla', 'drupal', 'magento', 'prestashop', 
                'shopify', 'wix', 'squarespace', 'typo3', 'concrete5']
    if any(cms in name_lower for cms in cms_list):
        summary['cms'].append(tech_string)
    
    # Web Servers
    elif any(server in name_lower for server in ['apache', 'nginx', 'iis', 'lighttpd', 'tomcat', 
                                                   'httpserver', 'vercel', 'cloudfront', 'netlify',
                                                   'github pages', 'caddy', 'litespeed']):
        summary['web_servers'].append(tech_string)
    
    # Programming Languages
    elif any(lang in name_lower for lang in ['php', 'python', 'ruby', 'perl', 'asp', 'jsp']):
        summary['programming_languages'].append(tech_string)
    
    # JavaScript Libraries
    elif any(lib in name_lower for lib in ['jquery', 'react', 'angular', 'vue', 'bootstrap', 
                                            'modernizr', 'backbone', 'ember', 'knockout']):
        summary['javascript_libraries'].append(tech_string)
    
    # Frameworks
    elif any(fw in name_lower for fw in ['laravel', 'django', 'rails', 'express', 'flask', 
                                          'symfony', 'codeigniter', 'cakephp', 'yii']):
        summary['frameworks'].append(tech_string)
    
    # Analytics
    elif any(analytics in name_lower for analytics in ['google-analytics', 'matomo', 'piwik', 
                                                        'clicky', 'statcounter']):
        summary['analytics'].append(tech_string)
    
    # Security
    elif any(sec in name_lower for sec in ['cloudflare', 'ssl', 'tls', 'hsts', 'csp', 
                                            'x-frame-options', 'waf']):
        summary['security'].append(tech_string)
    
    # Other
    else:
        summary['other'].append(tech_string)


def get_technology_summary(technologies: Dict[str, Any]) -> str:
    """
    Generate human-readable summary of detected technologies.
    
    Args:
        technologies: Parsed technology data
        
    Returns:
        Summary string
    """
    summary = technologies.get('summary', {})
    parts = []
    
    if summary.get('cms'):
        parts.append(f"CMS: {', '.join(summary['cms'])}")
    
    if summary.get('web_servers'):
        parts.append(f"Web Server: {', '.join(summary['web_servers'])}")
    
    if summary.get('programming_languages'):
        parts.append(f"Languages: {', '.join(summary['programming_languages'])}")
    
    if summary.get('frameworks'):
        parts.append(f"Frameworks: {', '.join(summary['frameworks'])}")
    
    if summary.get('javascript_libraries'):
        libs = summary['javascript_libraries'][:3]  # Limit to 3
        parts.append(f"JS Libraries: {', '.join(libs)}")
    
    return " | ".join(parts) if parts else "No technologies detected"


def check_outdated_versions(technologies: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Check for known outdated/vulnerable versions.
    
    Args:
        technologies: Parsed technology data
        
    Returns:
        List of outdated technologies with recommendations
    """
    outdated = []
    
    # Known outdated versions (simplified - in production, use CVE database)
    known_outdated = {
        'Apache': {'2.2': 'EOL - Upgrade to 2.4+', '2.4.0': 'Multiple CVEs - Upgrade to 2.4.41+'},
        'PHP': {'5.6': 'EOL - Upgrade to 7.4+', '7.0': 'EOL - Upgrade to 7.4+', '7.1': 'EOL - Upgrade to 7.4+'},
        'jQuery': {'1.': 'Multiple XSS vulnerabilities - Upgrade to 3.5+'},
        'WordPress': {'4.': 'Multiple vulnerabilities - Upgrade to 6.0+', '5.0': 'Upgrade to 6.0+'},
        'nginx': {'1.10': 'Outdated - Upgrade to 1.20+'},
    }
    
    plugins = technologies.get('plugins', {})
    
    for plugin_name, plugin_data in plugins.items():
        version = plugin_data.get('version')
        if not version:
            continue
        
        for tech, versions in known_outdated.items():
            if tech.lower() in plugin_name.lower():
                for old_ver, recommendation in versions.items():
                    if str(version).startswith(old_ver):
                        outdated.append({
                            'technology': plugin_name,
                            'version': version,
                            'issue': 'Outdated version detected',
                            'recommendation': recommendation,
                            'severity': 'high' if 'EOL' in recommendation or 'CVE' in recommendation else 'medium'
                        })
    
    return outdated


if __name__ == '__main__':
    # Test the parser
    import sys
    
    if len(sys.argv) > 1:
        result = parse_whatweb_json(sys.argv[1])
        print(json.dumps(result, indent=2))
        print("\nSummary:", get_technology_summary(result))
        
        outdated = check_outdated_versions(result)
        if outdated:
            print("\nOutdated Technologies:")
            for item in outdated:
                print(f"  - {item['technology']} {item['version']}: {item['recommendation']}")
