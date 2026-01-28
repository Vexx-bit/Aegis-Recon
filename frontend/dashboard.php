<?php
require_once __DIR__ . '/../backend/config/env.php';
$apiKey = getenv('API_KEY');
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AEGIS RECON | Cyber Intelligence</title>
    
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&display=swap" rel="stylesheet">
    
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Bootstrap Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    
    <!-- Custom Cyberpunk Theme -->
    <link href="css/cyberpunk.css" rel="stylesheet">
    
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    
    <!-- Config Injection -->
    <script>
        window.AEGIS_CONFIG = {
            apiKey: "<?php echo htmlspecialchars($apiKey ?? ''); ?>",
            apiBaseUrl: "../backend/api.php"
        };
    </script>
</head>
<body>
    <div class="scan-overlay"></div>
    
    <div class="container dashboard-container py-5">
        <!-- Header -->
        <div class="text-center mb-5">
            <h1 class="header-logo"><i class="bi bi-shield-lock"></i> AEGIS RECON</h1>
            <div class="header-subtitle">ADVANCED THREAT INTELLIGENCE SYSTEM</div>
        </div>

        <!-- Scan Form -->
        <div class="row justify-content-center mb-5">
            <div class="col-lg-8">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <span><i class="bi bi-terminal"></i> INITIATE SCAN SEQUENCE</span>
                        <span class="badge bg-transparent border border-primary text-primary">SYSTEM READY</span>
                    </div>
                    <div class="card-body p-4">
                        <form id="scanForm">
                            <div class="input-group input-group-lg mb-4">
                                <span class="input-group-text bg-dark border-primary text-primary"><i class="bi bi-globe"></i></span>
                                <input type="text" class="form-control" id="domainInput" 
                                       placeholder="ENTER TARGET IDENTIFIER (e.g. domain.com)" required>
                            </div>
                            <button type="submit" class="btn btn-primary btn-lg w-100" id="startScanBtn">
                                <i class="bi bi-play-circle-fill"></i> EXECUTE RECONNAISSANCE
                            </button>
                        </form>
                        <div id="alertContainer" class="mt-3"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Scan Status -->
        <div id="statusSection" class="hidden mb-5">
            <div class="card">
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-md-3">
                            <small class="text-muted d-block">JOB ID</small>
                            <code class="text-primary" id="jobIdDisplay">--</code>
                        </div>
                        <div class="col-md-5">
                            <small class="text-muted d-block">TARGET</small>
                            <span class="fs-5 fw-bold" id="targetDisplay">--</span>
                        </div>
                        <div class="col-md-4 text-end">
                            <span id="statusDisplay" class="status-badge">INITIALIZING</span>
                        </div>
                    </div>
                    <div class="progress mt-3">
                        <div id="progressBar" class="progress-bar progress-bar-striped progress-bar-animated" style="width: 0%"></div>
                    </div>
                    <div class="text-end mt-2">
                        <small id="statusMessage" class="text-info font-monospace">Waiting for command...</small>
                    </div>
                </div>
            </div>
        </div>

        <!-- Results Section -->
        <div id="resultsSection" class="hidden">
            <!-- Stats Grid -->
            <div class="row g-4 mb-5">
                <div class="col-md-3">
                    <div class="stat-card p-3">
                        <div class="stat-number text-primary" id="statSubdomains">0</div>
                        <div class="stat-label">SUBDOMAINS</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card p-3">
                        <div class="stat-number text-success" id="statHosts">0</div>
                        <div class="stat-label">ACTIVE HOSTS</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card p-3">
                        <div class="stat-number text-danger" id="statVulns">0</div>
                        <div class="stat-label">THREATS</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card p-3">
                        <div class="stat-number text-info" id="statEmails">0</div>
                        <div class="stat-label">IDENTITIES</div>
                    </div>
                </div>
            </div>
            
            <div id="resultsHeaderActions"></div>

            <!-- Main Findings Area -->
            <div class="row">
                <!-- Left Column: Tech & Findings -->
                <div class="col-lg-8">
                    <div class="card mb-4">
                        <div class="card-header"><i class="bi bi-hdd-network"></i> DETAILED FINDINGS</div>
                        <div class="card-body">
                            <div id="hostsContent"></div>
                            
                            <div id="technologySection" class="hidden mt-4">
                                <h5 class="text-primary mb-3">TECHNOLOGY STACK</h5>
                                <div id="technologyContent"></div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Right Column: OSINT & Visuals -->
                <div class="col-lg-4">
                    <div id="osintSection" class="card mb-4 hidden">
                        <div class="card-header"><i class="bi bi-incognito"></i> OSINT DATA</div>
                        <div class="card-body">
                            <div id="emailsList" class="mb-3"></div>
                            <div id="hostsList"></div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header"><i class="bi bi-activity"></i> SYSTEM ACTIONS</div>
                        <div class="card-body text-center">
                            <button class="btn btn-outline-info w-100 mb-2" id="newScanBtn">
                                <i class="bi bi-arrow-repeat"></i> NEW SCAN
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="js/dashboard_enhanced.js"></script>
</body>
</html>
