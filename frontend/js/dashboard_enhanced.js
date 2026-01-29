/**
 * Aegis Recon - Enhanced Dashboard JavaScript
 * Handles scan submission, status polling, and results visualization
 */

// Configuration
const API_BASE_URL = window.AEGIS_CONFIG?.apiBaseUrl || '../backend/api.php';
const API_KEY = window.AEGIS_CONFIG?.apiKey || ''; // Securely injected from backend


const POLL_INTERVAL = 3000; // 3 seconds

// State
let currentJobId = null;
let pollingInterval = null;

// DOM Elements
const scanForm = document.getElementById('scanForm');
const domainInput = document.getElementById('domainInput');
const startScanBtn = document.getElementById('startScanBtn');
const alertContainer = document.getElementById('alertContainer');

const statusSection = document.getElementById('statusSection');
const jobIdDisplay = document.getElementById('jobIdDisplay');
const targetDisplay = document.getElementById('targetDisplay');
const statusDisplay = document.getElementById('statusDisplay');
const progressBar = document.getElementById('progressBar');
const statusMessage = document.getElementById('statusMessage');

const resultsSection = document.getElementById('resultsSection');
const newScanBtn = document.getElementById('newScanBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    scanForm.addEventListener('submit', handleScanSubmit);
    newScanBtn.addEventListener('click', resetDashboard);
});

/**
 * Hash email to generate user_id
 */
async function hashEmail(email) {
    const encoder = new TextEncoder();
    const data = encoder.encode(email);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    alertContainer.innerHTML = '';
    alertContainer.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

/**
 * Handle scan form submission
 */
async function handleScanSubmit(e) {
    e.preventDefault();
    
    const domain = domainInput.value.trim();
    
    if (!domain) {
        showAlert('Please enter a domain or IP address', 'warning');
        return;
    }
    
    // Get or prompt for user email
    let userEmail = localStorage.getItem('user_email');
    if (!userEmail) {
        userEmail = prompt('Please enter your email address for tracking:');
        if (!userEmail || !userEmail.includes('@')) {
            showAlert('Valid email address is required', 'danger');
            return;
        }
        localStorage.setItem('user_email', userEmail);
    }
    
    // Generate user_id from email
    const userId = await hashEmail(userEmail);
    
    // Disable form
    startScanBtn.disabled = true;
    startScanBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Scanning...';
    
    try {
        // Call enqueue endpoint
        const response = await fetch(`${API_BASE_URL}?action=enqueue`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-KEY': API_KEY
            },
            body: JSON.stringify({ 
                domain: domain,
                user_id: userId
            })
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            // Check if consent is required
            if (data.error_code === 'CONSENT_REQUIRED') {
                showAlert('Consent required! Redirecting to consent form...', 'warning');
                setTimeout(() => {
                    window.location.href = 'consent.php?domain=' + encodeURIComponent(domain);
                }, 2000);
                return;
            }
            throw new Error(data.error || 'Failed to start scan');
        }
        
        // Store job ID and start monitoring
        currentJobId = data.job_id;
        
        // Show status section
        showStatusSection(data);
        
        // Start polling for status
        startStatusPolling();
        
        showAlert('Scan started successfully! Monitoring progress...', 'success');
        
    } catch (error) {
        console.error('Error starting scan:', error);
        showAlert('Error: ' + error.message, 'danger');
        startScanBtn.disabled = false;
        startScanBtn.innerHTML = '<i class="bi bi-search"></i> Scan';
    }
}

/**
 * Show status section (one-page inline version)
 */
function showStatusSection(data) {
    const jobIdEl = document.getElementById('jobIdDisplay');
    const targetEl = document.getElementById('targetDisplay');
    
    if (jobIdEl) jobIdEl.textContent = data.job_id;
    if (targetEl) targetEl.textContent = data.target || domainInput.value;
    
    // Show inline status bar
    statusSection.classList.remove('hidden');
    
    // Show scanning indicator in header
    const statusBadge = document.getElementById('statusDisplay');
    if (statusBadge) {
        statusBadge.style.display = 'inline-flex';
    }
    
    updateStatus(data.status || 'queued');
}

/**
 * Update status display with progress information
 */
