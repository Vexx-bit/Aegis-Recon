"""
Stunning Visualizations for Aegis Recon
Creates interactive 3D network graphs, heatmaps, and gauges using Plotly
"""

import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


def create_3d_network_graph(scan_results: Dict[str, Any]) -> str:
    """
    Create stunning 3D network topology visualization.
    
    Args:
        scan_results: Complete scan results dictionary
        
    Returns:
        HTML string with embedded Plotly graph
    """
    try:
        # Create network graph
        G = nx.Graph()
        
        # Get target
        target = scan_results.get('target', 'Unknown')
        target_risk = calculate_overall_risk(scan_results)
        G.add_node(target, type='target', risk=target_risk, size=25)
        
        # Add subdomain nodes
        subdomains = scan_results.get('phases', {}).get('subdomains', [])
        for subdomain in subdomains:
            if subdomain != target:  # Don't duplicate target
                risk = calculate_subdomain_risk(subdomain, scan_results)
                G.add_node(subdomain, type='subdomain', risk=risk, size=15)
                G.add_edge(target, subdomain, weight=1.0)
        
        # Add OSINT nodes (emails, hosts)
        osint = scan_results.get('phases', {}).get('osint', {})
        
        # Add email nodes
        for email in osint.get('emails', [])[:5]:  # Limit to 5 for clarity
            G.add_node(email, type='email', risk=0.3, size=10)
            G.add_edge(target, email, weight=0.5)
        
        # Add discovered host nodes
        for host in osint.get('hosts', [])[:5]:
            if host not in G.nodes():
                G.add_node(host, type='osint_host', risk=0.4, size=12)
                G.add_edge(target, host, weight=0.7)
        
        # If graph is too small, add some context
        if len(G.nodes()) < 2:
            G.add_node('Internet', type='context', risk=0.1, size=20)
            G.add_edge(target, 'Internet', weight=0.3)
        
        # Generate 3D spring layout
        pos = nx.spring_layout(G, dim=3, seed=42, k=0.5, iterations=50)
        
        # Extract node positions
        node_x = []
        node_y = []
        node_z = []
        node_colors = []
        node_sizes = []
        node_text = []
        node_hover = []
        
        for node in G.nodes():
            x, y, z = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_z.append(z)
            
            # Get node attributes
            risk = G.nodes[node].get('risk', 0)
            node_type = G.nodes[node].get('type', 'unknown')
            size = G.nodes[node].get('size', 15)
            
            # Color gradient based on risk: green (safe) → yellow → red (critical)
            if risk < 0.3:
                color = 'rgb(34, 197, 94)'  # Green
            elif risk < 0.7:
                color = 'rgb(251, 191, 36)'  # Yellow/Orange
            else:
                color = 'rgb(239, 68, 68)'  # Red
            
            node_colors.append(color)
            node_sizes.append(size)
            
            # Node labels
            node_text.append(node[:20] if len(node) > 20 else node)
            
            # Hover text
            type_emoji = {
                'target': '🎯',
                'subdomain': '🌐',
                'email': '📧',
                'osint_host': '🔍',
                'context': '🌍'
            }
            emoji = type_emoji.get(node_type, '•')
            node_hover.append(
                f"{emoji} <b>{node}</b><br>"
                f"Type: {node_type.replace('_', ' ').title()}<br>"
                f"Risk Level: {risk:.0%}<br>"
                f"Connections: {len(list(G.neighbors(node)))}"
            )
        
        # Create edges
        edge_x = []
        edge_y = []
        edge_z = []
        edge_colors = []
        
        for edge in G.edges(data=True):
            x0, y0, z0 = pos[edge[0]]
            x1, y1, z1 = pos[edge[1]]
            
            # Edge color based on weight
            weight = edge[2].get('weight', 1.0)
            alpha = int(weight * 255)
            edge_colors.append(f'rgba(125, 125, 125, {weight * 0.5})')
            
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_z.extend([z0, z1, None])
        
        # Create Plotly figure
        fig = go.Figure()
        
        # Add edges as lines
        fig.add_trace(go.Scatter3d(
            x=edge_x, y=edge_y, z=edge_z,
            mode='lines',
            line=dict(color='rgba(125, 125, 125, 0.3)', width=2),
            hoverinfo='none',
            showlegend=False,
            name='Connections'
        ))
        
        # Add nodes as markers
        fig.add_trace(go.Scatter3d(
            x=node_x, y=node_y, z=node_z,
            mode='markers+text',
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(color='rgba(255, 255, 255, 0.8)', width=2),
                opacity=0.9,
                symbol='circle'
            ),
            text=node_text,
            textposition='top center',
            textfont=dict(size=10, color='white', family='Arial Black'),
            hovertext=node_hover,
            hoverinfo='text',
            showlegend=False,
            name='Network Nodes'
        ))
        
        # Update layout for stunning dark theme
        fig.update_layout(
            title=dict(
                text=f'<b>🌐 3D Network Topology: {target}</b>',
                font=dict(size=22, color='white', family='Arial'),
                x=0.5,
                xanchor='center'
            ),
            scene=dict(
                xaxis=dict(
                    showbackground=False,
                    showgrid=False,
                    zeroline=False,
                    visible=False
                ),
                yaxis=dict(
                    showbackground=False,
                    showgrid=False,
                    zeroline=False,
                    visible=False
                ),
                zaxis=dict(
                    showbackground=False,
                    showgrid=False,
                    zeroline=False,
                    visible=False
                ),
                bgcolor='rgba(15, 15, 25, 1)',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.2)
                )
            ),
            paper_bgcolor='rgba(15, 15, 25, 1)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            hovermode='closest',
            margin=dict(l=0, r=0, t=50, b=0),
            height=600,
            font=dict(color='white')
        )
        
        # Add annotation
        fig.add_annotation(
            text=f"<i>Nodes: {len(G.nodes())} | Connections: {len(G.edges())} | Risk: {target_risk:.0%}</i>",
            xref="paper", yref="paper",
            x=0.5, y=0.02,
            showarrow=False,
            font=dict(size=12, color='rgba(255,255,255,0.7)')
        )
        
        # Return HTML with custom styling
        html = fig.to_html(
            include_plotlyjs='cdn',
            div_id='network-graph-3d',
            config={'displayModeBar': True, 'displaylogo': False}
        )
        
        return html
        
    except Exception as e:
        logger.error(f"Error creating 3D network graph: {str(e)}")
        return f'<div class="alert alert-warning">3D visualization unavailable: {str(e)}</div>'


