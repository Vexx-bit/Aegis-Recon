-- ============================================================================
-- Aegis Recon - Consent Management Schema
-- MySQL/MariaDB Schema for Legal Consent Tracking
-- ============================================================================

USE aegis_recon;

-- ============================================================================
-- Table: scan_consents
-- Stores legal consent records for authorized security scanning
-- ============================================================================

CREATE TABLE IF NOT EXISTS scan_consents (
    -- Primary key
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- User identification
    user_id VARCHAR(64) NOT NULL COMMENT 'Hashed user identifier',
    user_email VARCHAR(255) NOT NULL COMMENT 'User email address',
    
    -- Target information
    target_domain VARCHAR(255) NOT NULL COMMENT 'Domain or IP authorized for scanning',
    
    -- Consent details
    consent_text TEXT NOT NULL COMMENT 'Full text of consent agreement',
    
    -- Audit information
    ip_address VARCHAR(45) NOT NULL COMMENT 'IP address of user providing consent',
    user_agent TEXT NULL COMMENT 'Browser user agent string',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'When consent was provided',
    expires_at TIMESTAMP GENERATED ALWAYS AS (DATE_ADD(created_at, INTERVAL 24 HOUR)) STORED COMMENT 'When consent expires (24 hours)',
    
    -- Status
    revoked BOOLEAN DEFAULT FALSE COMMENT 'Whether consent has been revoked',
    revoked_at TIMESTAMP NULL COMMENT 'When consent was revoked',
    
    -- Indexes for performance
    INDEX idx_user_id (user_id),
    INDEX idx_user_email (user_email),
    INDEX idx_target_domain (target_domain),
    INDEX idx_created_at (created_at),
    INDEX idx_expires_at (expires_at),
    INDEX idx_user_target (user_id, target_domain, created_at),
    
    -- Composite index for consent validation
    INDEX idx_consent_validation (user_id, target_domain, expires_at, revoked)
    
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Legal consent records for authorized security scanning';

-- ============================================================================
-- Table: consent_audit_log (Optional - for detailed audit trail)
-- ============================================================================

CREATE TABLE IF NOT EXISTS consent_audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    consent_id INT NOT NULL,
    action ENUM('created', 'used', 'revoked', 'expired') NOT NULL,
    scan_job_id VARCHAR(100) NULL COMMENT 'Associated scan job if applicable',
    ip_address VARCHAR(45) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_consent_id (consent_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at),
    
    FOREIGN KEY (consent_id) REFERENCES scan_consents(id) ON DELETE CASCADE
    
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Audit log for consent usage and modifications';

-- ============================================================================
-- Stored Procedures
-- ============================================================================

-- Check if valid consent exists for user and domain
DELIMITER //

CREATE PROCEDURE IF NOT EXISTS check_consent(
    IN p_user_id VARCHAR(64),
    IN p_target_domain VARCHAR(255)
)
BEGIN
    SELECT 
        id,
        user_email,
        target_domain,
        created_at,
        expires_at,
        CASE 
            WHEN revoked = TRUE THEN 'revoked'
            WHEN NOW() > expires_at THEN 'expired'
            ELSE 'valid'
        END as status
    FROM scan_consents
    WHERE user_id = p_user_id
      AND target_domain = p_target_domain
      AND revoked = FALSE
      AND NOW() <= expires_at
    ORDER BY created_at DESC
    LIMIT 1;
END //

-- Revoke consent
CREATE PROCEDURE IF NOT EXISTS revoke_consent(
    IN p_consent_id INT
)
BEGIN
    UPDATE scan_consents
    SET revoked = TRUE,
        revoked_at = NOW()
    WHERE id = p_consent_id
      AND revoked = FALSE;
    
    SELECT ROW_COUNT() as affected_rows;
END //

-- Clean up expired consents (run periodically)
CREATE PROCEDURE IF NOT EXISTS cleanup_expired_consents(
    IN p_days_old INT
)
BEGIN
    DELETE FROM scan_consents
    WHERE expires_at < DATE_SUB(NOW(), INTERVAL p_days_old DAY)
      OR (revoked = TRUE AND revoked_at < DATE_SUB(NOW(), INTERVAL p_days_old DAY));
    
    SELECT ROW_COUNT() as deleted_rows;
END //

DELIMITER ;

-- ============================================================================
-- Sample Queries
-- ============================================================================

-- Get all active consents for a user
-- SELECT * FROM scan_consents 
-- WHERE user_id = 'user_hash' 
--   AND revoked = FALSE 
--   AND NOW() <= expires_at
-- ORDER BY created_at DESC;

-- Get consent statistics
-- SELECT 
--     DATE(created_at) as date,
--     COUNT(*) as total_consents,
--     COUNT(DISTINCT user_id) as unique_users,
--     COUNT(DISTINCT target_domain) as unique_targets
-- FROM scan_consents
-- WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
-- GROUP BY DATE(created_at)
-- ORDER BY date DESC;

-- Find expired consents
-- SELECT * FROM scan_consents
-- WHERE NOW() > expires_at
--   AND revoked = FALSE
-- ORDER BY expires_at DESC;

-- ============================================================================
-- Initial Setup
-- ============================================================================

-- Grant necessary permissions (adjust username as needed)
-- GRANT SELECT, INSERT, UPDATE ON aegis_recon.scan_consents TO 'aegis_user'@'localhost';
-- GRANT SELECT, INSERT ON aegis_recon.consent_audit_log TO 'aegis_user'@'localhost';
-- GRANT EXECUTE ON PROCEDURE aegis_recon.check_consent TO 'aegis_user'@'localhost';
-- GRANT EXECUTE ON PROCEDURE aegis_recon.revoke_consent TO 'aegis_user'@'localhost';