function updateStatus(status, progressData = null) {
    const statusBadges = {
        'queued': '<span class="status-badge status-queued"><i class="bi bi-hourglass-split"></i> Queued</span>',
        'running': '<span class="status-badge status-running"><span class="spinner-border spinner-border-sm me-2"></span>Running</span>',
        'done': '<span class="status-badge status-done"><i class="bi bi-check-circle-fill"></i> Completed</span>',
        'error': '<span class="status-badge status-error"><i class="bi bi-x-circle-fill"></i> Error</span>'
    };
    
    statusDisplay.innerHTML = statusBadges[status] || statusBadges['queued'];
    
    // Update progress bar and message with real-time data
    if (progressData && status === 'running') {
        const progress = progressData.progress || 0;
        const phase = progressData.phase || 'Initializing';
        const activity = progressData.activity || 'Starting scan...';
        const elapsed = progressData.elapsed_seconds || 0;
        const phaseElapsed = progressData.phase_elapsed_seconds || 0;
        const phaseRemaining = progressData.phase_remaining_seconds || 0;
        
        // Update progress bar
        progressBar.style.width = progress + '%';
        
        // Format time
        const formatTime = (seconds) => {
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            if (mins > 0) {
                return `${mins}m ${secs}s`;
            }
            return `${secs}s`;
        };
        
        // Phase-specific hints - IMPACTFUL & SECURITY-FOCUSED
        const phaseHints = {
            'Subdomain Enumeration': '🎯 Every subdomain is a potential attack vector - finding hidden entry points hackers could exploit!',
            'OSINT Intelligence Gathering': '🕵️ Exposed emails = phishing targets! Discovering what attackers can find about you online.',
            'Port Scanning': '🚪 Open ports are open doors for hackers - identifying which services are exposed to the internet!',
            'Technology Detection': '⚠️ Outdated software = security holes! Detecting vulnerable frameworks attackers love to exploit.',
            'Vulnerability Scanning': '💣 Finding the weaknesses before hackers do - testing for exploitable security flaws!'
        };
        
        const hint = phaseHints[phase] || '⚙️ Processing scan data...';
        
        // Build detailed status message with phase-specific time
        let message = `
            <div class="mb-2">
                <strong><i class="bi bi-gear-fill"></i> ${phase}</strong>
            </div>
            <div class="mb-2 text-muted small">
                ${activity}
            </div>
            <div class="mb-2" style="font-size: 0.85rem; color: #6c757d; font-style: italic;">
                ${hint}
            </div>
        `;
        
        // Show phase-specific time if available, otherwise show total time
        if (phaseElapsed > 0 || phaseRemaining > 0) {
            message += `
                <div class="small text-muted">
                    <i class="bi bi-clock"></i> Elapsed: ${formatTime(phaseElapsed)}
                    ${phaseRemaining > 0 ? ` | Est. Remaining: ~${formatTime(phaseRemaining)}` : ''}
                </div>
            `;
        } else if (elapsed > 0) {
            // Fallback to total elapsed time
            message += `
                <div class="small text-muted">
                    <i class="bi bi-clock"></i> Total Elapsed: ${formatTime(elapsed)}
                </div>
            `;
        }
        
        statusMessage.innerHTML = message;
    } else {
        // Default messages for non-running states
        const defaultMessages = {
            'queued': '<i class="bi bi-hourglass-split"></i> Scan queued, waiting to start...',
            'running': '<i class="bi bi-gear-fill"></i> Scan in progress...',
            'done': '<i class="bi bi-check-circle-fill"></i> Scan completed successfully!',
            'error': '<i class="bi bi-exclamation-triangle-fill"></i> Scan encountered an error'
        };
        
        const defaultProgress = {
            'queued': 10,
            'running': 50,
            'done': 100,
            'error': 100
        };
        
        statusMessage.innerHTML = defaultMessages[status] || defaultMessages['queued'];
        progressBar.style.width = defaultProgress[status] + '%';
    }
    
    if (status === 'done') {
        progressBar.classList.remove('progress-bar-animated');
    }
}

/**
 * Start polling for status
 */
function startStatusPolling() {
    // Clear any existing interval
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    
    // Poll immediately, then every POLL_INTERVAL
    pollStatus();
    pollingInterval = setInterval(pollStatus, POLL_INTERVAL);
}

/**
 * Poll for scan status
 */
