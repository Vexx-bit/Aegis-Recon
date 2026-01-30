"""
Aegis Recon - GROQ AI Analysis Endpoint
Generates threat intelligence reports using GROQ API
"""

import json
import os
import requests
from datetime import datetime, timezone


def handler(request):
    """Vercel serverless handler for AI analysis"""
    
    # Handle CORS preflight
    if request.method == "OPTIONS":
        return cors_response("")
    
    try:
        # Parse request body
        body = json.loads(request.body) if request.body else {}
        scan_results = body.get("results", {})
        
        if not scan_results:
            return error_response("Scan results are required", 400)
        
        # Generate AI analysis
        analysis = generate_analysis(scan_results)
        
        return cors_response(json.dumps({
            "success": True,
            "analysis": analysis,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))
        
    except Exception as e:
        return error_response(str(e), 500)


def cors_response(body, status_code=200):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        },
        "body": body
    }


def error_response(message, status_code=400):
    return cors_response(json.dumps({
        "success": False,
        "error": message
    }), status_code)


def generate_analysis(scan_results):
    """Use GROQ to generate threat analysis"""
    
    groq_key = os.environ.get('GROQ_API_KEY')
    
    if not groq_key:
        return generate_fallback_analysis(scan_results)
    
    try:
        # Prepare context for GROQ
        target = scan_results.get('target', 'Unknown')
        phases = scan_results.get('phases', {})
        score = scan_results.get('security_score', 100)
        
        # Build summary
        subdomain_count = len(phases.get('subdomains', []))
        host_count = len(phases.get('hosts', []))
        email_count = len(phases.get('osint', {}).get('emails', []))
        tech_count = len(phases.get('technologies', []))
        
        # Get open ports summary
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
- Technologies: {[t['name'] for t in phases.get('technologies', [])]}

Provide a professional threat assessment report with:
1. Executive Summary (2-3 sentences)
2. Key Findings (bullet points)
3. Risk Assessment (Low/Medium/High/Critical with explanation)
4. Recommended Actions (prioritized list)

Keep the response concise and actionable. Format in clean markdown."""

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": "You are a professional cybersecurity analyst specializing in threat intelligence and vulnerability assessment."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.3
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "report": data['choices'][0]['message']['content'],
                "model": "groq-llama-3.1-8b",
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        else:
            return generate_fallback_analysis(scan_results)
            
    except Exception as e:
        return generate_fallback_analysis(scan_results)


def generate_fallback_analysis(scan_results):
    """Generate basic analysis without AI"""
    
    target = scan_results.get('target', 'Unknown')
    phases = scan_results.get('phases', {})
    score = scan_results.get('security_score', 100)
    
    # Determine risk level
    if score >= 80:
        risk_level = "Low"
        risk_color = "green"
    elif score >= 60:
        risk_level = "Medium"
        risk_color = "yellow"
    elif score >= 40:
        risk_level = "High"
        risk_color = "orange"
    else:
        risk_level = "Critical"
        risk_color = "red"
    
    # Build findings
    findings = []
    
    subdomain_count = len(phases.get('subdomains', []))
    if subdomain_count > 10:
        findings.append(f"Large attack surface: {subdomain_count} subdomains discovered")
    
    email_count = len(phases.get('osint', {}).get('emails', []))
    if email_count > 0:
        findings.append(f"Email exposure: {email_count} email addresses found publicly")
    
    # Check for risky ports
    risky_ports_found = []
    for host in phases.get('hosts', []):
        for port in host.get('ports', []):
            if port in [21, 22, 23, 3389, 5900]:
                risky_ports_found.append(port)
    
    if risky_ports_found:
        findings.append(f"Sensitive ports exposed: {sorted(set(risky_ports_found))}")
    
    if not findings:
        findings.append("No major security concerns identified")
    
    report = f"""## Threat Assessment Report

**Target:** {target}  
**Security Score:** {score}/100  
**Risk Level:** {risk_level}

### Key Findings
"""
    for finding in findings:
        report += f"- {finding}\n"
    
    report += """
### Recommendations
- Regularly audit subdomain inventory
- Implement email harvesting countermeasures
- Review firewall rules for exposed services
- Enable security headers on web servers
"""
    
    return {
        "report": report,
        "model": "fallback-rules",
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
