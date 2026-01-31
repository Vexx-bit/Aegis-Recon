/**
 * ╔═══════════════════════════════════════════════════════════════════════════╗
 * ║                            AEGIS RECON                                     ║
 * ║              Advanced Threat Intelligence System                           ║
 * ╠═══════════════════════════════════════════════════════════════════════════╣
 * ║  Author: VexSpitta                                                         ║
 * ║  GitHub: https://github.com/Vexx-bit                                       ║
 * ║  Project: https://github.com/Vexx-bit/Aegis-Recon                         ║
 * ║                                                                            ║
 * ║  © 2024-2026 VexSpitta. All Rights Reserved.                              ║
 * ║  Unauthorized copying, modification, or distribution is prohibited.       ║
 * ╚═══════════════════════════════════════════════════════════════════════════╝
 */

// ============================================================================
// AUTHOR PROTECTION & BRANDING
// ============================================================================
(function() {
    // Console Branding
    const ASCII_BANNER = `
%c╔═══════════════════════════════════════════════════════════════╗
║     _    _____ ____ ___ ____    ____  _____ ____ ___  _   _   ║
║    / \\  | ____/ ___|_ _/ ___|  |  _ \\| ____/ ___/ _ \\| \\ | |  ║
║   / _ \\ |  _|| |  _ | |\\___ \\  | |_) |  _|| |  | | | |  \\| |  ║
║  / ___ \\| |__| |_| || | ___) | |  _ <| |__| |__| |_| | |\\  |  ║
║ /_/   \\_\\_____\\____|___|____/  |_| \\_\\_____\\____\\___/|_| \\_|  ║
╠═══════════════════════════════════════════════════════════════╣
║  🛡️  Advanced Threat Intelligence System                       ║
║  👤 Author: VexSpitta                                          ║
║  🔗 GitHub: https://github.com/Vexx-bit                        ║
║  📦 Repo:   https://github.com/Vexx-bit/Aegis-Recon            ║
╠═══════════════════════════════════════════════════════════════╣
║  ⚠️  WARNING: This software is protected by copyright law.     ║
║  Unauthorized reproduction or distribution is prohibited.      ║
╚═══════════════════════════════════════════════════════════════╝
`;
    
    console.log(ASCII_BANNER, 'color: #00ff88; font-family: monospace; font-weight: bold;');
    console.log('%c🔐 Aegis Recon v1.0.0 | © 2024-2026 VexSpitta', 'color: #3b82f6; font-size: 14px; font-weight: bold;');
    console.log('%c⚠️ If you found this code useful, please credit the author!', 'color: #f59e0b; font-size: 12px;');
    
    // Anti-DevTools Warning (non-intrusive)
    if (typeof console.clear === 'function') {
        console.log('%c🚫 Inspecting? Please respect the author\'s work.', 'color: #ef4444; font-size: 11px;');
    }
})();

// ============================================================================
// CONFIGURATION
// ============================================================================
const API_BASE_URL = window.AEGIS_CONFIG?.apiBaseUrl || '/api';
const AUTHOR = {
    name: 'VexSpitta',
    github: 'https://github.com/Vexx-bit',
    repo: 'https://github.com/Vexx-bit/Aegis-Recon',
    version: '1.0.0'
};

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

// ============================================================================
// ANTI-COPY PROTECTIONS (Basic)
// ============================================================================
(function applyProtections() {
    // Disable right-click context menu
    document.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        console.warn('🔐 Right-click disabled. Source: github.com/Vexx-bit/Aegis-Recon');
    });
    
    // Disable common keyboard shortcuts for view source
    document.addEventListener('keydown', (e) => {
        // Ctrl+U (View Source)
        if (e.ctrlKey && e.key === 'u') {
            e.preventDefault();
            console.warn('🔐 View source disabled. Author: VexSpitta');
        }
        // Ctrl+Shift+I (DevTools)
        if (e.ctrlKey && e.shiftKey && e.key === 'I') {
            e.preventDefault();
            console.warn('🔐 Please respect the author\'s work. Author: VexSpitta');
        }
        // F12 (DevTools)
        if (e.key === 'F12') {
            e.preventDefault();
        }
    });
    
    // Disable text selection on sensitive areas (optional - can be annoying)
    // document.body.style.userSelect = 'none';
    
    // Add watermark to console periodically
    setInterval(() => {
        if (console._aegisWarned) return;
        console.log('%c🛡️ Aegis Recon by VexSpitta | github.com/Vexx-bit', 'color: #6366f1; font-size: 10px;');
    }, 30000);
})();

