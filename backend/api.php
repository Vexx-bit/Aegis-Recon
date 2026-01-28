<?php
/**
 * Aegis Recon - API Backend
 * Secure REST API for managing security scan jobs
 * 
 * Endpoints:
 * - POST /api.php?action=enqueue - Queue a new scan job
 * - GET /api.php?action=status&job_id={id} - Get scan status
 * - GET /api.php?action=result&job_id={id} - Get scan results
 */

// Error reporting for development (disable in production)
error_reporting(E_ALL);
ini_set('display_errors', 0);
ini_set('log_errors', 1);
ini_set('error_log', __DIR__ . '/logs/php_errors.log');

// CORS headers (adjust for production)
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, X-API-KEY');
header('Content-Type: application/json');

// Handle preflight requests
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Load environment variables
require_once __DIR__ . '/config/env.php';

// Database configuration
require_once __DIR__ . '/config/database.php';

/**
 * Send JSON response and exit
 */
function sendResponse($data, $statusCode = 200) {
    http_response_code($statusCode);
    echo json_encode($data, JSON_PRETTY_PRINT);
    exit();
}

/**
 * Send error response
 */
function sendError($message, $statusCode = 400, $errorCode = null) {
    sendResponse([
        'success' => false,
        'error' => $message,
        'error_code' => $errorCode,
        'timestamp' => date('c')
    ], $statusCode);
}

/**
 * Validate API key from request headers
 */
function validateApiKey() {
    $headers = getallheaders();
    $apiKey = $headers['X-API-KEY'] ?? $headers['X-Api-Key'] ?? null;
    
    if (!$apiKey) {
        sendError('Missing API key. Include X-API-KEY header.', 401, 'MISSING_API_KEY');
    }
    
    $validApiKey = getenv('API_KEY') ?: 'your-secret-api-key-here';
    
    if ($apiKey !== $validApiKey) {
        sendError('Invalid API key', 403, 'INVALID_API_KEY');
    }
    
    return true;
}

/**
 * Sanitize domain input
 */
function sanitizeDomain($domain) {
    // Remove whitespace
    $domain = trim($domain);
    
    // Basic validation
    if (empty($domain)) {
        return null;
    }
    
    // Remove protocol if present
    $domain = preg_replace('#^https?://#i', '', $domain);
    
    // Remove trailing slashes
    $domain = rtrim($domain, '/');
    
    // Validate domain/IP format
    if (!filter_var($domain, FILTER_VALIDATE_DOMAIN, FILTER_FLAG_HOSTNAME) && 
        !filter_var($domain, FILTER_VALIDATE_IP)) {
        return null;
    }
    
    return $domain;
}

/**
 * Generate unique job ID
 */
function generateJobId() {
    return 'scan_' . uniqid() . '_' . bin2hex(random_bytes(4));
}

/**
 * Check if valid consent exists for user and domain
 */
function checkConsent($db, $userId, $domain) {
    try {
        $stmt = $db->prepare(
            "SELECT id, created_at, expires_at 
             FROM scan_consents 
             WHERE user_id = ? 
               AND target_domain = ? 
               AND revoked = FALSE 
               AND NOW() <= expires_at
             ORDER BY created_at DESC 
             LIMIT 1"
        );
        
        $stmt->bind_param('ss', $userId, $domain);
        $stmt->execute();
        $result = $stmt->get_result();
        
        if ($result->num_rows > 0) {
            $consent = $result->fetch_assoc();
            $stmt->close();
            
            // Log consent usage (optional)
            error_log("Consent validated for user {$userId} and domain {$domain}");
            
            return true;
        }
        
        $stmt->close();
        return false;
        
    } catch (Exception $e) {
        error_log('Consent check error: ' . $e->getMessage());
        return false;
    }
}

/**
 * Execute Python scan worker asynchronously
 */
