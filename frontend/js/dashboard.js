/**
 * ╔═══════════════════════════════════════════════════════════════════════════╗
 * ║                            AEGIS RECON v2.0                                ║
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
// CONSOLE BRANDING
// ============================================================================
(function () {
    const B = `
%c╔═══════════════════════════════════════════════════════════════╗
║     _    _____ ____ ___ ____    ____  _____ ____ ___  _   _   ║
║    / \\  | ____/ ___|_ _/ ___|  |  _ \\| ____/ ___/ _ \\| \\ | |  ║
║   / _ \\ |  _|| |  _ | |\\___ \\  | |_) |  _|| |  | | | |  \\| |  ║
║  / ___ \\| |__| |_| || | ___) | |  _ <| |__| |__| |_| | |\\  |  ║
║ /_/   \\_\\_____\\____|___|____/  |_| \\_\\_____\\____\\___/|_| \\_|  ║
╠═══════════════════════════════════════════════════════════════╣
║  🛡️  Advanced Threat Intelligence System  v2.0                 ║
║  ⚡ Powered by: Rapid Tech Solutions                            ║
║  🔗 https://rapidtech.software                                 ║
╚═══════════════════════════════════════════════════════════════╝`;
    console.log(B, 'color:#00ff88;font-family:monospace;font-weight:bold;');
    console.log('%c🔐 Aegis Recon v2.0.0 | © 2024-2026 Rapid Tech Solutions', 'color:#3b82f6;font-size:14px;font-weight:bold;');
})();

// ============================================================================
// CONFIGURATION
// ============================================================================
const API_BASE_URL = window.AEGIS_CONFIG?.apiBaseUrl || '/api';
const AUTHOR = { name: 'Rapid Tech Solutions', website: 'https://rapidtech.software', github: 'https://github.com/Vexx-bit', repo: 'https://github.com/Vexx-bit/Aegis-Recon', version: '2.0.0' };

// State
let currentResults = null;
let cachedReport = null;

// DOM refs
const scanForm = document.getElementById('scanForm');
const domainInput = document.getElementById('domainInput');
const startScanBtn = document.getElementById('startScanBtn');
const alertContainer = document.getElementById('alertContainer');
const statusSection = document.getElementById('statusSection');
const statusMessage = document.getElementById('statusMessage');
const progressBar = document.getElementById('progressBar');
const targetDisplay = document.getElementById('targetDisplay');
const newScanBtn = document.getElementById('newScanBtn');

// ============================================================================
// PROTECTIONS (non-intrusive)
// ============================================================================
(function () {
    document.addEventListener('contextmenu', e => { e.preventDefault(); });
    document.addEventListener('keydown', e => {
        if ((e.ctrlKey && e.key === 'u') || e.key === 'F12') e.preventDefault();
    });
})();

// ============================================================================
// INIT
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    scanForm.addEventListener('submit', handleScanSubmit);
    newScanBtn.addEventListener('click', resetDashboard);

    const reportBtn = document.getElementById('generateReportBtn');
    if (reportBtn) reportBtn.addEventListener('click', generateReport);

    // Modal close handlers (pure JS, no Bootstrap)
    const modalOverlay = document.getElementById('reportModal');
    const modalCloseBtn = document.getElementById('modalCloseBtn');
    const modalDismissBtn = document.getElementById('modalDismissBtn');
    if (modalCloseBtn) modalCloseBtn.addEventListener('click', () => modalOverlay.classList.remove('active'));
    if (modalDismissBtn) modalDismissBtn.addEventListener('click', () => modalOverlay.classList.remove('active'));
    if (modalOverlay) modalOverlay.addEventListener('click', e => { if (e.target === modalOverlay) modalOverlay.classList.remove('active'); });
});

// ============================================================================
// SCAN HANDLING
// ============================================================================
async function handleScanSubmit(e) {
    e.preventDefault();
    const domain = domainInput.value.trim();
    if (!domain) { showAlert('Please enter a domain', 'warning'); return; }

    // ── Consent gate ──
    const consentCb = document.getElementById('consentCheckbox');
    const consentLabel = document.getElementById('consentLabel');
    if (consentCb && !consentCb.checked) {
        consentLabel.classList.add('consent-check--error');
        showAlert('You must confirm authorization before scanning', 'warning');
        consentCb.addEventListener('change', () => consentLabel.classList.remove('consent-check--error'), { once: true });
        return;
    }

    const cleanDomain = domain.replace(/^https?:\/\//, '').replace(/\/.*$/, '');

    // UI → scanning state
    startScanBtn.disabled = true;
    startScanBtn.innerHTML = '<span class="status-spinner" style="width:14px;height:14px;border-width:2px;display:inline-block;"></span><span>Scanning...</span>';

    statusSection.classList.remove('hidden');
    targetDisplay.textContent = cleanDomain;
    statusMessage.innerHTML = '<i class="bi bi-gear-fill"></i> Scanning in progress...';
    progressBar.style.width = '30%';

    const statusDisplay = document.getElementById('statusDisplay');
    if (statusDisplay) statusDisplay.style.display = 'inline-flex';

    try {
        console.log(`[AEGIS] 🔍 Scanning: ${cleanDomain}`);
        const response = await fetch(`${API_BASE_URL}/scan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ domain: cleanDomain })
        });
        progressBar.style.width = '70%';
        const data = await response.json();
        console.log('[AEGIS] 📊 Response:', data);

        if (!response.ok || !data.success) throw new Error(data.error || 'Scan failed');

        progressBar.style.width = '100%';
        statusMessage.innerHTML = '<i class="bi bi-check-circle-fill"></i> Scan complete!';

        currentResults = data.results;
        displayResults(data.results);

        setTimeout(() => {
            statusSection.classList.add('hidden');
            if (statusDisplay) statusDisplay.style.display = 'none';
        }, 1500);

        newScanBtn.style.display = 'inline-flex';
        const reportBtn = document.getElementById('generateReportBtn');
        if (reportBtn) reportBtn.disabled = false;

    } catch (error) {
        console.error('[AEGIS] ❌', error);
        showAlert('Scan failed: ' + error.message, 'danger');
        statusMessage.innerHTML = '<i class="bi bi-exclamation-triangle-fill"></i> ' + error.message;
        progressBar.style.background = 'var(--c-danger)';
    } finally {
        startScanBtn.disabled = false;
        startScanBtn.innerHTML = '<i class="bi bi-radar"></i><span>Scan</span>';
    }
}

// ============================================================================
// DISPLAY RESULTS
// ============================================================================
function displayResults(results) {
    if (!results || !results.phases) return;
    const phases = results.phases;

    // Stat counters
    animateNumber('statSubdomains', phases.subdomains?.length || 0);
    animateNumber('statHosts', phases.hosts?.length || 0);
    animateNumber('statEmails', phases.osint?.emails?.length || 0);

    // DNS count
    const dnsCount = (results.dns_records || []).length;
    animateNumber('statDns', dnsCount);

    // Threats
    let threatCount = 0;
    (phases.hosts || []).forEach(h => { (h.ports || []).forEach(p => { if ([21, 22, 23, 3389, 5900].includes(p)) threatCount++; }); });
    threatCount += (results.known_cves || []).length;
    animateNumber('statVulns', threatCount);

    // Host count pill
    const hostCountEl = document.getElementById('hostCount');
    if (hostCountEl) hostCountEl.textContent = `${phases.hosts?.length || 0} hosts`;

    // Score
    displaySecurityScore(results.security_score || 70, results);

    // Sections
    displayHosts(phases.hosts || []);
    displayTechnologies(phases.technologies || []);
    displayOSINT(phases.osint || {});
    displaySecurityHeaders(results.security_headers);
    displaySSLInfo(results.ssl_info);
    displayAdminPanels(results.admin_panels);
    displayKnownCVEs(results.known_cves);
    displayRobotsTxt(results.robots_txt);
    displayDirectoryListing(results.directory_listing);

    // New OSINT panels
    displayDnsRecords(results.dns_records);
    displayWhois(results.whois_info);
    displayCookieSecurity(results.cookie_security);
    displayHttpMethods(results.http_methods);
    displayCors(results.cors_check);

    // Export button
    const exportBtn = document.getElementById('exportJsonBtn');
    if (exportBtn) { exportBtn.disabled = false; exportBtn.onclick = () => exportJSON(results); }
}

// ============================================================================
// ANIMATE NUMBER
// ============================================================================
function animateNumber(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    const dur = 800, inc = target / (dur / 16);
    let cur = 0;
    const t = setInterval(() => {
        cur += inc;
        if (cur >= target) { el.textContent = target; clearInterval(t); }
        else el.textContent = Math.floor(cur);
    }, 16);
}

// ============================================================================
// SECURITY SCORE (SVG Ring)
// ============================================================================
function displaySecurityScore(score, results = {}) {
    const section = document.getElementById('securityScoreSection');
    const ring = document.getElementById('scoreRing');
    const val = document.getElementById('securityScoreValue');
    const lbl = document.getElementById('scoreLabel');
    const desc = document.getElementById('scoreDescription');
    const factorsEl = document.getElementById('scoreFactors');

    if (!section) return;
    section.classList.remove('hidden');

    // Ring animation
    const circumference = 2 * Math.PI * 52; // ~326.73
    const offset = circumference - (score / 100) * circumference;

    // Color by score
    let color, label;
    if (score >= 80) { color = '#10b981'; label = 'Low Exposure'; }
    else if (score >= 60) { color = '#f59e0b'; label = 'Moderate Exposure'; }
    else if (score >= 40) { color = '#f97316'; label = 'High Exposure'; }
    else { color = '#ef4444'; label = 'Critical Exposure'; }

    // Animate
    let cur = 0;
    const timer = setInterval(() => {
        cur += 2;
        if (cur >= score) {
            cur = score;
            clearInterval(timer);
        }
        if (val) val.textContent = cur;
        if (ring) {
            const o = circumference - (cur / 100) * circumference;
            ring.style.strokeDashoffset = o;
            ring.style.stroke = color;
        }
    }, 18);

    if (val) val.style.color = color;
    if (lbl) lbl.textContent = label;
    if (desc) desc.textContent = results.score_disclaimer || 'Score reflects visible exposure from passive reconnaissance only.';

    // Score factors
    if (factorsEl && results.score_factors) {
        factorsEl.innerHTML = results.score_factors.slice(0, 8).map(f => {
            const cls = f.startsWith('+') ? 'score-factor--pos' : 'score-factor--neg';
            return `<span class="score-factor ${cls}">${f}</span>`;
        }).join('');
    }
}

// ============================================================================
// HOSTS
// ============================================================================
function displayHosts(hosts) {
    const c = document.getElementById('hostsContent');
    if (!hosts || hosts.length === 0) {
        c.innerHTML = '<div class="empty-state"><i class="bi bi-server"></i><h4>No Active Hosts</h4><p>No responsive hosts detected</p></div>';
        return;
    }
    const portNames = { 21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS', 80: 'HTTP', 443: 'HTTPS', 3306: 'MySQL', 3389: 'RDP', 5432: 'Postgres', 5900: 'VNC', 8080: 'HTTP-Alt', 8443: 'HTTPS-Alt' };

    let html = '<div class="host-list">';
    hosts.forEach((h, i) => {
        const portBadges = (h.ports || []).map(p => {
            const risky = [21, 22, 23, 3389, 5900].includes(p);
            const cls = risky ? 'badge--warning' : 'badge--info';
            return `<span class="badge badge--port ${cls}">${risky ? '<i class="bi bi-exclamation-triangle-fill"></i> ' : ''}${p} <small style="opacity:.7">${portNames[p] || ''}</small></span>`;
        }).join('');

        let geoHtml = '';
        if (h.geo && (h.geo.city || h.geo.country)) {
            geoHtml = `<span class="host-item__geo"><i class="bi bi-geo-alt-fill"></i> ${[h.geo.city, h.geo.country].filter(Boolean).join(', ')}</span>`;
        }
        let orgHtml = '';
        if (h.geo?.org) orgHtml = `<div class="host-item__org"><i class="bi bi-building"></i> ${h.geo.org}</div>`;

        html += `
            <div class="host-item fade-in" style="animation-delay:${i * .07}s">
                <div class="host-item__top">
                    <div>
                        <div class="host-item__name">${h.hostname}</div>
                        <div style="display:flex;align-items:center;gap:.35rem;flex-wrap:wrap;margin-top:.2rem;">
                            <span class="host-item__ip">${h.ip}</span>
                            ${geoHtml}
                        </div>
                        ${orgHtml}
                    </div>
                    <span class="badge ${h.status === 'up' ? 'badge--success' : 'badge--muted'}">
                        <i class="bi ${h.status === 'up' ? 'bi-check-circle' : 'bi-x-circle'}"></i> ${h.status}
                    </span>
                </div>
                <div class="host-item__ports">
                    ${portBadges || '<span class="muted" style="font-size:.68rem;"><i class="bi bi-shield-check"></i> No open ports</span>'}
                </div>
            </div>`;
    });
    html += '</div>';
    c.innerHTML = html;
}

// ============================================================================
// TECHNOLOGIES
// ============================================================================
function displayTechnologies(techs) {
    const c = document.getElementById('technologyContent');
    if (!techs || techs.length === 0) { c.innerHTML = '<p class="muted">No technologies detected</p>'; return; }

    const icons = { wordpress: 'bi-wordpress', apache: 'bi-server', nginx: 'bi-server', cloudflare: 'bi-cloud', react: 'bi-code-slash', vue: 'bi-code-slash', angular: 'bi-code-slash', jquery: 'bi-code-slash', bootstrap: 'bi-grid', php: 'bi-filetype-php', node: 'bi-diagram-3', python: 'bi-filetype-py', next: 'bi-code-slash', shopify: 'bi-cart3', wix: 'bi-palette', tailwind: 'bi-wind' };
    function getIcon(name) {
        const l = name.toLowerCase();
        for (const [k, v] of Object.entries(icons)) { if (l.includes(k)) return v; }
        return 'bi-cpu';
    }

    c.innerHTML = '<div class="tech-grid">' + techs.map(t =>
        `<span class="tech-tag"><i class="bi ${getIcon(t.name)}"></i> ${t.name}</span>`
    ).join('') + '</div>';
}

// ============================================================================
// OSINT (Emails)
// ============================================================================
function displayOSINT(osint) {
    const c = document.getElementById('emailsList');
    const emails = osint.emails || [];
    if (emails.length === 0) { c.innerHTML = '<p class="muted">No exposed emails found</p>'; return; }
    c.innerHTML = '<ul class="email-list">' + emails.map(e =>
        `<li><i class="bi bi-envelope-fill"></i><span>${e}</span></li>`
    ).join('') + '</ul>';
}

// ============================================================================
// SECURITY HEADERS
// ============================================================================
function displaySecurityHeaders(data) {
    const c = document.getElementById('securityHeadersContent');
    if (!c) return;
    if (!data || data.error) { c.innerHTML = '<p class="muted">Unable to check security headers</p>'; return; }

    let html = `<div class="grade-display">
        <div class="grade-circle grade-${data.grade}">${data.grade}</div>
        <div>
            <strong style="color:var(--c-text)">Security Headers Grade</strong><br>
            <span class="muted">${data.score_percentage || 0}% coverage</span>
        </div>
    </div>`;

    if (data.headers_missing?.length) {
        html += '<div class="header-list">';
        data.headers_missing.forEach(h => {
            html += `<div class="header-row header-row--missing"><i class="bi bi-x-circle-fill"></i><span style="color:var(--c-text-2)">${h.name}</span></div>`;
        });
        html += '</div>';
    }
    if (data.headers_found?.length) {
        html += '<div class="header-list" style="margin-top:.5rem;">';
        data.headers_found.forEach(h => {
            html += `<div class="header-row header-row--found"><i class="bi bi-check-circle-fill"></i><span style="color:var(--c-text-2)">${h.name}</span></div>`;
        });
        html += '</div>';
    }
    c.innerHTML = html;
}

// ============================================================================
// SSL / TLS
// ============================================================================
function displaySSLInfo(data) {
    const c = document.getElementById('sslInfoContent');
    if (!c) return;
    if (!data || !data.valid) {
        c.innerHTML = '<div class="inline-alert inline-alert--warning"><i class="bi bi-exclamation-triangle"></i> SSL certificate could not be verified</div>';
        return;
    }
    const isExpiring = data.days_until_expiry < 30;
    const color = data.is_expired ? 'danger' : (isExpiring ? 'warning' : 'success');
    const label = data.is_expired ? 'Certificate Expired!' : (isExpiring ? 'Expiring Soon' : 'Valid Certificate');

    c.innerHTML = `
        <div class="ssl-status">
            <i class="bi bi-shield-lock-fill text-${color}" style="font-size:1.3rem;"></i>
            <strong class="text-${color}">${label}</strong>
        </div>
        <table class="info-table">
            <tr><td>Issuer</td><td>${data.issuer}</td></tr>
            <tr><td>TLS Version</td><td>${data.tls_version || 'Unknown'}</td></tr>
            <tr><td>Expires In</td><td class="text-${color}">${data.days_until_expiry !== undefined ? data.days_until_expiry + ' days' : 'Unknown'}</td></tr>
        </table>`;
}

// ============================================================================
// ADMIN PANELS
// ============================================================================
function displayAdminPanels(data) {
    const c = document.getElementById('adminPanelsContent');
    if (!c) return;
    if (!data || !data.found || data.found.length === 0) {
        c.innerHTML = '<div class="inline-alert inline-alert--success"><i class="bi bi-check-circle"></i> No exposed admin panels detected</div>';
        return;
    }
    c.innerHTML = data.found.map(p => {
        const badge = p.accessible
            ? '<span class="badge badge--danger">Accessible</span>'
            : '<span class="badge badge--warning">Protected</span>';
        return `<div class="panel-row"><code>${p.path}</code>${badge}</div>`;
    }).join('');
}

// ============================================================================
// KNOWN CVEs
// ============================================================================
function displayKnownCVEs(data) {
    const c = document.getElementById('knownCVEsContent');
    if (!c) return;
    if (!data || data.length === 0) {
        c.innerHTML = '<div class="inline-alert inline-alert--success"><i class="bi bi-check-circle"></i> No known CVEs detected</div>';
        return;
    }
    const sevMap = { Critical: 'critical', High: 'high', Medium: 'medium', Low: 'low' };
    c.innerHTML = data.map(cve => `
        <div class="cve-item cve-item--${sevMap[cve.severity] || 'low'}">
            <div class="cve-item__header">
                <span class="badge badge--${cve.severity === 'Critical' ? 'danger' : cve.severity === 'High' ? 'warning' : 'info'}">${cve.severity}</span>
                <span class="cve-item__id">${cve.cve}</span>
            </div>
            <div class="cve-item__tech">${cve.technology}</div>
            <div class="cve-item__desc">${cve.description}</div>
        </div>
    `).join('');
}

// ============================================================================
// ROBOTS.TXT
// ============================================================================
function displayRobotsTxt(data) {
    const c = document.getElementById('robotsTxtContent');
    if (!c) return;
    if (!data || !data.found) { c.innerHTML = '<p class="muted">No robots.txt found</p>'; return; }

    let html = '';
    if (data.sensitive_paths?.length) {
        html += '<div style="margin-bottom:.4rem;"><span class="text-warning" style="font-size:.72rem;"><i class="bi bi-exclamation-triangle"></i> Sensitive Paths:</span></div>';
        html += data.sensitive_paths.map(p =>
            `<div style="font-size:.72rem;padding:.15rem 0;"><code style="color:var(--c-amber);">${p.path}</code> <span class="muted">(${p.keyword})</span></div>`
        ).join('');
    }
    if (data.all_disallowed?.length) {
        html += `<details><summary>${data.all_disallowed.length} disallowed paths</summary>` +
            data.all_disallowed.slice(0, 12).map(p => `<div style="font-size:.68rem;color:var(--c-text-3);padding:.1rem 0;"><code>${p}</code></div>`).join('') +
            '</details>';
    }
    if (!html) html = '<p class="muted">robots.txt found, no sensitive paths</p>';
    c.innerHTML = html;
}

// ============================================================================
// DIRECTORY LISTING
// ============================================================================
function displayDirectoryListing(data) {
    const c = document.getElementById('directoryListingContent');
    if (!c) return;
    if (!data || !data.vulnerable) {
        c.innerHTML = '<div class="inline-alert inline-alert--success"><i class="bi bi-check-circle"></i> No directory listing vulnerabilities</div>';
        return;
    }
    c.innerHTML = `<div class="inline-alert inline-alert--danger"><i class="bi bi-exclamation-triangle-fill"></i> <strong>Directory Listing Enabled!</strong></div>` +
        '<div style="margin-top:.4rem;">' + data.exposed_dirs.map(d => `<div style="font-size:.72rem;"><code style="color:var(--c-rose);">${d}</code></div>`).join('') + '</div>';
}

// ============================================================================
// DNS RECORDS (NEW)
// ============================================================================
function displayDnsRecords(data) {
    const c = document.getElementById('dnsRecordsContent');
    if (!c) return;
    if (!data || data.length === 0) { c.innerHTML = '<p class="muted">No DNS records retrieved</p>'; return; }

    let html = '<table class="dns-table"><thead><tr><th>Type</th><th>Value</th></tr></thead><tbody>';
    data.forEach(r => {
        html += `<tr><td><span class="dns-type-badge">${r.type}</span></td><td>${r.value}</td></tr>`;
    });
    html += '</tbody></table>';
    c.innerHTML = html;
}

// ============================================================================
// WHOIS (NEW)
// ============================================================================
function displayWhois(data) {
    const c = document.getElementById('whoisContent');
    if (!c) return;
    if (!data || data.error) { c.innerHTML = '<p class="muted">WHOIS data unavailable</p>'; return; }

    const fields = [
        { label: 'Registrar', value: data.registrar },
        { label: 'Created', value: data.creation_date },
        { label: 'Expires', value: data.expiry_date },
        { label: 'Updated', value: data.updated_date },
        { label: 'Name Servers', value: data.name_servers },
        { label: 'Registrant Country', value: data.registrant_country },
        { label: 'DNSSEC', value: data.dnssec },
    ].filter(f => f.value);

    if (fields.length === 0) { c.innerHTML = '<p class="muted">Limited WHOIS data available</p>'; return; }

    c.innerHTML = '<div class="whois-grid">' + fields.map(f =>
        `<div class="whois-item"><div class="whois-item__label">${f.label}</div><div class="whois-item__value">${f.value}</div></div>`
    ).join('') + '</div>';
}

// ============================================================================
// COOKIE SECURITY (NEW)
// ============================================================================
function displayCookieSecurity(data) {
    const c = document.getElementById('cookieSecurityContent');
    if (!c) return;
    if (!data || !data.cookies || data.cookies.length === 0) {
        c.innerHTML = '<div class="inline-alert inline-alert--success"><i class="bi bi-check-circle"></i> No cookies detected or all cookies secure</div>';
        return;
    }

    c.innerHTML = data.cookies.map(ck => {
        const flags = [];
        if (ck.secure) flags.push('<span class="cookie-flag cookie-flag--ok">Secure</span>');
        else flags.push('<span class="cookie-flag cookie-flag--warn">No Secure</span>');
        if (ck.httponly) flags.push('<span class="cookie-flag cookie-flag--ok">HttpOnly</span>');
        else flags.push('<span class="cookie-flag cookie-flag--warn">No HttpOnly</span>');
        if (ck.samesite) flags.push(`<span class="cookie-flag cookie-flag--ok">SameSite=${ck.samesite}</span>`);
        else flags.push('<span class="cookie-flag cookie-flag--warn">No SameSite</span>');
        return `<div class="cookie-item"><div class="cookie-name">${ck.name}</div><div class="cookie-flags">${flags.join('')}</div></div>`;
    }).join('');
}

// ============================================================================
// HTTP METHODS (NEW)
// ============================================================================
function displayHttpMethods(data) {
    const c = document.getElementById('httpMethodsContent');
    if (!c) return;
    if (!data || !data.methods) { c.innerHTML = '<p class="muted">Unable to test HTTP methods</p>'; return; }

    const safe = ['GET', 'HEAD', 'OPTIONS'];
    const risky = ['PUT', 'DELETE', 'TRACE', 'CONNECT', 'PATCH'];

    c.innerHTML = '<div class="method-list">' + data.methods.map(m => {
        let cls = 'method-tag--info';
        if (safe.includes(m)) cls = 'method-tag--safe';
        if (risky.includes(m)) cls = 'method-tag--risky';
        return `<span class="method-tag ${cls}">${m}</span>`;
    }).join('') + '</div>' +
    (data.risky_methods?.length ? `<div class="inline-alert inline-alert--warning" style="margin-top:.5rem;"><i class="bi bi-exclamation-triangle"></i> Risky methods enabled: ${data.risky_methods.join(', ')}</div>` : '');
}

// ============================================================================
// CORS (NEW)
// ============================================================================
function displayCors(data) {
    const c = document.getElementById('corsContent');
    if (!c) return;
    if (!data) { c.innerHTML = '<p class="muted">CORS check unavailable</p>'; return; }

    if (data.wildcard_origin) {
        c.innerHTML = '<div class="cors-status cors-status--warn"><i class="bi bi-exclamation-triangle-fill"></i> Wildcard (*) CORS — any origin can access resources</div>';
    } else if (data.reflects_origin) {
        c.innerHTML = '<div class="cors-status cors-status--warn"><i class="bi bi-exclamation-triangle"></i> Origin reflected — potential CORS misconfiguration</div>';
    } else if (data.cors_enabled) {
        c.innerHTML = '<div class="cors-status cors-status--info"><i class="bi bi-info-circle"></i> CORS enabled with restricted origins</div>';
    } else {
        c.innerHTML = '<div class="cors-status cors-status--ok"><i class="bi bi-check-circle-fill"></i> No permissive CORS policy detected</div>';
    }
}

// ============================================================================
// EXPORT JSON
// ============================================================================
function exportJSON(results) {
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `aegis-recon-${results.target}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
    showAlert('Results exported!', 'success');
}

// ============================================================================
// GENERATE REPORT
// ============================================================================
async function generateReport() {
    if (!currentResults) { showAlert('No scan results available', 'warning'); return; }

    const modal = document.getElementById('reportModal');
    modal.classList.add('active');

    if (cachedReport && cachedReport.target === currentResults.target) {
        displayReport(cachedReport.analysis);
        return;
    }

    document.getElementById('reportModalBody').innerHTML =
        '<div class="loading-state"><span class="loader"></span><p>Generating AI threat analysis...</p></div>';

    try {
        const res = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ results: currentResults })
        });
        const data = await res.json();
        if (!res.ok || !data.success) throw new Error(data.error || 'Report generation failed');

        cachedReport = { target: currentResults.target, analysis: data.analysis, scanResults: currentResults, cachedAt: new Date().toISOString() };
        displayReport(data.analysis);
    } catch (err) {
        document.getElementById('reportModalBody').innerHTML = `
            <div style="text-align:center;padding:2rem;">
                <i class="bi bi-exclamation-triangle" style="font-size:2.5rem;color:var(--c-rose);"></i>
                <h4 style="margin:.75rem 0 .5rem;">Report Generation Failed</h4>
                <p class="muted">${err.message}</p>
                <button class="btn btn--ghost" onclick="generateReport()" style="margin-top:.75rem;"><i class="bi bi-arrow-repeat"></i> Retry</button>
            </div>`;
    }
}

// ============================================================================
// DISPLAY REPORT (in modal)
// ============================================================================
function displayReport(analysis) {
    const c = document.getElementById('reportModalBody');
    const target = cachedReport?.target || currentResults?.target || 'Unknown';
    const score = cachedReport?.scanResults?.security_score || currentResults?.security_score || 100;

    let riskLevel, riskColor, riskBg;
    if (score >= 80) { riskLevel = 'LOW'; riskColor = '#10b981'; riskBg = 'rgba(16,185,129,.15)'; }
    else if (score >= 60) { riskLevel = 'MEDIUM'; riskColor = '#f59e0b'; riskBg = 'rgba(245,158,11,.15)'; }
    else if (score >= 40) { riskLevel = 'HIGH'; riskColor = '#f97316'; riskBg = 'rgba(249,115,22,.15)'; }
    else { riskLevel = 'CRITICAL'; riskColor = '#ef4444'; riskBg = 'rgba(239,68,68,.15)'; }

    let content = analysis.report
        .replace(/^### (.*$)/gim, '<h5 style="color:#f8fafc;margin-top:1.2rem;margin-bottom:.5rem;font-weight:600;">$1</h5>')
        .replace(/^## (.*$)/gim, '<h4 style="color:#f8fafc;margin-top:1.2rem;margin-bottom:.5rem;font-weight:700;border-bottom:1px solid rgba(255,255,255,.08);padding-bottom:.35rem;">$1</h4>')
        .replace(/\*\*(.*?)\*\*/g, '<strong style="color:#f8fafc;">$1</strong>')
        .replace(/^- (.*$)/gim, '<li style="color:#cbd5e1;margin-bottom:.35rem;position:relative;padding-left:1rem;"><span style="position:absolute;left:0;color:var(--c-indigo);">▸</span>$1</li>')
        .replace(/`(.*?)`/g, '<code style="background:rgba(99,102,241,.15);color:#a5b4fc;padding:.1rem .35rem;border-radius:3px;font-size:.8rem;">$1</code>')
        .replace(/\n\n/g, '</p><p style="color:#94a3b8;line-height:1.7;">')
        .replace(/\n/g, '<br>');

    c.innerHTML = `
        <div id="reportPrintArea" style="background:linear-gradient(135deg,#0f172a,#1e293b);">
            <div style="background:linear-gradient(135deg,#6366f1,#4f46e5);padding:1.5rem;text-align:center;border-radius:var(--r-lg) var(--r-lg) 0 0;">
                <h2 style="margin:0;color:#fff;font-weight:800;">🛡️ AEGIS RECON</h2>
                <p style="margin:.25rem 0 0;color:rgba(255,255,255,.75);font-size:.75rem;letter-spacing:.15em;">THREAT INTELLIGENCE REPORT</p>
            </div>
            <div style="background:rgba(0,0,0,.25);padding:.75rem 1.25rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.75rem;">
                <div><small style="color:#64748b;text-transform:uppercase;letter-spacing:.08em;font-size:.6rem;">Target</small><div style="color:#f8fafc;font-weight:600;">${target}</div></div>
                <div style="text-align:center;"><small style="color:#64748b;text-transform:uppercase;letter-spacing:.08em;font-size:.6rem;">Score</small><div style="color:${riskColor};font-weight:800;font-size:1.3rem;">${score}/100</div></div>
                <div style="text-align:right;"><small style="color:#64748b;text-transform:uppercase;letter-spacing:.08em;font-size:.6rem;">Risk</small><div style="background:${riskBg};color:${riskColor};padding:.15rem .6rem;border-radius:20px;font-weight:700;font-size:.78rem;">${riskLevel}</div></div>
            </div>
            <div style="padding:1.25rem;"><p style="color:#94a3b8;line-height:1.7;">${content}</p></div>
            <div style="border-top:1px solid rgba(255,255,255,.06);padding:1rem 1.25rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.75rem;">
                <div style="color:#64748b;font-size:.7rem;"><i class="bi bi-robot"></i> ${analysis.model || 'AI'} &bull; ${new Date(analysis.generated_at).toLocaleString()}</div>
                <div style="color:#475569;font-size:.65rem;">© ${new Date().getFullYear()} Rapid Tech Solutions &bull; rapidtech.software</div>
            </div>
        </div>`;
}

