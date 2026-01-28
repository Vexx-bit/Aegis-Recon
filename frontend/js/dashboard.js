/**
 * Aegis Recon - Dashboard JavaScript
 * Vanilla JS implementation for scan management and results visualization
 */

// Configuration
const API_BASE_URL = '../backend/api.php';
let currentJobId = null;
let currentApiKey = null;
let statusPollInterval = null;
let hostsDataTable = null;

// DOM Elements
const scanForm = document.getElementById('scanForm');
const domainInput = document.getElementById('domainInput');
const apiKeyInput = document.getElementById('apiKeyInput');
const startScanBtn = document.getElementById('startScanBtn');
const statusSection = document.getElementById('statusSection');
const resultsSection = document.getElementById('resultsSection');
const jobIdDisplay = document.getElementById('jobIdDisplay');
const targetDisplay = document.getElementById('targetDisplay');
const statusDisplay = document.getElementById('statusDisplay');
const progressBar = document.getElementById('progressBar');
const statusMessage = document.getElementById('statusMessage');
const downloadPdfBtn = document.getElementById('downloadPdfBtn');
const newScanBtn = document.getElementById('newScanBtn');

/**
 * Initialize dashboard
 */
document.addEventListener('DOMContentLoaded', function() {
    // Load saved API key if exists
    const savedApiKey = localStorage.getItem('aegis_api_key');
    if (savedApiKey) {
        apiKeyInput.value = savedApiKey;
    }
    
    // Event listeners
    scanForm.addEventListener('submit', handleScanSubmit);
    downloadPdfBtn.addEventListener('click', handleDownloadPdf);
    newScanBtn.addEventListener('click', resetDashboard);
    
    console.log('Dashboard initialized');
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
 * Handle scan form submission
 */
async function handleScanSubmit(e) {
    e.preventDefault();
    
    const domain = domainInput.value.trim();
    const apiKey = apiKeyInput.value.trim();
    
    if (!domain || !apiKey) {
        showAlert('Please enter both domain and API key', 'danger');
        return;
    }
    
    // Get or prompt for user email
    let userEmail = localStorage.getItem('user_email');
    if (!userEmail) {
        userEmail = prompt('Please enter your email address for consent tracking:');
        if (!userEmail || !userEmail.includes('@')) {
            showAlert('Valid email address is required', 'danger');
            return;
        }
        localStorage.setItem('user_email', userEmail);
    }
    
    // Generate user_id from email
    const userId = await hashEmail(userEmail);
    
    // Save API key
    localStorage.setItem('aegis_api_key', apiKey);
    currentApiKey = apiKey;
    
    // Disable form
    startScanBtn.disabled = true;
    startScanBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Starting scan...';
    
    try {
        // Call enqueue endpoint
        const response = await fetch(`${API_BASE_URL}?action=enqueue`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-KEY': apiKey
            },
            body: JSON.stringify({ 
                domain: domain,
                user_id: userId  // Include user_id
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
        
        showAlert('Scan started successfully!', 'success');
        
    } catch (error) {
        console.error('Error starting scan:', error);
        showAlert('Error: ' + error.message, 'danger');
        startScanBtn.disabled = false;
        startScanBtn.innerHTML = '<i class="bi bi-play-circle"></i> Start Scan';
    }
}

/**
 * Show status section with initial data
 */
function showStatusSection(data) {
    statusSection.classList.remove('hidden');
    jobIdDisplay.textContent = data.job_id;
    targetDisplay.textContent = data.target;
    updateStatus(data.status);
    
    // Scroll to status section
    statusSection.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Start polling for scan status
 */
function startStatusPolling() {
    // Clear any existing interval
    if (statusPollInterval) {
        clearInterval(statusPollInterval);
    }
    
    // Poll every 3 seconds
    statusPollInterval = setInterval(checkScanStatus, 3000);
    
    // Check immediately
    checkScanStatus();
}

/**
 * Check scan status
 */
async function checkScanStatus() {
    if (!currentJobId || !currentApiKey) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}?action=status&job_id=${currentJobId}`, {
            headers: {
                'X-API-KEY': currentApiKey
            }
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Failed to get status');
        }
        
        // Update status display
        updateStatus(data.status);
        
        // Check if scan is complete
        if (data.status === 'done' || data.status === 'completed') {
            clearInterval(statusPollInterval);
            progressBar.style.width = '100%';
            progressBar.classList.remove('progress-bar-animated');
            statusMessage.textContent = 'Scan completed! Loading results...';
            
            // Fetch and display results
            setTimeout(() => fetchResults(), 1000);
        } else if (data.status === 'error' || data.status === 'failed') {
            clearInterval(statusPollInterval);
            progressBar.classList.remove('progress-bar-animated');
            progressBar.classList.add('bg-danger');
            statusMessage.textContent = 'Scan failed: ' + (data.error_message || 'Unknown error');
        }
        
    } catch (error) {
        console.error('Error checking status:', error);
        statusMessage.textContent = 'Error checking status: ' + error.message;
    }
}

/**
 * Update status display
 */
function updateStatus(status) {
    let badgeClass = 'status-queued';
    let progressWidth = '25%';
    let message = 'Scan queued...';
    
    switch (status) {
        case 'running':
            badgeClass = 'status-running';
            progressWidth = '50%';
            message = 'Scanning in progress... This may take several minutes.';
            break;
        case 'done':
        case 'completed':
            badgeClass = 'status-done';
            progressWidth = '100%';
            message = 'Scan completed successfully!';
            break;
        case 'error':
        case 'failed':
            badgeClass = 'status-error';
            progressWidth = '100%';
            message = 'Scan failed. Please check the logs.';
            break;
    }
    
    statusDisplay.innerHTML = `<span class="status-badge ${badgeClass}">${status.toUpperCase()}</span>`;
    progressBar.style.width = progressWidth;
    statusMessage.textContent = message;
}

/**
 * Fetch and display scan results
 */
async function fetchResults() {
    try {
        const response = await fetch(`${API_BASE_URL}?action=result&job_id=${currentJobId}`, {
            headers: {
                'X-API-KEY': currentApiKey
            }
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Failed to get results');
        }
        
        // Display results
        displayResults(data.results);
        
    } catch (error) {
        console.error('Error fetching results:', error);
        showAlert('Error loading results: ' + error.message, 'danger');
    }
}

/**
 * Display scan results
 */
function displayResults(results) {
    // Show results section
    resultsSection.classList.remove('hidden');
    resultsSection.scrollIntoView({ behavior: 'smooth' });
    
    // Calculate risk score
    const riskScore = calculateRiskScore(results);
    
    // Display executive summary
    displayExecutiveSummary(results, riskScore);
    
    // Display statistics
    displayStatistics(results, riskScore);
    
    // Display charts
    displayCharts(results);
    
    // Display hosts table
    displayHostsTable(results.hosts);
    
    // Display vulnerabilities
    displayVulnerabilities(results.hosts);
}

/**
 * Calculate risk score based on findings
 */
function calculateRiskScore(results) {
    let score = 0;
    
    const totalVulns = results.metadata.total_vulnerabilities || 0;
    const totalPorts = results.metadata.total_ports || 0;
    
    // Base score on vulnerabilities (0-70 points)
    score += Math.min(totalVulns * 10, 70);
    
    // Add points for open ports (0-30 points)
    score += Math.min(totalPorts * 2, 30);
    
    return Math.min(score, 100);
}

/**
 * Display executive summary
 */
function displayExecutiveSummary(results, riskScore) {
    const metadata = results.metadata;
    const riskLevel = riskScore >= 70 ? 'CRITICAL' : riskScore >= 50 ? 'HIGH' : riskScore >= 30 ? 'MEDIUM' : 'LOW';
    const riskClass = riskScore >= 70 ? 'risk-critical' : riskScore >= 50 ? 'risk-high' : riskScore >= 30 ? 'risk-medium' : 'risk-low';
    
    const summary = `
        <h4>Scan Summary for <strong>${results.target}</strong></h4>
        <p class="mb-3">Scan completed on ${new Date(metadata.scan_date).toLocaleString()}</p>
        <div class="row">
            <div class="col-md-6">
                <p><strong>Overall Risk Level:</strong> <span class="${riskClass} fs-4">${riskLevel}</span></p>
                <p><strong>Total Hosts Scanned:</strong> ${metadata.total_hosts}</p>
                <p><strong>Total Open Ports:</strong> ${metadata.total_ports}</p>
                <p><strong>Total Vulnerabilities:</strong> ${metadata.total_vulnerabilities}</p>
            </div>
            <div class="col-md-6">
                <p><strong>Scanner Version:</strong> ${metadata.scanner_version}</p>
                <p><strong>Scan Duration:</strong> ${calculateDuration(results)}</p>
                <p><strong>Job ID:</strong> <code>${results.job_id}</code></p>
            </div>
        </div>
        <hr>
        <p class="mb-0"><strong>Recommendation:</strong> ${getRecommendation(riskScore)}</p>
    `;
    
    document.getElementById('executiveSummary').innerHTML = summary;
}

/**
 * Get recommendation based on risk score
 */
function getRecommendation(score) {
    if (score >= 70) {
        return 'Immediate action required! Critical vulnerabilities detected that require urgent remediation.';
    } else if (score >= 50) {
        return 'High priority issues found. Schedule remediation within the next 7 days.';
    } else if (score >= 30) {
        return 'Medium risk detected. Plan remediation within the next 30 days.';
    } else {
        return 'Low risk profile. Continue monitoring and maintain security best practices.';
    }
}

/**
 * Calculate scan duration
 */
function calculateDuration(results) {
    // This is a placeholder - actual duration would come from scan metadata
    return 'N/A';
}

/**
 * Display statistics
 */
function displayStatistics(results, riskScore) {
    const riskClass = riskScore >= 70 ? 'risk-critical' : riskScore >= 50 ? 'risk-high' : riskScore >= 30 ? 'risk-medium' : 'risk-low';
    
    document.getElementById('riskScore').textContent = riskScore;
    document.getElementById('riskScore').className = 'stat-number ' + riskClass;
    document.getElementById('totalHosts').textContent = results.metadata.total_hosts;
    document.getElementById('totalPorts').textContent = results.metadata.total_ports;
    document.getElementById('totalVulns').textContent = results.metadata.total_vulnerabilities;
}

/**
 * Display charts
 */
function displayCharts(results) {
    // Port distribution chart
    const portData = aggregatePortData(results.hosts);
    createPortChart(portData);
    
    // Service distribution chart
    const serviceData = aggregateServiceData(results.hosts);
    createServiceChart(serviceData);
}

/**
 * Aggregate port data
 */
function aggregatePortData(hosts) {
    const portCounts = {};
    
    hosts.forEach(host => {
        host.ports.forEach(port => {
            const portNum = port.port;
            portCounts[portNum] = (portCounts[portNum] || 0) + 1;
        });
    });
    
    // Get top 10 ports
    const sorted = Object.entries(portCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);
    
    return {
        labels: sorted.map(([port]) => `Port ${port}`),
        data: sorted.map(([, count]) => count)
    };
}

/**
 * Aggregate service data
 */
function aggregateServiceData(hosts) {
    const serviceCounts = {};
    
    hosts.forEach(host => {
        host.ports.forEach(port => {
            const service = port.service || 'unknown';
            serviceCounts[service] = (serviceCounts[service] || 0) + 1;
        });
    });
    
    const sorted = Object.entries(serviceCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 8);
    
    return {
        labels: sorted.map(([service]) => service),
        data: sorted.map(([, count]) => count)
    };
}

/**
 * Create port distribution chart
 */
function createPortChart(data) {
    const ctx = document.getElementById('portChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Occurrences',
                data: data.data,
                backgroundColor: 'rgba(54, 162, 235, 0.7)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

/**
 * Create service distribution chart
 */
function createServiceChart(data) {
    const ctx = document.getElementById('serviceChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.data,
                backgroundColor: [
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 206, 86, 0.7)',
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(153, 102, 255, 0.7)',
                    'rgba(255, 159, 64, 0.7)',
                    'rgba(199, 199, 199, 0.7)',
                    'rgba(83, 102, 255, 0.7)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { position: 'right' }
            }
        }
    });
}

/**
 * Display hosts table
 */
function displayHostsTable(hosts) {
    const tbody = document.getElementById('hostsTableBody');
    tbody.innerHTML = '';
    
    hosts.forEach(host => {
        const row = document.createElement('tr');
        
        const portsHtml = host.ports.map(p => 
            `<span class="port-badge port-open">${p.port}/${p.protocol}</span>`
        ).join('');
        
        const servicesHtml = host.ports.map(p => 
            `<small>${p.service}${p.version ? ' ' + p.version : ''}</small>`
        ).join('<br>');
        
        const vulnCount = host.web_vulns ? host.web_vulns.length : 0;
        const vulnBadge = vulnCount > 0 
            ? `<span class="badge bg-danger">${vulnCount}</span>` 
            : '<span class="badge bg-success">0</span>';
        
        row.innerHTML = `
            <td><strong>${host.host}</strong></td>
            <td>${portsHtml}</td>
            <td>${servicesHtml}</td>
            <td>${vulnBadge}</td>
        `;
        
        tbody.appendChild(row);
    });
    
    // Initialize DataTable
    if (hostsDataTable) {
        hostsDataTable.destroy();
    }
    
    hostsDataTable = $('#hostsTable').DataTable({
        pageLength: 10,
        order: [[3, 'desc']]
    });
}

/**
 * Display vulnerabilities
 */
function displayVulnerabilities(hosts) {
    const container = document.getElementById('vulnerabilitiesContainer');
    container.innerHTML = '';
    
    let totalVulns = 0;
    
    hosts.forEach(host => {
        if (host.web_vulns && host.web_vulns.length > 0) {
            totalVulns += host.web_vulns.length;
            
            host.web_vulns.forEach(vuln => {
                const vulnDiv = document.createElement('div');
                vulnDiv.className = 'vuln-item';
                vulnDiv.innerHTML = `
                    <h6><i class="bi bi-exclamation-triangle-fill"></i> ${vuln.msg || 'Vulnerability detected'}</h6>
                    <p class="mb-1"><strong>Host:</strong> ${host.host}</p>
                    <p class="mb-1"><strong>URL:</strong> <code>${vuln.url || 'N/A'}</code></p>
                    <p class="mb-1"><strong>Method:</strong> ${vuln.method || 'N/A'}</p>
                    ${vuln.osvdb ? `<p class="mb-0"><strong>OSVDB:</strong> ${vuln.osvdb}</p>` : ''}
                `;
                container.appendChild(vulnDiv);
            });
        }
    });
    
    if (totalVulns === 0) {
        container.innerHTML = '<p class="text-success"><i class="bi bi-check-circle"></i> No vulnerabilities detected!</p>';
    }
}

/**
 * Handle PDF download
 */
function handleDownloadPdf() {
    if (!currentJobId) return;
    
    // For now, show alert (PDF generation would be implemented server-side)
    showAlert('PDF download feature coming soon! Job ID: ' + currentJobId, 'info');
    
    // In production, this would call:
    // window.open(`${API_BASE_URL}?action=download&job_id=${currentJobId}`, '_blank');
}

/**
 * Reset dashboard for new scan
 */
function resetDashboard() {
    // Clear current job
    currentJobId = null;
    
    // Clear intervals
    if (statusPollInterval) {
        clearInterval(statusPollInterval);
    }
    
    // Hide sections
    statusSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    
    // Reset form
    domainInput.value = '';
    startScanBtn.disabled = false;
    startScanBtn.innerHTML = '<i class="bi bi-play-circle"></i> Start Scan';
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}