// ============================================================================
// INITIALIZATION
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    scanForm.addEventListener('submit', handleScanSubmit);
    newScanBtn.addEventListener('click', resetDashboard);
    
    // Report button
    const reportBtn = document.getElementById('generateReportBtn');
    if (reportBtn) {
        reportBtn.addEventListener('click', generateReport);
    }
    
    // Add author footer dynamically
    addAuthorFooter();
});

/**
 * Add author footer to the page
 */
function addAuthorFooter() {
    const footer = document.createElement('footer');
    footer.innerHTML = `
        <div class="text-center py-3 mt-4 border-top" style="font-size: 0.8rem; color: #64748b;">
            <span>🛡️ Aegis Recon v${AUTHOR.version}</span> | 
            <span>Developed by <a href="${AUTHOR.github}" target="_blank" rel="noopener" style="color: #3b82f6; text-decoration: none;">${AUTHOR.name}</a></span> |
            <a href="${AUTHOR.repo}" target="_blank" rel="noopener" style="color: #6366f1; text-decoration: none;">
                <i class="bi bi-github"></i> Source
            </a>
        </div>
    `;
    document.body.appendChild(footer);
}

// ============================================================================
// SCAN HANDLING
// ============================================================================

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
    progressBar.classList.remove('bg-danger');
    
    // Show scanning badge in header
    const statusDisplay = document.getElementById('statusDisplay');
    if (statusDisplay) statusDisplay.style.display = 'inline-block';
    
    try {
        console.log(`[AEGIS] 🔍 Starting scan for: ${cleanDomain} | By ${AUTHOR.name}`);
        
        // Call serverless API
        const response = await fetch(`${API_BASE_URL}/scan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ domain: cleanDomain })
        });
        
        progressBar.style.width = '70%';
        
        const data = await response.json();
        console.log('[AEGIS] 📊 Response:', data);
        
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
        console.error('[AEGIS] ❌ Error:', error);
        showAlert('Scan failed: ' + error.message, 'danger');
        statusMessage.innerHTML = '<i class="bi bi-exclamation-triangle-fill"></i> ' + error.message;
        progressBar.classList.add('bg-danger');
    } finally {
        startScanBtn.disabled = false;
        startScanBtn.innerHTML = '<i class="bi bi-search"></i> Scan';
    }
}

// ============================================================================
// DISPLAY FUNCTIONS
// ============================================================================

/**
 * Display scan results
 */
function displayResults(results) {
    if (!results || !results.phases) {
        console.warn('[AEGIS] No results to display');
        return;
    }
    
    const phases = results.phases;
    
    // Update stats with animation
    animateNumber('statSubdomains', phases.subdomains?.length || 0);
    animateNumber('statHosts', phases.hosts?.length || 0);
    animateNumber('statEmails', phases.osint?.emails?.length || 0);
    
    // Calculate threats
    let threatCount = 0;
    (phases.hosts || []).forEach(host => {
        (host.ports || []).forEach(port => {
            if ([21, 22, 23, 3389, 5900].includes(port)) threatCount++;
        });
    });
    animateNumber('statVulns', threatCount);
    
    // Display security score
    const score = results.security_score || 100;
    displaySecurityScore(score);
    
    // Display hosts
    displayHosts(phases.hosts || []);
    
    // Display technologies
    displayTechnologies(phases.technologies || []);
    
    // Display OSINT
    displayOSINT(phases.osint || {});
    
    // Enable export button
    const exportBtn = document.getElementById('exportJsonBtn');
    if (exportBtn) {
        exportBtn.disabled = false;
        exportBtn.onclick = () => exportJSON(results);
    }
}

/**
 * Animate number counting
 */
function animateNumber(elementId, target) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const duration = 800;
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = target;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current);
        }
    }, 16);
}

/**
 * Display security score with animated progress
 */
function displaySecurityScore(score) {
    const section = document.getElementById('securityScoreSection');
    const scoreValue = document.getElementById('securityScoreValue');
    const progressBar = document.getElementById('scoreProgressBar');
    
    if (!section || !scoreValue || !progressBar) return;
    
    section.style.display = 'block';
    
    // Animate score
    let current = 0;
    const timer = setInterval(() => {
        current += 2;
        if (current >= score) {
            scoreValue.textContent = score + '/100';
            progressBar.style.width = score + '%';
            clearInterval(timer);
        } else {
            scoreValue.textContent = current + '/100';
            progressBar.style.width = current + '%';
        }
    }, 20);
    
    // Update color based on score
    if (score >= 80) {
        progressBar.style.background = 'linear-gradient(90deg, #10b981, #34d399)';
    } else if (score >= 60) {
        progressBar.style.background = 'linear-gradient(90deg, #f59e0b, #fbbf24)';
    } else if (score >= 40) {
        progressBar.style.background = 'linear-gradient(90deg, #f97316, #fb923c)';
    } else {
        progressBar.style.background = 'linear-gradient(90deg, #ef4444, #f87171)';
    }
}

/**
 * Export results as JSON
 */
function exportJSON(results) {
    const dataStr = JSON.stringify(results, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `aegis-recon-${results.target}-${Date.now()}.json`;
    a.click();
    
    URL.revokeObjectURL(url);
    showAlert('Results exported successfully!', 'success');
}

/**
 * Display hosts list
 */
function displayHosts(hosts) {
    const container = document.getElementById('hostsContent');
    
    if (!hosts || hosts.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-server"></i>
                <h5 style="color: #94a3b8;">No Active Hosts</h5>
                <p class="mb-0">No responsive hosts were detected</p>
            </div>
        `;
        return;
    }
    
    // Port service names
    const portServices = {
        21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS',
        80: 'HTTP', 443: 'HTTPS', 3306: 'MySQL', 3389: 'RDP',
        5432: 'PostgreSQL', 5900: 'VNC', 8080: 'HTTP-ALT', 8443: 'HTTPS-ALT'
    };
    
    let html = '<div class="host-list">';
    
    hosts.forEach((host, index) => {
        const portBadges = (host.ports || []).map(port => {
            const isRisky = [21, 22, 23, 3389, 5900].includes(port);
            const service = portServices[port] || 'PORT';
            const badgeClass = isRisky ? 'bg-warning' : 'bg-primary';
            const icon = isRisky ? '<i class="bi bi-exclamation-triangle-fill me-1"></i>' : '';
            return `<span class="badge ${badgeClass} me-1">${icon}${port} <small style="opacity: 0.7">${service}</small></span>`;
        }).join('');
        
        // Geo info
        let geoHtml = '';
        if (host.geo && (host.geo.city || host.geo.country)) {
            const location = [host.geo.city, host.geo.country].filter(Boolean).join(', ');
            geoHtml = `<span class="geo-badge"><i class="bi bi-geo-alt-fill"></i> ${location}</span>`;
        }
        
        // Org info
        let orgHtml = '';
        if (host.geo && host.geo.org) {
            orgHtml = `<div class="text-muted small mt-1" style="font-size: 0.7rem;"><i class="bi bi-building"></i> ${host.geo.org}</div>`;
        }
        
        html += `
            <div class="host-item fade-in" style="animation-delay: ${index * 0.1}s">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>${host.hostname}</strong>
                        <div class="d-flex align-items-center gap-2 mt-1">
                            <code style="font-size: 0.8rem; color: #94a3b8; background: rgba(0,0,0,0.2); padding: 0.1rem 0.4rem; border-radius: 4px;">${host.ip}</code>
                            ${geoHtml}
                        </div>
                        ${orgHtml}
                    </div>
                    <span class="badge ${host.status === 'up' ? 'bg-success' : 'bg-secondary'}">
                        <i class="bi ${host.status === 'up' ? 'bi-check-circle' : 'bi-x-circle'}"></i> ${host.status}
                    </span>
                </div>
                <div class="mt-2">
                    ${portBadges || '<span class="text-muted small"><i class="bi bi-shield-check"></i> No open ports detected</span>'}
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

// Cached report storage
let cachedReport = null;

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
    
    // Check if we have a cached report for this target in this session
    if (cachedReport && cachedReport.target === currentResults.target) {
        console.log('[AEGIS] Using session report cache');
        displayReport(cachedReport.analysis);
        return;
    }
    
    // Reset modal content - loading state
    document.getElementById('reportModalBody').innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border" style="color: #6366f1;" role="status"></div>
            <p class="mt-3" style="color: #94a3b8;">Generating AI threat analysis...</p>
            <small class="text-muted">This may take a few seconds</small>
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
        
        // Cache the report for this session only (no localStorage)
        cachedReport = {
            target: currentResults.target,
            analysis: data.analysis,
            scanResults: currentResults,
            cachedAt: new Date().toISOString()
        };
        
        // Display the report
        displayReport(data.analysis);
        
    } catch (error) {
        console.error('[AEGIS] Report Error:', error);
        document.getElementById('reportModalBody').innerHTML = `
            <div style="padding: 2rem; text-align: center;">
                <i class="bi bi-exclamation-triangle" style="font-size: 3rem; color: #f43f5e;"></i>
                <h5 class="mt-3" style="color: #f8fafc;">Report Generation Failed</h5>
                <p style="color: #94a3b8;">${error.message}</p>
                <button class="btn btn-outline-primary" onclick="generateReport()">
                    <i class="bi bi-arrow-repeat"></i> Retry
                </button>
            </div>
        `;
    }
}

/**
 * Display the generated report with rich formatting
 */
function displayReport(analysis) {
    const container = document.getElementById('reportModalBody');
    const target = cachedReport?.target || currentResults?.target || 'Unknown';
    const score = cachedReport?.scanResults?.security_score || currentResults?.security_score || 100;
    
    // Determine risk level
    let riskLevel, riskColor, riskBg;
    if (score >= 80) {
        riskLevel = 'LOW'; riskColor = '#10b981'; riskBg = 'rgba(16, 185, 129, 0.15)';
    } else if (score >= 60) {
        riskLevel = 'MEDIUM'; riskColor = '#f59e0b'; riskBg = 'rgba(245, 158, 11, 0.15)';
    } else if (score >= 40) {
        riskLevel = 'HIGH'; riskColor = '#f97316'; riskBg = 'rgba(249, 115, 22, 0.15)';
    } else {
        riskLevel = 'CRITICAL'; riskColor = '#ef4444'; riskBg = 'rgba(239, 68, 68, 0.15)';
    }
    
    // Convert markdown to styled HTML
    let reportContent = analysis.report
        .replace(/^### (.*$)/gim, '<h5 style="color: #f8fafc; margin-top: 1.5rem; margin-bottom: 0.75rem; font-weight: 600;">$1</h5>')
        .replace(/^## (.*$)/gim, '<h4 style="color: #f8fafc; margin-top: 1.5rem; margin-bottom: 0.75rem; font-weight: 700; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.5rem;">$1</h4>')
        .replace(/\*\*(.*?)\*\*/g, '<strong style="color: #f8fafc;">$1</strong>')
        .replace(/^- (.*$)/gim, '<li style="color: #cbd5e1; margin-bottom: 0.5rem;">$1</li>')
        .replace(/`(.*?)`/g, '<code style="background: rgba(99, 102, 241, 0.2); color: #a5b4fc; padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.85rem;">$1</code>')
        .replace(/\n\n/g, '</p><p style="color: #94a3b8; line-height: 1.7;">')
        .replace(/\n/g, '<br>');
    
    // Wrap lists properly
    reportContent = reportContent.replace(/(<li.*?<\/li>)+/g, '<ul style="list-style: none; padding-left: 0; margin: 1rem 0;">$&</ul>');
    reportContent = reportContent.replace(/<li/g, '<li style="position: relative; padding-left: 1.5rem;"><span style="position: absolute; left: 0; color: #6366f1;">▸</span');
    
    container.innerHTML = `
        <div id="reportPrintArea" style="background: linear-gradient(135deg, #0f172a, #1e293b); padding: 0;">
            
            <!-- Report Header -->
            <div style="background: linear-gradient(135deg, #6366f1, #4f46e5); padding: 2rem; text-align: center; border-radius: 12px 12px 0 0;">
                <div style="display: flex; align-items: center; justify-content: center; gap: 0.75rem; margin-bottom: 0.5rem;">
                    <i class="bi bi-shield-fill-check" style="font-size: 2rem; color: white;"></i>
                    <h2 style="margin: 0; color: white; font-weight: 800; letter-spacing: -0.02em;">AEGIS RECON</h2>
                </div>
                <p style="margin: 0; color: rgba(255,255,255,0.8); font-size: 0.85rem; letter-spacing: 2px;">THREAT INTELLIGENCE REPORT</p>
            </div>
            
            <!-- Target Info Bar -->
            <div style="background: rgba(0,0,0,0.3); padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <small style="color: #64748b; text-transform: uppercase; letter-spacing: 1px; font-size: 0.7rem;">Target</small>
                    <div style="color: #f8fafc; font-weight: 600; font-size: 1.1rem;">${target}</div>
                </div>
                <div style="text-align: center;">
                    <small style="color: #64748b; text-transform: uppercase; letter-spacing: 1px; font-size: 0.7rem;">Security Score</small>
                    <div style="color: ${riskColor}; font-weight: 800; font-size: 1.5rem;">${score}/100</div>
                </div>
                <div style="text-align: right;">
                    <small style="color: #64748b; text-transform: uppercase; letter-spacing: 1px; font-size: 0.7rem;">Risk Level</small>
                    <div style="background: ${riskBg}; color: ${riskColor}; padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: 700; font-size: 0.85rem; display: inline-block;">${riskLevel}</div>
                </div>
            </div>
            
            <!-- Report Content -->
            <div style="padding: 2rem;">
                <p style="color: #94a3b8; line-height: 1.7;">
                    ${reportContent}
                </p>
            </div>
            
            <!-- Report Footer -->
            <div style="border-top: 1px solid rgba(255,255,255,0.1); padding: 1.5rem 2rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <div style="display: flex; align-items: center; gap: 0.5rem; color: #64748b; font-size: 0.8rem;">
                        <i class="bi bi-robot"></i>
                        <span>Generated by ${analysis.model || 'AI Analysis'}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem; color: #64748b; font-size: 0.8rem; margin-top: 0.25rem;">
                        <i class="bi bi-clock"></i>
                        <span>${new Date(analysis.generated_at).toLocaleString()}</span>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="color: #64748b; font-size: 0.75rem;">
                        <i class="bi bi-github"></i> github.com/Vexx-bit/Aegis-Recon
                    </div>
                    <div style="color: #475569; font-size: 0.7rem; margin-top: 0.25rem;">
                        © ${new Date().getFullYear()} VexSpitta. All Rights Reserved.
                    </div>
                </div>
            </div>
            
        </div>
    `;
}

/**
 * Download report as professionally styled PDF
 */
function downloadReportPDF() {
    if (!cachedReport && !currentResults) {
        showAlert('No report to download', 'warning');
        return;
    }
    
    const target = cachedReport?.target || currentResults?.target || 'scan';
    const score = cachedReport?.scanResults?.security_score || currentResults?.security_score || 100;
    const timestamp = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    const reportContent = cachedReport?.analysis?.report || 'No report content available.';
    
    // Determine risk level
    let riskLevel, riskColor;
    if (score >= 80) { riskLevel = 'LOW RISK'; riskColor = '#10b981'; }
    else if (score >= 60) { riskLevel = 'MEDIUM RISK'; riskColor = '#f59e0b'; }
    else if (score >= 40) { riskLevel = 'HIGH RISK'; riskColor = '#f97316'; }
    else { riskLevel = 'CRITICAL RISK'; riskColor = '#ef4444'; }
    
    // Create a simple, reliable PDF container
    const pdfContainer = document.createElement('div');
    pdfContainer.id = 'pdf-export-container';
    pdfContainer.style.cssText = 'position: absolute; left: -9999px; top: 0; width: 800px; background: white;';
    
    // Simple markdown to HTML conversion
    const formattedContent = reportContent
        .replace(/^## (.*$)/gim, '<h2 style="font-size: 16px; font-weight: 700; color: #1e293b; border-bottom: 2px solid #3b82f6; padding-bottom: 8px; margin: 25px 0 15px 0;">$1</h2>')
        .replace(/^### (.*$)/gim, '<h3 style="font-size: 14px; font-weight: 600; color: #334155; margin: 20px 0 10px 0;">$1</h3>')
        .replace(/\*\*(.*?)\*\*/g, '<strong style="font-weight: 600;">$1</strong>')
        .replace(/^- (.*$)/gim, '<div style="margin: 8px 0; padding-left: 20px; position: relative;"><span style="position: absolute; left: 0; color: #3b82f6; font-weight: bold;">▸</span>$1</div>')
        .replace(/`(.*?)`/g, '<code style="background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 12px; color: #1e293b;">$1</code>')
        .replace(/🟢/g, '<span style="color:#10b981">●</span>')
        .replace(/🟡/g, '<span style="color:#f59e0b">●</span>')
        .replace(/🟠/g, '<span style="color:#f97316">●</span>')
        .replace(/🔴/g, '<span style="color:#ef4444">●</span>')
        .replace(/⚠️/g, '<span style="color:#f59e0b">⚠</span>')
        .replace(/\n\n/g, '<br><br>')
        .replace(/\n/g, '<br>');
    
    pdfContainer.innerHTML = `
        <div style="font-family: Arial, Helvetica, sans-serif; padding: 40px; font-size: 13px; line-height: 1.6; color: #1e293b;">
            
            <!-- Header -->
            <div style="border-bottom: 3px solid #3b82f6; padding-bottom: 20px; margin-bottom: 30px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-end;">
                    <div>
                        <div style="font-size: 28px; font-weight: 800; color: #0f172a; letter-spacing: -1px;">AEGIS RECON</div>
                        <div style="font-size: 12px; color: #64748b; margin-top: 4px; text-transform: uppercase; letter-spacing: 2px;">Threat Intelligence Report</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 11px; color: #64748b;">CONFIDENTIAL</div>
                        <div style="font-size: 13px; font-weight: 600; color: #0f172a;">${timestamp}</div>
                    </div>
                </div>
            </div>
            
            <!-- Summary Box -->
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="width: 40%; padding-right: 20px; border-right: 1px solid #cbd5e1;">
                            <div style="font-size: 10px; color: #64748b; text-transform: uppercase; font-weight: 600; margin-bottom: 5px;">Target Domain</div>
                            <div style="font-size: 16px; font-weight: 700; color: #0f172a;">${target}</div>
                        </td>
                        <td style="width: 30%; padding: 0 20px; text-align: center; border-right: 1px solid #cbd5e1;">
                            <div style="font-size: 10px; color: #64748b; text-transform: uppercase; font-weight: 600; margin-bottom: 5px;">Security Score</div>
                            <div style="font-size: 32px; font-weight: 800; color: ${riskColor};">${score}</div>
                        </td>
                        <td style="width: 30%; padding-left: 20px; text-align: right;">
                            <div style="font-size: 10px; color: #64748b; text-transform: uppercase; font-weight: 600; margin-bottom: 5px;">Risk Level</div>
                            <div style="display: inline-block; background: ${riskColor}; color: white; padding: 6px 16px; border-radius: 20px; font-size: 12px; font-weight: 700;">${riskLevel}</div>
                        </td>
                    </tr>
                </table>
            </div>
            
            <!-- Report Content -->
            <div style="margin-bottom: 40px;">
                ${formattedContent}
            </div>
            
            <!-- Footer -->
            <div style="border-top: 1px solid #e2e8f0; padding-top: 20px; margin-top: 40px; font-size: 10px; color: #94a3b8; display: flex; justify-content: space-between;">
                <div>Generated by Aegis Recon AI • v${AUTHOR.version}</div>
                <div>© ${new Date().getFullYear()} ${AUTHOR.name}. All Rights Reserved.</div>
            </div>
        </div>
    `;
    
    document.body.appendChild(pdfContainer);
    
    // PDF generation options
    const options = {
        margin: 10,
        filename: `Aegis-Recon-${target.replace(/[^a-zA-Z0-9]/g, '-')}-Report.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { 
            scale: 2,
            useCORS: true, 
            logging: false,
            backgroundColor: '#ffffff'
        },
        jsPDF: { 
            unit: 'mm', 
            format: 'a4', 
            orientation: 'portrait' 
        }
    };
    
    // Generate PDF from the container content
    html2pdf()
        .set(options)
        .from(pdfContainer.firstChild)
        .save()
        .then(() => {
            pdfContainer.remove();
            showAlert('✓ Report Downloaded', 'success');
        })
        .catch(err => {
            pdfContainer.remove();
            console.error('[AEGIS] PDF Error:', err);
            showAlert('PDF generation failed', 'danger');
        });
}
// ============================================================================
// UTILITIES
// ============================================================================

/**
 * Reset dashboard for new scan
 */
function resetDashboard() {
    domainInput.value = '';
    
    document.getElementById('statSubdomains').textContent = '0';
    document.getElementById('statHosts').textContent = '0';
    document.getElementById('statVulns').textContent = '0';
    document.getElementById('statEmails').textContent = '0';
    
    document.getElementById('hostsContent').innerHTML = `
        <div class="text-center py-5 text-muted">
            <i class="bi bi-search fs-1"></i>
            <p class="mt-3 mb-0">Enter a domain above to start scanning</p>
        </div>
    `;
    document.getElementById('technologyContent').innerHTML = '<p class="text-muted small mb-0">No data yet</p>';
    document.getElementById('emailsList').innerHTML = '<p class="text-muted small mb-0">No data yet</p>';
    
    newScanBtn.style.display = 'none';
    statusSection.classList.add('hidden');
    
    const reportBtn = document.getElementById('generateReportBtn');
    if (reportBtn) reportBtn.disabled = true;
    
    currentResults = null;
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
    
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

// ============================================================================
// SIGNATURE - DO NOT REMOVE
// ============================================================================
console.log(`%c
    ╔══════════════════════════════════════╗
    ║  🛡️ AEGIS RECON - Loaded Successfully ║
    ║  👤 Author: ${AUTHOR.name.padEnd(24)}║
    ║  📦 Version: ${AUTHOR.version.padEnd(23)}║
    ╚══════════════════════════════════════╝
`, 'color: #10b981; font-family: monospace;');