// ============================================================================
// PDF DOWNLOAD
// ============================================================================
function downloadReportPDF() {
    if (!cachedReport?.analysis) { showAlert('Generate a report first', 'warning'); return; }

    const target = cachedReport.target || 'Unknown';
    const score = cachedReport.scanResults?.security_score || 100;
    const timestamp = new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    const timeGen = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    const reportContent = typeof cachedReport.analysis === 'string' ? cachedReport.analysis : cachedReport.analysis?.report || '';

    let riskLevel, riskColor;
    if (score >= 80) { riskLevel = 'LOW RISK'; riskColor = [16, 185, 129]; }
    else if (score >= 60) { riskLevel = 'MEDIUM RISK'; riskColor = [245, 158, 11]; }
    else if (score >= 40) { riskLevel = 'HIGH RISK'; riskColor = [249, 115, 22]; }
    else { riskLevel = 'CRITICAL'; riskColor = [239, 68, 68]; }

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
    const pw = 210, ph = 297, m = 15, cw = pw - m * 2;
    let y = 0;

    // Header
    doc.setFillColor(15, 23, 42); doc.rect(0, 0, pw, 42, 'F');
    doc.setFillColor(99, 102, 241); doc.rect(0, 0, pw, 3, 'F');
    doc.setTextColor(255, 255, 255); doc.setFontSize(20); doc.setFont('helvetica', 'bold');
    doc.text('AEGIS RECON', m, 22);
    doc.setFontSize(9); doc.setTextColor(148, 163, 184); doc.setFont('helvetica', 'normal');
    doc.text('THREAT INTELLIGENCE REPORT', m, 30);
    doc.setFontSize(8); doc.setTextColor(239, 68, 68); doc.setFont('helvetica', 'bold');
    doc.text('CONFIDENTIAL', pw - m, 15, { align: 'right' });
    doc.setTextColor(148, 163, 184); doc.setFont('helvetica', 'normal');
    doc.text(timestamp, pw - m, 23, { align: 'right' });
    doc.text(timeGen, pw - m, 30, { align: 'right' });

    y = 52;
    // Summary card
    doc.setFillColor(255, 255, 255); doc.setDrawColor(226, 232, 240);
    doc.roundedRect(m, y, cw, 30, 3, 3, 'FD');
    doc.setFontSize(7); doc.setTextColor(100, 116, 139); doc.setFont('helvetica', 'bold');
    doc.text('TARGET', m + 5, y + 10);
    doc.setFontSize(11); doc.setTextColor(15, 23, 42);
    doc.text(target.length > 30 ? target.substring(0, 27) + '...' : target, m + 5, y + 18);

    doc.setFontSize(7); doc.setTextColor(100, 116, 139);
    doc.text('SCORE', m + 75, y + 10);
    doc.setFontSize(16); doc.setTextColor(riskColor[0], riskColor[1], riskColor[2]); doc.setFont('helvetica', 'bold');
    doc.text(String(score), m + 85, y + 22);

    doc.setFontSize(7); doc.setTextColor(100, 116, 139); doc.setFont('helvetica', 'bold');
    doc.text('RISK', m + 120, y + 10);
    doc.setFillColor(riskColor[0], riskColor[1], riskColor[2]);
    doc.roundedRect(m + 120, y + 13, 45, 10, 5, 5, 'F');
    doc.setFontSize(8); doc.setTextColor(255, 255, 255);
    doc.text(riskLevel, m + 142, y + 20, { align: 'center' });

    y += 40;

    // Content
    function pageBreak(n) { if (y + n > ph - 25) { doc.addPage(); y = 20; } }

    reportContent.split('\n').forEach(line => {
        line = line.trim();
        if (!line || line.startsWith('*Report') || line === '---') return;

        if (line.startsWith('## ')) {
            pageBreak(16); y += 6;
            doc.setFillColor(99, 102, 241); doc.rect(m, y - 4, 3, 10, 'F');
            doc.setFontSize(12); doc.setFont('helvetica', 'bold'); doc.setTextColor(15, 23, 42);
            doc.text(line.replace('## ', ''), m + 6, y + 2); y += 10; return;
        }
        if (line.startsWith('### ')) {
            pageBreak(10); y += 3;
            doc.setFontSize(10); doc.setFont('helvetica', 'bold'); doc.setTextColor(51, 65, 85);
            doc.text(line.replace('### ', ''), m, y); y += 6; return;
        }
        if (line.startsWith('- ') || line.startsWith('▸')) {
            pageBreak(8);
            let t = line.replace(/^[-▸]\s*/, '').replace(/\*\*(.*?)\*\*/g, '$1').replace(/`(.*?)`/g, '"$1"').replace(/[🟢🟡🟠🔴⚠️]/g, '').trim();
            doc.setFillColor(99, 102, 241); doc.circle(m + 4, y - 1, 1.2, 'F');
            doc.setFontSize(9); doc.setFont('helvetica', 'normal'); doc.setTextColor(51, 65, 85);
            doc.splitTextToSize(t, cw - 12).forEach(l => { pageBreak(4.5); doc.text(l, m + 10, y); y += 4.5; });
            y += 1; return;
        }
        let t = line.replace(/\*\*(.*?)\*\*/g, '$1').replace(/`(.*?)`/g, '"$1"').replace(/[🟢🟡🟠🔴⚠️]/g, '');
        if (t.length) {
            pageBreak(6);
            doc.setFontSize(9); doc.setFont('helvetica', 'normal'); doc.setTextColor(71, 85, 105);
            doc.splitTextToSize(t, cw).forEach(l => { pageBreak(4.5); doc.text(l, m, y); y += 4.5; });
            y += 2;
        }
    });

    // Footers
    const pages = doc.internal.getNumberOfPages();
    for (let p = 1; p <= pages; p++) {
        doc.setPage(p);
        doc.setDrawColor(226, 232, 240); doc.setLineWidth(0.3); doc.line(m, ph - 16, pw - m, ph - 16);
        doc.setFontSize(7); doc.setTextColor(148, 163, 184); doc.setFont('helvetica', 'normal');
        doc.text(`Aegis Recon v${AUTHOR.version}`, m, ph - 10);
        doc.text(`Page ${p}/${pages}`, pw / 2, ph - 10, { align: 'center' });
        doc.text(`© ${new Date().getFullYear()} ${AUTHOR.name}`, pw - m, ph - 10, { align: 'right' });
    }

    doc.save(`Aegis-Recon-${target.replace(/[^a-zA-Z0-9]/g, '-')}-Report.pdf`);
    showAlert('Report downloaded!', 'success');
}