async function pollStatus() {
    if (!currentJobId) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}?action=status&job_id=${currentJobId}`, {
            headers: {
                'X-API-KEY': API_KEY
            }
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Failed to get status');
        }
        
        // Normalize status - Python scanner uses 'finished', frontend expects 'done'
        let normalizedStatus = data.status;
        if (normalizedStatus === 'finished') {
            normalizedStatus = 'done';
        }
        
        // Update status with progress data
        updateStatus(normalizedStatus, data.progress);
        
        // If done/finished, fetch results
        if (normalizedStatus === 'done') {
            clearInterval(pollingInterval);
            await fetchResults();
        }
        
        // If error, stop polling
        if (data.status === 'error' || data.status === 'failed') {
            clearInterval(pollingInterval);
            showAlert('Scan failed: ' + (data.error_message || 'Unknown error'), 'danger');
        }
        
    } catch (error) {
        console.error('Error polling status:', error);
    }
}

/**
 * Fetch and display results (with retry logic for consistency)
 */
async function fetchResults(retryCount = 0) {
    const maxRetries = 3;
    
    try {
        const response = await fetch(`${API_BASE_URL}?action=result&job_id=${currentJobId}`, {
            headers: {
                'X-API-KEY': API_KEY
            }
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Failed to fetch results');
        }
        
        // CRITICAL FIX: Verify results are complete before displaying
        if (!data.results || !data.results.phases || !data.results.phases.hosts) {
            if (retryCount < maxRetries) {
                console.warn(`Results not complete yet (attempt ${retryCount + 1}/${maxRetries}), retrying in 2 seconds...`);
                await new Promise(resolve => setTimeout(resolve, 2000));
                return await fetchResults(retryCount + 1);
            } else {
                console.error('Results incomplete after max retries');
                // Display what we have
            }
        }
        
        // Display results
        displayResults(data.results);
        
        // Hide inline status bar (scan complete)
        statusSection.classList.add('hidden');
        
        // Reset the scan button
        startScanBtn.disabled = false;
        startScanBtn.innerHTML = '<i class="bi bi-search"></i> Scan';
        
        // Show "New Scan" button in header
        const newScanBtn = document.getElementById('newScanBtn');
        if (newScanBtn) newScanBtn.style.display = 'inline-block';
        
        // Hide scanning badge
        const statusBadge = document.getElementById('statusDisplay');
        if (statusBadge) statusBadge.style.display = 'none';
        
    } catch (error) {
        console.error('Error fetching results:', error);
        
        // Retry on error if we haven't exceeded max retries
        if (retryCount < maxRetries) {
            console.warn(`Fetch error (attempt ${retryCount + 1}/${maxRetries}), retrying in 2 seconds...`);
            await new Promise(resolve => setTimeout(resolve, 2000));
            return await fetchResults(retryCount + 1);
        }
        
        showAlert('Error fetching results: ' + error.message, 'danger');
    }
}

/**
 * Generate visualizations DIRECTLY from results (no API calls, no Chart.js!)
 */
function generateVisualizationsDirectly(results) {
    console.log('Generating visualizations directly from results...');
    
    // Show visualizations section
    const vizSection = document.getElementById('visualizationsSection');
    if (vizSection) {
        vizSection.style.display = 'block';
    }
    
    // Count vulnerabilities smartly (Nikto + outdated software)
    const niktoVulns = results.metadata?.total_vulnerabilities || 0;
    let outdatedCount = 0;
    const hosts = results.phases?.hosts || [];
    hosts.forEach(host => {
        if (host.whatweb?.outdated_technologies) {
            outdatedCount += host.whatweb.outdated_technologies.length;
        }
    });
    const totalVulns = niktoVulns + outdatedCount;
    
    // Get counts
    const subdomains = results.phases?.subdomains || [];
    const osint = results.phases?.osint || {};
    const subdomainCount = subdomains.length;
    const emailCount = (osint.emails || []).length;
    const hostCount = hosts.length;
    
    // Calculate security score
    const risk = Math.min(totalVulns * 0.05, 1.0);
    const score = Math.round((1 - risk) * 100);
    let level, color, emoji;
    if (score >= 80) {
        level = 'Excellent'; color = '#10b981'; emoji = '🟢';
    } else if (score >= 60) {
        level = 'Good'; color = '#f59e0b'; emoji = '🟡';
    } else if (score >= 40) {
        level = 'Fair'; color = '#f97316'; emoji = '🟠';
    } else {
        level = 'Critical'; color = '#ef4444'; emoji = '🔴';
    }
    
    // Generate Network Overview (only if element exists)
    const networkEl = document.getElementById('viz-3d-network');
    if (networkEl) {
        networkEl.innerHTML = `
            <div class="p-4">
                <h5 class="text-white text-center mb-4">Network Overview: ${results.target || 'Unknown'}</h5>
                <div class="row text-center mb-4">
                    <div class="col-3">
                        <div style="font-size: 48px; color: #667eea;">🎯</div>
                        <div style="color: white; font-size: 24px; font-weight: bold;">1</div>
                        <div style="color: rgba(255,255,255,0.6); font-size: 14px;">Target</div>
                    </div>
                    <div class="col-3">
                        <div style="font-size: 48px; color: #f59e0b;">🌐</div>
                        <div style="color: white; font-size: 24px; font-weight: bold;">${subdomainCount}</div>
                        <div style="color: rgba(255,255,255,0.6); font-size: 14px;">Subdomains</div>
                    </div>
                    <div class="col-3">
                        <div style="font-size: 48px; color: #10b981;">📧</div>
                        <div style="color: white; font-size: 24px; font-weight: bold;">${emailCount}</div>
                        <div style="color: rgba(255,255,255,0.6); font-size: 14px;">Emails</div>
                    </div>
                    <div class="col-3">
                        <div style="font-size: 48px; color: #ef4444;">🐛</div>
                        <div style="color: white; font-size: 24px; font-weight: bold;">${totalVulns}</div>
                        <div style="color: rgba(255,255,255,0.6); font-size: 14px;">Security Issues</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Generate Risk Gauge (only if element exists)
    const needleAngle = -90 + (score * 1.8);
    const gaugeEl = document.getElementById('viz-risk-gauge');
    if (gaugeEl) {
        gaugeEl.innerHTML = `<div class="text-center p-4">Gauge Visualization</div>`;
    }
    
    // Generate Vulnerability Chart (only if element exists)
    const vulnChartEl = document.getElementById('viz-vulnerability-chart');
    if (vulnChartEl) {
        if (totalVulns === 0) {
            vulnChartEl.innerHTML = `
                <div class="alert alert-success m-3">
                    <i class="bi bi-shield-check"></i> No security issues detected - Your site is secure! 🎉
                </div>
            `;
    } else {
        let chartHTML = '<div class="p-4"><h6 class="text-white mb-3">Security Issues by Host</h6>';
        hosts.forEach(host => {
            const hostVulns = (host.vulnerabilities || []).length;
            const hostOutdated = (host.whatweb?.outdated_technologies || []).length;
            const hostTotal = hostVulns + hostOutdated;
            
            if (hostTotal > 0) {
                const vulnPercent = hostTotal > 0 ? (hostVulns / hostTotal * 100) : 0;
                const outdatedPercent = hostTotal > 0 ? (hostOutdated / hostTotal * 100) : 0;
                
                chartHTML += `
                    <div class="mb-3">
                        <div class="text-white mb-1">${host.host || 'Unknown'}</div>
                        <div style="display: flex; height: 30px; border-radius: 5px; overflow: hidden;">
                            ${hostVulns > 0 ? `<div style="width: ${vulnPercent}%; background: #ef4444; display: flex; align-items: center; justify-content: center; color: white; font-size: 12px;">${hostVulns}</div>` : ''}
                            ${hostOutdated > 0 ? `<div style="width: ${outdatedPercent}%; background: #f59e0b; display: flex; align-items: center; justify-content: center; color: white; font-size: 12px;">${hostOutdated}</div>` : ''}
                        </div>
                        <div class="text-white-50 small mt-1">
                            <span style="color: #ef4444;">●</span> ${hostVulns} vulnerabilities
                            <span style="color: #f59e0b; margin-left: 10px;">●</span> ${hostOutdated} outdated software
                        </div>
                    </div>
                `;
            }
        });
        chartHTML += '</div>';
        vulnChartEl.innerHTML = chartHTML;
    }
    } // Close the vulnChartEl if block
    
    console.log('✅ Visualizations generated (if containers exist)');
}

