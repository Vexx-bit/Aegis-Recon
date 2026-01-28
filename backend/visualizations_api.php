<?php
/**
 * Visualizations API
 * Generates stunning Plotly visualizations for scan results using JavaScript/Plotly.js
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, X-API-KEY');

// Handle preflight
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

require_once __DIR__ . '/config/database.php';

// Get action
$action = $_GET['action'] ?? '';
$job_id = $_GET['job_id'] ?? '';

if (empty($action) || empty($job_id)) {
    echo json_encode(['success' => false, 'error' => 'Missing action or job_id']);
    exit();
}

try {
    $db = getDatabaseConnection();
    
    // Fetch scan results
    $stmt = $db->prepare("SELECT results FROM scans WHERE job_id = ?");
    $stmt->bind_param("s", $job_id);
    $stmt->execute();
    $result = $stmt->get_result();
    $row = $result->fetch_assoc();
    
    if (!$row) {
        echo json_encode(['success' => false, 'error' => 'Scan not found']);
        exit();
    }
    
    $results = json_decode($row['results'], true);
    
    // Generate visualization HTML based on action
    $html = '';
    
    switch ($action) {
        case '3d_network':
            $html = generate3DNetwork($results);
            break;
        case 'risk_gauge':
            $html = generateRiskGauge($results);
            break;
        case 'vulnerability_chart':
            $html = generateVulnerabilityChart($results);
            break;
        default:
            echo json_encode(['success' => false, 'error' => 'Unknown action']);
            exit();
    }
    
    echo json_encode([
        'success' => true,
        'html' => $html
    ]);
    
} catch (Exception $e) {
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage()
    ]);
}

/**
 * Generate Network Topology using PURE HTML/CSS (no scripts!)
 */
function generate3DNetwork($results) {
    $target = $results['target'] ?? 'Unknown';
    $subdomains = $results['phases']['subdomains'] ?? [];
    $osint = $results['phases']['osint'] ?? [];
    $hosts = $results['phases']['hosts'] ?? [];
    
    // Count outdated software as vulnerabilities
    $niktoVulns = $results['metadata']['total_vulnerabilities'] ?? 0;
    $outdatedCount = 0;
    foreach ($hosts as $host) {
        if (isset($host['whatweb']['outdated_technologies'])) {
            $outdatedCount += count($host['whatweb']['outdated_technologies']);
        }
    }
    $vulnCount = $niktoVulns + $outdatedCount;
    
    $subdomainCount = count($subdomains);
    $emailCount = count($osint['emails'] ?? []);
    $hostCount = count($hosts);
    
    return <<<HTML
<div class="p-4">
    <h5 class="text-white text-center mb-4">Network Overview: $target</h5>
    <div class="row text-center mb-4">
        <div class="col-3">
            <div style="font-size: 48px; color: #667eea;">🎯</div>
            <div style="color: white; font-size: 24px; font-weight: bold;">1</div>
            <div style="color: rgba(255,255,255,0.6); font-size: 14px;">Target</div>
        </div>
        <div class="col-3">
            <div style="font-size: 48px; color: #f59e0b;">🌐</div>
            <div style="color: white; font-size: 24px; font-weight: bold;">$subdomainCount</div>
            <div style="color: rgba(255,255,255,0.6); font-size: 14px;">Subdomains</div>
        </div>
        <div class="col-3">
            <div style="font-size: 48px; color: #10b981;">📧</div>
            <div style="color: white; font-size: 24px; font-weight: bold;">$emailCount</div>
            <div style="color: rgba(255,255,255,0.6); font-size: 14px;">Emails</div>
        </div>
        <div class="col-3">
            <div style="font-size: 48px; color: #ef4444;">🐛</div>
            <div style="color: white; font-size: 24px; font-weight: bold;">$vulnCount</div>
            <div style="color: rgba(255,255,255,0.6); font-size: 14px;">Vulnerabilities</div>
        </div>
    </div>
    <canvas id="$chartId" height="300"></canvas>
</div>
<script>
(function() {
    const ctx = document.getElementById('$chartId').getContext('2d');
    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Subdomains', 'Hosts', 'Emails', 'Vulnerabilities', 'Attack Surface'],
            datasets: [{
                label: 'Security Metrics',
                data: [$subdomainCount, $hostCount, $emailCount, $vulnCount, Math.max($subdomainCount, $hostCount, $emailCount)],
                backgroundColor: 'rgba(102, 126, 234, 0.2)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(102, 126, 234, 1)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(102, 126, 234, 1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                r: {
                    beginAtZero: true,
                    ticks: { color: 'white', backdropColor: 'transparent' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    pointLabels: { color: 'white', font: { size: 14 } }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
})();
</script>
HTML;
}

/**
 * Generate Risk Gauge using Chart.js (simpler, faster)
 */
function generateRiskGauge($results) {
    // SMART vulnerability counting: Include Nikto vulns + outdated software
    $niktoVulns = $results['metadata']['total_vulnerabilities'] ?? 0;
    $outdatedCount = 0;
    
    // Count outdated technologies as vulnerabilities
    $hosts = $results['phases']['hosts'] ?? [];
    foreach ($hosts as $host) {
        if (isset($host['whatweb']['outdated_technologies'])) {
            $outdatedCount += count($host['whatweb']['outdated_technologies']);
        }
    }
    
    $totalVulns = $niktoVulns + $outdatedCount;
    $risk = min($totalVulns * 0.05, 1.0);
    $score = (int)((1 - $risk) * 100);
    
    if ($score >= 80) {
        $level = "Excellent";
        $color = "#10b981";
        $emoji = "🟢";
    } elseif ($score >= 60) {
        $level = "Good";
        $color = "#f59e0b";
        $emoji = "🟡";
    } elseif ($score >= 40) {
        $level = "Fair";
        $color = "#f97316";
        $emoji = "🟠";
    } else {
        $level = "Critical";
        $color = "#ef4444";
        $emoji = "🔴";
    }
    
    $chartId = 'gauge-' . uniqid();
    
    return <<<HTML
<div class="text-center p-4">
    <div style="font-size: 80px; font-weight: bold; color: $color; margin: 20px 0;">$score</div>
    <div style="font-size: 24px; color: white; margin: 10px 0;">$emoji $level</div>
    <div style="width: 100%; height: 20px; background: rgba(255,255,255,0.1); border-radius: 10px; margin: 20px 0; overflow: hidden;">
        <div style="width: {$score}%; height: 100%; background: $color; transition: width 1s ease;"></div>
    </div>
    <canvas id="$chartId" width="400" height="200"></canvas>
</div>
<script>
(function() {
    const ctx = document.getElementById('$chartId').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [$score, 100 - $score],
                backgroundColor: ['$color', 'rgba(255,255,255,0.1)'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            }
        }
    });
})();
</script>
HTML;
}