// ============================================================================
// RESET
// ============================================================================
function resetDashboard() {
    domainInput.value = '';
    const consentCb = document.getElementById('consentCheckbox');
    if (consentCb) consentCb.checked = false;
    ['statSubdomains', 'statHosts', 'statVulns', 'statEmails', 'statDns'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = '0';
    });
    document.getElementById('hostsContent').innerHTML = '<div class="empty-state"><i class="bi bi-shield-shaded"></i><h4>Ready to Scan</h4><p>Enter a target domain to begin</p></div>';
    ['technologyContent', 'emailsList', 'securityHeadersContent', 'sslInfoContent', 'knownCVEsContent',
     'adminPanelsContent', 'robotsTxtContent', 'directoryListingContent', 'dnsRecordsContent',
     'whoisContent', 'cookieSecurityContent', 'httpMethodsContent', 'corsContent'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = '<p class="muted">Awaiting scan...</p>';
    });
    const scoreSection = document.getElementById('securityScoreSection');
    if (scoreSection) scoreSection.classList.add('hidden');
    newScanBtn.style.display = 'none';
    statusSection.classList.add('hidden');
    const reportBtn = document.getElementById('generateReportBtn');
    if (reportBtn) reportBtn.disabled = true;
    const exportBtn = document.getElementById('exportJsonBtn');
    if (exportBtn) exportBtn.disabled = true;
    currentResults = null;
    cachedReport = null;
    domainInput.focus();
}

// ============================================================================
// ALERTS
// ============================================================================
function showAlert(message, type = 'info') {
    const el = document.createElement('div');
    el.className = `alert-item alert-item--${type}`;
    el.innerHTML = `<span>${message}</span><button class="alert-close" onclick="this.parentElement.remove()">&times;</button>`;
    alertContainer.appendChild(el);
    setTimeout(() => el.remove(), 5000);
}

// ============================================================================
// SIGNATURE
// ============================================================================
console.log(`%c 🛡️ AEGIS RECON v${AUTHOR.version} — Loaded | ${AUTHOR.name}`, 'color:#10b981;font-family:monospace;');
