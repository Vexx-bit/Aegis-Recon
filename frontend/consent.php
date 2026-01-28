<?php
/**
 * Aegis Recon - Consent Management System
 * Legal consent form for authorized security scanning
 */

session_start();

require_once __DIR__ . '/../backend/config/env.php';
require_once __DIR__ . '/../backend/config/database.php';

// Handle form submission
$error = null;
$success = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $domain = trim($_POST['domain'] ?? '');
    $user_email = trim($_POST['user_email'] ?? '');
    $consent_confirmed = isset($_POST['consent_confirmed']);
    $ownership_confirmed = isset($_POST['ownership_confirmed']);
    
    // Validation
    if (empty($domain)) {
        $error = 'Domain is required';
    } elseif (empty($user_email)) {
        $error = 'Email is required';
    } elseif (!filter_var($user_email, FILTER_VALIDATE_EMAIL)) {
        $error = 'Invalid email address';
    } elseif (!$consent_confirmed) {
        $error = 'You must agree to the terms and conditions';
    } elseif (!$ownership_confirmed) {
        $error = 'You must confirm ownership or authorization';
    } else {
        // Sanitize domain
        $domain = preg_replace('#^https?://#i', '', $domain);
        $domain = rtrim($domain, '/');
        
        // Validate domain format
        if (!filter_var($domain, FILTER_VALIDATE_DOMAIN, FILTER_FLAG_HOSTNAME) && 
            !filter_var($domain, FILTER_VALIDATE_IP)) {
            $error = 'Invalid domain or IP address format';
        } else {
            try {
                $db = getDatabaseConnection();
                
                // Generate user_id from email (or use session-based user ID in production)
                $user_id = hash('sha256', $user_email);
                
                // Consent text
                $consent_text = "I confirm that I own or have explicit authorization to perform security scanning on the domain/IP: {$domain}. "
                              . "I understand that unauthorized scanning may be illegal and agree to use Aegis Recon only for lawful purposes. "
                              . "I accept full responsibility for any scans performed.";
                
                // Insert consent record
                $stmt = $db->prepare(
                    "INSERT INTO scan_consents (user_id, user_email, target_domain, consent_text, ip_address, user_agent, created_at) 
                     VALUES (?, ?, ?, ?, ?, ?, NOW())"
                );
                
                $ip_address = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
                $user_agent = $_SERVER['HTTP_USER_AGENT'] ?? 'unknown';
                
                $stmt->bind_param('ssssss', $user_id, $user_email, $domain, $consent_text, $ip_address, $user_agent);
                
                if ($stmt->execute()) {
                    $consent_id = $db->insert_id;
                    
                    // Store consent info in session
                    $_SESSION['consent_id'] = $consent_id;
                    $_SESSION['user_id'] = $user_id;
                    $_SESSION['user_email'] = $user_email;
                    $_SESSION['consented_domain'] = $domain;
                    
                    $success = "Consent recorded successfully! You may now scan {$domain} for the next 24 hours.";
                    
                    // Redirect to dashboard after 2 seconds
                    header("Refresh: 2; url=dashboard.html?domain=" . urlencode($domain));
                } else {
                    $error = 'Failed to record consent: ' . $stmt->error;
                }
                
                $stmt->close();
                $db->close();
                
            } catch (Exception $e) {
                $error = 'Database error: ' . $e->getMessage();
            }
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scan Consent - Aegis Recon</title>
    
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Bootstrap Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem 0;
        }
        
        .consent-container {
            max-width: 800px;
            margin: 0 auto;
        }
        
        .card {
            border: none;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .card-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px 15px 0 0 !important;
            padding: 1.5rem;
        }
        
        .legal-text {
            background: #f8f9fa;
            border-left: 4px solid #0d6efd;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 5px;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .warning-box {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 5px;
        }
        
        .checkbox-label {
            font-weight: 500;
            cursor: pointer;
        }
        
        .header-logo {
            font-size: 2rem;
            font-weight: bold;
            color: white;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            text-align: center;
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <div class="container consent-container">
        <!-- Header -->
        <div class="header-logo">
            <i class="bi bi-shield-lock"></i> AEGIS RECON
        </div>
        
        <!-- Consent Form -->
        <div class="card">
            <div class="card-header">
                <h4 class="mb-0"><i class="bi bi-file-text"></i> Security Scan Authorization & Consent</h4>
            </div>
            <div class="card-body">
                <?php if ($error): ?>
                    <div class="alert alert-danger alert-dismissible fade show" role="alert">
                        <i class="bi bi-exclamation-triangle"></i> <?php echo htmlspecialchars($error); ?>
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                <?php endif; ?>
                
                <?php if ($success): ?>
                    <div class="alert alert-success alert-dismissible fade show" role="alert">
                        <i class="bi bi-check-circle"></i> <?php echo htmlspecialchars($success); ?>
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                <?php endif; ?>
                
                <div class="warning-box">
                    <h5><i class="bi bi-exclamation-triangle-fill text-warning"></i> Important Legal Notice</h5>
                    <p class="mb-0">
                        Unauthorized security scanning of systems you do not own or have explicit permission to test 
                        may be <strong>illegal</strong> under the Computer Misuse and Cybercrimes Act (2018) and 
                        other applicable laws. By proceeding, you confirm that you have proper authorization.
                    </p>
                </div>
                
                <form method="POST" action="" id="consentForm">
                    <div class="mb-3">
                        <label for="user_email" class="form-label">Your Email Address *</label>
                        <input type="email" class="form-control" id="user_email" name="user_email" 
                               placeholder="your.email@example.com" required
                               value="<?php echo htmlspecialchars($_POST['user_email'] ?? ''); ?>">
                        <div class="form-text">Used for consent tracking and audit purposes</div>
                    </div>
                    
                    <div class="mb-3">
                        <label for="domain" class="form-label">Target Domain or IP Address *</label>
                        <input type="text" class="form-control" id="domain" name="domain" 
                               placeholder="example.com or 192.168.1.1" required
                               value="<?php echo htmlspecialchars($_POST['domain'] ?? ''); ?>">
                        <div class="form-text">Enter the domain or IP you own or have authorization to scan</div>
                    </div>
                    
                    <div class="legal-text">
                        <h6>Terms and Conditions</h6>
                        <p><strong>1. Authorization Requirement</strong></p>
                        <p>You must own the target system or have explicit written authorization from the system owner 
                        to perform security testing. Aegis Recon is designed for authorized security assessments only.</p>
                        
                        <p><strong>2. Legal Compliance</strong></p>
                        <p>You agree to comply with all applicable laws including but not limited to:</p>
                        <ul>
                            <li>Computer Misuse and Cybercrimes Act (2018) - Kenya</li>
                            <li>Data Protection Act (2019) - Kenya</li>
                            <li>Computer Fraud and Abuse Act (CFAA) - United States</li>
                            <li>Computer Misuse Act - United Kingdom</li>
                            <li>All other applicable local, national, and international laws</li>
                        </ul>
                        
                        <p><strong>3. Scope of Scanning</strong></p>
                        <p>The security scan will include:</p>
                        <ul>
                            <li>Subdomain enumeration</li>
                            <li>Port scanning and service detection</li>
                            <li>Web vulnerability scanning</li>
                            <li>Version detection of running services</li>
                        </ul>
                        
                        <p><strong>4. Data Handling</strong></p>
                        <p>Scan results will be stored temporarily and may include sensitive information about your 
                        infrastructure. You are responsible for securing and properly disposing of these reports.</p>
                        
                        <p><strong>5. Liability</strong></p>
                        <p>You accept full responsibility for any scans performed. Aegis Recon and its operators are 
                        not liable for any damages, legal consequences, or issues arising from your use of this service.</p>
                        
                        <p><strong>6. Consent Duration</strong></p>
                        <p>This consent is valid for 24 hours from the time of submission. After this period, you must 
                        provide consent again to perform additional scans.</p>
                        
                        <p><strong>7. Audit Trail</strong></p>
                        <p>Your consent, including timestamp, IP address, and user agent, will be logged for legal 
                        compliance and audit purposes.</p>
                    </div>
                    
                    <div class="mb-3 form-check">
                        <input type="checkbox" class="form-check-input" id="ownership_confirmed" 
                               name="ownership_confirmed" required>
                        <label class="form-check-label checkbox-label" for="ownership_confirmed">
                            I confirm that I <strong>own</strong> the target domain/IP or have <strong>explicit written 
                            authorization</strong> from the owner to perform security testing. *
                        </label>
                    </div>
                    
                    <div class="mb-3 form-check">
                        <input type="checkbox" class="form-check-input" id="consent_confirmed" 
                               name="consent_confirmed" required>
                        <label class="form-check-label checkbox-label" for="consent_confirmed">
                            I have read and agree to the terms and conditions above. I understand that unauthorized 
                            scanning is illegal and accept full responsibility for my actions. *
                        </label>
                    </div>
                    
                    <div class="mb-3 form-check">
                        <input type="checkbox" class="form-check-input" id="legal_confirmed">
                        <label class="form-check-label checkbox-label" for="legal_confirmed">
                            I understand that this consent will be recorded with my IP address, timestamp, and other 
                            identifying information for legal compliance.
                        </label>
                    </div>
                    
                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-primary btn-lg" id="submitBtn">
                            <i class="bi bi-check-circle"></i> I Agree - Authorize Scan
                        </button>
                        <a href="dashboard.html" class="btn btn-secondary">
                            <i class="bi bi-x-circle"></i> Cancel
                        </a>
                    </div>
                </form>
                
                <hr class="my-4">
                
                <div class="text-muted small">
                    <p><strong>Need Help?</strong></p>
                    <p>If you're unsure whether you have authorization to scan a target, contact the system owner 
                    or your organization's security team before proceeding.</p>
                    <p><strong>Reporting Issues:</strong> If you believe someone is using this service for 
                    unauthorized scanning, please contact: security@aegisrecon.example.com</p>
                </div>
            </div>
        </div>
        
        <div class="text-center mt-3">
            <p class="text-white small">
                <i class="bi bi-shield-check"></i> Your privacy and legal compliance are our priority
            </p>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Form validation
        document.getElementById('consentForm').addEventListener('submit', function(e) {
            const ownership = document.getElementById('ownership_confirmed').checked;
            const consent = document.getElementById('consent_confirmed').checked;
            
            if (!ownership || !consent) {
                e.preventDefault();
                alert('You must confirm ownership/authorization and agree to the terms to proceed.');
                return false;
            }
            
            // Confirm submission
            if (!confirm('Are you absolutely certain you have authorization to scan this target?')) {
                e.preventDefault();
                return false;
            }
        });
    </script>
</body>
</html>
