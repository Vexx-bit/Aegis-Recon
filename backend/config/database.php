<?php
/**
 * Database Configuration and Connection
 */

/**
 * Get database connection
 * @return mysqli Database connection object
 * @throws Exception if connection fails
 */
function getDatabaseConnection() {
    // Database credentials from environment or defaults
    $host = getenv('DB_HOST') ?: 'localhost';
    $username = getenv('DB_USER') ?: 'root';
    $password = getenv('DB_PASS') ?: '';
    $database = getenv('DB_NAME') ?: 'aegis_recon';
    $port = getenv('DB_PORT') ?: 3306;
    
    // Create connection
    $conn = new mysqli($host, $username, $password, $database, $port);
    
    // Check connection
    if ($conn->connect_error) {
        error_log('Database connection failed: ' . $conn->connect_error);
        throw new Exception('Database connection failed');
    }
    
    // Set charset
    $conn->set_charset('utf8mb4');
    
    return $conn;
}

/**
 * Initialize database tables if they don't exist
 */
function initializeDatabase() {
    try {
        $db = getDatabaseConnection();
        
        // Create scans table
        $createTableSQL = "
        CREATE TABLE IF NOT EXISTS scans (
            id INT AUTO_INCREMENT PRIMARY KEY,
            job_id VARCHAR(100) UNIQUE NOT NULL,
            target_domain VARCHAR(255) NOT NULL,
            status ENUM('queued', 'running', 'done', 'completed', 'error', 'failed') DEFAULT 'queued',
            result_json LONGTEXT NULL,
            error_message TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            completed_at TIMESTAMP NULL,
            INDEX idx_job_id (job_id),
            INDEX idx_status (status),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        ";
        
        if (!$db->query($createTableSQL)) {
            throw new Exception('Failed to create scans table: ' . $db->error);
        }
        
        // Create scan_consents table
        $createConsentsSQL = "
        CREATE TABLE IF NOT EXISTS scan_consents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(64) NOT NULL COMMENT 'Hashed user identifier',
            user_email VARCHAR(255) NOT NULL COMMENT 'User email address',
            target_domain VARCHAR(255) NOT NULL COMMENT 'Domain or IP authorized for scanning',
            consent_text TEXT NOT NULL COMMENT 'Full text of consent agreement',
            ip_address VARCHAR(45) NOT NULL COMMENT 'IP address of user providing consent',
            user_agent TEXT NULL COMMENT 'Browser user agent string',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'When consent was provided',
            expires_at TIMESTAMP GENERATED ALWAYS AS (DATE_ADD(created_at, INTERVAL 24 HOUR)) STORED COMMENT 'When consent expires (24 hours)',
            revoked BOOLEAN DEFAULT FALSE COMMENT 'Whether consent has been revoked',
            revoked_at TIMESTAMP NULL COMMENT 'When consent was revoked',
            INDEX idx_user_id (user_id),
            INDEX idx_user_email (user_email),
            INDEX idx_target_domain (target_domain),
            INDEX idx_created_at (created_at),
            INDEX idx_expires_at (expires_at),
            INDEX idx_user_target (user_id, target_domain, created_at),
            INDEX idx_consent_validation (user_id, target_domain, expires_at, revoked)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        ";
        
        if (!$db->query($createConsentsSQL)) {
            throw new Exception('Failed to create scan_consents table: ' . $db->error);
        }
        
        $db->close();
        return true;
        
    } catch (Exception $e) {
        error_log('Database initialization error: ' . $e->getMessage());
        return false;
    }
}
