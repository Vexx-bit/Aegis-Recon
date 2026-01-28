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
    startScanBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Starting scan...';
    
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
        startScanBtn.innerHTML = '<i class="bi bi-play-circle-fill"></i> Start Comprehensive Scan';
    }
}

/**
 * Show status section
 */
function showStatusSection(data) {
    jobIdDisplay.textContent = data.job_id;
    targetDisplay.textContent = data.target || domainInput.value;
    
    // Hide form, show status
    scanForm.closest('.card').style.display = 'none';
    statusSection.classList.remove('hidden');
    
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
        
        // Update status with progress data
        updateStatus(data.status, data.progress);
        
        // If done, fetch results
        if (data.status === 'done') {
            clearInterval(pollingInterval);
            await fetchResults();
        }
        
        // If error, stop polling
        if (data.status === 'error') {
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
        
        // Hide status, show results
        statusSection.classList.add('hidden');
        resultsSection.classList.remove('hidden');
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
        
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
    
    // Generate Network Overview
    document.getElementById('viz-3d-network').innerHTML = `
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
    
    // Generate STUNNING Animated Speedometer
    const needleAngle = -90 + (score * 1.8); // -90 to 90 degrees
    document.getElementById('viz-risk-gauge').innerHTML = `
        <div class="text-center p-4">
            <svg viewBox="0 0 200 120" style="width: 100%; max-width: 400px; margin: 0 auto;">
                <!-- Speedometer Arc Background -->
                <defs>
                    <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" style="stop-color:#ef4444;stop-opacity:1" />
                        <stop offset="50%" style="stop-color:#f59e0b;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#10b981;stop-opacity:1" />
                    </linearGradient>
                </defs>
                
                <!-- Background Arc -->
                <path d="M 30 100 A 70 70 0 0 1 170 100" 
                      fill="none" 
                      stroke="rgba(255,255,255,0.1)" 
                      stroke-width="20" 
                      stroke-linecap="round"/>
                
                <!-- Colored Arc -->
                <path d="M 30 100 A 70 70 0 0 1 170 100" 
                      fill="none" 
                      stroke="url(#gaugeGradient)" 
                      stroke-width="20" 
                      stroke-linecap="round"/>
                
                <!-- Score Markers -->
                <text x="25" y="105" fill="white" font-size="10" font-weight="bold">0</text>
                <text x="95" y="25" fill="white" font-size="10" font-weight="bold" text-anchor="middle">50</text>
                <text x="170" y="105" fill="white" font-size="10" font-weight="bold" text-anchor="end">100</text>
                
                <!-- Needle (Animated) -->
                <g transform="translate(100, 100)">
                    <line x1="0" y1="0" x2="0" y2="-60" 
                          stroke="white" 
                          stroke-width="3" 
                          stroke-linecap="round"
                          transform="rotate(${needleAngle})"
                          style="transition: transform 1.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);">
                        <animateTransform
                            attributeName="transform"
                            type="rotate"
                            from="-90"
                            to="${needleAngle}"
                            dur="1.5s"
                            fill="freeze"/>
                    </line>
                    <circle cx="0" cy="0" r="8" fill="${color}" stroke="white" stroke-width="2"/>
                </g>
            </svg>
            
            <!-- Score Display -->
            <div style="font-size: 60px; font-weight: bold; color: ${color}; margin: 10px 0; text-shadow: 0 0 20px ${color};">
                ${score}
            </div>
            <div style="font-size: 20px; color: white; margin: 5px 0;">${emoji} ${level}</div>
            <div class="text-white-50 small mt-3">
                <strong>${totalVulns}</strong> security issues detected
                <br>
                <span style="color: #ef4444;">●</span> ${niktoVulns} vulnerabilities
                <span style="color: #f59e0b; margin-left: 10px;">●</span> ${outdatedCount} outdated software
            </div>
        </div>
    `;
    
    // Generate Vulnerability Chart
    if (totalVulns === 0) {
        document.getElementById('viz-vulnerability-chart').innerHTML = `
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
        document.getElementById('viz-vulnerability-chart').innerHTML = chartHTML;
    }
    
    console.log('✅ All visualizations generated!');
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
function clearPreviousResults() {
    console.log('Clearing previous scan results...');
    
    // Clear statistics
    document.getElementById('statSubdomains').textContent = '0';
    document.getElementById('statHosts').textContent = '0';
    document.getElementById('statVulns').textContent = '0';
    document.getElementById('statEmails').textContent = '0';
    
    // Clear technology section
    const technologySection = document.getElementById('technologySection');
    const technologyContent = document.getElementById('technologyContent');
    if (technologySection) {
        technologySection.classList.add('hidden');
    }
    if (technologyContent) {
        technologyContent.innerHTML = '';
    }
    
    // Clear OSINT section
    const osintSection = document.getElementById('osintSection');
    const emailsList = document.getElementById('emailsList');
    const hostsList = document.getElementById('hostsList');
    if (osintSection) {
        osintSection.classList.add('hidden');
    }
    if (emailsList) {
        emailsList.innerHTML = '';
    }
    if (hostsList) {
        hostsList.innerHTML = '';
    }
    
    // Clear hosts section
    const hostsContent = document.getElementById('hostsContent');
    if (hostsContent) {
        hostsContent.innerHTML = '';
    }
    
    // Hide visualizations section
    const vizSection = document.getElementById('visualizationsSection');
    if (vizSection) {
        vizSection.style.display = 'none';
    }
    
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
        return;
    }
    
    // Log target for debugging
    console.log('Displaying results for target:', results.target);
    
    // Update statistics with SMART counting
    const metadata = results.metadata || {};
    
    // Count ALL security issues (Nikto + outdated software)
    const niktoVulns = metadata.total_vulnerabilities || 0;
    let outdatedCount = 0;
    const hosts = results.phases?.hosts || [];
    hosts.forEach(host => {
        if (host.whatweb?.outdated_technologies) {
            outdatedCount += host.whatweb.outdated_technologies.length;
        }
    });
    const totalSecurityIssues = niktoVulns + outdatedCount;
    
    document.getElementById('statSubdomains').textContent = metadata.total_subdomains || 0;
    document.getElementById('statHosts').textContent = metadata.total_hosts_scanned || 0;
    document.getElementById('statVulns').textContent = totalSecurityIssues; // DYNAMIC!
    document.getElementById('statEmails').textContent = metadata.total_emails_found || 0;
    
    // Display OSINT data
    if (results.phases && results.phases.osint) {
        displayOSINT(results.phases.osint);
    }
    
    // Display technology stack
    if (results.phases && results.phases.hosts) {
        displayTechnologies(results.phases.hosts);
    }
    
    // Display hosts and vulnerabilities
    if (results.phases && results.phases.hosts) {
        displayHosts(results.phases.hosts);
    }
    
    // Generate visualizations DIRECTLY (no API calls!)
    console.log('Generating visualizations directly...');
    generateVisualizationsDirectly(results);
    
    // Inject AI Report Button
    injectAIButton(results.job_id);
}

