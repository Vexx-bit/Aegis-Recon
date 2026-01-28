-- ============================================================================
-- Aegis Recon - Database Schema
-- MySQL/MariaDB Database Schema for Scan Management
-- ============================================================================

-- Create database
CREATE DATABASE IF NOT EXISTS aegis_recon
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE aegis_recon;

-- ============================================================================
-- Table: scans
-- Stores scan job information and results
-- ============================================================================

CREATE TABLE IF NOT EXISTS scans (
    -- Primary key
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Job identification
    job_id VARCHAR(100) UNIQUE NOT NULL COMMENT 'Unique job identifier',
    
    -- Target information
    target_domain VARCHAR(255) NOT NULL COMMENT 'Domain or IP address to scan',
    
    -- Status tracking
    status ENUM('queued', 'running', 'done', 'completed', 'error', 'failed') 
        DEFAULT 'queued' 
        COMMENT 'Current status of the scan job',
    
    -- Results storage
    result_json LONGTEXT NULL COMMENT 'JSON-encoded scan results',
    
    -- Error handling
    error_message TEXT NULL COMMENT 'Error message if scan failed',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'When job was created',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last update time',
    completed_at TIMESTAMP NULL COMMENT 'When scan completed',
    
    -- Indexes for performance
    INDEX idx_job_id (job_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_target (target_domain)
    
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Scan job tracking and results';

-- ============================================================================
-- Table: scan_hosts (Optional - for detailed host tracking)
-- Stores individual host results from multi-host scans
-- ============================================================================

CREATE TABLE IF NOT EXISTS scan_hosts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Foreign key to scans table
    scan_id INT NOT NULL,
    job_id VARCHAR(100) NOT NULL,
    
    -- Host information
    host_address VARCHAR(255) NOT NULL COMMENT 'IP address or hostname',
    hostname VARCHAR(255) NULL COMMENT 'Resolved hostname',
    host_state ENUM('up', 'down', 'unknown') DEFAULT 'unknown',
    
    -- OS detection
    os_detection VARCHAR(500) NULL COMMENT 'Detected operating system',
    
    -- Port count summary
    open_ports_count INT DEFAULT 0,
    vulnerabilities_count INT DEFAULT 0,
    
    -- Detailed results
    ports_json TEXT NULL COMMENT 'JSON array of port details',
    vulnerabilities_json TEXT NULL COMMENT 'JSON array of vulnerabilities',
    
    -- Timestamps
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_scan_id (scan_id),
    INDEX idx_job_id (job_id),
    INDEX idx_host (host_address),
    
    -- Foreign key constraint
    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
    
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Individual host scan results';

-- ============================================================================
-- Table: api_keys (Optional - for multi-user API key management)
-- ============================================================================

CREATE TABLE IF NOT EXISTS api_keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- API key information
    api_key VARCHAR(64) UNIQUE NOT NULL COMMENT 'API key hash',
    key_name VARCHAR(100) NOT NULL COMMENT 'Descriptive name for the key',
    
    -- User/owner information
    owner_email VARCHAR(255) NULL,
    
    -- Status and limits
    is_active BOOLEAN DEFAULT TRUE,
    rate_limit INT DEFAULT 100 COMMENT 'Requests per hour',
    
    -- Usage tracking
    total_requests INT DEFAULT 0,
    last_used_at TIMESTAMP NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL COMMENT 'Expiration date (NULL = never)',
    
    -- Indexes
    INDEX idx_api_key (api_key),
    INDEX idx_active (is_active)
    
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='API key management';

-- ============================================================================
-- Sample Data (for testing)
-- ============================================================================

-- Insert a test scan record
INSERT INTO scans (job_id, target_domain, status, created_at) 
VALUES 
    ('scan_test_001', 'example.com', 'queued', NOW()),
    ('scan_test_002', '192.168.1.1', 'completed', NOW())
ON DUPLICATE KEY UPDATE job_id=job_id;

-- ============================================================================
-- Useful Queries
-- ============================================================================

-- Get all pending scans
-- SELECT * FROM scans WHERE status IN ('queued', 'running') ORDER BY created_at;

-- Get scan statistics
-- SELECT 
--     status, 
--     COUNT(*) as count,
--     AVG(TIMESTAMPDIFF(SECOND, created_at, completed_at)) as avg_duration_seconds
-- FROM scans 
-- WHERE completed_at IS NOT NULL
-- GROUP BY status;

-- Clean up old completed scans (older than 30 days)
-- DELETE FROM scans 
-- WHERE status = 'completed' 
-- AND completed_at < DATE_SUB(NOW(), INTERVAL 30 DAY);

-- ============================================================================
-- Maintenance
-- ============================================================================

-- Create stored procedure to clean old scans
DELIMITER //

CREATE PROCEDURE IF NOT EXISTS cleanup_old_scans(IN days_old INT)
BEGIN
    DELETE FROM scans 
    WHERE status IN ('completed', 'done', 'error', 'failed')
    AND completed_at < DATE_SUB(NOW(), INTERVAL days_old DAY);
    
    SELECT ROW_COUNT() as deleted_rows;
END //

DELIMITER ;

-- Usage: CALL cleanup_old_scans(30);