def create_risk_gauge(scan_results: Dict[str, Any]) -> str:
    """
    Create animated risk score gauge.
    
    Args:
        scan_results: Complete scan results dictionary
        
    Returns:
        HTML string with embedded Plotly gauge
    """
    try:
        risk = calculate_overall_risk(scan_results)
        score = int((1 - risk) * 100)  # Invert: 100 = safe, 0 = critical
        
        # Determine risk level
        if score >= 80:
            risk_level = "🟢 Excellent"
            risk_color = "green"
        elif score >= 60:
            risk_level = "🟡 Good"
            risk_color = "yellow"
        elif score >= 40:
            risk_level = "🟠 Fair"
            risk_color = "orange"
        else:
            risk_level = "🔴 Critical"
            risk_color = "red"
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={
                'text': f"<b>Security Score</b><br><span style='font-size:16px'>{risk_level}</span>",
                'font': {'size': 24, 'color': 'white'}
            },
            delta={'reference': 80, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
            number={'font': {'size': 60, 'color': 'white'}},
            gauge={
                'axis': {
                    'range': [None, 100],
                    'tickwidth': 2,
                    'tickcolor': "white",
                    'tickfont': {'color': 'white', 'size': 12}
                },
                'bar': {'color': risk_color, 'thickness': 0.75},
                'bgcolor': "rgba(255,255,255,0.1)",
                'borderwidth': 2,
                'bordercolor': "rgba(255,255,255,0.3)",
                'steps': [
                    {'range': [0, 40], 'color': 'rgba(239, 68, 68, 0.3)'},  # Red
                    {'range': [40, 70], 'color': 'rgba(251, 191, 36, 0.3)'},  # Yellow
                    {'range': [70, 100], 'color': 'rgba(34, 197, 94, 0.3)'}  # Green
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 3},
                    'thickness': 0.75,
                    'value': score
                }
            }
        ))
        
        fig.update_layout(
            paper_bgcolor='rgba(15, 15, 25, 1)',
            font={'color': "white", 'family': "Arial"},
            height=350,
            margin=dict(l=20, r=20, t=80, b=20)
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id='risk-gauge', config={'displayModeBar': False})
        
    except Exception as e:
        logger.error(f"Error creating risk gauge: {str(e)}")
        return f'<div class="alert alert-warning">Risk gauge unavailable: {str(e)}</div>'


