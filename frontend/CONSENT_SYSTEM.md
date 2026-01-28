# Aegis Recon - Consent Management System

## Overview

The consent management system ensures legal compliance by requiring users to explicitly authorize security scans before they can be performed. This system implements a 24-hour consent window and maintains a complete audit trail.

---

## Components

### 1. Frontend Consent Form (`frontend/consent.php`)

**Purpose**: Collect legal consent from users before allowing scans.

**Features:**
- Legal terms and conditions display
- User email collection for accountability
- Target domain/IP input
- Ownership/authorization confirmation checkboxes
- IP address and user agent logging
- 24-hour consent validity period

**URL**: `http://localhost/Aegis%20Recon/frontend/consent.php`

### 2. Database Table (`scan_consents`)

**Schema:**
```sql
CREATE TABLE scan_consents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,           -- Hashed user identifier
    user_email VARCHAR(255) NOT NULL,       -- User email
    target_domain VARCHAR(255) NOT NULL,    -- Authorized domain/IP
    consent_text TEXT NOT NULL,             -- Full consent agreement
    ip_address VARCHAR(45) NOT NULL,        -- User's IP address
    user_agent TEXT NULL,                   -- Browser user agent
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP GENERATED ALWAYS AS (DATE_ADD(created_at, INTERVAL 24 HOUR)) STORED,
    revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP NULL,
    -- Indexes for performance
    INDEX idx_consent_validation (user_id, target_domain, expires_at, revoked)
);
```

### 3. API Enforcement (`backend/api.php`)

**Function**: `checkConsent($db, $userId, $domain)`

**Validation Rules:**
- User ID must be provided
- Domain must match consent record
- Consent must not be revoked
- Consent must not be expired (< 24 hours old)

**Error Response:**
```json
{
  "success": false,
  "error": "No valid consent found for this user and domain. Please provide consent at /frontend/consent.php before scanning.",
  "error_code": "CONSENT_REQUIRED"
}
```

---

## Workflow

### Step 1: User Provides Consent

1. User visits `frontend/consent.php`
2. Enters email address and target domain
3. Reads legal terms and conditions
4. Confirms ownership/authorization
5. Submits form
6. System records:
   - User ID (SHA-256 hash of email)
   - Email address
   - Target domain
   - Full consent text
   - IP address
   - User agent
   - Timestamp

### Step 2: Consent Validation

When user attempts to start a scan via API:

1. API receives scan request with `user_id` and `domain`
2. `checkConsent()` function queries database:
   ```sql
   SELECT * FROM scan_consents
   WHERE user_id = ?
     AND target_domain = ?
     AND revoked = FALSE
     AND NOW() <= expires_at
   ORDER BY created_at DESC
   LIMIT 1
   ```
3. If valid consent found → Scan proceeds
4. If no valid consent → Return 403 error

### Step 3: Scan Execution

Only after consent validation passes:
- Scan job is created in `scans` table
- Python scan worker is executed
- Results are stored and returned

---

## Usage Examples

### Provide Consent (Frontend)

1. Navigate to consent form:
   ```
   http://localhost/Aegis%20Recon/frontend/consent.php
   ```

2. Fill in form:
   - Email: `user@example.com`
   - Domain: `example.com`
   - Check both confirmation boxes
   - Submit

3. Consent is valid for 24 hours

### API Request with Consent

```javascript
// Get user_id (SHA-256 hash of email)
const userEmail = 'user@example.com';
const userId = await crypto.subtle.digest('SHA-256', 
    new TextEncoder().encode(userEmail)
).then(hash => 
    Array.from(new Uint8Array(hash))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('')
);

// Make API request
const response = await fetch('/backend/api.php?action=enqueue', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-API-KEY': 'your-api-key'
    },
    body: JSON.stringify({
        domain: 'example.com',
        user_id: userId
    })
});
```

### Check Existing Consents (SQL)