/**
 * Inject AI Report Button
 */
function injectAIButton(jobId) {
    const container = document.getElementById('resultsHeaderActions') || document.getElementById('resultsSection');
    if (!container) return;
    
    // Check if button already exists
    if (document.getElementById('aiReportBtn')) return;
    
    const btnHtml = `
        <div id="aiActionContainer" class="text-center my-4">
            <button id="aiReportBtn" class="btn btn-lg btn-outline-primary" onclick="generateAIReport('${jobId}')">
                <i class="bi bi-robot"></i> Generate AI Threat Analysis
            </button>
            <div id="aiReportContent" class="mt-4 text-start" style="display:none; max-width: 800px; margin: 0 auto;"></div>
        </div>
    `;
    
    // Insert after statistics or at top of results
    const statsRow = document.querySelector('.row.g-4.mb-4');
    if (statsRow) {
        statsRow.insertAdjacentHTML('afterend', btnHtml);
    } else {
        container.insertAdjacentHTML('afterbegin', btnHtml);
    }
}

/**
 * Call API to generate AI report
 */
async function generateAIReport(jobId) {
    const btn = document.getElementById('aiReportBtn');
    const contentDiv = document.getElementById('aiReportContent');
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Analyzing with Llama 3...';
    
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
        
        // Render Markdown Report
        // Simple Markdown renderer (bold, list, headers)
        let html = data.report
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
            .replace(/^\- (.*$)/gim, '<li>$1</li>')
            .replace(/\n/gim, '<br>');
            
        contentDiv.innerHTML = `
            <div class="card shadow-sm border-primary">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0"><i class="bi bi-robot"></i> AI Threat Report (${data.model})</h5>
                </div>
                <div class="card-body">
                    ${html}
                </div>
            </div>
        `;
        contentDiv.style.display = 'block';
        btn.innerHTML = '<i class="bi bi-check-lg"></i> Report Generated';
        
    } catch (error) {
        console.error(error);
        alert('Failed to generate report: ' + error.message);
        btn.innerHTML = '<i class="bi bi-robot"></i> Retry Analysis';
        btn.disabled = false;
    }

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
 * Display technology stack
 */
