<?php
require_once __DIR__ . '/../backend/config/env.php';
$apiKey = getenv('API_KEY');
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AEGIS RECON | Cyber Intelligence Dashboard</title>
    
    <!-- Google Fonts - Inter for modern look -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Bootstrap Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    
    <!-- Professional Light Theme -->
    <link href="css/light-theme.css" rel="stylesheet">
    
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    
    <!-- Config Injection -->
    <script>
        window.AEGIS_CONFIG = {
            apiKey: "<?php echo htmlspecialchars($apiKey ?? ''); ?>",
            apiBaseUrl: "../backend/api.php"
        };
    </script>
    
    <style>
        /* ONE-PAGE DASHBOARD LAYOUT */
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 1.5rem;
        }
        
        .header-bar {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            color: white;
            padding: 1.5rem 2rem;
            border-radius: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .header-bar h1 {
            font-size: 1.5rem;
            font-weight: 800;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .header-bar .subtitle {
            font-size: 0.75rem;
            opacity: 0.7;
            letter-spacing: 2px;
        }
        
        /* Scan Input Bar */
        .scan-bar {
            background: white;
            border-radius: 12px;
            padding: 1rem 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        
        .scan-bar input {
            flex: 1;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            font-size: 1rem;
        }
        
        .scan-bar input:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
        }
        
        .scan-bar button {
            white-space: nowrap;
        }
        
        /* Stats Row */
        .stats-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
        }
        
        @media (max-width: 768px) {
            .stats-row { grid-template-columns: repeat(2, 1fr); }
        }
        
        /* Main Content Grid */
        .content-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 1.5rem;
        }
        
        @media (max-width: 992px) {
            .content-grid { grid-template-columns: 1fr; }
        }
        
        /* Status Inline */
        .status-inline {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.75rem 1rem;
            background: #f8fafc;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }
        
        .status-inline .spinner-border {
            width: 1.25rem;
            height: 1.25rem;
        }
        
        /* Quick Info Cards */
        .info-card {
            background: white;
            border-radius: 12px;
            padding: 1.25rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border: 1px solid #e2e8f0;
        }
        
        .info-card h6 {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #64748b;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .info-card h6 i {
            color: #3b82f6;
        }
    </style>
</head>
<body>
    <div class="container-fluid py-4" style="max-width: 1400px;">
        <div class="dashboard-grid">
            
            <!-- HEADER BAR -->
            <div class="header-bar">
                <div>
                    <h1><i class="bi bi-shield-lock-fill"></i> AEGIS RECON</h1>
                    <div class="subtitle">ADVANCED THREAT INTELLIGENCE SYSTEM</div>
                </div>
                <div class="d-flex align-items-center gap-3">
                    <span id="statusDisplay" class="status-badge status-queued" style="display: none;">
                        <span class="spinner-border spinner-border-sm"></span> Scanning...
                    </span>
                    <button class="btn btn-outline-light btn-sm" id="newScanBtn" style="display: none;">
                        <i class="bi bi-arrow-repeat"></i> New Scan
                    </button>
                </div>
            </div>
            
            <!-- SCAN INPUT BAR -->
            <div class="scan-bar">
                <i class="bi bi-globe2 text-primary fs-4"></i>
                <form id="scanForm" class="d-flex flex-grow-1 gap-2">
                    <input type="text" id="domainInput" placeholder="Enter target domain (e.g., example.com)" required>
                    <button type="submit" class="btn btn-primary px-4" id="startScanBtn">
                        <i class="bi bi-search"></i> Scan
                    </button>
                </form>
            </div>
            
            <!-- STATUS BAR (Inline, shows during scan) -->
            <div id="statusSection" class="hidden">
                <div class="status-inline">
                    <div class="spinner-border text-primary" role="status"></div>
                    <div class="flex-grow-1">
                        <strong id="targetDisplay">--</strong>
                        <small class="text-muted ms-2" id="jobIdDisplay">--</small>
                    </div>
                    <div id="statusMessage" class="text-info">Initializing...</div>
                    <div class="progress flex-grow-1" style="height: 6px; max-width: 200px;">
                        <div id="progressBar" class="progress-bar progress-bar-striped progress-bar-animated" style="width: 0%"></div>
                    </div>
                </div>
            </div>
            
            <!-- STATS ROW (Always visible, updates dynamically) -->
            <div class="stats-row" id="resultsSection">
                <div class="stat-card">
                    <div class="stat-number" id="statSubdomains">0</div>
                    <div class="stat-label">Subdomains</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" style="color: #10b981;" id="statHosts">0</div>
                    <div class="stat-label">Active Hosts</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" style="color: #ef4444;" id="statVulns">0</div>
                    <div class="stat-label">Threats</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" style="color: #0ea5e9;" id="statEmails">0</div>
                    <div class="stat-label">Identities</div>
                </div>
            </div>
            
            <!-- MAIN CONTENT GRID -->
            <div class="content-grid">
                
                <!-- LEFT: Detailed Findings -->
                <div>
                    <div class="info-card">
                        <h6><i class="bi bi-hdd-network-fill"></i> Reconnaissance Results</h6>
                        <div id="hostsContent">
                            <div class="text-center py-5 text-muted">
                                <i class="bi bi-search fs-1"></i>
                                <p class="mt-3 mb-0">Enter a domain above to start scanning</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- RIGHT: Side Panel -->
                <div class="d-flex flex-column gap-4">
                    
                    <!-- Email/Identity Panel -->
                    <div class="info-card" id="osintSection">
                        <h6><i class="bi bi-envelope-at"></i> Exposed Information</h6>
                        <div id="emailsList">
                            <p class="text-muted small mb-0">No data yet</p>
                        </div>
                    </div>
                    
                    <!-- Technology Panel -->
                    <div class="info-card" id="technologySection">
                        <h6><i class="bi bi-cpu-fill"></i> Technology Stack</h6>
                        <div id="technologyContent">
                            <p class="text-muted small mb-0">No data yet</p>
                        </div>
                    </div>
                    
                    <!-- Quick Actions -->
                    <div class="info-card">
                        <h6><i class="bi bi-lightning-fill"></i> Quick Actions</h6>
                        <div id="resultsHeaderActions"></div>
                        <button class="btn btn-outline-primary w-100 mt-2" id="generateReportBtn" disabled>
                            <i class="bi bi-file-earmark-text"></i> Generate Report
                        </button>
                    </div>
                    
                </div>
            </div>
            
        </div>
    </div>
    
    <!-- Hidden elements for backward compat -->
    <div id="hostsList" style="display:none;"></div>
    <div id="visualizationsSection" style="display:none;"></div>
    <div id="alertContainer"></div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="js/dashboard_enhanced.js"></script>
</body>
</html>
