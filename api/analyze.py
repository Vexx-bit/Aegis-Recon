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

Aegis Recon - GROQ AI Analysis Endpoint
Generates threat intelligence reports using GROQ API
"""

from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler for AI analysis"""
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """Handle analysis requests"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}
            
            scan_results = data.get('results', {})
            
            if not scan_results:
                self._send_json({'success': False, 'error': 'Scan results required'}, 400)
                return
            
            # Generate analysis
            analysis = self.generate_analysis(scan_results)
            
            self._send_json({
                'success': True,
                'analysis': analysis
            })
            
        except Exception as e:
            self._send_json({'success': False, 'error': str(e)}, 500)
    
    def do_GET(self):
        """Handle GET requests (health check)"""
        self._send_json({
            'status': 'ok',
            'service': 'Aegis Recon AI Analyzer',
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
    
    def generate_analysis(self, scan_results):
        """Use GROQ to generate threat analysis"""
        groq_key = os.environ.get('GROQ_API_KEY')
        
        if not groq_key:
            return self.generate_fallback_analysis(scan_results)
        
        try:
            # Prepare context
            target = scan_results.get('target', 'Unknown')
            phases = scan_results.get('phases', {})
            score = scan_results.get('security_score', 100)
            
            # Build summary
            subdomain_count = len(phases.get('subdomains', []))
            host_count = len(phases.get('hosts', []))
            email_count = len(phases.get('osint', {}).get('emails', []))
            tech_list = [t['name'] for t in phases.get('technologies', [])]
            
            # Get open ports
            all_ports = []
            for host in phases.get('hosts', []):
                all_ports.extend(host.get('ports', []))
            
            # Get new security check data
            headers_info = scan_results.get('security_headers', {})
            headers_grade = headers_info.get('grade', 'Unknown')
            missing_headers = [h['name'] for h in headers_info.get('headers_missing', [])]
            
            ssl_info = scan_results.get('ssl_info', {})
            ssl_valid = ssl_info.get('valid', False)
            ssl_issuer = ssl_info.get('issuer', 'Unknown')
            ssl_tls = ssl_info.get('tls_version', 'Unknown')
            ssl_days = ssl_info.get('days_until_expiry', 'Unknown')
            
            cves = scan_results.get('known_cves', [])
            cve_list = [f"{c['cve']} ({c['severity']}) - {c['technology']}" for c in cves]
            
            admin_panels = scan_results.get('admin_panels', {}).get('found', [])
            accessible_panels = [p['path'] for p in admin_panels if p.get('accessible')]
            protected_panels = [p['path'] for p in admin_panels if not p.get('accessible')]
            
            robots_data = scan_results.get('robots_txt', {})
            sensitive_paths = [p['path'] for p in robots_data.get('sensitive_paths', [])]
            
            dir_listing = scan_results.get('directory_listing', {})
            exposed_dirs = dir_listing.get('exposed_dirs', [])
            
            score_factors = scan_results.get('score_factors', [])
            
            prompt = f"""You are a senior cybersecurity consultant preparing a comprehensive threat intelligence report for {target}.

RECONNAISSANCE DATA:
- Target Domain: {target}
- Security Score: {score}/100
- Subdomains Discovered: {subdomain_count}
- Active Hosts Identified: {host_count}
- Open Ports Detected: {sorted(set(all_ports)) if all_ports else 'None detected'}
- Email Addresses Exposed: {email_count}
- Technology Stack: {', '.join(tech_list) if tech_list else 'None detected'}

SECURITY HEADERS ANALYSIS:
- Grade: {headers_grade}
- Missing Headers: {', '.join(missing_headers) if missing_headers else 'None'}

SSL/TLS CERTIFICATE:
- Valid: {ssl_valid}
- Issuer: {ssl_issuer}
- TLS Version: {ssl_tls}
- Days Until Expiry: {ssl_days}

KNOWN VULNERABILITIES (CVEs):
{chr(10).join(cve_list) if cve_list else 'No known CVEs detected'}

