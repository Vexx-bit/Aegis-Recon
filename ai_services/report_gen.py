#!/usr/bin/env python3
"""
Aegis Recon - PDF Report Generator
Generates professional security assessment reports from scan results.
"""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.pdfgen import canvas
except ImportError:
    print("Error: ReportLab not installed. Install with: pip install reportlab", file=sys.stderr)
    sys.exit(1)


class ReportGenerator:
    """Generate PDF security assessment reports."""
    
    def __init__(self, summary_data: dict):
        """
        Initialize report generator.
        
        Args:
            summary_data: Dictionary containing scan results and risk scoring
        """
        self.data = summary_data
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.story = []
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1d29'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#666666'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        # Section header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#0d6efd'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Risk level styles
        self.styles.add(ParagraphStyle(
            name='RiskCritical',
            parent=self.styles['Normal'],
            fontSize=18,
            textColor=colors.HexColor('#dc3545'),
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='RiskHigh',
            parent=self.styles['Normal'],
            fontSize=18,
            textColor=colors.HexColor('#fd7e14'),
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='RiskMedium',
            parent=self.styles['Normal'],
            fontSize=18,
            textColor=colors.HexColor('#ffc107'),
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='RiskLow',
            parent=self.styles['Normal'],
            fontSize=18,
            textColor=colors.HexColor('#198754'),
            fontName='Helvetica-Bold'
        ))
    
    def _add_cover_page(self):
        """Add cover page to report."""
        # Logo placeholder (shield icon)
        self.story.append(Spacer(1, 1.5*inch))
        
        # Project title
        title = Paragraph("AEGIS RECON", self.styles['CustomTitle'])
        self.story.append(title)
        
        subtitle = Paragraph("Security Assessment Report", self.styles['CustomSubtitle'])
        self.story.append(subtitle)
        
        self.story.append(Spacer(1, 0.5*inch))
        
        # Target information
        target = self.data.get('target', 'Unknown Target')
        target_para = Paragraph(f"<b>Target:</b> {target}", self.styles['Normal'])
        self.story.append(target_para)
        
        # Date
        report_date = datetime.now().strftime("%B %d, %Y")
        date_para = Paragraph(f"<b>Report Date:</b> {report_date}", self.styles['Normal'])
        self.story.append(date_para)
        
        # Job ID
        job_id = self.data.get('job_id', 'N/A')
        job_para = Paragraph(f"<b>Job ID:</b> {job_id}", self.styles['Normal'])
        self.story.append(job_para)
        
        self.story.append(Spacer(1, 1*inch))
        
        # Risk score box
        risk_score = self.data.get('risk_score', 0)
        risk_level = self.data.get('risk_level', 'UNKNOWN')
        
        risk_style_name = f'Risk{risk_level.title()}' if f'Risk{risk_level.title()}' in self.styles else 'Normal'
        
        risk_data = [
            ['Overall Risk Score', f'{risk_score}/100'],
            ['Risk Level', risk_level]
        ]
        
        risk_table = Table(risk_data, colWidths=[3*inch, 2*inch])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        self.story.append(risk_table)
        
        self.story.append(Spacer(1, 0.5*inch))
        
        # Confidentiality notice
        notice = Paragraph(
            "<i>CONFIDENTIAL - This report contains sensitive security information. "
            "Handle with appropriate care and distribute only to authorized personnel.</i>",
            self.styles['Normal']
        )
        self.story.append(notice)
        
        self.story.append(PageBreak())
    
    def _add_executive_summary(self):
        """Add executive summary section."""
        # Section header
        header = Paragraph("Executive Summary", self.styles['SectionHeader'])
        self.story.append(header)
        
        # Get metadata
        metadata = self.data.get('metadata', {})
        total_findings = metadata.get('total_findings', 0)
        
        # Summary text
        risk_score = self.data.get('risk_score', 0)
        risk_level = self.data.get('risk_level', 'UNKNOWN')
        target = self.data.get('target', 'the target system')
        
        summary_text = f"""
        This security assessment was conducted on <b>{target}</b> to identify potential 
        vulnerabilities and security weaknesses. The assessment included network reconnaissance, 
        port scanning, service enumeration, and web vulnerability scanning.
        <br/><br/>
        <b>Key Findings:</b>
        <br/>
        • Overall Risk Score: <b>{risk_score}/100</b> ({risk_level})
        <br/>
        • Total Security Findings: <b>{total_findings}</b>
        <br/>
        • Assessment Date: <b>{metadata.get('analyzed_at', 'N/A')}</b>
        <br/><br/>
        """
        
        # Add risk-based recommendation
        if risk_score >= 70:
            summary_text += """
            <b>Critical Action Required:</b> This assessment identified critical security issues 
            that require immediate attention. The vulnerabilities discovered could lead to system 
            compromise, data breach, or service disruption. Immediate remediation is strongly recommended.
            """
        elif risk_score >= 50:
            summary_text += """
            <b>High Priority Issues:</b> This assessment identified significant security concerns 
            that should be addressed promptly. Schedule remediation activities within the next 7 days 
            to reduce risk exposure.
            """
        elif risk_score >= 30:
            summary_text += """
            <b>Medium Risk Profile:</b> This assessment identified moderate security issues that 
            should be addressed as part of your regular security maintenance cycle. Plan remediation 
            within the next 30 days.
            """
        else:
            summary_text += """
            <b>Low Risk Profile:</b> This assessment found minimal security concerns. Continue 
            monitoring and maintain current security best practices. Address identified issues 
            during routine maintenance windows.
            """
        
        summary_para = Paragraph(summary_text, self.styles['BodyText'])
        self.story.append(summary_para)
        
        self.story.append(Spacer(1, 0.3*inch))
    
    def _add_findings_table(self):
        """Add table of top findings."""
        header = Paragraph("Security Findings", self.styles['SectionHeader'])
        self.story.append(header)
        
        findings = self.data.get('finding_scores', [])
        
        if not findings:
            no_findings = Paragraph("No security findings were identified during this assessment.", 
                                   self.styles['Normal'])
            self.story.append(no_findings)
            return
        
        # Sort findings by severity and points
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        sorted_findings = sorted(
            findings, 
            key=lambda x: (severity_order.get(x.get('severity', 'LOW'), 4), -x.get('points', 0))
        )
        
        # Create table data
        table_data = [['#', 'Severity', 'Finding Type', 'Host', 'Points', 'Description']]
        
        for idx, finding in enumerate(sorted_findings[:20], 1):  # Limit to top 20
            severity = finding.get('severity', 'UNKNOWN')
            finding_type = finding.get('type', 'unknown').replace('_', ' ').title()
            host = finding.get('host', 'N/A')
            points = finding.get('points', 0)
            
            # Get short description
            if finding.get('type') == 'exposed_database_port':
                desc = f"{finding.get('service', 'Database')} on port {finding.get('port', 'N/A')}"
            elif finding.get('type') == 'outdated_service':
                desc = f"{finding.get('service', 'Service')} v{finding.get('version', 'N/A')}"
            elif finding.get('type') == 'web_vulnerability':
                desc = finding.get('description', 'Web vulnerability')[:50] + '...'
            else:
                desc = finding.get('rationale', 'Security issue')[:50] + '...'
            
            table_data.append([
                str(idx),
                severity,
                finding_type,
                host,
                f'+{points}',
                desc
            ])
        
        # Create table
        findings_table = Table(table_data, colWidths=[0.3*inch, 0.8*inch, 1.2*inch, 1.5*inch, 0.5*inch, 2.2*inch])
        
        # Style table
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]
        
        # Color code severity column
        for idx, finding in enumerate(sorted_findings[:20], 1):
            severity = finding.get('severity', 'UNKNOWN')
            if severity == 'CRITICAL':
                table_style.append(('TEXTCOLOR', (1, idx), (1, idx), colors.HexColor('#dc3545')))
                table_style.append(('FONTNAME', (1, idx), (1, idx), 'Helvetica-Bold'))
            elif severity == 'HIGH':
                table_style.append(('TEXTCOLOR', (1, idx), (1, idx), colors.HexColor('#fd7e14')))
                table_style.append(('FONTNAME', (1, idx), (1, idx), 'Helvetica-Bold'))
            elif severity == 'MEDIUM':
                table_style.append(('TEXTCOLOR', (1, idx), (1, idx), colors.HexColor('#ffc107')))
        
        findings_table.setStyle(TableStyle(table_style))
        
        self.story.append(findings_table)
        self.story.append(Spacer(1, 0.3*inch))
    
    def _add_remediation_checklist(self):
        """Add remediation checklist."""
        self.story.append(PageBreak())
        
        header = Paragraph("Remediation Checklist", self.styles['SectionHeader'])
        self.story.append(header)
        
        intro = Paragraph(
            "The following checklist outlines recommended remediation actions based on the findings. "
            "Check off items as they are completed and track progress toward improving your security posture.",
            self.styles['Normal']
        )
        self.story.append(intro)
        self.story.append(Spacer(1, 0.2*inch))
        
        findings = self.data.get('finding_scores', [])
        
        if not findings:
            no_items = Paragraph("No remediation items required.", self.styles['Normal'])
            self.story.append(no_items)
            return
        
        # Group findings by type
        remediation_items = []
        seen_recommendations = set()
        
        for finding in findings:
            recommendation = finding.get('recommendation', '')
            if recommendation and recommendation not in seen_recommendations:
                seen_recommendations.add(recommendation)
                remediation_items.append({
                    'severity': finding.get('severity', 'MEDIUM'),
                    'recommendation': recommendation,
                    'type': finding.get('type', 'unknown')
                })
        
        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        remediation_items.sort(key=lambda x: severity_order.get(x['severity'], 4))
        
        # Create checklist table
        checklist_data = [['☐', 'Priority', 'Remediation Action']]
        
        for item in remediation_items[:15]:  # Limit to top 15
            severity = item['severity']
            recommendation = item['recommendation']
            
            checklist_data.append([
                '☐',
                severity,
                recommendation
            ])
        
        checklist_table = Table(checklist_data, colWidths=[0.3*inch, 0.8*inch, 5.4*inch])
        
        checklist_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#198754')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (0, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (1, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]
        
        checklist_table.setStyle(TableStyle(checklist_style))
        
        self.story.append(checklist_table)
        self.story.append(Spacer(1, 0.3*inch))
        
        # Add note
        note = Paragraph(
            "<i>Note: This checklist represents high-priority remediation items. "
            "Consult with your security team for detailed implementation guidance.</i>",
            self.styles['Normal']
        )
        self.story.append(note)
    
    def _add_footer(self):
        """Add footer section."""
        self.story.append(PageBreak())
        
        header = Paragraph("About This Report", self.styles['SectionHeader'])
        self.story.append(header)
        
        about_text = """
        This security assessment report was generated by <b>Aegis Recon</b>, an AI-powered 
        cyber defense and reconnaissance platform. The assessment utilized industry-standard 
        tools including Nmap, Nikto, and Sublist3r to identify potential security vulnerabilities.
        <br/><br/>
        <b>Methodology:</b>
        <br/>
        1. Subdomain enumeration to identify all accessible hosts
        <br/>
        2. Port scanning to discover open services
        <br/>
        3. Service version detection to identify outdated software
        <br/>
        4. Web vulnerability scanning for common security issues
        <br/>
        5. Risk scoring based on industry-standard severity classifications
        <br/><br/>
        <b>Disclaimer:</b>
        <br/>
        This report is provided for informational purposes only. The findings represent potential 
        security issues identified during automated scanning. Manual verification and additional 
        testing may be required to confirm vulnerabilities. Aegis Recon is not responsible for 
        any actions taken based on this report.
        <br/><br/>
        For questions or additional analysis, please contact your security team.
        """
        
        about_para = Paragraph(about_text, self.styles['Normal'])
        self.story.append(about_para)
    
    def generate_report(self, output_path: str) -> str:
        """
        Generate the PDF report.
        
        Args:
            output_path: Path where PDF should be saved
            
        Returns:
            Path to generated PDF file
        """
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Build report sections
        self._add_cover_page()
        self._add_executive_summary()
        self._add_findings_table()
        self._add_remediation_checklist()
        self._add_footer()
        
        # Build PDF
        doc.build(self.story)
        
        return output_path


def generate_pdf_report(summary_path: str, output_path: str) -> str:
    """
    Generate PDF report from summary JSON.
    
    Args:
        summary_path: Path to summary JSON file
        output_path: Path for output PDF file
        
    Returns:
        Path to generated PDF
    """
    # Load summary data
    try:
        with open(summary_path, 'r') as f:
            summary_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Summary file not found: {summary_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in summary file: {str(e)}")
    
    # Generate report
    generator = ReportGenerator(summary_data)
    output_file = generator.generate_report(output_path)
    
    return output_file


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Aegis Recon - PDF Report Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python report_gen.py --summary /tmp/summary-job123.json --out /tmp/report-job123.pdf
  python report_gen.py -s results.json -o report.pdf
        """
    )
    
    parser.add_argument(
        '--summary', '-s',
        required=True,
        help='Path to summary JSON file (from normalize_and_score.py)'
    )
    
    parser.add_argument(
        '--out', '-o',
        required=True,
        help='Output path for PDF report'
    )
    
    args = parser.parse_args()
    
    try:
        # Generate report
        output_file = generate_pdf_report(args.summary, args.out)
        
        # Print output path to stdout
        print(output_file)
        
        return 0
        
    except Exception as e:
        print(f"Error generating report: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
