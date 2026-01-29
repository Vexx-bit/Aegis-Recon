#!/usr/bin/env python3
"""
Aegis Recon - AI Analyst Service
Uses Groq (Llama 3 70B) to generate human-readable threat reports from scan data.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional

# Import Groq client directly or use requests if the library isn't installed in the environment yet
try:
    from groq import Groq
except ImportError:
    # Fallback or exit - standard environment should have it via requirements.txt
    print("Error: 'groq' library not found. Please run: pip install groq")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIAnalyst:
    def __init__(self, job_id: str, results_path: str):
        self.job_id = job_id
        self.results_path = results_path
        self.api_key = os.getenv('GROQ_API_KEY')
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
            
        self.client = Groq(api_key=self.api_key)

    def load_results(self) -> Dict[str, Any]:
        """Load the raw scan results from JSON."""
        if not os.path.exists(self.results_path):
            raise FileNotFoundError(f"Results file not found: {self.results_path}")
            
        with open(self.results_path, 'r') as f:
            return json.load(f)

    def generate_prompt(self, data: Dict[str, Any]) -> str:
        """Construct a concise prompt for the LLM."""
        
        # Extract key metrics to reduce token usage
        target = data.get('target', 'Unknown')
        phases = data.get('results', {}).get('phases', {})
        
        # Summarize hosts
        hosts_summary = []
        for host in phases.get('hosts', []):
            vulns = len(host.get('vulnerabilities', []))
            outdated = len(host.get('whatweb', {}).get('outdated_technologies', []))
            tech = ", ".join(host.get('technologies', {}).get('summary', {}).get('web_servers', []))
            hosts_summary.append(f"- {host['host']}: {vulns} vulns, {outdated} outdated apps. Tech: {tech}")
            
        # Summarize OSINT
        emails = len(phases.get('osint', {}).get('emails', []))
        
        # Construct the context
        context = f"""
Target: {target}
Scan Date: {data.get('results', {}).get('timestamp')}
Emails Found: {emails}
Hosts Scanned:
{chr(10).join(hosts_summary)}

Top Vulnerabilities (Sample):
"""
        # Add a few vulnerability details if they exist
        count = 0
        for host in phases.get('hosts', []):
            for vuln in host.get('vulnerabilities', []):
                if count < 5:
                    context += f"- [{host['host']}] {vuln.get('msg')}\n"
                    count += 1
        
        return f"""
You are a Senior Cybersecurity Analyst for Aegis Recon. 
Analyze the following security scan summary and write a specialized Threat Report.

DATA:
{context}

INSTRUCTIONS:
1. EXECUTIVE SUMMARY: A 2-sentence high-level overview of the security posture.
2. CRITICAL FINDINGS: List the top 3 most dangerous issues found (or state "None" if secure).
3. OSINT EXPOSURE: assessing the risk of the emails/info found.
4. REMEDIATION: Specific, actionable technical steps to fix the issues.

TONE: Professional, urgent but not alarmist. Use Markdown formatting.
"""

    def analyze(self) -> str:
        """Run the analysis."""
        logger.info(f"Starting AI analysis for Job {self.job_id}")
        
        data = self.load_results()
        prompt = self.generate_prompt(data)
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="llama-3.3-70b-versatile",  # Updated from deprecated llama3-70b-8192
                temperature=0.5,
                max_tokens=1000,
            )
            
            report = chat_completion.choices[0].message.content
            logger.info("AI Analysis complete")
            return report
            
        except Exception as e:
            logger.error(f"Groq API Error: {str(e)}")
            return f"Error generating AI report: {str(e)}"

    def save_analysis(self, report: str):
        """Save the analysis to a file alongside the results."""
        output_path = self.results_path.replace('.json', '_ai_report.md')
        
        # Also save as JSON for API easier consumption
        json_output_path = self.results_path.replace('.json', '_ai_analysis.json')
        
        with open(output_path, 'w') as f:
            f.write(report)
            
        with open(json_output_path, 'w') as f:
            json.dump({
                "job_id": self.job_id,
                "report_markdown": report,
                "model": "llama3-70b-8192"
            }, f)
            
        logger.info(f"Report saved to {output_path}")
        print(json_output_path) # Return path to standard out for PHP

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python ai_analyst.py <job_id> <results_json_path>")
        sys.exit(1)
        
    job_id = sys.argv[1]
    results_path = sys.argv[2]
    
    # Load env vars from parent .env if not set
    if not os.getenv('GROQ_API_KEY'):
        # Primitive .env loader since python-dotenv might not be there
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if 'GROQ_API_KEY=' in line:
                        os.environ['GROQ_API_KEY'] = line.strip().split('=', 1)[1]
    
    analyst = AIAnalyst(job_id, results_path)
    report = analyst.analyze()
    analyst.save_analysis(report)