function executeScanAsync($domain, $jobId, $useMock = false) {
    // Use enhanced worker for better results
    $pythonScript = realpath(__DIR__ . '/../ai_services/scan_worker_enhanced.py');
    
    // Fallback to original worker if enhanced not found
    if (!file_exists($pythonScript)) {
        $pythonScript = realpath(__DIR__ . '/../ai_services/scan_worker.py');
    }
    
    if (!file_exists($pythonScript)) {
        throw new Exception('Scan worker script not found');
    }
    
    // Escape arguments for shell
    $domainEscaped = escapeshellarg($domain);
    $jobIdEscaped = escapeshellarg($jobId);
    
    // Build command
    $pythonExe = 'python3'; // Use 'python' on Windows if python3 not available
    if (strtoupper(substr(PHP_OS, 0, 3)) === 'WIN') {
        $pythonExe = 'python';
    }
    
    // Add mock flag if testing with 127.0.0.1
    $mockFlag = ($useMock || $domain === '127.0.0.1') ? '--mock' : '';
    
    $command = sprintf(
        '%s %s %s --job-id=%s %s > %s 2>&1 &',
        $pythonExe,
        escapeshellarg($pythonScript),
        $domainEscaped,
        $jobIdEscaped,
        $mockFlag,
        escapeshellarg(__DIR__ . "/logs/scan_{$jobId}.log")
    );
    
    // Execute asynchronously
    if (strtoupper(substr(PHP_OS, 0, 3)) === 'WIN') {
        // Windows: use START command for background execution
        $command = sprintf(
            'start /B %s %s %s --job-id=%s > %s 2>&1',
            $pythonExe,
            escapeshellarg($pythonScript),
            $domainEscaped,
            $jobIdEscaped,
            escapeshellarg(__DIR__ . "/logs/scan_{$jobId}.log")
        );
        pclose(popen($command, 'r'));
    } else {
        // Unix/Linux: use & for background execution
        exec($command);
    }
    
    return true;
}

/**
 * Endpoint: Enqueue a new scan job
 */
function handleEnqueue($db) {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        sendError('Method not allowed. Use POST.', 405, 'METHOD_NOT_ALLOWED');
    }
    
    // Get POST data
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (!$input) {
        // Try form data
        $input = $_POST;
    }
    
    $domain = $input['domain'] ?? null;
    
    if (!$domain) {
        sendError('Missing required parameter: domain', 400, 'MISSING_DOMAIN');
    }
    
    // Sanitize domain
    $domain = sanitizeDomain($domain);
    
    if (!$domain) {
        sendError('Invalid domain format', 400, 'INVALID_DOMAIN');
    }
    
    // Get user_id from input (or session in production)
    $userId = $input['user_id'] ?? 'dev_user';  // Default for development
    
    // DEVELOPMENT MODE: Consent check disabled for testing
    // TODO: Re-enable consent check in production
    /*
    if (!$userId) {
        sendError('Missing user_id. Please provide consent first.', 400, 'MISSING_USER_ID');
    }
    
    // Check for valid consent within last 24 hours
    if (!checkConsent($db, $userId, $domain)) {
        sendError(
            'No valid consent found for this user and domain. Please provide consent at /frontend/consent.php before scanning.',
            403,
            'CONSENT_REQUIRED'
        );
    }
    */
    
    // Generate job ID
    $jobId = generateJobId();
    
    try {
        // Insert into database
        $stmt = $db->prepare(
            "INSERT INTO scans (job_id, target_domain, status, created_at, updated_at) 
             VALUES (?, ?, 'queued', NOW(), NOW())"
        );
        
        $stmt->bind_param('ss', $jobId, $domain);
        
        if (!$stmt->execute()) {
            throw new Exception('Failed to create scan record: ' . $stmt->error);
        }
        
        $stmt->close();
        
        // Execute scan asynchronously
        executeScanAsync($domain, $jobId);
        
        // Update status to running
        $stmt = $db->prepare(
            "UPDATE scans SET status = 'running', updated_at = NOW() WHERE job_id = ?"
        );
        $stmt->bind_param('s', $jobId);
        $stmt->execute();
        $stmt->close();
        
        // Return response
        sendResponse([
            'success' => true,
            'job_id' => $jobId,
            'target' => $domain,
            'status' => 'running',
            'message' => 'Scan job queued successfully',
            'timestamp' => date('c')
        ], 201);
        
    } catch (Exception $e) {
        error_log('Enqueue error: ' . $e->getMessage());
        sendError('Failed to enqueue scan: ' . $e->getMessage(), 500, 'ENQUEUE_FAILED');
    }
}

/**
 * Endpoint: Get scan status
 */