ADMIN PANELS DETECTED:
- Accessible (No Auth): {', '.join(accessible_panels) if accessible_panels else 'None'}
- Protected: {', '.join(protected_panels) if protected_panels else 'None'}

ROBOTS.TXT SENSITIVE PATHS:
{', '.join(sensitive_paths) if sensitive_paths else 'None found'}

DIRECTORY LISTING:
- Vulnerable: {dir_listing.get('vulnerable', False)}
- Exposed Directories: {', '.join(exposed_dirs) if exposed_dirs else 'None'}

SCORE BREAKDOWN:
{chr(10).join(score_factors) if score_factors else 'No detailed breakdown available'}

Generate a DETAILED professional threat assessment report with the following sections:

## Executive Summary
Provide a comprehensive 4-5 sentence overview of the target's security posture, key concerns, and overall risk profile. Reference the security score and major findings.

## Key Findings
Provide detailed bullet points for each discovery:
- Security Headers analysis and implications for XSS/clickjacking protection
- SSL/TLS configuration assessment
- Known CVEs affecting detected technologies
- Admin panel exposure risks
- Subdomain and email enumeration results
- Open port analysis with specific risks

## Risk Assessment
Provide a thorough risk analysis including:
- Overall risk rating (Critical/High/Medium/Low) with detailed justification
- Attack surface analysis based on all findings
- Potential threat vectors and exploitation paths
- Business impact considerations

## Vulnerabilities & Concerns
List specific security weaknesses identified:
- Each CVE with exploitation potential
- Missing security headers and their impact
- Exposed admin panels and sensitive paths
- Directory listing vulnerabilities
- Severity rating for each issue

## Recommended Actions
Provide a comprehensive remediation roadmap:
- Immediate actions (within 24-48 hours)
- Short-term improvements (1-2 weeks)
- Medium-term hardening (1-3 months)
- Long-term security strategy

Be thorough and detailed. This report will be presented to executive leadership. Use professional language and provide actionable insights."""

            # Call GROQ API
            request_data = json.dumps({
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": "You are a senior cybersecurity consultant with 15+ years of experience in penetration testing, threat intelligence, and security architecture. You provide detailed, professional reports suitable for executive briefings."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2500,
                "temperature": 0.4
            }).encode('utf-8')
            
            req = Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=request_data,
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            
            with urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                return {
                    "report": result['choices'][0]['message']['content'],
                    "model": "groq-llama-3.1-8b",
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            return self.generate_fallback_analysis(scan_results)
    
    def generate_fallback_analysis(self, scan_results):
        """Generate comprehensive rule-based analysis when GROQ is unavailable"""
        phases = scan_results.get('phases', {})
        target = scan_results.get('target', 'Unknown')
        score = scan_results.get('security_score', 100)
        
        # Analyze data
        subdomains = phases.get('subdomains', [])
        hosts = phases.get('hosts', [])
        emails = phases.get('osint', {}).get('emails', [])
        technologies = phases.get('technologies', [])
        
        # Get new security check data
        headers_info = scan_results.get('security_headers', {})
        headers_grade = headers_info.get('grade', 'Unknown')
        missing_headers = headers_info.get('headers_missing', [])
        
        ssl_info = scan_results.get('ssl_info', {})
        cves = scan_results.get('known_cves', [])
        admin_panels = scan_results.get('admin_panels', {}).get('found', [])
        dir_listing = scan_results.get('directory_listing', {})
        robots_data = scan_results.get('robots_txt', {})
        score_factors = scan_results.get('score_factors', [])
        
        # Collect all ports
        all_ports = []
        for host in hosts:
            all_ports.extend(host.get('ports', []))
        unique_ports = sorted(set(all_ports))
        
        # Determine risk level
        if score >= 80:
            risk_level = "Low"
            risk_color = "🟢"
            risk_desc = "The target maintains a strong security posture with minimal exposure."
        elif score >= 60:
            risk_level = "Medium"
            risk_color = "🟡"
            risk_desc = "Some security concerns identified that warrant attention."
        elif score >= 40:
            risk_level = "High"
            risk_color = "🟠"
            risk_desc = "Significant security weaknesses detected requiring immediate action."
        else:
            risk_level = "Critical"
            risk_color = "🔴"
            risk_desc = "Severe security vulnerabilities present with high exploitation risk."
        
        # Build comprehensive report
        report = f"""## Executive Summary

