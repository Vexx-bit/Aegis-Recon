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
            
            prompt = f"""You are a cybersecurity expert analyzing reconnaissance results for {target}.

SCAN SUMMARY:
- Target: {target}
- Security Score: {score}/100
- Subdomains Found: {subdomain_count}
- Active Hosts: {host_count}
- Open Ports: {sorted(set(all_ports)) if all_ports else 'None detected'}
- Emails Exposed: {email_count}
- Technologies: {tech_list if tech_list else 'None detected'}

Provide a professional threat assessment report with:
1. Executive Summary (2-3 sentences)
2. Key Findings (bullet points)
3. Risk Assessment (Low/Medium/High/Critical with explanation)
4. Recommended Actions (prioritized list)

Keep the response concise and actionable. Format in clean markdown."""

            # Call GROQ API
            request_data = json.dumps({
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": "You are a professional cybersecurity analyst specializing in threat intelligence and vulnerability assessment."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.3
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
        """Generate rule-based analysis when GROQ is unavailable"""
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
        
        # Determine risk level
        if score >= 80:
            risk_level = "Low"
            risk_color = "🟢"
        elif score >= 60:
            risk_level = "Medium"
            risk_color = "🟡"
        elif score >= 40:
            risk_level = "High"
            risk_color = "🟠"
        else:
            risk_level = "Critical"
            risk_color = "🔴"
        
        # Build report
        report = f"""## Executive Summary

This reconnaissance scan of **{target}** identified {len(subdomains)} subdomains, {len(hosts)} active hosts, and detected {len(technologies)} technologies. The overall security posture is rated at **{score}/100**.

## Key Findings

- **Subdomains Discovered:** {len(subdomains)} unique subdomains found via certificate transparency logs
- **Active Hosts:** {len(hosts)} hosts responding to network probes
- **Open Ports:** {sorted(set(all_ports)) if all_ports else 'No open ports detected'}
- **Exposed Emails:** {len(emails)} email addresses found ({', '.join(emails[:3])}{'...' if len(emails) > 3 else ''})
- **Technology Stack:** {', '.join([t['name'] for t in technologies[:5]]) if technologies else 'Not detected'}

## Risk Assessment

{risk_color} **{risk_level} Risk** (Score: {score}/100)

"""
        
        if 22 in all_ports:
            report += "- ⚠️ SSH (port 22) is exposed - ensure strong authentication\n"
        if 21 in all_ports:
            report += "- ⚠️ FTP (port 21) is exposed - consider using SFTP instead\n"
        if emails:
            report += f"- ⚠️ {len(emails)} email addresses are publicly exposed - phishing risk\n"
        
        report += """
## Recommended Actions

1. **Immediate:** Review exposed email addresses for potential phishing targets
2. **Short-term:** Audit open ports and disable unnecessary services
3. **Medium-term:** Implement security headers and HTTPS everywhere
4. **Ongoing:** Regular security assessments and monitoring

---
*Report generated by Aegis Recon | Author: VexSpitta*
"""
        
        return {
            "report": report,
            "model": "aegis-fallback-v1",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