/**
 * Insert HTML with scripts and execute them (innerHTML doesn't execute scripts!)
 */
function insertHTMLWithScripts(elementId, html) {
    const container = document.getElementById(elementId);
    if (!container) return;
    
    // Create a temporary div to parse the HTML
    const temp = document.createElement('div');
    temp.innerHTML = html;
    
    // Clear the container
    container.innerHTML = '';
    
    // Move all child nodes to the container
    while (temp.firstChild) {
        const node = temp.firstChild;
        if (node.tagName === 'SCRIPT') {
            // Create a new script element to execute it
            const script = document.createElement('script');
            script.textContent = node.textContent;
            container.appendChild(script);
        } else {
            container.appendChild(node);
        }
    }
}

/**
 * Clear previous scan results
 */
/**
 * Clear previous scan results
 */
function clearPreviousResults() {
    console.log('Clearing previous scan results...');
    
    // Clear statistics
    document.getElementById('statSubdomains').textContent = '0';
    document.getElementById('statHosts').textContent = '0';
    document.getElementById('statVulns').textContent = '0';
    document.getElementById('statEmails').textContent = '0';
    
    // Clear and Hide Technology
    const technologySection = document.getElementById('technologySection');
    const technologyContent = document.getElementById('technologyContent');
    if (technologySection) technologySection.classList.add('hidden'); // Ensure hidden class is applied
    if (technologyContent) technologyContent.innerHTML = '';
    
    // Clear and Hide OSINT
    const osintSection = document.getElementById('osintSection');
    const emailsList = document.getElementById('emailsList');
    if (osintSection) osintSection.classList.add('hidden'); // Ensure hidden class is applied
    if (emailsList) emailsList.innerHTML = '';
    
    // Clear Hosts
    const hostsContent = document.getElementById('hostsContent');
    if (hostsContent) {
        hostsContent.innerHTML = '<div class="text-center py-5 opacity-50"><i class="bi bi-search fs-1 display-1"></i><p class="mt-3">Awaiting scan data...</p></div>';
    }
    
    // Hide visualizations
    const vizSection = document.getElementById('visualizationsSection');
    if (vizSection) vizSection.style.display = 'none';
    
    console.log('Previous results cleared successfully');
}