This comprehensive threat intelligence assessment of **{target}** has identified {len(subdomains)} subdomains through certificate transparency analysis, {len(hosts)} active hosts responding to network probes, and {len(technologies)} distinct technologies in the infrastructure stack. The security posture analysis yields a score of **{score}/100**, indicating a **{risk_level.lower()} risk** environment. {risk_desc}

## Key Findings

### Security Headers Analysis
- **Grade: {headers_grade}** - """

        if headers_grade in ['A', 'B']:
            report += f"Good security header implementation with {100 - len(missing_headers) * 14}% coverage.\n"
        elif headers_grade == 'C':
            report += "Moderate security header coverage. Some important headers are missing.\n"
        else:
            report += "Poor security header implementation. Critical headers are missing.\n"
        
        if missing_headers:
            report += f"- **Missing Headers:** {', '.join([h['name'] for h in missing_headers[:5]])}\n"
            report += "- Missing headers expose the site to XSS, clickjacking, and MIME-sniffing attacks.\n"

        report += "\n### SSL/TLS Configuration\n"
        if ssl_info.get('valid'):
            report += f"- **Certificate:** Valid, issued by {ssl_info.get('issuer', 'Unknown')}\n"
            report += f"- **TLS Version:** {ssl_info.get('tls_version', 'Unknown')}\n"
            days = ssl_info.get('days_until_expiry', 0)
            if days < 30:
                report += f"- ⚠️ **Warning:** Certificate expires in {days} days - renewal required\n"
            else:
                report += f"- Certificate valid for {days} days\n"
        else:
            report += "- ⚠️ **Warning:** SSL certificate could not be verified or is not present\n"

        # Known CVEs section
        report += "\n### Known Vulnerabilities (CVEs)\n"
        if cves:
            for cve in cves[:5]:
                report += f"- **{cve.get('cve')}** ({cve.get('severity')}) - {cve.get('technology')}: {cve.get('description')}\n"
        else:
            report += "- No known CVEs detected in the identified technology stack.\n"

        # Admin Panels section
        report += "\n### Admin Panel Exposure\n"
        accessible_panels = [p for p in admin_panels if p.get('accessible')]
        protected_panels = [p for p in admin_panels if not p.get('accessible')]
        
        if accessible_panels:
            report += f"- ⚠️ **Critical:** {len(accessible_panels)} admin panel(s) accessible without authentication:\n"
            for panel in accessible_panels[:3]:
                report += f"  - `{panel['path']}` (Status: {panel.get('status')})\n"
        if protected_panels:
            report += f"- {len(protected_panels)} admin panel(s) detected but protected (requires authentication)\n"
        if not admin_panels:
            report += "- No common admin panels were detected.\n"

        # Directory Listing
        report += "\n### Directory Listing\n"
        if dir_listing.get('vulnerable'):
            exposed = dir_listing.get('exposed_dirs', [])
            report += f"- ⚠️ **Vulnerability:** Directory listing is enabled on {len(exposed)} directories:\n"
            for d in exposed[:3]:
                report += f"  - `{d}`\n"
            report += "- This exposes file structure and potentially sensitive files to attackers.\n"
        else:
            report += "- No directory listing vulnerabilities detected.\n"

        # Robots.txt
        report += "\n### Robots.txt Analysis\n"
        if robots_data.get('found'):
            sensitive = robots_data.get('sensitive_paths', [])
            if sensitive:
                report += f"- **Sensitive Paths Found:** {len(sensitive)} paths may expose administrative or sensitive areas:\n"
                for p in sensitive[:3]:
                    report += f"  - `{p['path']}` (keyword: {p.get('keyword')})\n"
            else:
                report += "- robots.txt found but no sensitive paths detected.\n"
        else:
            report += "- No robots.txt file found.\n"

        report += "\n### Infrastructure Discovery\n"
        report += f"- **Subdomain Enumeration:** Successfully identified {len(subdomains)} unique subdomains through certificate transparency logs.\n"
        report += f"- **Active Host Identification:** {len(hosts)} hosts are actively responding to network probes.\n"
        report += f"- **Network Exposure:** {'Ports ' + str(unique_ports) + ' are exposed' if unique_ports else 'No open ports were detected'}\n"

        report += "\n### Port Analysis\n"
        
        # Detailed port analysis
        if unique_ports:
            for port in unique_ports:
                if port == 21:
                    report += "- **Port 21 (FTP):** FTP transmits credentials in plaintext. Replace with SFTP or FTPS.\n"
                elif port == 22:
                    report += "- **Port 22 (SSH):** Ensure key-based authentication is enforced.\n"
                elif port == 23:
                    report += "- **Port 23 (Telnet):** Critical - Telnet transmits all data unencrypted. Replace with SSH.\n"
                elif port == 80:
                    report += "- **Port 80 (HTTP):** Ensure HTTP redirects to HTTPS with HSTS.\n"
                elif port == 443:
                    report += "- **Port 443 (HTTPS):** Secure web services running.\n"
                elif port == 3306:
                    report += "- **Port 3306 (MySQL):** Database exposed - high risk finding.\n"
                elif port == 3389:
                    report += "- **Port 3389 (RDP):** Remote Desktop exposed - protect with VPN.\n"
        else:
            report += "- No open ports were detected during this scan.\n"

        report += "\n### Email & OSINT Analysis\n"
        if emails:
            report += f"- **Exposed Emails:** {len(emails)} corporate email addresses discovered ({', '.join(emails[:3])}{'...' if len(emails) > 3 else ''})\n"
            report += "- These can be used for targeted phishing and social engineering attacks.\n"
        else:
            report += "- No email addresses were discovered - good privacy practices.\n"

        report += f"""
