#!/usr/bin/env python3
"""
Generate Visualizations Script
Called by PHP API to generate Plotly visualizations
"""

import sys
import json
from visualizations import (
    create_3d_network_graph,
    create_risk_gauge,
    create_vulnerability_chart
)

def main():
    if len(sys.argv) < 3:
        print("Usage: generate_visualizations.py <results_file> <visualization_type>")
        sys.exit(1)
    
    results_file = sys.argv[1]
    viz_type = sys.argv[2]
    
    # Load scan results
    with open(results_file, 'r') as f:
        scan_results = json.load(f)
    
    # Generate requested visualization
    if viz_type == '3d_network':
        html = create_3d_network_graph(scan_results)
    elif viz_type == 'risk_gauge':
        html = create_risk_gauge(scan_results)
    elif viz_type == 'vulnerability_chart':
        html = create_vulnerability_chart(scan_results)
    else:
        html = f'<div class="alert alert-danger">Unknown visualization type: {viz_type}</div>'
    
    # Output HTML
    print(html)

if __name__ == '__main__':
    main()
