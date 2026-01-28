# Integration Guide — PHP ↔ Python ↔ Tools

## Overview
The PHP backend triggers asynchronous scan jobs. Python worker executes tools and returns normalized JSON. PHP stores JSON in MySQL and returns summarized results to frontend.

## Recommended endpoints (backend/api.php)
- POST /api/scan → enqueues a scan: returns `job_id`.
- GET /api/scan/status?job_id= → returns status
- GET /api/scan/result?job_id= → returns result JSON

## Example PHP → Python call
```php
$domain = escapeshellarg($_POST['domain']);
$cmd = "python3 ../ai_services/scan_worker.py $domain";
$job_output = shell_exec($cmd); // for synchronous calls in MVP; use queue in production