/**
 * Display scan results
 */
function displayResults(results) {
    console.log('Displaying new results:', results);
    
    // CRITICAL: Clear all previous data first to prevent showing stale results!
    clearPreviousResults();
    
    // Validate we have the correct scan data
    if (!results || !results.target) {
        console.error('Invalid results data received');
        const statusMsg = document.getElementById('statusMessage');
        if (statusMsg) statusMsg.textContent = "Error: Invalid scan data.";
        return;
    }
    
    // Log target for debugging
    console.log('Displaying results for target:', results.target);
    
    // --- FIX 1: CALCULATE STATS DYNAMICALLY (Ignore Metadata) ---
    // The Python scanner might not send metadata totals, so we count them here.
    const phases = results.phases || {};
    const hosts = phases.hosts || [];
    
    const subdomainsCount = phases.subdomains ? phases.subdomains.length : 0;
    const activeHostsCount = hosts.length;
    
    // Calculate total emails locally
    const osintEmails = phases.osint && phases.osint.emails ? phases.osint.emails.length : 0;

    // Calculate total vulns by summing up vulnerabilities from each host
    let totalThreats = 0;
    hosts.forEach(host => {
        // Count Vulners/Offline CVEs (New)
        if (host.technologies?.vulners_cves) {
            totalThreats += host.technologies.vulners_cves.length;
        }
        // Count Legacy/Other Vulns
        if (host.vulnerabilities) {
            totalThreats += host.vulnerabilities.length;
        }
    });

    // Update DOM Elements
    // Use textContent for security, but ensure fallback to '0'
    document.getElementById('statSubdomains').textContent = subdomainsCount;
    document.getElementById('statHosts').textContent = activeHostsCount;
    document.getElementById('statVulns').textContent = totalThreats;
    document.getElementById('statEmails').textContent = osintEmails;
    
    // --- FIX 2: HANDLE EMPTY DATA GRACEFULLY ---
    
    // Display OSINT data (Emails)
    if (phases.osint && phases.osint.emails && phases.osint.emails.length > 0) {
        displayOSINT(phases.osint);
        // Only show the section if we have actual emails
        document.getElementById('osintSection').classList.remove('hidden');
    } else {
        // Keep hidden or show empty state if desired, but user wants clean 'hidden' look if empty
        console.log('No OSINT data to display. Keeping section hidden.');
    }
    
    // Display hosts and findings
    if (hosts.length > 0) {
        displayHosts(hosts);
    } else {
        document.getElementById('hostsContent').innerHTML = `
            <div class="alert alert-info border-info bg-opacity-10 text-center custom-font">
                <i class="bi bi-info-circle fs-4 d-block mb-3"></i>
                No active hosts responded to probes.
            </div>`;
    }
    
    // Visualizations
    console.log('Generating visualizations directly...');
    generateVisualizationsDirectly(results);
    
    // Inject AI Report Button
    injectAIButton(results.job_id);
}

