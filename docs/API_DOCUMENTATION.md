# Aegis Recon API Documentation

## Overview

The Aegis Recon API provides secure endpoints for managing security scan jobs. All endpoints require API key authentication.

**Base URL**: `http://localhost/Aegis%20Recon/backend/api.php`

---

## Authentication

All API requests must include an API key in the request headers:

```
X-API-KEY: your-secret-api-key-here
```

**Setup**: Configure your API key in the `.env` file:
```bash
API_KEY=your-secret-api-key-change-this-in-production
```

### Error Response (401 Unauthorized)
```json
{
  "success": false,
  "error": "Missing API key. Include X-API-KEY header.",
  "error_code": "MISSING_API_KEY",
  "timestamp": "2025-10-29T12:50:20+03:00"
}
```

---

## Endpoints

### 1. Enqueue Scan Job

Queue a new security scan for a domain or IP address.

**Endpoint**: `POST /api.php?action=enqueue`

**Headers**:
```
Content-Type: application/json
X-API-KEY: your-api-key
```

**Request Body**:
```json
{
  "domain": "example.com"
}
```

**Success Response** (201 Created):
```json
{
  "success": true,
  "job_id": "scan_6543210abc_1a2b3c4d",
  "target": "example.com",
  "status": "running",
  "message": "Scan job queued successfully",
  "timestamp": "2025-10-29T12:50:20+03:00"
}
```

**Error Responses**:

- **400 Bad Request** - Missing or invalid domain
```json
{
  "success": false,
  "error": "Missing required parameter: domain",
  "error_code": "MISSING_DOMAIN",
  "timestamp": "2025-10-29T12:50:20+03:00"
}
```

- **400 Bad Request** - Invalid domain format
```json
{
  "success": false,
  "error": "Invalid domain format",
  "error_code": "INVALID_DOMAIN",
  "timestamp": "2025-10-29T12:50:20+03:00"
}
```

**cURL Example**:
```bash
curl -X POST "http://localhost/Aegis%20Recon/backend/api.php?action=enqueue" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-api-key" \
  -d '{"domain": "example.com"}'
```

---

### 2. Check Scan Status

Retrieve the current status of a scan job.

**Endpoint**: `GET /api.php?action=status&job_id={job_id}`

**Headers**:
```
X-API-KEY: your-api-key
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "job_id": "scan_6543210abc_1a2b3c4d",
  "target": "example.com",
  "status": "running",
  "has_results": false,
  "created_at": "2025-10-29 12:50:20",
  "updated_at": "2025-10-29 12:51:15",
  "completed_at": null,
  "error_message": null,
  "timestamp": "2025-10-29T12:51:30+03:00"
}
```

**Status Values**:
- `queued` - Job is waiting to start
- `running` - Scan is in progress
- `done` / `completed` - Scan finished successfully
- `error` / `failed` - Scan encountered an error

**Error Responses**:

- **400 Bad Request** - Missing job_id
```json
{
  "success": false,
  "error": "Missing required parameter: job_id",
  "error_code": "MISSING_JOB_ID",
  "timestamp": "2025-10-29T12:50:20+03:00"
}
```

- **404 Not Found** - Job not found
```json
{
  "success": false,
  "error": "Scan job not found",
  "error_code": "JOB_NOT_FOUND",
  "timestamp": "2025-10-29T12:50:20+03:00"
}
```

**cURL Example**:
```bash
curl -X GET "http://localhost/Aegis%20Recon/backend/api.php?action=status&job_id=scan_6543210abc_1a2b3c4d" \
  -H "X-API-KEY: your-api-key"
```

---

### 3. Get Scan Results

Retrieve the complete results of a completed scan.

**Endpoint**: `GET /api.php?action=result&job_id={job_id}`

**Headers**:
```
X-API-KEY: your-api-key
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "job_id": "scan_6543210abc_1a2b3c4d",
  "results": {
    "job_id": "scan_6543210abc_1a2b3c4d",
    "target": "example.com",
    "hosts": [
      {
        "host": "example.com",
        "ports": [
          {
            "port": 80,
            "protocol": "tcp",
            "service": "http",
            "version": "nginx 1.14.0"
          },
          {
            "port": 443,
            "protocol": "tcp",
            "service": "https",
            "version": "nginx 1.14.0"
          }
        ],
        "web_vulns": [
          {
            "id": "000001",
            "method": "GET",
            "url": "http://example.com/",
            "msg": "Server leaks inodes via ETags",
            "osvdb": "3233"
          }
        ]
      }
    ],
    "metadata": {
      "scan_date": "2025-10-29T09:50:20Z",
      "total_hosts": 4,
      "total_ports": 12,
      "total_vulnerabilities": 5,
      "scanner_version": "1.0.0"
    }
  },
  "source": "database",
  "timestamp": "2025-10-29T12:55:30+03:00"
}
```

**Error Responses**:

