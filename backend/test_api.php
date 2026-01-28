<?php
/**
 * API Test Script
 * Simple script to test API endpoints
 */

// Configuration
$baseUrl = 'http://localhost/Aegis%20Recon/backend/api.php';
$apiKey = 'your-secret-api-key-change-this-in-production'; // Change this to match your .env

echo "=============================================================\n";
echo "Aegis Recon - API Test Suite\n";
echo "=============================================================\n\n";

/**
 * Make API request
 */
function makeRequest($url, $method = 'GET', $data = null, $apiKey = null) {
    $ch = curl_init();
    
    $headers = [
        'Content-Type: application/json',
        'X-API-KEY: ' . $apiKey
    ];
    
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
    if ($method === 'POST') {
        curl_setopt($ch, CURLOPT_POST, true);
        if ($data) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }
    }
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    
    curl_close($ch);
    
    if ($error) {
        return ['error' => $error, 'http_code' => $httpCode];
    }
    
    return [
        'http_code' => $httpCode,
        'response' => json_decode($response, true)
    ];
}

// Test 1: Enqueue a scan
echo "[Test 1] Enqueue Scan Job\n";
echo "-----------------------------------------------------------\n";

$result = makeRequest(
    $baseUrl . '?action=enqueue',
    'POST',
    ['domain' => 'example.com'],
    $apiKey
);

if ($result['http_code'] === 201) {
    echo "✓ Status: {$result['http_code']} Created\n";
    $jobId = $result['response']['job_id'];
    echo "✓ Job ID: $jobId\n";
    echo "✓ Target: {$result['response']['target']}\n";
    echo "✓ Status: {$result['response']['status']}\n";
} else {
    echo "✗ Failed with status: {$result['http_code']}\n";
    echo "Response: " . json_encode($result['response'], JSON_PRETTY_PRINT) . "\n";
    exit(1);
}

echo "\n";

// Test 2: Check status
echo "[Test 2] Check Scan Status\n";
echo "-----------------------------------------------------------\n";

sleep(2); // Wait a bit

$result = makeRequest(
    $baseUrl . '?action=status&job_id=' . urlencode($jobId),
    'GET',
    null,
    $apiKey
);

if ($result['http_code'] === 200) {
    echo "✓ Status: {$result['http_code']} OK\n";
    echo "✓ Job ID: {$result['response']['job_id']}\n";
    echo "✓ Target: {$result['response']['target']}\n";
    echo "✓ Status: {$result['response']['status']}\n";
    echo "✓ Has Results: " . ($result['response']['has_results'] ? 'Yes' : 'No') . "\n";
} else {
    echo "✗ Failed with status: {$result['http_code']}\n";
    echo "Response: " . json_encode($result['response'], JSON_PRETTY_PRINT) . "\n";
}

echo "\n";

// Test 3: Try to get results (will likely fail as scan is still running)
echo "[Test 3] Get Scan Results (Expected to fail if not done)\n";
echo "-----------------------------------------------------------\n";

$result = makeRequest(
    $baseUrl . '?action=result&job_id=' . urlencode($jobId),
    'GET',
    null,
    $apiKey
);

if ($result['http_code'] === 200) {
    echo "✓ Status: {$result['http_code']} OK\n";
    echo "✓ Results retrieved successfully\n";
    echo "✓ Total hosts: {$result['response']['results']['metadata']['total_hosts']}\n";
} else {
    echo "⚠ Status: {$result['http_code']} - {$result['response']['error']}\n";
    echo "  (This is expected if scan is still running)\n";
}

echo "\n";

// Test 4: Test invalid API key
echo "[Test 4] Test Invalid API Key\n";
echo "-----------------------------------------------------------\n";

$result = makeRequest(
    $baseUrl . '?action=status&job_id=' . urlencode($jobId),
    'GET',
    null,
    'invalid-key'
);

if ($result['http_code'] === 403) {
    echo "✓ Status: {$result['http_code']} Forbidden (as expected)\n";
    echo "✓ Error: {$result['response']['error']}\n";
} else {
    echo "✗ Unexpected status: {$result['http_code']}\n";
}

echo "\n";

// Test 5: Test missing action
echo "[Test 5] Test Missing Action Parameter\n";
echo "-----------------------------------------------------------\n";

$result = makeRequest(
    $baseUrl,
    'GET',
    null,
    $apiKey
);

if ($result['http_code'] === 400) {
    echo "✓ Status: {$result['http_code']} Bad Request (as expected)\n";
    echo "✓ Error: {$result['response']['error']}\n";
} else {
    echo "✗ Unexpected status: {$result['http_code']}\n";
}

echo "\n";

echo "=============================================================\n";
echo "API Test Suite Completed\n";
echo "=============================================================\n\n";

echo "Summary:\n";
echo "- Job ID created: $jobId\n";
echo "- Check scan progress with: ?action=status&job_id=$jobId\n";
echo "- Get results when done with: ?action=result&job_id=$jobId\n\n";