/**
 * Inject AI Report Button
 */
let reportGenerated = false;

function injectAIButton(jobId) {
    const container = document.getElementById('resultsHeaderActions');
    if (!container) return;
    
    // Store job ID and reset report state
    currentJobId = jobId;
    reportGenerated = false;
    
    // Simple button that opens the modal
    container.innerHTML = `
        <button id="aiReportBtn" class="btn btn-primary w-100" onclick="openReportModal('${jobId}')">
            <i class="bi bi-shield-exclamation"></i> Generate Threat Report
        </button>
    `;
}

/**
 * Open report modal - show cached if available, otherwise generate
 */
function openReportModal(jobId) {
    const reportModal = new bootstrap.Modal(document.getElementById('reportModal'));
    
    // If report already generated, just show the modal
    if (reportGenerated && currentReportData) {
        reportModal.show();
        return;
    }
    
    // Generate new report
    generateAIReport(jobId);
}

/**
 * Call API to generate AI report - Opens in professional modal
 */
let currentReportData = null; // Store for PDF export

async function generateAIReport(jobId) {
    const btn = document.getElementById('aiReportBtn');
    const modalBody = document.getElementById('reportModalBody');
    
    // Show modal immediately with loading state
    const reportModal = new bootstrap.Modal(document.getElementById('reportModal'));
    modalBody.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status"></div>
            <p class="mt-3 text-muted">Analyzing security data with AI...</p>
            <small class="text-muted">This may take a few seconds</small>
        </div>
    `;
    reportModal.show();
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Generating...';
    
    try {
        const response = await fetch(`${API_BASE_URL}?action=analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-KEY': API_KEY
            },
            body: JSON.stringify({ job_id: jobId })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Analysis failed');
        }
        
        // Store for PDF export
        currentReportData = data;
        
        // Render Markdown Report with better formatting
        let html = data.report
            .replace(/####\s*(.*?)(?=\n|$)/gim, '<h4 class="text-primary mt-4 mb-3 border-bottom pb-2">$1</h4>')
            .replace(/###\s*(.*?)(?=\n|$)/gim, '<h4 class="mt-4 mb-3">$1</h4>')
            .replace(/##\s*(.*?)(?=\n|$)/gim, '<h3 class="mt-4 mb-3">$1</h3>')
            .replace(/#\s*(.*?)(?=\n|$)/gim, '<h2 class="mt-4 mb-3">$1</h2>')
            .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
            .replace(/^\d+\.\s+(.*?)$/gim, '<li class="mb-2">$1</li>')
            .replace(/^\*\s+(.*?)$/gim, '<li class="mb-1">$1</li>')
            .replace(/^-\s+(.*?)$/gim, '<li class="mb-1">$1</li>')
            .replace(/`(.*?)`/gim, '<code class="bg-light px-1 rounded">$1</code>')
            .replace(/\n\n/gim, '</p><p>')
            .replace(/\n/gim, '<br>');
        
        // Get target from current scan
        const targetEl = document.getElementById('targetDisplay');
        const target = targetEl ? targetEl.textContent : 'Unknown Target';
        const scanDate = new Date().toLocaleDateString('en-US', { 
            year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' 
        });
        
        modalBody.innerHTML = `
            <div id="reportContent" class="report-printable">
                <!-- Report Header for PDF -->
                <div class="text-center mb-4 pb-3 border-bottom">
                    <h2 class="text-primary mb-1">
                        <i class="bi bi-shield-fill-check"></i> AEGIS RECON
                    </h2>
                    <p class="text-muted mb-0">Security Threat Assessment Report</p>
                </div>
                
                <!-- Report Meta -->
                <div class="row mb-4 bg-light p-3 rounded">
                    <div class="col-md-6">
                        <small class="text-muted">TARGET</small>
                        <div class="fw-bold">${target}</div>
                    </div>
                    <div class="col-md-6 text-md-end">
                        <small class="text-muted">GENERATED</small>
                        <div class="fw-bold">${scanDate}</div>
                    </div>
                </div>
                
                <!-- Report Content -->
                <div class="report-body">
                    ${html}
                </div>
                
                <!-- Footer -->
                <div class="mt-5 pt-3 border-top text-center text-muted">
                    <small>Generated by Aegis Recon Security Platform</small>
                </div>
            </div>
        `;
        
        // Mark report as generated so we can show cached version
        reportGenerated = true;
        
        btn.innerHTML = '<i class="bi bi-eye"></i> View Report';
        btn.disabled = false;
        
    } catch (error) {
        console.error(error);
        modalBody.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i> 
                <strong>Analysis Failed</strong><br>
                ${error.message}
            </div>
            <button class="btn btn-primary" onclick="generateAIReport('${jobId}')">
                <i class="bi bi-arrow-repeat"></i> Retry
            </button>
        `;
        btn.innerHTML = '<i class="bi bi-arrow-repeat"></i> Retry';
        btn.disabled = false;
    }
}

/**
 * Download report as PDF
 */
function downloadReportPDF() {
    const element = document.getElementById('reportContent');
    if (!element) {
        alert('No report to download. Please generate a report first.');
        return;
    }
    
    const targetEl = document.getElementById('targetDisplay');
    const target = targetEl ? targetEl.textContent.replace(/[^a-z0-9]/gi, '_') : 'report';
    const filename = `aegis_recon_${target}_${Date.now()}.pdf`;
    
    const opt = {
        margin: [10, 10, 10, 10],
        filename: filename,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };
    
    // Show loading state
    const btn = document.getElementById('downloadPdfBtn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Generating PDF...';
    btn.disabled = true;
    
    html2pdf().set(opt).from(element).save().then(() => {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }).catch(() => {
        btn.innerHTML = originalText;
        btn.disabled = false;
        alert('Failed to generate PDF. Please try again.');
    });
}

/**
 * Display OSINT findings
 */
function displayOSINT(osint) {
    const osintSection = document.getElementById('osintSection');
    const emailsList = document.getElementById('emailsList');
    const hostsList = document.getElementById('hostsList');
    
    // Display emails
    if (osint.emails && osint.emails.length > 0) {
        emailsList.innerHTML = osint.emails.map(email => 
            `<div class="email-item">
                <i class="bi bi-envelope"></i>
                <span>${email}</span>
            </div>`
        ).join('');
        osintSection.classList.remove('hidden');
    } else {
        emailsList.innerHTML = '<p class="text-muted">No emails discovered</p>';
    }
    
    // Display additional hosts
    if (osint.hosts && osint.hosts.length > 0) {
        hostsList.innerHTML = osint.hosts.map(host => 
            `<div class="email-item">
                <i class="bi bi-hdd-network"></i>
                <span>${host}</span>
            </div>`
        ).join('');
        osintSection.classList.remove('hidden');
    } else {
        hostsList.innerHTML = '<p class="text-muted">No additional hosts found</p>';
    }
}

/**
 * Display hosts and detailed findings with enhanced UI
 */
function displayHosts(hosts) {
    const hostsContent = document.getElementById('hostsContent');
    let html = '';
    
    hosts.forEach((hostData, index) => {
        // --- 1. Host Header ---
        html += `
        <div class="card mb-4 host-card border-0 shadow-lg">
            <div class="host-header">
                <div class="d-flex align-items-center">
                    <div class="me-3">
                        <i class="bi bi-hdd-network-fill fs-2 text-primary"></i>
                    </div>
                    <div>
                        <h4 class="mb-0 fw-bold text-light custom-font">${hostData.host}</h4>
                        <small class="text-primary opacity-75">TARGET SYSTEM DETECTED</small>
                    </div>
                </div>
                <div class="text-end">
                    <span class="badge bg-dark border border-primary text-primary px-3 py-2">LIVE</span>
                </div>
            </div>
            
            <div class="host-body">
        `;

        // --- 2. Tech Stack Integration ---
        // Handle both structures: host.technologies OR host.technologies.summary
        let tech = hostData.technologies || {};
        if (tech.summary) {
            tech = tech.summary; // If nested
        }
        
        // Check if we actually have tech data to show
        let hasTechData = false;
        const categories = ['web_servers', 'cms', 'programming_languages', 'frameworks', 'security', 'languages'];
        if (tech && typeof tech === 'object') {
            hasTechData = categories.some(cat => tech[cat] && tech[cat].length > 0);
        }

        if (hasTechData) {
            html += `<div class="mb-4">
                <h6 class="text-secondary text-uppercase mb-3 letter-spacing-2">
                    <i class="bi bi-cpu-fill me-2"></i> Technology Fingerprint
                </h6>
                <div class="tech-grid">`;
                
            // Helper to render distinct tech blocks
            const renderTech = (list, icon, type) => {
                if (!list || list.length === 0) return '';
                return list.map(t => `
                    <div class="tech-item">
                        <i class="${icon}"></i>
                        <div class="tech-info">
                            <div class="tech-label">${type}</div>
                            <div class="tech-value">${t}</div>
                        </div>
                    </div>
                `).join('');
            };

            html += renderTech(tech.web_servers, 'bi bi-server', 'Server');
            html += renderTech(tech.cms, 'bi bi-wordpress', 'CMS');
            html += renderTech(tech.programming_languages || tech.languages, 'bi bi-code-slash', 'Language');
            html += renderTech(tech.frameworks, 'bi bi-boxes', 'Framework');
            html += renderTech(tech.security, 'bi bi-shield-lock', 'Security');
            
            html += `</div></div>`;
        }

        // --- 3. Ports Grid (Replaces old table) ---
        const ports = hostData.ports || hostData.nmap?.ports || [];
        if (ports.length > 0) {
            html += `
            <div class="mb-4">
                <h6 class="text-secondary text-uppercase mb-3 letter-spacing-2">
                    <i class="bi bi-ethernet me-2"></i> Open Service Ports
                </h6>
                <div class="ports-grid">
            `;
            
            html += ports.map(port => `
                <div class="port-item">
                    <div class="port-number">${port.port}</div>
                    <div class="port-service">
                        <i class="bi bi-circle-fill text-success" style="font-size: 6px; vertical-align: middle; margin-right: 4px;"></i>
                        ${port.service || 'UNKNOWN'}
                    </div>
                </div>
            `).join('');
            
            html += `</div></div>`;
        } else {
             html += `<div class="alert alert-dark border-secondary mb-4 opacity-50">
                <i class="bi bi-dash-circle"></i> No open ports discovered on this host.
            </div>`;
        }

        // --- 4. Vulnerabilities (Visual Alerts) ---
        let vulns = [...(hostData.vulnerabilities || [])];
        if (hostData.technologies?.vulners_cves) {
             hostData.technologies.vulners_cves.forEach(cve => {
                 vulns.push({
                     title: cve.id, // Explicit ID for display
                     desc: cve.title,
                     url: cve.link,
                     score: cve.score || 10.0,
                     severity: 'critical'
                 });
             });
        }

        if (vulns.length > 0) {
            html += `
            <div>
                <h6 class="text-danger text-uppercase mb-3 letter-spacing-2">
                    <i class="bi bi-radioactive me-2"></i> Critical Threats Detected
                </h6>
            `;
            
            html += vulns.map(vuln => `
                <div class="vuln-card">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div class="vuln-title">
                            <i class="bi bi-bug-fill me-2"></i> 
                            ${vuln.title || 'UNKNOWN CVE'}
                        </div>
                        ${vuln.score ? `<span class="badge bg-danger text-white">CVSS ${vuln.score}</span>` : ''}
                    </div>
                    <p class="vuln-desc">${vuln.desc || vuln.msg || 'Vulnerability detected via scanner.'}</p>
                    ${vuln.url ? `<a href="${vuln.url}" target="_blank" class="btn btn-sm btn-outline-danger py-0" style="font-size: 0.7rem;">VIEW INTEL <i class="bi bi-box-arrow-up-right ms-1"></i></a>` : ''}
                </div>
            `).join('');
            
            html += `</div>`;
        } else {
            html += `
            <div class="secure-state">
                <i class="bi bi-shield-check"></i>
                <h5>System Appears Secure</h5>
                <p>No high-risk vulnerabilities detected based on current intelligence feeds.</p>
            </div>
            `;
        }

        html += `</div></div>`; // End Card Body & Card
    });

    hostsContent.innerHTML = html || `
    <div class="text-center py-5 opacity-50">
        <i class="bi bi-search fs-1 display-1"></i>
        <p class="mt-3">Awaiting scan data...</p>
    </div>`;
}

// Deprecate old function to avoid duplicate display
function displayTechnologies(hosts) {
    // Logic moved inside displayHosts for unified view
}

/**
 * Reset dashboard for new scan
 */
function resetDashboard() {
    // Clear state
    currentJobId = null;
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    
    // Reset form
    domainInput.value = '';
    startScanBtn.disabled = false;
    startScanBtn.innerHTML = '<i class="bi bi-play-circle-fill"></i> EXECUTE RECONNAISSANCE';
    
    // Show form, hide sections
    scanForm.closest('.card').style.display = 'block';
    statusSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