- **400 Bad Request** - Scan not completed
```json
{
  "success": false,
  "error": "Scan not completed yet. Current status: running",
  "error_code": "SCAN_NOT_COMPLETED",
  "timestamp": "2025-10-29T12:50:20+03:00"
}
```

- **404 Not Found** - Results not available
```json
{
  "success": false,
  "error": "Results not available",
  "error_code": "RESULTS_NOT_FOUND",
  "timestamp": "2025-10-29T12:50:20+03:00"
}
```

**cURL Example**:
```bash
curl -X GET "http://localhost/Aegis%20Recon/backend/api.php?action=result&job_id=scan_6543210abc_1a2b3c4d" \
  -H "X-API-KEY: your-api-key"
```

---

## Complete Workflow Example

### Step 1: Start a Scan
```bash
RESPONSE=$(curl -s -X POST "http://localhost/Aegis%20Recon/backend/api.php?action=enqueue" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-api-key" \
  -d '{"domain": "example.com"}')

JOB_ID=$(echo $RESPONSE | jq -r '.job_id')
echo "Job ID: $JOB_ID"
```

### Step 2: Poll for Status
```bash
while true; do
  STATUS=$(curl -s "http://localhost/Aegis%20Recon/backend/api.php?action=status&job_id=$JOB_ID" \
    -H "X-API-KEY: your-api-key" | jq -r '.status')
  
  echo "Current status: $STATUS"
  
  if [ "$STATUS" = "done" ] || [ "$STATUS" = "completed" ]; then
    break
  fi
  
  sleep 10
done
```

### Step 3: Retrieve Results
```bash
curl -s "http://localhost/Aegis%20Recon/backend/api.php?action=result&job_id=$JOB_ID" \
  -H "X-API-KEY: your-api-key" | jq '.'
```

---

## Error Codes Reference

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `MISSING_API_KEY` | 401 | API key not provided in headers |
| `INVALID_API_KEY` | 403 | API key is invalid |
| `MISSING_ACTION` | 400 | Action parameter not specified |
| `INVALID_ACTION` | 400 | Invalid action value |
| `METHOD_NOT_ALLOWED` | 405 | Wrong HTTP method used |
| `MISSING_DOMAIN` | 400 | Domain parameter not provided |
| `INVALID_DOMAIN` | 400 | Domain format is invalid |
| `MISSING_JOB_ID` | 400 | Job ID parameter not provided |
| `JOB_NOT_FOUND` | 404 | Scan job does not exist |
| `SCAN_NOT_COMPLETED` | 400 | Results not ready yet |
| `RESULTS_NOT_FOUND` | 404 | Results file not found |
| `ENQUEUE_FAILED` | 500 | Failed to create scan job |
| `STATUS_FAILED` | 500 | Failed to retrieve status |
| `RESULT_FAILED` | 500 | Failed to retrieve results |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## Rate Limiting

Currently, rate limiting is not enforced. For production use, consider implementing:
- Per-API-key rate limits
- IP-based rate limiting
- Request throttling

---

## Security Best Practices

1. **Always use HTTPS in production**
2. **Rotate API keys regularly**
3. **Store API keys in environment variables, never in code**
4. **Implement IP whitelisting for sensitive operations**
5. **Monitor API usage and set up alerts**
6. **Sanitize all user inputs**
7. **Keep scan results encrypted at rest**

---

## Testing with Postman

### Collection Setup

1. Create a new collection: "Aegis Recon API"
2. Add environment variable: `api_key` = your API key
3. Add environment variable: `base_url` = `http://localhost/Aegis%20Recon/backend/api.php`

### Request Examples

**Enqueue Scan**:
- Method: POST
- URL: `{{base_url}}?action=enqueue`
- Headers: `X-API-KEY: {{api_key}}`
- Body (JSON): `{"domain": "example.com"}`

**Check Status**:
- Method: GET
- URL: `{{base_url}}?action=status&job_id={{job_id}}`
- Headers: `X-API-KEY: {{api_key}}`

**Get Results**:
- Method: GET
- URL: `{{base_url}}?action=result&job_id={{job_id}}`
- Headers: `X-API-KEY: {{api_key}}`

---

## Troubleshooting

### Issue: "Database connection failed"
**Solution**: Check database credentials in `.env` file and ensure MySQL is running.

### Issue: "Scan worker script not found"
**Solution**: Verify that `ai_services/scan_worker.py` exists and is executable.

### Issue: "ALLOW_SCANS environment variable not set"
**Solution**: Add `ALLOW_SCANS=1` to your `.env` file.

### Issue: Results not found after scan completes
**Solution**: Check `/tmp/results-{job_id}.json` exists and has proper permissions.

---

## Support

For issues or questions:
- Check logs in `backend/logs/php_errors.log`
- Review scan logs in `backend/logs/scan_{job_id}.log`
- Verify database connectivity
- Ensure all dependencies are installed
