/**
 * Aegis Recon - Dashboard JavaScript (Vercel Edition)
 * Simplified for serverless architecture - no polling needed
 */

// Configuration
const API_BASE_URL = window.AEGIS_CONFIG?.apiBaseUrl || '/api';

// State
let currentResults = null;

// DOM Elements
const scanForm = document.getElementById('scanForm');
const domainInput = document.getElementById('domainInput');
const startScanBtn = document.getElementById('startScanBtn');
const alertContainer = document.getElementById('alertContainer');
const statusSection = document.getElementById('statusSection');
const statusMessage = document.getElementById('statusMessage');
const progressBar = document.getElementById('progressBar');
const targetDisplay = document.getElementById('targetDisplay');
const resultsSection = document.getElementById('resultsSection');
const newScanBtn = document.getElementById('newScanBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    scanForm.addEventListener('submit', handleScanSubmit);
    newScanBtn.addEventListener('click', resetDashboard);
    
    // Report button
    const reportBtn = document.getElementById('generateReportBtn');
    if (reportBtn) {
        reportBtn.addEventListener('click', generateReport);
    }
});

/**
 * Handle scan form submission
 */
async function handleScanSubmit(e) {
    e.preventDefault();
    
    const domain = domainInput.value.trim();
    if (!domain) {
        showAlert('Please enter a domain', 'warning');
        return;
    }
    
    // Clean domain
    const cleanDomain = domain.replace(/^https?:\/\//, '').replace(/\/.*$/, '');
    
    // Update UI
    startScanBtn.disabled = true;
    startScanBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Scanning...';
    
    // Show status
    statusSection.classList.remove('hidden');
    targetDisplay.textContent = cleanDomain;
    statusMessage.innerHTML = '<i class="bi bi-gear-fill"></i> Scanning in progress...';
    progressBar.style.width = '30%';
    
    // Show scanning badge in header
    const statusDisplay = document.getElementById('statusDisplay');
    if (statusDisplay) statusDisplay.style.display = 'inline-block';
    
    try {
        console.log('[SCAN] Starting scan for:', cleanDomain);
        
        // Call Vercel serverless API
        const response = await fetch(`${API_BASE_URL}/scan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ domain: cleanDomain })
        });
        
        progressBar.style.width = '70%';
        
        const data = await response.json();
        console.log('[SCAN] Response:', data);
        
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Scan failed');
        }
        
        progressBar.style.width = '100%';
        statusMessage.innerHTML = '<i class="bi bi-check-circle-fill"></i> Scan complete!';
        
        // Store and display results
        currentResults = data.results;
        displayResults(data.results);
        
        // Hide status after brief delay
        setTimeout(() => {
            statusSection.classList.add('hidden');
            if (statusDisplay) statusDisplay.style.display = 'none';
        }, 1500);
        
        // Show new scan button
        newScanBtn.style.display = 'inline-block';
        
        // Enable report button
        const reportBtn = document.getElementById('generateReportBtn');
        if (reportBtn) reportBtn.disabled = false;
        
    } catch (error) {
        console.error('[SCAN] Error:', error);
        showAlert('Scan failed: ' + error.message, 'danger');
        statusMessage.innerHTML = '<i class="bi bi-exclamation-triangle-fill"></i> ' + error.message;
        progressBar.classList.add('bg-danger');
    } finally {
        startScanBtn.disabled = false;
        startScanBtn.innerHTML = '<i class="bi bi-search"></i> Scan';
    }
}

/**
 * Display scan results
 */
function displayResults(results) {
    if (!results || !results.phases) {
        console.warn('[DISPLAY] No results to display');
        return;
    }
    
    const phases = results.phases;
    
    // Update stats
    document.getElementById('statSubdomains').textContent = phases.subdomains?.length || 0;
    document.getElementById('statHosts').textContent = phases.hosts?.length || 0;
    document.getElementById('statEmails').textContent = phases.osint?.emails?.length || 0;
    
    // Calculate threats (ports on non-standard services)
    let threatCount = 0;
    (phases.hosts || []).forEach(host => {
        (host.ports || []).forEach(port => {
            if ([21, 22, 23, 3389, 5900].includes(port)) threatCount++;
        });
    });
    document.getElementById('statVulns').textContent = threatCount;
    
    // Display hosts
    displayHosts(phases.hosts || []);
    
    // Display technologies
    displayTechnologies(phases.technologies || []);
    
    // Display OSINT
    displayOSINT(phases.osint || {});
}

/**
 * Display hosts list
 */
function displayHosts(hosts) {
    const container = document.getElementById('hostsContent');
    
    if (!hosts || hosts.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4 text-muted">
                <i class="bi bi-server fs-2"></i>
                <p class="mt-2 mb-0">No active hosts found</p>
            </div>
        `;
        return;
    }
    
    let html = '<div class="host-list">';
    
    hosts.forEach(host => {
        const portBadges = (host.ports || []).map(port => {
            const portClass = [21, 22, 23, 3389].includes(port) ? 'bg-warning' : 'bg-primary';
            return `<span class="badge ${portClass} me-1">${port}</span>`;
        }).join('');
        
        const geoInfo = host.geo ? `${host.geo.city || ''}, ${host.geo.country || ''}`.trim() : '';
        
        html += `
            <div class="host-item p-3 mb-2 rounded border" style="background: #f8fafc;">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong class="text-dark">${host.hostname}</strong>
                        <div class="text-muted small">${host.ip}</div>
                        ${geoInfo ? `<div class="text-muted small"><i class="bi bi-geo-alt"></i> ${geoInfo}</div>` : ''}
                    </div>
                    <span class="badge ${host.status === 'up' ? 'bg-success' : 'bg-secondary'}">${host.status}</span>
                </div>
                <div class="mt-2">
                    ${portBadges || '<span class="text-muted small">No open ports</span>'}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

/**
 * Display technologies
 */
function displayTechnologies(technologies) {
    const container = document.getElementById('technologyContent');
    
    if (!technologies || technologies.length === 0) {
        container.innerHTML = '<p class="text-muted small mb-0">No technologies detected</p>';
        return;
    }
    
    let html = '<div class="d-flex flex-wrap gap-2">';
    
    technologies.forEach(tech => {
        const icon = getTechIcon(tech.name);
        html += `
            <span class="badge bg-light text-dark border" style="font-size: 0.8rem;">
                <i class="bi ${icon}"></i> ${tech.name}
            </span>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

/**
 * Get icon for technology
 */
function getTechIcon(name) {
    const icons = {
        'wordpress': 'bi-wordpress',
        'apache': 'bi-server',
        'nginx': 'bi-server',
        'cloudflare': 'bi-cloud',
        'react': 'bi-code-slash',
        'vue': 'bi-code-slash',
        'angular': 'bi-code-slash',
        'jquery': 'bi-code-slash',
        'bootstrap': 'bi-grid',
        'php': 'bi-filetype-php',
        'node': 'bi-diagram-3',
        'python': 'bi-filetype-py'
    };
    
    const lowerName = name.toLowerCase();
    for (const [key, icon] of Object.entries(icons)) {
        if (lowerName.includes(key)) return icon;
    }
    return 'bi-cpu';
}

/**
 * Display OSINT data
 */
function displayOSINT(osint) {
    const container = document.getElementById('emailsList');
    const emails = osint.emails || [];
    
    if (emails.length === 0) {
        container.innerHTML = '<p class="text-muted small mb-0">No exposed emails found</p>';
        return;
    }
    
    let html = '<ul class="list-unstyled mb-0">';
    
    emails.forEach(email => {
        html += `
            <li class="d-flex align-items-center py-1">
                <i class="bi bi-envelope text-danger me-2"></i>
                <span class="small">${email}</span>
            </li>
        `;
    });
    
    html += '</ul>';
    container.innerHTML = html;
}

/**
 * Generate AI threat report
 */
async function generateReport() {
    if (!currentResults) {
        showAlert('No scan results available', 'warning');
        return;
    }
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('reportModal'));
    modal.show();
    
    // Reset modal content
    document.getElementById('reportModalBody').innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-3">Generating AI threat analysis...</p>
        </div>
    `;
    
    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ results: currentResults })
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Failed to generate report');
        }
        
        // Display the report
        displayReport(data.analysis);
        
    } catch (error) {
        console.error('[REPORT] Error:', error);
        document.getElementById('reportModalBody').innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i> ${error.message}
            </div>
        `;
    }
}

/**
 * Display the generated report
 */
function displayReport(analysis) {
    const container = document.getElementById('reportModalBody');
    
    // Convert markdown to HTML (basic)
    let reportHtml = analysis.report
        .replace(/^### (.*$)/gim, '<h5 class="mt-4 mb-3">$1</h5>')
        .replace(/^## (.*$)/gim, '<h4 class="mt-4 mb-3">$1</h4>')
        .replace(/^\*\*(.*)\*\*/gim, '<strong>$1</strong>')
        .replace(/^- (.*$)/gim, '<li>$1</li>')
        .replace(/\n/g, '<br>');
    
    // Wrap lists
    reportHtml = reportHtml.replace(/(<li>.*<\/li>)+/g, '<ul class="mb-3">$&</ul>');
    
    container.innerHTML = `
        <div class="report-content">
            ${reportHtml}
        </div>
        <hr>
        <div class="text-muted small">
            <i class="bi bi-robot"></i> Generated by: ${analysis.model || 'AI Analysis'}
            <br>
            <i class="bi bi-clock"></i> ${new Date(analysis.generated_at).toLocaleString()}
        </div>
    `;
}

/**
 * Download report as PDF
 */
function downloadReportPDF() {
    const element = document.getElementById('reportModalBody');
    const opt = {
        margin: 1,
        filename: `aegis-recon-report-${Date.now()}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
    };
    
    html2pdf().set(opt).from(element).save();
}

/**
 * Reset dashboard for new scan
 */
function resetDashboard() {
    // Clear input
    domainInput.value = '';
    
    // Reset stats
    document.getElementById('statSubdomains').textContent = '0';
    document.getElementById('statHosts').textContent = '0';
    document.getElementById('statVulns').textContent = '0';
    document.getElementById('statEmails').textContent = '0';
    
    // Reset content areas
    document.getElementById('hostsContent').innerHTML = `
        <div class="text-center py-5 text-muted">
            <i class="bi bi-search fs-1"></i>
            <p class="mt-3 mb-0">Enter a domain above to start scanning</p>
        </div>
    `;
    document.getElementById('technologyContent').innerHTML = '<p class="text-muted small mb-0">No data yet</p>';
    document.getElementById('emailsList').innerHTML = '<p class="text-muted small mb-0">No data yet</p>';
    
    // Hide buttons
    newScanBtn.style.display = 'none';
    statusSection.classList.add('hidden');
    
    // Disable report button
    const reportBtn = document.getElementById('generateReportBtn');
    if (reportBtn) reportBtn.disabled = true;
    
    // Clear stored results
    currentResults = null;
    
    // Focus input
    domainInput.focus();
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alert.remove();
    }, 5000);
}