function displayTechnologies(hosts) {
    const technologySection = document.getElementById('technologySection');
    const technologyContent = document.getElementById('technologyContent');
    
    let hastech = false;
    let html = '';
    
    hosts.forEach(hostData => {
        // Support both old (technologies.summary) and new (technologies) structure
        let tech = hostData.technologies?.summary || hostData.technologies;
        
        if (tech && (Object.keys(tech).length > 0)) {
            hastech = true;
            
            html += `<div class="host-card">
                <h6 class="fw-semibold mb-3">
                    <i class="bi bi-globe"></i> ${hostData.host}
                </h6>`;
            
            // Helper to render badges
            const renderBadges = (list, type) => {
                if (!list || list.length === 0) return '';
                return `<div class="mb-2">
                    <strong class="text-muted small">${type}:</strong><br>
                    ${list.map(t => `<span class="tech-badge ${type.toLowerCase()}">${t}</span>`).join('')}
                </div>`;
            };

            html += renderBadges(tech.cms, 'CMS');
            html += renderBadges(tech.web_servers, 'Server');
            html += renderBadges(tech.programming_languages || tech.languages, 'Language');
            html += renderBadges(tech.frameworks, 'Framework');
            html += renderBadges(tech.security, 'Security');
            
            // Outdated technologies warning (Legacy support)
            if (hostData.outdated_technologies && hostData.outdated_technologies.length > 0) {
                html += `<div class="alert alert-warning mt-3 mb-0">
                    <i class="bi bi-exclamation-triangle-fill"></i> 
                    <strong>Outdated Technologies Detected:</strong><br>
                    <ul class="mb-0 mt-2">
                        ${hostData.outdated_technologies.map(t => 
                            `<li>${t.technology} ${t.version}: ${t.recommendation}</li>`
                        ).join('')}
                    </ul>
                </div>`;
            }
            
            html += `</div>`;
        }
    });
    
    if (hastech) {
        technologyContent.innerHTML = html;
        technologySection.classList.remove('hidden');
    }
}

/**
 * Display hosts and vulnerabilities
 */
function displayHosts(hosts) {
    const hostsContent = document.getElementById('hostsContent');
    
    let html = '';
    
    hosts.forEach((hostData, index) => {
        html += `<div class="host-card">
            <h5 class="fw-bold mb-3">
                <i class="bi bi-hdd-network-fill text-primary"></i> ${hostData.host}
            </h5>`;
        
        // Open Ports (Handle Nmap nesting OR direct list)
        const ports = hostData.ports || hostData.nmap?.ports || [];
        
        if (ports.length > 0) {
            html += `<div class="mb-3">
                <h6 class="fw-semibold"><i class="bi bi-door-open"></i> Open Ports</h6>
                <div class="table-responsive">
                    <table class="table table-sm text-white-50">
                        <thead>
                            <tr>
                                <th>PORT</th>
                                <th>STATE</th>
                                <th>SERVICE</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${ports.map(port => `
                                <tr>
                                    <td class="text-primary font-monospace">${port.port}</td>
                                    <td><span class="badge bg-success bg-opacity-25 text-success border border-success">${port.state || 'open'}</span></td>
                                    <td class="text-white">${port.service || 'unknown'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>`;
        }
        
        // Vulnerabilities (Handle legacy separate list OR new Tech/Vulners issues)
        let vulns = [...(hostData.vulnerabilities || [])];
        
        if (hostData.technologies?.vulners_cves) {
             hostData.technologies.vulners_cves.forEach(cve => {
                 vulns.push({
                     title: `<span class="text-danger fw-bold">${cve.id}</span>: ${cve.title}`,
                     url: cve.link,
                     severity: 'critical'
                 });
             });
        }
        
        if (vulns.length > 0) {
            html += `<div class="mb-3">
                <h6 class="fw-semibold text-danger">
                    <i class="bi bi-exclamation-triangle-fill"></i> DETECTED THREATS (${vulns.length})
                </h6>
                ${vulns.map(vuln => `
                    <div class="vuln-item critical mb-2 p-3 border border-danger bg-danger bg-opacity-10 rounded">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <div class="mb-1">${vuln.msg || vuln.title || 'Vulnerability'}</div>
                                ${vuln.url ? `<a href="${vuln.url}" target="_blank" class="text-info text-decoration-none small"><i class="bi bi-link-45deg"></i> Reference Link</a>` : ''}
                            </div>
                            <span class="badge bg-danger">CRITICAL</span>
                        </div>
                    </div>
                `).join('')}
            </div>`;
        } else {
            html += `<div class="alert alert-success bg-success bg-opacity-10 border-success text-success mb-0">
                <i class="bi bi-shield-check"></i> No critical vulnerabilities detected
            </div>`;
        }
        
        html += `</div>`;
    });
    
    hostsContent.innerHTML = html || '<p class="text-muted">No host data available</p>';
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
    startScanBtn.innerHTML = '<i class="bi bi-play-circle-fill"></i> EXECUTE RECONNAISSANCE'; // Reset to futuristic Text
    
    // Show form, hide sections
    scanForm.closest('.card').style.display = 'block';
    statusSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