function handleStatus($db) {
    if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
        sendError('Method not allowed. Use GET.', 405, 'METHOD_NOT_ALLOWED');
    }
    
    $jobId = $_GET['job_id'] ?? null;
    
    if (!$jobId) {
        sendError('Missing required parameter: job_id', 400, 'MISSING_JOB_ID');
    }
    
    // Sanitize job_id
    $jobId = preg_replace('/[^a-zA-Z0-9_-]/', '', $jobId);
    
    try {
        $stmt = $db->prepare(
            "SELECT job_id, target_domain, status, created_at, updated_at, 
                    completed_at, error_message, progress_data 
             FROM scans 
             WHERE job_id = ?"
        );
        
        $stmt->bind_param('s', $jobId);
        $stmt->execute();
        $result = $stmt->get_result();
        
        if ($result->num_rows === 0) {
            sendError('Scan job not found', 404, 'JOB_NOT_FOUND');
        }
        
        $scan = $result->fetch_assoc();
        $stmt->close();
        
        // Parse progress data if available
        $progress = null;
        if (!empty($scan['progress_data'])) {
            $progress = json_decode($scan['progress_data'], true);
        }
        
        // Check if results file exists for completed scans
        $resultsFile = "/tmp/results-{$jobId}.json";
        $hasResults = file_exists($resultsFile);
        
        sendResponse([
            'success' => true,
            'job_id' => $scan['job_id'],
            'target' => $scan['target_domain'],
            'status' => $scan['status'],
            'has_results' => $hasResults,
            'progress' => $progress,
            'created_at' => $scan['created_at'],
            'updated_at' => $scan['updated_at'],
            'completed_at' => $scan['completed_at'],
            'error_message' => $scan['error_message'],
            'timestamp' => date('c')
        ]);
        
    } catch (Exception $e) {
        error_log('Status error: ' . $e->getMessage());
        sendError('Failed to retrieve status: ' . $e->getMessage(), 500, 'STATUS_FAILED');
    }
}

/**
 * Endpoint: Get scan results
 */
function handleResult($db) {
    if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
        sendError('Method not allowed. Use GET.', 405, 'METHOD_NOT_ALLOWED');
    }
    
    $jobId = $_GET['job_id'] ?? null;
    
    if (!$jobId) {
        sendError('Missing required parameter: job_id', 400, 'MISSING_JOB_ID');
    }
    
    // Sanitize job_id
    $jobId = preg_replace('/[^a-zA-Z0-9_-]/', '', $jobId);
    
    try {
        // Check if scan exists and is completed
        $stmt = $db->prepare(
            "SELECT job_id, target_domain, status, results 
             FROM scans 
             WHERE job_id = ?"
        );
        
        $stmt->bind_param('s', $jobId);
        $stmt->execute();
        $result = $stmt->get_result();
        
        if ($result->num_rows === 0) {
            sendError('Scan job not found', 404, 'JOB_NOT_FOUND');
        }
        
        $scan = $result->fetch_assoc();
        $stmt->close();
        
        if ($scan['status'] !== 'done' && $scan['status'] !== 'completed') {
            sendError(
                'Scan not completed yet. Current status: ' . $scan['status'], 
                400, 
                'SCAN_NOT_COMPLETED'
            );
        }
        
        // Try to get results from database first
        if (!empty($scan['results'])) {
            $results = json_decode($scan['results'], true);
            
            if ($results) {
                sendResponse([
                    'success' => true,
                    'job_id' => $jobId,
                    'results' => $results,
                    'source' => 'database',
                    'timestamp' => date('c')
                ]);
            }
        }
        
        // Try to get results from file
        $resultsFile = "/tmp/results-{$jobId}.json";
        
        if (file_exists($resultsFile)) {
            $resultsJson = file_get_contents($resultsFile);
            $results = json_decode($resultsJson, true);
            
            if ($results) {
                // Optionally store in database for future retrieval
                $stmt = $db->prepare(
                    "UPDATE scans SET result_json = ?, updated_at = NOW() WHERE job_id = ?"
                );
                $stmt->bind_param('ss', $resultsJson, $jobId);
                $stmt->execute();
                $stmt->close();
                
                sendResponse([
                    'success' => true,
                    'job_id' => $jobId,
                    'results' => $results,
                    'source' => 'file',
                    'timestamp' => date('c')
                ]);
            }
        }
        
        sendError('Results not available', 404, 'RESULTS_NOT_FOUND');
        
    } catch (Exception $e) {
        error_log('Result error: ' . $e->getMessage());
        sendError('Failed to retrieve results: ' . $e->getMessage(), 500, 'RESULT_FAILED');
    }
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================

try {
    // Validate API key
    validateApiKey();
    
    // Get database connection
    $db = getDatabaseConnection();
    
    // Get action parameter
    $action = $_GET['action'] ?? null;
    
    if (!$action) {
        sendError('Missing required parameter: action', 400, 'MISSING_ACTION');
    }
    
    // Route to appropriate handler
    switch ($action) {
        case 'enqueue':
            handleEnqueue($db);
            break;
            
        case 'status':
            handleStatus($db);
            break;
            
        case 'result':
            handleResult($db);
            break;
            
        default:
            sendError(
                'Invalid action. Valid actions: enqueue, status, result', 
                400, 
                'INVALID_ACTION'
            );
    }
    
    // Close database connection
    $db->close();
    
} catch (Exception $e) {
    error_log('API error: ' . $e->getMessage());
    sendError('Internal server error', 500, 'INTERNAL_ERROR');
}
