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
    
    // Add CVE count to threats
    const cveCount = (results.known_cves || []).length;
    threatCount += cveCount;
    
    animateNumber('statVulns', threatCount);
    
    // Display security score
    const score = results.security_score || 70;
    displaySecurityScore(score, results);
    
    // Display hosts
    displayHosts(phases.hosts || []);
    
    // Display technologies
    displayTechnologies(phases.technologies || []);
    
    // Display OSINT
    displayOSINT(phases.osint || {});
    
    // Display new security check results
    displaySecurityHeaders(results.security_headers);
    displaySSLInfo(results.ssl_info);
    displayAdminPanels(results.admin_panels);
    displayKnownCVEs(results.known_cves);
    displayRobotsTxt(results.robots_txt);
    displayDirectoryListing(results.directory_listing);
    
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
function displaySecurityScore(score, results = {}) {
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
    let scoreLabel = '';
    if (score >= 80) {
        progressBar.style.background = 'linear-gradient(90deg, #10b981, #34d399)';
        scoreLabel = 'Low Exposure';
    } else if (score >= 60) {
        progressBar.style.background = 'linear-gradient(90deg, #f59e0b, #fbbf24)';
        scoreLabel = 'Moderate Exposure';
    } else if (score >= 40) {
        progressBar.style.background = 'linear-gradient(90deg, #f97316, #fb923c)';
        scoreLabel = 'High Exposure';
    } else {
        progressBar.style.background = 'linear-gradient(90deg, #ef4444, #f87171)';
        scoreLabel = 'Critical Exposure';
    }
    
    // Add disclaimer below score
    const disclaimer = results.score_disclaimer || 
        'This score reflects visible exposure from passive reconnaissance only.';
    
    // Check if disclaimer element exists, if not create it
    let disclaimerEl = section.querySelector('.score-disclaimer');
    if (!disclaimerEl) {
        disclaimerEl = document.createElement('div');
        disclaimerEl.className = 'score-disclaimer';
        disclaimerEl.style.cssText = `
            font-size: 11px;
            color: #94a3b8;
            margin-top: 10px;
            padding: 8px 12px;
            background: rgba(148, 163, 184, 0.1);
            border-radius: 6px;
            border-left: 3px solid #64748b;
        `;
        section.appendChild(disclaimerEl);
    }
    disclaimerEl.innerHTML = `
        <strong style="color: #64748b;">⚠️ ${scoreLabel}</strong><br>
        <span style="font-size: 10px;">${disclaimer}</span>
    `;
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

/**
 * Display Security Headers Analysis
 */
function displaySecurityHeaders(headersData) {
    const container = document.getElementById('securityHeadersContent');
    if (!container) return;
    
    if (!headersData || headersData.error) {
        container.innerHTML = '<p class="text-muted small">Unable to check security headers</p>';
        return;
    }
    
    const gradeColors = {
        'A': '#10b981', 'B': '#22c55e', 'C': '#f59e0b', 'D': '#f97316', 'F': '#ef4444'
    };
    
    let html = `
        <div class="d-flex align-items-center mb-3">
            <div class="me-3" style="
                width: 50px; height: 50px; 
                border-radius: 50%; 
                background: ${gradeColors[headersData.grade] || '#6b7280'};
                display: flex; align-items: center; justify-content: center;
            ">
                <span style="color: white; font-weight: bold; font-size: 1.5rem;">${headersData.grade}</span>
            </div>
            <div>
                <strong style="color: #e2e8f0;">Security Headers Grade</strong><br>
                <small class="text-muted">${headersData.score_percentage || 0}% of recommended headers present</small>
            </div>
        </div>
    `;
    
    if (headersData.headers_missing && headersData.headers_missing.length > 0) {
        html += '<div class="mb-2"><small class="text-danger"><i class="bi bi-exclamation-triangle"></i> Missing Headers:</small></div>';
        html += '<div class="d-flex flex-wrap gap-1 mb-2">';
        headersData.headers_missing.forEach(h => {
            html += `<span class="badge bg-danger bg-opacity-25 text-danger" title="${h.description}">${h.name}</span>`;
        });
        html += '</div>';
    }
    
    if (headersData.headers_found && headersData.headers_found.length > 0) {
        html += '<div class="mb-2"><small class="text-success"><i class="bi bi-check-circle"></i> Found Headers:</small></div>';
        html += '<div class="d-flex flex-wrap gap-1">';
        headersData.headers_found.forEach(h => {
            html += `<span class="badge bg-success bg-opacity-25 text-success">${h.name}</span>`;
        });
        html += '</div>';
    }
    
    container.innerHTML = html;
}

/**
 * Display SSL/TLS Certificate Info
 */
function displaySSLInfo(sslData) {
    const container = document.getElementById('sslInfoContent');
    if (!container) return;
    
    if (!sslData || !sslData.valid) {
        container.innerHTML = `
            <div class="alert alert-warning py-2 mb-0">
                <i class="bi bi-exclamation-triangle"></i>
                <small>SSL certificate could not be verified</small>
            </div>
        `;
        return;
    }
    
    const isExpiringSoon = sslData.days_until_expiry < 30;
    const statusColor = sslData.is_expired ? 'danger' : (isExpiringSoon ? 'warning' : 'success');
    
    let html = `
        <div class="d-flex align-items-center mb-2">
            <i class="bi bi-shield-lock-fill text-${statusColor} me-2" style="font-size: 1.5rem;"></i>
            <div>
                <strong class="text-${statusColor}">
                    ${sslData.is_expired ? 'Certificate Expired!' : (isExpiringSoon ? 'Expiring Soon' : 'Valid Certificate')}
                </strong>
            </div>
        </div>
        <table class="table table-sm table-borderless mb-0" style="font-size: 0.8rem;">
            <tr><td class="text-muted">Issuer:</td><td class="text-light">${sslData.issuer}</td></tr>
            <tr><td class="text-muted">TLS Version:</td><td class="text-light">${sslData.tls_version || 'Unknown'}</td></tr>
            <tr><td class="text-muted">Expires:</td><td class="text-${statusColor}">
                ${sslData.days_until_expiry !== undefined ? sslData.days_until_expiry + ' days' : 'Unknown'}
            </td></tr>
        </table>
    `;
    
    container.innerHTML = html;
}

/**
 * Display Admin Panels Detection
 */
function displayAdminPanels(panelsData) {
    const container = document.getElementById('adminPanelsContent');
    if (!container) return;
    
    if (!panelsData || !panelsData.found || panelsData.found.length === 0) {
        container.innerHTML = `
            <div class="text-success small">
                <i class="bi bi-check-circle"></i> No exposed admin panels detected
            </div>
        `;
        return;
    }
    
    let html = '<ul class="list-unstyled mb-0">';
    panelsData.found.forEach(panel => {
        const statusBadge = panel.accessible 
            ? '<span class="badge bg-danger">Accessible</span>'
            : '<span class="badge bg-warning text-dark">Protected</span>';
        html += `
            <li class="d-flex align-items-center justify-content-between py-1 border-bottom border-secondary">
                <code class="text-info">${panel.path}</code>
                ${statusBadge}
            </li>
        `;
    });
    html += '</ul>';
    
    container.innerHTML = html;
}

/**
 * Display Known CVEs
 */
function displayKnownCVEs(cvesData) {
    const container = document.getElementById('knownCVEsContent');
    if (!container) return;
    
    if (!cvesData || cvesData.length === 0) {
        container.innerHTML = `
            <div class="text-success small">
                <i class="bi bi-check-circle"></i> No known CVEs detected in detected technologies
            </div>
        `;
        return;
    }
    
    const severityColors = {
        'Critical': 'danger',
        'High': 'warning',
        'Medium': 'info',
        'Low': 'secondary'
    };
    
    let html = '';
    cvesData.forEach(cve => {
        const color = severityColors[cve.severity] || 'secondary';
        html += `
            <div class="border border-${color} rounded p-2 mb-2" style="background: rgba(255,255,255,0.02);">
                <div class="d-flex align-items-center mb-1">
                    <span class="badge bg-${color} me-2">${cve.severity}</span>
                    <code class="text-light">${cve.cve}</code>
                </div>
                <small class="text-muted">${cve.technology}</small><br>
                <small class="text-light">${cve.description}</small>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

/**
 * Display Robots.txt Analysis
 */
function displayRobotsTxt(robotsData) {
    const container = document.getElementById('robotsTxtContent');
    if (!container) return;
    
    if (!robotsData || !robotsData.found) {
        container.innerHTML = '<p class="text-muted small">No robots.txt found</p>';
        return;
    }
    
    let html = '';
    
    if (robotsData.sensitive_paths && robotsData.sensitive_paths.length > 0) {
        html += '<div class="mb-2"><small class="text-warning"><i class="bi bi-exclamation-triangle"></i> Sensitive Paths Found:</small></div>';
        html += '<ul class="list-unstyled mb-2">';
        robotsData.sensitive_paths.forEach(p => {
            html += `<li><code class="text-warning">${p.path}</code> <small class="text-muted">(${p.keyword})</small></li>`;
        });
        html += '</ul>';
    }
    
    if (robotsData.all_disallowed && robotsData.all_disallowed.length > 0) {
        html += `<details><summary class="small text-muted cursor-pointer">View ${robotsData.all_disallowed.length} disallowed paths</summary>`;
        html += '<ul class="list-unstyled mt-1">';
        robotsData.all_disallowed.slice(0, 10).forEach(path => {
            html += `<li><code class="text-muted small">${path}</code></li>`;
        });
        html += '</ul></details>';
    }
    
    if (!html) {
        html = '<p class="text-muted small">robots.txt found but no sensitive paths detected</p>';
    }
    
    container.innerHTML = html;
}

/**
 * Display Directory Listing Check
 */
function displayDirectoryListing(dirData) {
    const container = document.getElementById('directoryListingContent');
    if (!container) return;
    
    if (!dirData || !dirData.vulnerable) {
        container.innerHTML = `
            <div class="text-success small">
                <i class="bi bi-check-circle"></i> No directory listing vulnerabilities detected
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="alert alert-danger py-2 mb-2">
            <i class="bi bi-exclamation-triangle-fill"></i>
            <strong>Directory Listing Enabled!</strong>
        </div>
        <small class="text-muted">Exposed directories:</small>
        <ul class="list-unstyled mb-0">
    `;
    
    dirData.exposed_dirs.forEach(dir => {
        html += `<li><code class="text-danger">${dir}</code></li>`;
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
 * Download report as PDF using jsPDF directly
 * Premium professional design with enhanced visual elements
 */
function downloadReportPDF() {
    if (!cachedReport || !cachedReport.analysis) {
        showAlert('Please generate a report first', 'warning');
        return;
    }
    
    const target = cachedReport.target || currentResults?.target || 'Unknown';
    const score = cachedReport.scanResults?.security_score || currentResults?.security_score || 100;
    const timestamp = new Date().toLocaleDateString('en-US', { 
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' 
    });
    const timeGenerated = new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', minute: '2-digit' 
    });
    
    // Get report content
    const reportContent = typeof cachedReport.analysis === 'string' 
        ? cachedReport.analysis 
        : cachedReport.analysis?.report || '';
    
    // Determine risk level with colors
    let riskLevel, riskColor, riskBg;
    if (score >= 80) { 
        riskLevel = 'LOW RISK'; 
        riskColor = [16, 185, 129]; 
        riskBg = [220, 252, 231];
    } else if (score >= 60) { 
        riskLevel = 'MEDIUM RISK'; 
        riskColor = [245, 158, 11]; 
        riskBg = [254, 243, 199];
    } else if (score >= 40) { 
        riskLevel = 'HIGH RISK'; 
        riskColor = [249, 115, 22]; 
        riskBg = [255, 237, 213];
    } else { 
        riskLevel = 'CRITICAL'; 
        riskColor = [239, 68, 68]; 
        riskBg = [254, 226, 226];
    }
    
    // Initialize jsPDF
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
    
    const pageWidth = 210;
    const pageHeight = 297;
    const margin = 15;
    const contentWidth = pageWidth - (margin * 2);
    let y = 0;
    
    // ========== HEADER BANNER ==========
    // Dark header background
    doc.setFillColor(15, 23, 42);
    doc.rect(0, 0, pageWidth, 45, 'F');
    
    // Blue accent strip at top
    doc.setFillColor(59, 130, 246);
    doc.rect(0, 0, pageWidth, 3, 'F');
    
    // Shield icon (drawn with shapes)
    doc.setFillColor(59, 130, 246);
    doc.roundedRect(margin, 12, 22, 25, 3, 3, 'F');
    doc.setFillColor(30, 64, 175);
    doc.roundedRect(margin + 2, 14, 18, 21, 2, 2, 'F');
    doc.setFillColor(255, 255, 255);
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.text('AR', margin + 11, 27, { align: 'center' });
    
    // Title
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(22);
    doc.setFont('helvetica', 'bold');
    doc.text('AEGIS RECON', margin + 28, 22);
    
    doc.setFontSize(10);
    doc.setTextColor(148, 163, 184);
    doc.setFont('helvetica', 'normal');
    doc.text('THREAT INTELLIGENCE REPORT', margin + 28, 30);
    
    // Right side - Date & Classification
    doc.setFontSize(8);
    doc.setTextColor(239, 68, 68);
    doc.setFont('helvetica', 'bold');
    doc.text('CONFIDENTIAL', pageWidth - margin, 15, { align: 'right' });
    
    doc.setTextColor(148, 163, 184);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(9);
    doc.text(timestamp, pageWidth - margin, 23, { align: 'right' });
    doc.text(timeGenerated, pageWidth - margin, 30, { align: 'right' });
    
    y = 55;
    
    // ========== SUMMARY CARD ==========
    // Card background with shadow effect
    doc.setFillColor(241, 245, 249);
    doc.roundedRect(margin - 1, y - 1, contentWidth + 2, 37, 4, 4, 'F');
    doc.setFillColor(255, 255, 255);
    doc.setDrawColor(226, 232, 240);
    doc.roundedRect(margin, y, contentWidth, 35, 3, 3, 'FD');
    
    // Column widths
    const col1 = margin + 5;
    const col2 = margin + 70;
    const col3 = margin + 115;
    
    // Vertical dividers
    doc.setDrawColor(226, 232, 240);
    doc.setLineWidth(0.3);
    doc.line(margin + 65, y + 5, margin + 65, y + 30);
    doc.line(margin + 110, y + 5, margin + 110, y + 30);
    
    // Target Domain
    doc.setFontSize(7);
    doc.setTextColor(100, 116, 139);
    doc.setFont('helvetica', 'bold');
    doc.text('TARGET DOMAIN', col1, y + 10);
    doc.setFontSize(11);
    doc.setTextColor(15, 23, 42);
    doc.setFont('helvetica', 'bold');
    // Truncate long domains
    const displayTarget = target.length > 25 ? target.substring(0, 22) + '...' : target;
    doc.text(displayTarget, col1, y + 20);
    
    // Security Score with circular indicator
    doc.setFontSize(7);
    doc.setTextColor(100, 116, 139);
    doc.text('SECURITY SCORE', col2, y + 10);
    
    // Score circle background
    doc.setFillColor(riskBg[0], riskBg[1], riskBg[2]);
    doc.circle(col2 + 15, y + 22, 10, 'F');
    doc.setFontSize(16);
    doc.setTextColor(riskColor[0], riskColor[1], riskColor[2]);
    doc.setFont('helvetica', 'bold');
    doc.text(String(score), col2 + 15, y + 26, { align: 'center' });
    
    // Risk Level
    doc.setFontSize(7);
    doc.setTextColor(100, 116, 139);
    doc.text('RISK ASSESSMENT', col3, y + 10);
    
    // Risk badge
    doc.setFillColor(riskColor[0], riskColor[1], riskColor[2]);
    doc.roundedRect(col3, y + 15, 50, 12, 6, 6, 'F');
    doc.setFontSize(9);
    doc.setTextColor(255, 255, 255);
    doc.setFont('helvetica', 'bold');
    doc.text(riskLevel, col3 + 25, y + 23, { align: 'center' });
    
    y += 45;
    
    // ========== REPORT CONTENT ==========
    const lines = reportContent.split('\n');
    
    // Helper function for page breaks
    function checkPageBreak(needed) {
        if (y + needed > pageHeight - 25) {
            doc.addPage();
            y = 20;
            return true;
        }
        return false;
    }
    
    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();
        if (!line) { y += 2; continue; }
        
        // Skip metadata
        if (line.startsWith('*Report generated') || line.startsWith('---')) continue;
        
        // H2 Headers - Section titles
        if (line.startsWith('## ')) {
            checkPageBreak(18);
            y += 8;
            
            // Blue left border
            doc.setFillColor(59, 130, 246);
            doc.rect(margin, y - 4, 3, 10, 'F');
            
            doc.setFontSize(13);
            doc.setFont('helvetica', 'bold');
            doc.setTextColor(15, 23, 42);
            doc.text(line.replace('## ', ''), margin + 6, y + 2);
            
            y += 10;
            continue;
        }
        
        // H3 Headers
        if (line.startsWith('### ')) {
            checkPageBreak(12);
            y += 4;
            doc.setFontSize(11);
            doc.setFont('helvetica', 'bold');
            doc.setTextColor(51, 65, 85);
            doc.text(line.replace('### ', ''), margin, y);
            y += 6;
            continue;
        }
        
        // Bullet points with colored dots
        if (line.startsWith('- ') || line.startsWith('▸')) {
            checkPageBreak(10);
            let bulletText = line.replace(/^[-▸]\s*/, '');
            
            // Check for warning indicators
            let bulletColor = [59, 130, 246]; // Default blue
            if (bulletText.includes('⚠️') || bulletText.includes('!')) {
                bulletColor = [245, 158, 11]; // Warning orange
            }
            if (bulletText.includes('🟢')) bulletColor = [16, 185, 129];
            if (bulletText.includes('🟡')) bulletColor = [245, 158, 11];
            if (bulletText.includes('🟠')) bulletColor = [249, 115, 22];
            if (bulletText.includes('🔴')) bulletColor = [239, 68, 68];
            
            // Clean emojis
            bulletText = bulletText.replace(/[🟢🟡🟠🔴⚠️]/g, '').trim();
            bulletText = bulletText.replace(/\*\*(.*?)\*\*/g, '$1').replace(/`(.*?)`/g, '"$1"');
            
            // Draw bullet
            doc.setFillColor(bulletColor[0], bulletColor[1], bulletColor[2]);
            doc.circle(margin + 4, y - 1, 1.5, 'F');
            
            doc.setFontSize(10);
            doc.setFont('helvetica', 'normal');
            doc.setTextColor(51, 65, 85);
            
            const bulletLines = doc.splitTextToSize(bulletText, contentWidth - 12);
            for (let j = 0; j < bulletLines.length; j++) {
                if (j > 0) checkPageBreak(4.5);
                doc.text(bulletLines[j], margin + 10, y);
                y += 4.5;
            }
            y += 1;
            continue;
        }
        
        // Numbered items - simple corporate style
        if (/^\d+\./.test(line)) {
            checkPageBreak(10);
            let itemText = line.replace(/\*\*(.*?)\*\*/g, '$1');
            
            doc.setFontSize(10);
            doc.setFont('helvetica', 'normal');
            doc.setTextColor(51, 65, 85);
            
            const itemLines = doc.splitTextToSize(itemText, contentWidth - 5);
            for (let j = 0; j < itemLines.length; j++) {
                if (j > 0) checkPageBreak(4.5);
                doc.text(itemLines[j], margin + 5, y);
                y += 4.5;
            }
            y += 1;
            continue;
        }
        
        // Regular text
        line = line.replace(/\*\*(.*?)\*\*/g, '$1').replace(/`(.*?)`/g, '"$1"');
        line = line.replace(/[🟢🟡🟠🔴⚠️]/g, '');
        
        if (line.length > 0) {
            checkPageBreak(6);
            doc.setFontSize(10);
            doc.setFont('helvetica', 'normal');
            doc.setTextColor(71, 85, 105);
            
            const paraLines = doc.splitTextToSize(line, contentWidth);
            for (let j = 0; j < paraLines.length; j++) {
                checkPageBreak(4.5);
                doc.text(paraLines[j], margin, y);
                y += 4.5;
            }
            y += 2;
        }
    }
    
    // ========== FOOTER ON ALL PAGES ==========
    const totalPages = doc.internal.getNumberOfPages();
    for (let p = 1; p <= totalPages; p++) {
        doc.setPage(p);
        
        // Footer line
        doc.setDrawColor(226, 232, 240);
        doc.setLineWidth(0.3);
        doc.line(margin, pageHeight - 18, pageWidth - margin, pageHeight - 18);
        
        // Footer text
        doc.setFontSize(8);
        doc.setTextColor(148, 163, 184);
        doc.setFont('helvetica', 'normal');
        doc.text(`Aegis Recon AI v${AUTHOR.version}`, margin, pageHeight - 12);
        doc.text(`Page ${p} of ${totalPages}`, pageWidth / 2, pageHeight - 12, { align: 'center' });
        doc.text(`© ${new Date().getFullYear()} ${AUTHOR.name}`, pageWidth - margin, pageHeight - 12, { align: 'right' });
        
        // Small branding
        doc.setFontSize(7);
        doc.setTextColor(180, 190, 200);
        doc.text('github.com/Vexx-bit/Aegis-Recon', pageWidth / 2, pageHeight - 8, { align: 'center' });
    }
    
    // Save PDF
    doc.save(`Aegis-Recon-${target.replace(/[^a-zA-Z0-9]/g, '-')}-Report.pdf`);
    showAlert('✓ Report Downloaded', 'success');
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