/**
 * Generate Vulnerability Chart using Chart.js (simpler, faster)
 */
function generateVulnerabilityChart($results) {
    $hosts = $results['phases']['hosts'] ?? [];
    
    $hostNames = [];
    $vulnCounts = [];
    $outdatedCounts = [];
    
    foreach ($hosts as $host) {
        $hostNames[] = $host['host'] ?? 'Unknown';
        
        // Count Nikto vulnerabilities
        $niktoVulns = count($host['vulnerabilities'] ?? []);
        
        // Count outdated technologies as vulnerabilities
        $outdatedVulns = 0;
        if (isset($host['whatweb']['outdated_technologies'])) {
            $outdatedVulns = count($host['whatweb']['outdated_technologies']);
        }
        
        $vulnCounts[] = $niktoVulns;
        $outdatedCounts[] = $outdatedVulns;
    }
    
    $totalIssues = array_sum($vulnCounts) + array_sum($outdatedCounts);
    
    if ($totalIssues === 0) {
        return '<div class="alert alert-success m-3"><i class="bi bi-shield-check"></i> No security issues detected - Your site is secure! 🎉</div>';
    }
    
    $hostNamesJson = json_encode($hostNames);
    $vulnCountsJson = json_encode($vulnCounts);
    $outdatedCountsJson = json_encode($outdatedCounts);
    
    $chartId = 'vuln-' . uniqid();
    
    return <<<HTML
<div class="p-4">
    <h6 class="text-white mb-3">Security Issues by Host</h6>
    <canvas id="$chartId" height="300"></canvas>
</div>
<script>
(function() {
    const ctx = document.getElementById('$chartId').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: $hostNamesJson,
            datasets: [
                {
                    label: 'Vulnerabilities',
                    data: $vulnCountsJson,
                    backgroundColor: 'rgba(239, 68, 68, 0.8)',
                    borderColor: 'rgba(239, 68, 68, 1)',
                    borderWidth: 2
                },
                {
                    label: 'Outdated Software',
                    data: $outdatedCountsJson,
                    backgroundColor: 'rgba(251, 191, 36, 0.8)',
                    borderColor: 'rgba(251, 191, 36, 1)',
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    stacked: true,
                    ticks: { color: 'white', stepSize: 1 },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                x: {
                    stacked: true,
                    ticks: { color: 'white' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            },
            plugins: {
                legend: { 
                    display: true,
                    labels: { color: 'white' }
                }
            }
        }
    });
})();
</script>
HTML;
}