def create_vulnerability_chart(scan_results: Dict[str, Any]) -> str:
    """
    Create vulnerability distribution chart.
    
    Args:
        scan_results: Complete scan results dictionary
        
    Returns:
        HTML string with embedded Plotly chart
    """
    try:
        # Collect all vulnerabilities
        all_vulns = []
        hosts = scan_results.get('phases', {}).get('hosts', [])
        
        for host in hosts:
            vulns = host.get('vulnerabilities', [])
            for vuln in vulns:
                all_vulns.append({
                    'host': host.get('host', 'Unknown'),
                    'message': vuln.get('msg', 'Unknown'),
                    'method': vuln.get('method', 'GET'),
                    'url': vuln.get('url', '/')
                })
        
        if not all_vulns:
            return '<div class="alert alert-info">No vulnerabilities detected - Great job! 🎉</div>'
        
        # Create bar chart
        vuln_counts = {}
        for vuln in all_vulns:
            host = vuln['host']
            vuln_counts[host] = vuln_counts.get(host, 0) + 1
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(vuln_counts.keys()),
                y=list(vuln_counts.values()),
                marker=dict(
                    color=list(vuln_counts.values()),
                    colorscale='Reds',
                    showscale=False
                ),
                text=list(vuln_counts.values()),
                textposition='auto',
                hovertemplate='<b>%{x}</b><br>Vulnerabilities: %{y}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title=dict(
                text='<b>Vulnerabilities by Host</b>',
                font=dict(size=20, color='white')
            ),
            xaxis=dict(
                title='Host',
                color='white',
                gridcolor='rgba(255,255,255,0.1)'
            ),
            yaxis=dict(
                title='Count',
                color='white',
                gridcolor='rgba(255,255,255,0.1)'
            ),
            paper_bgcolor='rgba(15, 15, 25, 1)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=300,
            margin=dict(l=60, r=20, t=60, b=60)
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id='vuln-chart', config={'displayModeBar': False})
        
    except Exception as e:
        logger.error(f"Error creating vulnerability chart: {str(e)}")
        return f'<div class="alert alert-warning">Vulnerability chart unavailable: {str(e)}</div>'


def calculate_overall_risk(scan_results: Dict[str, Any]) -> float:
    """
    Calculate overall risk score (0-1).
    
    Args:
        scan_results: Complete scan results dictionary
        
    Returns:
        Risk score from 0.0 (safe) to 1.0 (critical)
    """
    score = 0.0
    
    # Factor in vulnerabilities (max 0.5)
    vuln_count = scan_results.get('metadata', {}).get('total_vulnerabilities', 0)
    score += min(vuln_count * 0.05, 0.5)
    
    # Factor in outdated technologies (max 0.3)
    hosts = scan_results.get('phases', {}).get('hosts', [])
    outdated_count = 0
    for host in hosts:
        if host.get('outdated_technologies'):
            outdated_count += len(host.get('outdated_technologies', []))
    score += min(outdated_count * 0.1, 0.3)
    
    # Factor in dangerous open ports (max 0.2)
    dangerous_ports = [21, 23, 445, 3389, 1433, 3306]  # FTP, Telnet, SMB, RDP, MSSQL, MySQL
    for host in hosts:
        ports = host.get('nmap', {}).get('ports', [])
        for port in ports:
            if port.get('port') in dangerous_ports and port.get('state') == 'open':
                score += 0.05
    
    return min(score, 1.0)


def calculate_subdomain_risk(subdomain: str, scan_results: Dict[str, Any]) -> float:
    """
    Calculate risk for a specific subdomain.
    
    Args:
        subdomain: Subdomain to calculate risk for
        scan_results: Complete scan results dictionary
        
    Returns:
        Risk score from 0.0 (safe) to 1.0 (critical)
    """
    hosts = scan_results.get('phases', {}).get('hosts', [])
    
    for host in hosts:
        if host.get('host') == subdomain:
            # Calculate risk for this specific host
            host_risk = 0.0
            
            # Vulnerabilities
            vuln_count = len(host.get('vulnerabilities', []))
            host_risk += min(vuln_count * 0.1, 0.6)
            
            # Outdated tech
            if host.get('outdated_technologies'):
                host_risk += 0.2
            
            # Open ports
            ports = host.get('nmap', {}).get('ports', [])
            open_count = sum(1 for p in ports if p.get('state') == 'open')
            host_risk += min(open_count * 0.02, 0.2)
            
            return min(host_risk, 1.0)
    
    return 0.3  # Default moderate risk if not found