```sql
-- View all active consents
SELECT 
    user_email,
    target_domain,
    created_at,
    expires_at,
    TIMESTAMPDIFF(HOUR, NOW(), expires_at) as hours_remaining
FROM scan_consents
WHERE revoked = FALSE
  AND NOW() <= expires_at
ORDER BY created_at DESC;

-- Check specific user consent
SELECT * FROM scan_consents
WHERE user_id = 'user_hash'
  AND target_domain = 'example.com'
  AND revoked = FALSE
  AND NOW() <= expires_at;
```

---

## Legal Compliance

### Laws Addressed

1. **Computer Misuse and Cybercrimes Act (2018) - Kenya**
   - Requires authorization before accessing computer systems
   - Consent form documents authorization

2. **Data Protection Act (2019) - Kenya**
   - User data (email, IP) collected with explicit consent
   - Audit trail maintained

3. **Computer Fraud and Abuse Act (CFAA) - United States**
   - Requires authorization for computer access
   - Consent system provides documented authorization

### Consent Text

The system records the following consent agreement:

> "I confirm that I own or have explicit authorization to perform security scanning on the domain/IP: {domain}. I understand that unauthorized scanning may be illegal and agree to use Aegis Recon only for lawful purposes. I accept full responsibility for any scans performed."

### Audit Trail

Each consent record includes:
- ✅ User identification (email + hashed ID)
- ✅ Target domain/IP
- ✅ Full consent text
- ✅ Timestamp
- ✅ IP address
- ✅ User agent
- ✅ Expiration time (24 hours)
- ✅ Revocation status

---

## Administration

### Revoke Consent

```sql
UPDATE scan_consents
SET revoked = TRUE,
    revoked_at = NOW()
WHERE id = <consent_id>;
```

### Clean Up Expired Consents

```sql
-- Delete consents older than 90 days
DELETE FROM scan_consents
WHERE expires_at < DATE_SUB(NOW(), INTERVAL 90 DAY)
   OR (revoked = TRUE AND revoked_at < DATE_SUB(NOW(), INTERVAL 90 DAY));
```

### View Consent Statistics

```sql
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_consents,
    COUNT(DISTINCT user_email) as unique_users,
    COUNT(DISTINCT target_domain) as unique_targets
FROM scan_consents
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

---

## Security Considerations

1. **User ID Hashing**: Email addresses are hashed (SHA-256) for user_id to provide some privacy
2. **IP Logging**: IP addresses logged for accountability and fraud prevention
3. **24-Hour Expiration**: Limits consent window to reduce risk of stale authorizations
4. **Revocation Support**: Consents can be revoked if authorization is withdrawn
5. **Audit Trail**: Complete record of all consent activities

---

## Integration with Dashboard

Update `frontend/dashboard.html` JavaScript to include user_id:

```javascript
// Calculate user_id from email
async function hashEmail(email) {
    const encoder = new TextEncoder();
    const data = encoder.encode(email);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

// In scan submission
const userEmail = localStorage.getItem('user_email') || prompt('Enter your email:');
const userId = await hashEmail(userEmail);

const response = await fetch(`${API_BASE_URL}?action=enqueue`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-API-KEY': apiKey
    },
    body: JSON.stringify({ 
        domain: domain,
        user_id: userId 
    })
});
```

---

## Troubleshooting

### Error: "CONSENT_REQUIRED"

**Solution**: User must visit `frontend/consent.php` and provide consent before scanning.

### Error: "MISSING_USER_ID"

**Solution**: Include `user_id` in API request body.

### Consent Expired

**Solution**: Consent is only valid for 24 hours. User must provide consent again.

### Database Error

**Solution**: Ensure `scan_consents` table exists. Run:
```bash
php backend/init_database.php
```

---

## Future Enhancements

1. **Email Verification**: Send verification email before accepting consent
2. **Multi-Factor Authentication**: Require additional verification for high-risk scans
3. **Consent Templates**: Different consent levels for different scan types
4. **Automated Expiration Notices**: Email users when consent is about to expire
5. **Consent Dashboard**: Allow users to view and manage their consents
6. **API Key Linking**: Link consents to specific API keys for better tracking

---

## Support

For questions about the consent system:
- Review this documentation
- Check database logs
- Contact: security@aegisrecon.example.com
