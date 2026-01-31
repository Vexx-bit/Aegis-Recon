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
            
            prompt = f"""You are a senior cybersecurity consultant preparing a comprehensive threat intelligence report for {target}.

RECONNAISSANCE DATA:
- Target Domain: {target}
- Security Score: {score}/100
- Subdomains Discovered: {subdomain_count}
- Active Hosts Identified: {host_count}
- Open Ports Detected: {sorted(set(all_ports)) if all_ports else 'None detected'}
- Email Addresses Exposed: {email_count}
- Technology Stack: {', '.join(tech_list) if tech_list else 'None detected'}

Generate a DETAILED professional threat assessment report with the following sections:

## Executive Summary
Provide a comprehensive 4-5 sentence overview of the target's security posture, key concerns, and overall risk profile.

## Key Findings
Provide detailed bullet points for each discovery:
- Subdomain analysis and implications
- Host enumeration results and exposure level
- Port analysis with specific risks for each open port
- Email exposure and social engineering risks
- Technology stack vulnerabilities and version concerns

## Risk Assessment
Provide a thorough risk analysis including:
- Overall risk rating with detailed justification
- Attack surface analysis
- Potential threat vectors
- Business impact considerations

## Vulnerabilities & Concerns
List specific security weaknesses identified:
- Each vulnerability with technical details
- Potential exploitation methods
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

### Infrastructure Discovery
- **Subdomain Enumeration:** Successfully identified {len(subdomains)} unique subdomains through certificate transparency logs and DNS analysis. Each subdomain represents a potential entry point that requires security assessment.
- **Active Host Identification:** {len(hosts)} hosts are actively responding to network probes, indicating live infrastructure that may be accessible to potential attackers.
- **Network Exposure:** {'Ports ' + str(unique_ports) + ' are exposed to the internet' if unique_ports else 'No open ports were detected during the scan window'}

### Port Analysis
"""
        
        # Detailed port analysis
        if unique_ports:
            for port in unique_ports:
                if port == 21:
                    report += "- **Port 21 (FTP):** File Transfer Protocol detected. FTP transmits credentials in plaintext and should be replaced with SFTP or FTPS for secure file transfers.\n"
                elif port == 22:
                    report += "- **Port 22 (SSH):** Secure Shell access is available. Ensure key-based authentication is enforced and password authentication is disabled.\n"
                elif port == 23:
                    report += "- **Port 23 (Telnet):** Telnet detected - this is a critical finding as Telnet transmits all data unencrypted. Immediate replacement with SSH is recommended.\n"
                elif port == 25:
                    report += "- **Port 25 (SMTP):** Mail server detected. Verify SPF, DKIM, and DMARC records are properly configured to prevent email spoofing.\n"
                elif port == 80:
                    report += "- **Port 80 (HTTP):** Unencrypted web traffic is accepted. Ensure all HTTP traffic is redirected to HTTPS with proper HSTS headers.\n"
                elif port == 443:
                    report += "- **Port 443 (HTTPS):** Secure web services are running. Verify TLS configuration meets current best practices (TLS 1.2+ only).\n"
                elif port == 3306:
                    report += "- **Port 3306 (MySQL):** Database port is exposed. This is a high-risk finding - databases should never be directly accessible from the internet.\n"
                elif port == 3389:
                    report += "- **Port 3389 (RDP):** Remote Desktop Protocol is exposed. This is frequently targeted by attackers and should be protected with VPN access.\n"
                else:
                    report += f"- **Port {port}:** Service detected on non-standard port. Investigate the purpose and security implications of this service.\n"
        else:
            report += "- No open ports were detected during this scan. This may indicate strong firewall rules or the scan was blocked.\n"

        report += """
### Email & OSINT Analysis
"""
        if emails:
            report += f"- **Exposed Email Addresses:** {len(emails)} corporate email addresses were discovered through OSINT techniques ({', '.join(emails[:5])}{'...' if len(emails) > 5 else ''})\n"
            report += "- **Social Engineering Risk:** These emails can be used for targeted phishing campaigns, credential stuffing attacks, or business email compromise (BEC) schemes.\n"
            report += "- **Recommendation:** Implement email security awareness training and consider using email aliases for public-facing communications.\n"
        else:
            report += "- No email addresses were discovered during OSINT reconnaissance. This indicates good privacy practices.\n"

        report += """
### Technology Stack Analysis
"""
        if technologies:
            tech_names = [t['name'] for t in technologies]
            report += f"- **Detected Technologies:** {', '.join(tech_names[:8])}\n"
            for tech in technologies[:5]:
                if 'version' in tech.get('name', '').lower() or tech.get('version'):
                    report += f"- Consider checking **{tech['name']}** for known CVEs and security advisories.\n"
        else:
            report += "- Technology fingerprinting did not yield specific results. The target may be using techniques to obscure their technology stack.\n"

        report += f"""
## Risk Assessment

{risk_color} **{risk_level} Risk** (Score: {score}/100)

### Attack Surface Analysis
- **Entry Points:** {len(subdomains) + len(hosts)} potential entry points identified (subdomains + active hosts)
- **Service Exposure:** {len(unique_ports)} unique services accessible from the internet
- **Information Leakage:** {len(emails)} email addresses discoverable through public sources

### Threat Vector Assessment
"""
        
        if 21 in unique_ports or 23 in unique_ports:
            report += "- ⚠️ **Critical:** Legacy protocols (FTP/Telnet) detected that transmit data in cleartext\n"
        if 3306 in unique_ports or 5432 in unique_ports or 1433 in unique_ports:
            report += "- ⚠️ **Critical:** Database ports exposed to the internet - immediate remediation required\n"
        if 3389 in unique_ports:
            report += "- ⚠️ **High:** RDP exposure creates significant risk of brute-force and ransomware attacks\n"
        if emails:
            report += f"- ⚠️ **Medium:** {len(emails)} exposed emails increase phishing and social engineering risk\n"
        if len(subdomains) > 10:
            report += f"- ⚠️ **Medium:** Large subdomain footprint ({len(subdomains)}) increases attack surface management complexity\n"

        report += """
## Recommended Actions

### Immediate Priority (24-48 hours)
1. **Audit Exposed Services:** Review all detected open ports and disable any unnecessary services immediately
2. **Email Protection:** Notify security team about exposed email addresses and increase phishing awareness
3. **Credential Review:** Rotate any credentials that may have been exposed through detected services

### Short-Term Improvements (1-2 weeks)
1. **Vulnerability Scanning:** Conduct authenticated vulnerability scans on all detected hosts
2. **Access Controls:** Implement IP whitelisting for administrative services (SSH, RDP, databases)
3. **Security Headers:** Deploy comprehensive security headers (HSTS, CSP, X-Frame-Options) on all web properties

### Medium-Term Hardening (1-3 months)
1. **Network Segmentation:** Isolate sensitive services behind VPN or zero-trust architecture
2. **Monitoring Implementation:** Deploy SIEM/log aggregation for all identified assets
3. **Penetration Testing:** Engage third-party security firm for comprehensive assessment

### Long-Term Strategy
1. **Continuous Monitoring:** Implement ongoing attack surface monitoring and threat intelligence
2. **Security Program:** Develop formal vulnerability management and incident response programs
3. **Regular Assessments:** Schedule quarterly security assessments and annual penetration tests

---
*Report generated by Aegis Recon | Author: VexSpitta*
"""
        
        return {
            "report": report,
            "model": "aegis-fallback-v1",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

