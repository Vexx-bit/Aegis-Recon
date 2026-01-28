#!/usr/bin/env python3
"""
Test script for PDF report generation
Creates a sample summary and generates a test report
"""

import json
import os
import tempfile
from normalize_and_score import create_test_case_2, RiskScorer
from report_gen import generate_pdf_report

def test_report_generation():
    """Test PDF report generation with sample data."""
    print("=" * 70)
    print("PDF REPORT GENERATOR TEST")
    print("=" * 70)
    
    try:
        # Step 1: Create test scan data
        print("\n[1] Creating test scan data...")
        scan_data = create_test_case_2()
        print("    ✓ Test data created")
        
        # Step 2: Generate risk score
        print("\n[2] Calculating risk scores...")
        scorer = RiskScorer()
        summary_data = scorer.analyze_scan_results(scan_data)
        print(f"    ✓ Risk score calculated: {summary_data['risk_score']}/100")
        
        # Step 3: Save summary to temp file
        print("\n[3] Saving summary JSON...")
        temp_dir = tempfile.gettempdir()
        summary_path = os.path.join(temp_dir, "test_summary.json")
        
        with open(summary_path, 'w') as f:
            json.dump(summary_data, f, indent=2)
        print(f"    ✓ Summary saved to: {summary_path}")
        
        # Step 4: Generate PDF report
        print("\n[4] Generating PDF report...")
        output_path = os.path.join(temp_dir, "test_report.pdf")
        
        result_path = generate_pdf_report(summary_path, output_path)
        print(f"    ✓ PDF generated: {result_path}")
        
        # Step 5: Verify file exists
        print("\n[5] Verifying output...")
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"    ✓ PDF file exists ({file_size:,} bytes)")
        else:
            print("    ✗ PDF file not found")
            return False
        
        print("\n" + "=" * 70)
        print("TEST PASSED ✓")
        print("=" * 70)
        print(f"\nGenerated report: {result_path}")
        print("Open this file to view the PDF report.")
        
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    import sys
    success = test_report_generation()
    sys.exit(0 if success else 1)