## Risk Assessment

{risk_color} **{risk_level} Risk** (Score: {score}/100)

### Score Breakdown
"""
        for factor in score_factors[:10]:
            report += f"- {factor}\n"

        report += f"""
### Attack Surface Analysis
- **Entry Points:** {len(subdomains) + len(hosts)} potential entry points identified
- **Service Exposure:** {len(unique_ports)} unique services accessible from the internet
- **Information Leakage:** {len(emails)} email addresses discoverable
- **Known Vulnerabilities:** {len(cves)} CVEs affecting detected technologies

## Recommended Actions

### Immediate Priority (24-48 hours)
1. **Security Headers:** Implement HSTS, CSP, X-Frame-Options on all web properties
2. **CVE Remediation:** Address all critical and high severity CVEs immediately
3. **Admin Panels:** Restrict access to detected admin panels with authentication/IP filtering

### Short-Term Improvements (1-2 weeks)
1. **SSL Configuration:** Ensure TLS 1.2+ only, renew expiring certificates
2. **Disable Directory Listing:** Configure web server to prevent directory browsing
3. **Review robots.txt:** Remove sensitive paths or password-protect those areas

### Medium-Term Hardening (1-3 months)
1. **Network Segmentation:** Isolate sensitive services behind VPN
2. **Vulnerability Scanning:** Conduct authenticated scans on all hosts
3. **Penetration Testing:** Engage third-party for comprehensive assessment

### Long-Term Strategy
1. **Continuous Monitoring:** Implement attack surface monitoring
2. **Security Program:** Develop formal vulnerability management
3. **Regular Assessments:** Schedule quarterly security audits

---
*Report generated by Aegis Recon | Author: VexSpitta*
"""
        
        return {
            "report": report,
            "model": "aegis-fallback-v2",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
